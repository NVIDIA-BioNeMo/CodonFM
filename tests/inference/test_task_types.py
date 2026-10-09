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
Unit tests for src/inference/task_types.py

Tests cover:
- TaskTypes enum values
- Enum string conversion
- Enum comparison
"""

import pytest

from src.inference.task_types import TaskTypes


class TestTaskTypes:
    """Tests for TaskTypes enum."""

    def test_all_task_types_exist(self):
        """Test that all expected task types exist."""
        expected_types = [
            "MUTATION_PREDICTION",
            "MASKED_LANGUAGE_MODELING",
            "FITNESS_PREDICTION",
            "EMBEDDING_PREDICTION",
            "DOWNSTREAM_PREDICTION",
        ]
        
        for type_name in expected_types:
            assert hasattr(TaskTypes, type_name)

    def test_task_type_values(self):
        """Test that task type values are correct strings."""
        assert TaskTypes.MUTATION_PREDICTION.value == "mutation_prediction"
        assert TaskTypes.MASKED_LANGUAGE_MODELING.value == "masked_language_modeling"
        assert TaskTypes.FITNESS_PREDICTION.value == "fitness_prediction"
        assert TaskTypes.EMBEDDING_PREDICTION.value == "embedding_prediction"
        assert TaskTypes.DOWNSTREAM_PREDICTION.value == "downstream_prediction"

    def test_task_type_string_conversion(self):
        """Test that TaskTypes can be used as strings."""
        # TaskTypes inherits from str, so it should work as a string
        task = TaskTypes.MUTATION_PREDICTION
        # The value is the string representation for comparisons
        assert task.value == "mutation_prediction"
        
        # Should be usable in string comparisons (via value)
        assert task == "mutation_prediction"

    def test_task_type_from_value(self):
        """Test creating TaskTypes from string values."""
        task = TaskTypes("mutation_prediction")
        assert task == TaskTypes.MUTATION_PREDICTION
        
        task = TaskTypes("fitness_prediction")
        assert task == TaskTypes.FITNESS_PREDICTION

    def test_task_type_invalid_value(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            TaskTypes("invalid_task_type")

    def test_task_type_comparison(self):
        """Test task type comparison operations."""
        task1 = TaskTypes.FITNESS_PREDICTION
        task2 = TaskTypes.FITNESS_PREDICTION
        task3 = TaskTypes.EMBEDDING_PREDICTION
        
        assert task1 == task2
        assert task1 != task3

    def test_task_type_membership(self):
        """Test membership checks."""
        all_tasks = list(TaskTypes)
        
        assert TaskTypes.MUTATION_PREDICTION in all_tasks
        assert len(all_tasks) == 5

    def test_task_type_iteration(self):
        """Test iterating over TaskTypes."""
        task_values = [t.value for t in TaskTypes]
        
        assert "mutation_prediction" in task_values
        assert "fitness_prediction" in task_values

    def test_task_type_hashing(self):
        """Test that TaskTypes can be used as dict keys."""
        task_dict = {
            TaskTypes.FITNESS_PREDICTION: "fitness_handler",
            TaskTypes.EMBEDDING_PREDICTION: "embedding_handler",
        }
        
        assert task_dict[TaskTypes.FITNESS_PREDICTION] == "fitness_handler"
        assert task_dict[TaskTypes.EMBEDDING_PREDICTION] == "embedding_handler"

    def test_task_type_in_conditionals(self):
        """Test using TaskTypes in conditional logic."""
        task = TaskTypes.MUTATION_PREDICTION
        
        if task == TaskTypes.MUTATION_PREDICTION:
            result = "mutation"
        elif task == TaskTypes.FITNESS_PREDICTION:
            result = "fitness"
        else:
            result = "other"
        
        assert result == "mutation"


class TestTaskTypesUsagePatterns:
    """Tests for common usage patterns with TaskTypes."""

    def test_dispatch_pattern(self):
        """Test using TaskTypes for method dispatch."""
        handlers = {
            TaskTypes.MUTATION_PREDICTION: lambda: "predict_mutation",
            TaskTypes.MASKED_LANGUAGE_MODELING: lambda: "predict_mlm",
            TaskTypes.FITNESS_PREDICTION: lambda: "predict_fitness",
            TaskTypes.EMBEDDING_PREDICTION: lambda: "extract_embeddings",
            TaskTypes.DOWNSTREAM_PREDICTION: lambda: "predict_downstream",
        }
        
        task = TaskTypes.FITNESS_PREDICTION
        handler = handlers.get(task)
        
        assert handler is not None
        assert handler() == "predict_fitness"

    def test_match_from_string_input(self):
        """Test matching task type from string input (common CLI pattern)."""
        user_input = "fitness_prediction"
        
        try:
            task = TaskTypes(user_input)
            matched = True
        except ValueError:
            matched = False
        
        assert matched
        assert task == TaskTypes.FITNESS_PREDICTION

    def test_validation_pattern(self):
        """Test validation pattern for task types."""
        valid_tasks = {"fitness_prediction", "mutation_prediction", "embedding_prediction"}
        
        def validate_task(task_str: str) -> bool:
            try:
                task = TaskTypes(task_str)
                return task.value in valid_tasks
            except ValueError:
                return False
        
        assert validate_task("fitness_prediction") is True
        assert validate_task("mutation_prediction") is True
        assert validate_task("invalid_task") is False
        assert validate_task("unknown_task") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
