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

"""
Unit tests for src/inference/model_outputs.py

Tests cover:
- Dataclass instantiation and field access
- Default values
- Type handling for numpy arrays
"""

import pytest
import numpy as np

from src.inference.model_outputs import (
    MaskedLMOutput,
    MutationPredictionOutput,
    FitnessPredictionOutput,
    EmbeddingOutput,
    DownstreamPredictionOutput,
)


class TestMaskedLMOutput:
    """Tests for MaskedLMOutput dataclass."""

    def test_basic_creation(self):
        """Test creating a MaskedLMOutput with required fields."""
        preds = np.array([[0.1, 0.9], [0.8, 0.2]])
        labels = np.array([1, 0])
        
        output = MaskedLMOutput(preds=preds, labels=labels)
        
        assert np.array_equal(output.preds, preds)
        assert np.array_equal(output.labels, labels)
        assert output.ids is None

    def test_with_ids(self):
        """Test creating a MaskedLMOutput with ids."""
        preds = np.array([[0.1, 0.9]])
        labels = np.array([1])
        ids = np.array(["seq_1"])
        
        output = MaskedLMOutput(preds=preds, labels=labels, ids=ids)
        
        assert np.array_equal(output.ids, ids)

    def test_empty_arrays(self):
        """Test with empty arrays."""
        preds = np.array([])
        labels = np.array([])
        
        output = MaskedLMOutput(preds=preds, labels=labels)
        
        assert len(output.preds) == 0
        assert len(output.labels) == 0


class TestMutationPredictionOutput:
    """Tests for MutationPredictionOutput dataclass."""

    def test_basic_creation(self):
        """Test creating a MutationPredictionOutput with required fields."""
        ref_likes = np.array([-1.0, -0.5])
        alt_likes = np.array([-2.0, -0.3])
        ratios = np.array([1.0, -0.2])
        
        output = MutationPredictionOutput(
            ref_likelihoods=ref_likes,
            alt_likelihoods=alt_likes,
            likelihood_ratios=ratios
        )
        
        assert np.array_equal(output.ref_likelihoods, ref_likes)
        assert np.array_equal(output.alt_likelihoods, alt_likes)
        assert np.array_equal(output.likelihood_ratios, ratios)
        assert output.ids is None

    def test_with_ids(self):
        """Test with sequence identifiers."""
        ref_likes = np.array([-1.0])
        alt_likes = np.array([-2.0])
        ratios = np.array([1.0])
        ids = np.array(["mutation_1"])
        
        output = MutationPredictionOutput(
            ref_likelihoods=ref_likes,
            alt_likelihoods=alt_likes,
            likelihood_ratios=ratios,
            ids=ids
        )
        
        assert np.array_equal(output.ids, ids)


class TestFitnessPredictionOutput:
    """Tests for FitnessPredictionOutput dataclass."""

    def test_basic_creation(self):
        """Test creating a FitnessPredictionOutput."""
        fitness = np.array([0.8, 0.9, 0.7])
        
        output = FitnessPredictionOutput(fitness=fitness)
        
        assert np.array_equal(output.fitness, fitness)
        assert output.ids is None

    def test_with_ids(self):
        """Test with sequence identifiers."""
        fitness = np.array([0.8])
        ids = np.array(["seq_1"])
        
        output = FitnessPredictionOutput(fitness=fitness, ids=ids)
        
        assert np.array_equal(output.ids, ids)

    def test_single_value(self):
        """Test with single fitness value."""
        fitness = np.array([0.95])
        
        output = FitnessPredictionOutput(fitness=fitness)
        
        assert len(output.fitness) == 1
        assert output.fitness[0] == 0.95


