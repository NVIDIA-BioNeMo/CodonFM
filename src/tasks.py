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

from typing import Any, Dict
import os
from pathlib import Path

from lightning.pytorch import seed_everything, Trainer
from src.config import create_strategy_from_config
from src.utils import RankedLogger
from src.utils.checkpoints import (
    install_legacy_checkpoint_aliases,
    load_trusted_checkpoint,
)
from safetensors.torch import load_file

# Initialize logger at module level so it's available to all functions
logging = RankedLogger(__name__, rank_zero_only=True)


def train(config: Dict[str, Any], 
          ckpt_path: str, 
          seed: int, 
          config_dict: Dict[str, Any], 
          out_dir: str):
    """Launches the pre-training process for the Encodon model.

    Args:
        config: A dictionary containing the configuration for the model, data, and trainer.
        ckpt_path: The path to the checkpoint file to resume training from.
        seed: The random seed to use for reproducibility.
    """
    seed_everything(seed, workers=True)
    
    os.makedirs(out_dir, exist_ok=True)
    
    logger, data, trainer_kwargs, model, callbacks = config["log"], \
                                              config["data"], \
                                              config["trainer"], \
                                              config["model"], \
                                              config["callbacks"]
    trainer_kwargs = create_strategy_from_config(dict(trainer_kwargs))
    trainer = Trainer(**trainer_kwargs)
    
    if logger and hasattr(logger, "log_hyperparams"):
        logger.log_hyperparams(config_dict)
        
    if os.path.exists(ckpt_path):
        state_dict = load_trusted_checkpoint(ckpt_path)
        model.configure_model(state_dict=state_dict.get("state_dict"))
    else:
        model.configure_model()
    
    trainer.callbacks = list(callbacks.values())
    trainer.logger = logger
    logging.info(f"Starting pre-training from {ckpt_path}")
    trainer_ckpt_path = ckpt_path if os.path.exists(ckpt_path) else None
    fit_kwargs = {}
    if trainer_ckpt_path is not None:
        install_legacy_checkpoint_aliases()
        fit_kwargs["weights_only"] = False
    trainer.fit(
        model,
        datamodule=data,
        ckpt_path=trainer_ckpt_path,
        **fit_kwargs,
    )

def finetune(config: Dict[str, Any],
             pretrained_ckpt_path: str,
             seed: int,
             resume_trainer_state: bool,
             config_dict: Dict[str, Any], 
             out_dir: str,
             ckpt_path: str):
    """Launches the fine-tuning process for the Encodon model.

    Args:
        config: A dictionary containing the configuration for the model, data, and trainer.
        ckpt_path: The path to save the fine-tuned model checkpoint.
        pretrained_ckpt_path: The path to the pre-trained model checkpoint to start fine-tuning from.
        seed: The random seed to use for reproducibility.
        resume_trainer_state: Whether to resume the trainer state from the checkpoint.
    """
    seed_everything(seed, workers=True)
    
    os.makedirs(out_dir, exist_ok=True)
    
    logger, data, trainer_kwargs, model, callbacks = config["log"], \
                                              config["data"], \
                                              config["trainer"], \
                                              config["model"], \
                                              config["callbacks"]
    trainer_kwargs = create_strategy_from_config(dict(trainer_kwargs))
    trainer = Trainer(**trainer_kwargs)
    
    if logger and hasattr(logger, "log_hyperparams"):
        logger.log_hyperparams(config_dict)
        
    pretrained_exists = bool(pretrained_ckpt_path) and os.path.exists(pretrained_ckpt_path)
    checkpoint_exists = bool(ckpt_path) and os.path.exists(ckpt_path)
    if pretrained_exists and not checkpoint_exists:
        # first time finetuning from a pretrained checkpoint: can be a .safetensors or a .ckpt file.
        ckpt_suffix = Path(pretrained_ckpt_path).suffix.lower()
        if ckpt_suffix == ".safetensors":
            state_dict = load_file(str(Path(pretrained_ckpt_path)))
            model.configure_model(state_dict=state_dict)
            trainer_ckpt_path = None
        elif ckpt_suffix == ".ckpt":
            state_dict = load_trusted_checkpoint(pretrained_ckpt_path)
            model.configure_model(state_dict=state_dict.get("state_dict"))
        else:
            raise ValueError(
                "Pretrained checkpoint must be a .ckpt or .safetensors file."
            )
    else:
        logging.info(f"No pretrained checkpoint found at {pretrained_ckpt_path}, starting from scratch")
        model.configure_model()
    
    trainer.callbacks = list(callbacks.values())
    trainer.logger = logger
    
    if resume_trainer_state and pretrained_exists and not checkpoint_exists:
        if Path(pretrained_ckpt_path).suffix.lower() != ".ckpt":
            raise ValueError(
                "Pretrained checkpoint must be a .ckpt file when resuming trainer state."
            )
        trainer_ckpt_path = pretrained_ckpt_path
    else:
        trainer_ckpt_path = ckpt_path if checkpoint_exists else None
    
    logging.info(f"Starting finetuning from {trainer_ckpt_path} \
        with resume_trainer_state={resume_trainer_state} and ckpt_path={ckpt_path}")
    fit_kwargs = {}
    if trainer_ckpt_path is not None:
        install_legacy_checkpoint_aliases()
        fit_kwargs["weights_only"] = False
    trainer.fit(
        model,
        datamodule=data,
        ckpt_path=trainer_ckpt_path,
        **fit_kwargs,
    )


def evaluate(
    config: Dict[str, Any],
    config_dict: Dict[str, Any],
    model_ckpt_path: str,
    out_dir: str,
    seed: int = 123,
) -> None:
    """Launches the evaluation process for the Encodon model.

    Args:
        config: A dictionary containing the configuration for the model, data, and trainer.
        config_dict: A dictionary containing the configuration for the model, data, and trainer.
        
    Note: Evaluation must be run in a single run as resuming the trainer state is not supported for prediction.
    """
    seed_everything(seed, workers=True)

    os.makedirs(out_dir, exist_ok=True)

    logger, data, trainer_kwargs, model, callbacks = config["log"], \
                                          config["data"], \
                                          config["trainer"], \
                                          config["model"], \
                                          config["callbacks"]
    
    trainer_kwargs = create_strategy_from_config(dict(trainer_kwargs))
    trainer = Trainer(**trainer_kwargs)
    
    if logger and hasattr(logger, "log_hyperparams"):
        logger.log_hyperparams(config_dict)
        
    model.configure_model()

    data.setup("test")
    if (
        os.path.exists(model_ckpt_path)
        and Path(model_ckpt_path).suffix.lower() == ".ckpt"
    ):
        logging.info(f"Loading dataset checkpoint from {model_ckpt_path}")
        checkpoint = load_trusted_checkpoint(model_ckpt_path)
        datamodule_state = checkpoint.get(data.__class__.__qualname__)
        if datamodule_state is not None:
            data.load_state_dict(datamodule_state)
            model.prediction_counter = data.init_global_step
    
    trainer.logger = logger
    trainer.callbacks = list(callbacks.values())
    
    logging.info("Starting Evaluation!")
    trainer.predict(model, 
                    datamodule=data, 
                    return_predictions=False)
    return
