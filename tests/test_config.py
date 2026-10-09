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

from types import SimpleNamespace

import fiddle as fdl
import pytest
from lightning.pytorch.loggers import CSVLogger

from src.config import create_strategy_from_config, get_dataset_config, get_logger_config
from src.data.metadata import TrainerModes


def test_create_strategy_removes_private_trainer_keys():
    trainer_kwargs = {
        "_strategy_type": "ddp",
        "_fsdp_config": None,
        "max_steps": 1,
    }

    converted = create_strategy_from_config(trainer_kwargs)

    assert converted["strategy"] == "ddp"
    assert converted["max_steps"] == 1
    assert "_strategy_type" not in converted
    assert "_fsdp_config" not in converted


def test_direct_run_uses_csv_logger_by_default(tmp_path):
    config = get_logger_config(
        SimpleNamespace(
            enable_wandb=False,
            out_dir=str(tmp_path),
            exp_name="release-test",
        )
    )

    logger = fdl.build(config)

    assert isinstance(logger, CSVLogger)
    assert logger.save_dir == str(tmp_path)


def test_predict_rejects_memmap_dataset_without_mutating_ratio():
    args = SimpleNamespace(
        dataset_name="CodonMemmapDataset",
        mode=TrainerModes.PREDICT,
        train_val_test_ratio=[0.8, 0.1, 0.1],
    )

    with pytest.raises(ValueError, match="CodonMemmapDataset.*PREDICT"):
        get_dataset_config(args, process_item_cfg=None)

    assert args.train_val_test_ratio == [0.8, 0.1, 0.1]