class TestEmbeddingOutput:
    """Tests for EmbeddingOutput dataclass."""

    def test_basic_creation(self):
        """Test creating an EmbeddingOutput."""
        embeddings = np.random.randn(2, 768)  # batch_size=2, hidden_size=768
        
        output = EmbeddingOutput(embeddings=embeddings)
        
        assert output.embeddings.shape == (2, 768)
        assert output.ids is None

    def test_with_ids(self):
        """Test with sequence identifiers."""
        embeddings = np.random.randn(3, 256)
        ids = np.array(["a", "b", "c"])
        
        output = EmbeddingOutput(embeddings=embeddings, ids=ids)
        
        assert len(output.ids) == 3

    def test_single_embedding(self):
        """Test with single embedding."""
        embeddings = np.random.randn(1, 512)
        
        output = EmbeddingOutput(embeddings=embeddings)
        
        assert output.embeddings.shape == (1, 512)


class TestDownstreamPredictionOutput:
    """Tests for DownstreamPredictionOutput dataclass."""

    def test_regression_output(self):
        """Test regression output (no probabilities or classes)."""
        predictions = np.array([0.5, 0.7, 0.3])
        
        output = DownstreamPredictionOutput(predictions=predictions)
        
        assert np.array_equal(output.predictions, predictions)
        assert output.probabilities is None
        assert output.predicted_classes is None
        assert output.ids is None

    def test_classification_output(self):
        """Test classification output with all fields."""
        predictions = np.array([[0.1, 0.9], [0.8, 0.2]])
        probabilities = np.array([[0.1, 0.9], [0.8, 0.2]])
        predicted_classes = np.array([1, 0])
        ids = np.array(["s1", "s2"])
        
        output = DownstreamPredictionOutput(
            predictions=predictions,
            probabilities=probabilities,
            predicted_classes=predicted_classes,
            ids=ids
        )
        
        assert np.array_equal(output.predictions, predictions)
        assert np.array_equal(output.probabilities, probabilities)
        assert np.array_equal(output.predicted_classes, predicted_classes)
        assert np.array_equal(output.ids, ids)

    def test_classification_without_ids(self):
        """Test classification output without ids."""
        predictions = np.array([[0.1, 0.9]])
        probabilities = np.array([[0.1, 0.9]])
        predicted_classes = np.array([1])
        
        output = DownstreamPredictionOutput(
            predictions=predictions,
            probabilities=probabilities,
            predicted_classes=predicted_classes
        )
        
        assert output.ids is None


class TestDataclassInteroperability:
    """Tests for output dataclass interoperability with common patterns."""

    def test_fitness_to_dict_pattern(self):
        """Test accessing fields as dict-like pattern."""
        fitness = np.array([0.8, 0.9])
        output = FitnessPredictionOutput(fitness=fitness)
        
        # Common pattern: access as dict
        from dataclasses import asdict
        d = asdict(output)
        
        assert "fitness" in d
        assert "ids" in d

    def test_embedding_batch_indexing(self):
        """Test batch indexing on embeddings."""
        embeddings = np.random.randn(5, 256)
        output = EmbeddingOutput(embeddings=embeddings)
        
        # Should be able to index into embeddings
        first_embedding = output.embeddings[0]
        assert first_embedding.shape == (256,)
        
        batch_slice = output.embeddings[:3]
        assert batch_slice.shape == (3, 256)

    def test_mutation_output_stacking(self):
        """Test stacking multiple mutation outputs."""
        out1 = MutationPredictionOutput(
            ref_likelihoods=np.array([-1.0]),
            alt_likelihoods=np.array([-2.0]),
            likelihood_ratios=np.array([1.0])
        )
        out2 = MutationPredictionOutput(
            ref_likelihoods=np.array([-0.5]),
            alt_likelihoods=np.array([-0.3]),
            likelihood_ratios=np.array([-0.2])
        )
        
        # Common pattern: concatenate results
        combined_refs = np.concatenate([out1.ref_likelihoods, out2.ref_likelihoods])
        combined_alts = np.concatenate([out1.alt_likelihoods, out2.alt_likelihoods])
        
        assert len(combined_refs) == 2
        assert len(combined_alts) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
