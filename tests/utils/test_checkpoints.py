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

from functools import partial
from types import SimpleNamespace

import torch
from transformers.tokenization_python import Trie

import src.utils.checkpoints as checkpoints


def test_load_trusted_checkpoint_supports_lightning_hyperparameters(tmp_path):
    checkpoint_path = tmp_path / "model.ckpt"
    optimizer = partial(torch.optim.Adam, lr=1e-3)
    torch.save({"hyper_parameters": {"optimizer": optimizer}}, checkpoint_path)

    checkpoint = checkpoints.load_trusted_checkpoint(checkpoint_path)

    loaded_optimizer = checkpoint["hyper_parameters"]["optimizer"]
    assert loaded_optimizer.func is torch.optim.Adam
    assert loaded_optimizer.keywords == {"lr": 1e-3}


def test_install_legacy_checkpoint_aliases(monkeypatch):
    legacy_module = SimpleNamespace()
    monkeypatch.setattr(
        checkpoints,
        "import_module",
        lambda module_name: legacy_module,
    )

    checkpoints.install_legacy_checkpoint_aliases()

    assert legacy_module.Trie is Trie
