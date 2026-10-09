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

import torch
import pytest
from src.models.components.cross_attention import CrossAttention


@pytest.fixture
def hidden_dim():
    return 64


@pytest.fixture
def n_out():
    return 2


@pytest.fixture
def num_heads():
    return 8


@pytest.fixture
def cross_attention(hidden_dim, n_out, num_heads):
    return CrossAttention(
        hidden_dim=hidden_dim,
        n_out=n_out,
        num_heads=num_heads,
        dropout=0.0,
    )


class TestCrossAttention:
    def test_init(self, cross_attention, hidden_dim, n_out, num_heads):
        assert cross_attention.hidden_dim == hidden_dim
        assert cross_attention.cross_attention.embed_dim == hidden_dim
        assert cross_attention.cross_attention.num_heads == num_heads
        assert cross_attention.query_linear.out_features == hidden_dim
        assert cross_attention.output.out_features == n_out
        assert isinstance(cross_attention.norm1, torch.nn.LayerNorm)
        assert isinstance(cross_attention.norm2, torch.nn.LayerNorm)

    def test_forward_shape(self, cross_attention, hidden_dim, n_out):
        batch_size = 4
        seq_len = 10
        query_input = torch.randn(batch_size, hidden_dim)
        key_value_input = torch.randn(batch_size, seq_len, hidden_dim)
        attention_mask = torch.ones(batch_size, seq_len)

        out = cross_attention(query_input, key_value_input, attention_mask)

        assert out.shape == (batch_size, n_out)
        assert out.dtype == query_input.dtype

    def test_forward_with_padding_mask(self, cross_attention, hidden_dim, n_out):
        batch_size = 2
        seq_len = 5
        query_input = torch.randn(batch_size, hidden_dim)
        key_value_input = torch.randn(batch_size, seq_len, hidden_dim)
        # Mask last 2 positions
        attention_mask = torch.tensor([[1, 1, 1, 0, 0], [1, 1, 0, 0, 0]], dtype=torch.float32)

        out = cross_attention(query_input, key_value_input, attention_mask)

        assert out.shape == (batch_size, n_out)
        assert not torch.isnan(out).any()
        assert not torch.isinf(out).any()

    def test_forward_attention_mask_none(self, cross_attention, hidden_dim, n_out):
        batch_size = 2
        seq_len = 4
        query_input = torch.randn(batch_size, hidden_dim)
        key_value_input = torch.randn(batch_size, seq_len, hidden_dim)

        out = cross_attention(query_input, key_value_input, attention_mask=None)

        assert out.shape == (batch_size, n_out)

    def test_forward_deterministic_with_dropout_zero(self, cross_attention, hidden_dim, n_out):
        cross_attention.eval()
        batch_size = 2
        seq_len = 4
        query_input = torch.randn(batch_size, hidden_dim)
        key_value_input = torch.randn(batch_size, seq_len, hidden_dim)
        attention_mask = torch.ones(batch_size, seq_len)

        out1 = cross_attention(query_input, key_value_input, attention_mask)
        out2 = cross_attention(query_input, key_value_input, attention_mask)

        torch.testing.assert_close(out1, out2)
