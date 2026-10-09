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

from src.data.preprocess.mutation_pred import (
    _construct_sentence,
    mlm_process_item,
    likelihood_process_item
)
from src.data.metadata import MetadataFields


def _mock_tokenizer():
    t = MagicMock()
    t.encoder = {
        "<CLS>": 0,
        "<SEP>": 1,
        "<PAD>": 3,
        "<MASK>": 4,
        "TAG": 10,
        "TAA": 11,
        "TGA": 12,
        "AAA": 20,
        "CCC": 21,
    }
    t.cls_token_id = 0
    t.sep_token_id = 1
    t.pad_token_id = 3
    t.mask_token_id = 4
    # ref_seq "AAA" -> 1 codon; "AAAAAACCC" -> 3 codons
    t.tokenize = lambda s: [s[i : i + 3] for i in range(0, len(s), 3) if i + 3 <= len(s)]
    t.convert_tokens_to_ids = lambda x: (
        [t.encoder.get(tok, 0) for tok in x]
        if isinstance(x, (list, tuple))
        else t.encoder.get(x, 0)
    )
    return t


@pytest.fixture
def tokenizer():
    return _mock_tokenizer()


class TestConstructSentence:
    def test_mask_mutation_and_use_alt_raises(self, tokenizer):
        with pytest.raises(AssertionError, match="Cannot mask mutation and use alt"):
            _construct_sentence(
                "AAAAAACCC",
                codon_position=0,
                ref_codon="AAA",
                alt_codon="CCC",
                context_length=10,
                tokenizer=tokenizer,
                mask_mutation=True,
                use_alt=True,
            )

    def test_returns_five_values(self, tokenizer):
        tokenizer.tokenize = lambda s: ["AAA", "AAA", "CCC"]
        tokenizer.convert_tokens_to_ids = lambda x: [20, 20, 21] if isinstance(x, list) and len(x) == 3 else (20 if x == "AAA" else 21)
        inp, ref_t, alt_t, attn, mut_idx = _construct_sentence(
            "AAAAAACCC",
            codon_position=1,
            ref_codon="AAA",
            alt_codon="CCC",
            context_length=8,
            tokenizer=tokenizer,
            mask_mutation=False,
            use_alt=False,
        )
        assert inp.shape == (8,) or len(inp) == 8
        assert attn.shape == (8,) or len(attn) == 8
        assert mut_idx == 2

    def test_mutation_token_idx_out_of_bounds_raises(self, tokenizer):
        tokenizer.tokenize = lambda s: ["AAA"]
        tokenizer.convert_tokens_to_ids = lambda x: [20] if isinstance(x, list) else 20
        with pytest.raises(ValueError, match="out of bounds"):
            _construct_sentence(
                "AAA",
                codon_position=5,
                ref_codon="AAA",
                alt_codon="CCC",
                context_length=8,
                tokenizer=tokenizer,
                mask_mutation=False,
                use_alt=False,
            )


class TestMlmProcessItem:
    def test_output_keys(self, tokenizer):
        tokenizer.tokenize = lambda s: ["AAA", "AAA", "CCC"]
        tokenizer.convert_tokens_to_ids = lambda x: [20, 20, 21] if isinstance(x, list) and len(x) == 3 else (20 if x == "AAA" else 21)
        out = mlm_process_item(
            "AAAAAACCC",
            codon_position=1,
            ref_codon="AAA",
            alt_codon="CCC",
            context_length=8,
            tokenizer=tokenizer,
            mask_mutation=True,
        )
        assert MetadataFields.INPUT_IDS in out
        assert MetadataFields.REF_CODON_TOKS in out
        assert MetadataFields.ALT_CODON_TOKS in out
        assert MetadataFields.ATTENTION_MASK in out
        assert MetadataFields.MUTATION_TOKEN_IDX in out

    def test_mutation_token_idx_shape(self, tokenizer):
        tokenizer.tokenize = lambda s: ["AAA", "AAA", "CCC"]
        tokenizer.convert_tokens_to_ids = lambda x: [20, 20, 21] if isinstance(x, list) and len(x) == 3 else (20 if x == "AAA" else 21)
        out = mlm_process_item(
            "AAAAAACCC",
            codon_position=1,
            ref_codon="AAA",
            alt_codon="CCC",
            context_length=8,
            tokenizer=tokenizer,
        )
        assert np.asarray(out[MetadataFields.MUTATION_TOKEN_IDX]).ndim >= 1


class TestLikelihoodProcessItem:
    def test_output_keys(self, tokenizer):
        tokenizer.tokenize = lambda s: ["AAA", "AAA", "CCC"]
        tokenizer.convert_tokens_to_ids = lambda x: [20, 20, 21] if isinstance(x, list) and len(x) == 3 else (20 if x == "AAA" else 21)
        out = likelihood_process_item(
            "AAAAAACCC",
            codon_position=1,
            ref_codon="AAA",
            alt_codon="CCC",
            context_length=8,
            tokenizer=tokenizer,
        )
        assert MetadataFields.INPUT_IDS in out
        assert MetadataFields.ATTENTION_MASK in out