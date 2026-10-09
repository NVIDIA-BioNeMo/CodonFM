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

"""Checkpoint loading helpers."""

from importlib import import_module
from os import PathLike
from typing import Any, Union

import torch


def install_legacy_checkpoint_aliases() -> None:
    """Expose classes at paths used by pre-Transformers-5 checkpoints."""
    from transformers.tokenization_python import Trie

    tokenization_utils = import_module("transformers.tokenization_utils")
    if getattr(tokenization_utils, "Trie", None) is not Trie:
        setattr(tokenization_utils, "Trie", Trie)


def load_trusted_checkpoint(
    checkpoint_path: Union[str, PathLike[str]], map_location: Any = "cpu"
) -> Any:
    """Load a trusted full checkpoint that can contain serialized objects.

    Pickle data can execute code, so callers must only pass project-controlled
    or otherwise trusted Lightning checkpoints.
    """
    install_legacy_checkpoint_aliases()
    return torch.load(
        checkpoint_path,
        map_location=map_location,
        weights_only=False,
    )
