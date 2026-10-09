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

import sys

import pytest

from src import runner


def test_task_type_choices_reject_unknown_value():
    with pytest.raises(SystemExit):
        runner.get_parser().parse_args(
            [
                "eval",
                "--exp_name",
                "invalid-task",
                "--data_path",
                "data.csv",
                "--process_item",
                "mutation_pred_mlm",
                "--dataset_name",
                "MutationDataset",
                "--model_name",
                "encodon_80m",
                "--checkpoint_path",
                "model.safetensors",
                "--task_type",
                "not-a-task",
            ]
        )


def test_eval_requires_task_type(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner.py",
            "eval",
            "--exp_name",
            "missing-task",
            "--data_path",
            "data.csv",
            "--process_item",
            "mutation_pred_mlm",
            "--dataset_name",
            "MutationDataset",
            "--model_name",
            "encodon_80m",
            "--checkpoint_path",
            "model.safetensors",
        ],
    )

    with pytest.raises(SystemExit):
        runner.main()

    assert "--task_type is required for mode 'eval'" in capsys.readouterr().err
