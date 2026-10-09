# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Dict

import torch
import numpy as np
import torch.distributed as dist
from safetensors.torch import load_file
import json
from pathlib import Path

from src.tokenizer import Tokenizer
from src.inference.base import BaseInference
from src.inference.task_types import TaskTypes
from src.inference.model_outputs import (
    MaskedLMOutput,
    MutationPredictionOutput,
    FitnessPredictionOutput,
    EmbeddingOutput,
    DownstreamPredictionOutput,
)
from src.models.encodon_pl import EncodonPL
from src.data.metadata import MetadataFields
from src.utils.checkpoints import load_trusted_checkpoint


class EncodonInference(BaseInference):
    """Inference class for Encodon models."""
    
    def configure_model(self):
        """Loads the model and tokenizer for inference."""
        if self.model is not None:
            return
        self.tokenizer = Tokenizer()
        
        state_dict = None
        hparams = None
        
        # Expect a full file path to either a .ckpt or a .safetensors file
        model_path = Path(self.model_path)
        if model_path.suffix.lower() not in [".ckpt", ".safetensors"]:
            raise ValueError(
                f"Expected a file path to a .ckpt or .safetensors file, got: {self.model_path}"
            )
        if not model_path.is_file():
            raise FileNotFoundError(f"Model file not found at {self.model_path}")

        suffix = model_path.suffix.lower()
        if suffix == ".safetensors":
            # Ensure config.json exists in the same directory
            config_path = model_path.parent / "config.json"
            if not config_path.exists():
                raise FileNotFoundError(
                    f"config.json is required to load safetensors checkpoint at: {config_path}"
                )
            if dist.is_initialized():
                broadcasted_objects = [None, None]
                if dist.get_rank() == 0:
                    state_dict = load_file(str(model_path))
                    with open(config_path, 'r') as f:
                        hparams = json.load(f)
                    broadcasted_objects = [state_dict, hparams]
                dist.broadcast_object_list(broadcasted_objects, src=0)
                state_dict, hparams = broadcasted_objects
            else:
                state_dict = load_file(str(model_path))
                with open(config_path, 'r') as f:
                    hparams = json.load(f)
        elif suffix == ".ckpt":
            # Load from PyTorch Lightning checkpoint
            if dist.is_initialized():
                broadcasted_objects = [None, None]
                if dist.get_rank() == 0:
                    ckpt = load_trusted_checkpoint(self.model_path)
                    hparams = ckpt.get("hyper_parameters")
                    state_dict = ckpt.get("state_dict")
                    broadcasted_objects = [state_dict, hparams]
                dist.broadcast_object_list(broadcasted_objects, src=0)
                state_dict, hparams = broadcasted_objects
            else:
                ckpt = load_trusted_checkpoint(self.model_path)
                hparams = ckpt.get("hyper_parameters")
                state_dict = ckpt.get("state_dict")
        else:
            raise ValueError(
                f"Unsupported model file type: {suffix}. Expected .ckpt or .safetensors"
            )

        if hparams is None:
            raise ValueError(
                f"Failed to load hyperparameters from checkpoint at '{self.model_path}'."
            )
        if state_dict is None:
            raise ValueError(
                f"Failed to load state_dict from checkpoint at '{self.model_path}'."
            )

        # The hparams from lightning checkpoint might be nested.
        if 'hparams' in hparams:
            hparams = hparams['hparams']
        
        # For inference we don't need optimizer and scheduler, but EncodonPL expects them.
        def dummy_optimizer(params):
            return torch.optim.Adam(params)
        
        hparams['optimizer'] = dummy_optimizer
        hparams['scheduler'] = None

        self.model = EncodonPL(**hparams)
        self.model.configure_model(state_dict=state_dict)
        self.model.to(self.device)
        self.model.eval()
        
    def predict_mlm(self, batch, ids=None) -> Dict[str, np.ndarray]:
        """
        Predict masked tokens in a batch.
        
        Args:
            batch: Dictionary with INPUT_MASK and LABELS fields.
            ids: Optional sequence identifiers.
            
        Returns:
            MaskedLMOutput with predictions and labels at masked positions.
        """
        if MetadataFields.INPUT_MASK not in batch:
            raise ValueError(f"Batch missing required field: {MetadataFields.INPUT_MASK}")
        if MetadataFields.LABELS not in batch:
            raise ValueError(f"Batch missing required field: {MetadataFields.LABELS}")
        
        with torch.no_grad():
            output = self.model(batch)
            preds = output.logits
            if preds.dtype != torch.float:
                preds = preds.float()
            mask = batch[MetadataFields.INPUT_MASK].bool()
            y = batch[MetadataFields.LABELS]
            y = y[mask]
            preds = preds[mask]
            preds = preds.cpu().numpy()
            y = y.cpu().numpy()
            
        return MaskedLMOutput(preds=preds, labels=y, ids=ids)
        
    def predict_mutation(self, batch, ids=None) -> Dict[str, np.ndarray]:
        """
        Score variants by comparing log probabilities at the mutation position.
        
        Args:
            batch: Dictionary with REF_CODON_TOKS, ALT_CODON_TOKS, MUTATION_TOKEN_IDX.
            ids: Optional sequence identifiers.
            
        Returns:
            MutationPredictionOutput with ref/alt likelihoods and ratios.
        """
        required_fields = [
            MetadataFields.REF_CODON_TOKS,
            MetadataFields.ALT_CODON_TOKS,
            MetadataFields.MUTATION_TOKEN_IDX
        ]
        for field in required_fields:
            if field not in batch:
                raise ValueError(f"Batch missing required field for mutation prediction: {field}")
        
        with torch.no_grad():
            output = self.model(batch)
            preds = output.logits
            if preds.dtype != torch.float:
                preds = preds.float()
            ref_toks = batch[MetadataFields.REF_CODON_TOKS].view(-1)
            alt_toks = batch[MetadataFields.ALT_CODON_TOKS].view(-1)
            mutation_token_idx = batch[MetadataFields.MUTATION_TOKEN_IDX].view(-1)
            
            seq_len = preds.shape[1]
            if (mutation_token_idx >= seq_len).any() or (mutation_token_idx < 0).any():
                raise ValueError(
                    f"mutation_token_idx contains out-of-bounds indices. "
                    f"Valid range: [0, {seq_len-1}], got min={mutation_token_idx.min().item()}, "
                    f"max={mutation_token_idx.max().item()}"
                )
            
            batch_indices = torch.arange(preds.shape[0], device=preds.device)
            preds = preds[batch_indices, mutation_token_idx, :]
            preds = torch.nn.functional.log_softmax(preds, dim=-1)
            ref_likelihoods = preds[batch_indices, ref_toks]
            alt_likelihoods = preds[batch_indices, alt_toks]
            likelihood_ratios = ref_likelihoods - alt_likelihoods
        return MutationPredictionOutput(
            ref_likelihoods=ref_likelihoods.cpu().numpy(),
            alt_likelihoods=alt_likelihoods.cpu().numpy(),
            likelihood_ratios=likelihood_ratios.cpu().numpy(),
            ids=ids,
        )

    def extract_embeddings(self, batch, ids=None) -> Dict[str, np.ndarray]:
        """
        Extract sequence embeddings from the [CLS] token.
        
        Args:
            batch: Dictionary containing input_ids and attention_mask.
            ids: Optional sequence identifiers.
            
        Returns:
            EmbeddingOutput with embeddings array of shape (batch_size, hidden_size).
        """
        with torch.no_grad():
            output = self.model(batch, return_hidden_states=True)
            embeddings = output.all_hidden_states[-1]
            if embeddings.dtype != torch.float:
                embeddings = embeddings.float()
            embeddings = embeddings[:, 0, :].cpu().numpy()
        return EmbeddingOutput(embeddings=embeddings, ids=ids)
    
    def predict_fitness(self, batch, ids=None) -> Dict[str, np.ndarray]:
        """
        Compute sequence fitness as mean log-likelihood of tokens.
        
        Uses parallel scoring (all positions evaluated simultaneously).
        
        Args:
            batch: Dictionary containing INPUT_IDS field.
            ids: Optional sequence identifiers.
            
        Returns:
            FitnessPredictionOutput with fitness scores.
        """
        if MetadataFields.INPUT_IDS not in batch:
            raise ValueError(f"Batch missing required field: {MetadataFields.INPUT_IDS}")
        
        with torch.no_grad():
            output = self.model(batch)
            preds = output.logits
            if preds.dtype != torch.float:
                preds = preds.float()
            
            log_probs = torch.nn.functional.log_softmax(preds, dim=-1)
            selected_log_probs = log_probs.gather(-1, batch[MetadataFields.INPUT_IDS].unsqueeze(-1)).squeeze(-1)
            non_padding_mask = batch[MetadataFields.INPUT_IDS] != self.tokenizer.pad_token_id
            masked_log_probs = selected_log_probs * non_padding_mask
            log_likelihoods_sum = masked_log_probs.sum(dim=-1)
            non_padding_counts = non_padding_mask.sum(dim=-1).clamp(min=1)
            log_likelihoods_mean = (log_likelihoods_sum / non_padding_counts).cpu().numpy()
        return FitnessPredictionOutput(fitness=log_likelihoods_mean, ids=ids)

    def predict_downstream(self, batch, ids=None) -> DownstreamPredictionOutput:
        """Predict using cross-attention head (requires use_downstream_head=True)."""
        with torch.no_grad():
            if not hasattr(self.model.model, 'cross_attention_head') or not hasattr(self.model.model, 'cross_attention_input_proj'):
                raise ValueError("Model does not have downstream cross-attention heads. Ensure the model was trained with use_downstream_head=True.")
            
            if MetadataFields.ATTENTION_MASK not in batch:
                raise ValueError(f"Batch missing required field: {MetadataFields.ATTENTION_MASK}")
            
            output = self.model(batch)
            hidden_states = output.last_hidden_state
            attention_mask = batch[MetadataFields.ATTENTION_MASK]
            
            projected_states = self.model.model.cross_attention_input_proj(hidden_states)
            query_input = projected_states[:, 0, :]
            key_value_input = projected_states
            preds = self.model.model.cross_attention_head(query_input, key_value_input, attention_mask)
            
            loss_type = getattr(self.model.hparams, 'loss_type', 'regression')
            
            if loss_type == "classification":
                preds_float = preds.float()
                probabilities = torch.nn.functional.softmax(preds_float, dim=-1).cpu().numpy()
                predicted_classes = preds_float.argmax(dim=-1).cpu().numpy()
                preds_np = preds_float.cpu().numpy()
                
                return DownstreamPredictionOutput(
                    predictions=preds_np,
                    probabilities=probabilities,
                    predicted_classes=predicted_classes,
                    ids=ids
                )
            else:
                preds = preds.squeeze(-1).float().cpu().numpy()
                return DownstreamPredictionOutput(predictions=preds, ids=ids)

    def _predict_step(self, batch, batch_idx):
        """Dispatch to appropriate prediction method based on task type."""
        ids = None
        if MetadataFields.ID in batch:
            ids = batch[MetadataFields.ID]
            del batch[MetadataFields.ID]
        
        if self.task_type == TaskTypes.MUTATION_PREDICTION:
            predict = self.predict_mutation
        elif self.task_type == TaskTypes.MASKED_LANGUAGE_MODELING:
            predict = self.predict_mlm
        elif self.task_type == TaskTypes.FITNESS_PREDICTION:
            predict = self.predict_fitness
        elif self.task_type == TaskTypes.EMBEDDING_PREDICTION:
            predict = self.extract_embeddings
        elif self.task_type == TaskTypes.DOWNSTREAM_PREDICTION:
            predict = self.predict_downstream
        else:
            raise ValueError(f"Unsupported task type: {self.task_type}")
        
        outputs = predict(batch, ids)
        return outputs
