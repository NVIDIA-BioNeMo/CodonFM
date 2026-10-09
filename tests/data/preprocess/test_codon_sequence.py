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

import numpy as np
import pytest
from unittest.mock import MagicMock

from src.data.preprocess.codon_sequence import process_item


def _make_mock_tokenizer():
    t = MagicMock()
    t.encoder = {
        "<CLS>": 0,
        "<SEP>": 1,
        "<PAD>": 3,
        "ATG": 10,
        "TAG": 11,
        "TAA": 12,
        "TGA": 13,
    }
    t.cls_token_id = 0
    t.sep_token_id = 1
    t.pad_token_id = 3
    return t


@pytest.fixture
def mock_tokenizer():
    return _make_mock_tokenizer()


class TestCodonSequenceProcessItem:
    """Tests for MLM-style process_item (CLS, SEP, padding)."""

    def test_output_keys(self, mock_tokenizer):
        mock_tokenizer.tokenize = lambda s: ["ATG", "TAG"]
        mock_tokenizer.convert_tokens_to_ids = lambda toks: [10, 11]
        out = process_item("ATGTAG", context_length=8, tokenizer=mock_tokenizer)
        assert "input_ids" in out
        assert "attention_mask" in out

    def test_output_shape(self, mock_tokenizer):
        mock_tokenizer.tokenize = lambda s: ["ATG", "TAG"]
        mock_tokenizer.convert_tokens_to_ids = lambda toks: [10, 11]
        out = process_item("ATGTAG", context_length=8, tokenizer=mock_tokenizer)
        assert out["input_ids"].shape == (8,)
        assert out["attention_mask"].shape == (8,)
        assert out["input_ids"].dtype == np.int64

    def test_cls_sep_added(self, mock_tokenizer):
        mock_tokenizer.tokenize = lambda s: ["ATG", "TAG"]
        mock_tokenizer.convert_tokens_to_ids = lambda toks: [10, 11]
        out = process_item("ATGTAG", context_length=6, tokenizer=mock_tokenizer)
        assert out["input_ids"][0] == 0
        assert out["input_ids"][3] == 1
