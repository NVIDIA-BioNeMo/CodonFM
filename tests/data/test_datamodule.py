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

import os
import pytest
import torch
import lightning as L
from torch.utils.data import Dataset
from src.data.datamodule import CodonFMDataModule
import math

class SimpleIndexDataset(Dataset):
    """A simple dataset that returns its indices for easy testing."""
    def __init__(self, size=100, split='train'):
        self.size = size
        self.split = split
        self.data = list(range(size))
    
    def __len__(self):
        return self.size
    
    def __getitem__(self, idx):
        return {'index': self.data[idx], 'split': self.split}

class IndexTrackingDataset:
    """Dataset class that provides different splits while tracking indices.

    The ``train_size`` can be configured so that we can easily test scenarios where
    the dataset size **is** or **is not** a multiple of the training batch size.
    """
    def __init__(self, seed=None, train_size: int = 100):
        self.train_size = train_size
        self.val_size = 32
        self.test_size = 16
        
    def get_train(self, process_item=None):
        return SimpleIndexDataset(self.train_size, 'train')
    
    def get_validation(self, process_item=None):
        return SimpleIndexDataset(self.val_size, 'val')
    
    def get_test(self, process_item=None):
        return SimpleIndexDataset(self.test_size, 'test')

def collate_fn(batch):
    """Simple collate function that preserves indices."""
    return {
        'indices': torch.tensor([item['index'] for item in batch]),
        'split': [item['split'] for item in batch]
    }

@pytest.fixture(params=[100, 102], ids=["multiple_of_batch", "not_multiple_of_batch"])
def datamodule(request):
    """Create a ``CodonFMDataModule`` with a configurable training dataset size.

    Two configurations are tested:
        1. ``train_size`` **is** a multiple of ``train_batch_size`` (100 vs 4).
        2. ``train_size`` **is not** a multiple of ``train_batch_size`` (102 vs 4).
    """

    train_size = request.param
    train_batch_size = 4

    # ``train_iters`` chosen such that total samples ~= 1.5 epochs
    batches_per_epoch = math.ceil(train_size / train_batch_size)
    train_iters = math.ceil(batches_per_epoch * 1.5)

    def dataset_fn(seed=None):
        return IndexTrackingDataset(seed, train_size=train_size)

    return CodonFMDataModule(
        dataset=dataset_fn,
        num_workers=0,
        seed=42,
        world_size=1,
        train_iters=train_iters,
        collate_fn=collate_fn,
        train_batch_size=train_batch_size,
        val_batch_size=8,
        shuffle=True
    )

def test_train_dataloader_indices(datamodule):
    """Test that training dataloader properly handles indices with StatefulDataset."""
    datamodule.setup('fit')
    train_loader = datamodule.train_dataloader()
    
    # Get one full pass through the dataset
    all_indices = []
    for batch in train_loader:
        assert batch['split'][0] == 'train'  # Verify we're getting training data
        indices = batch['indices'].tolist()
        all_indices.extend(indices)
        # All batches should be full size since drop_last=True
        assert len(indices) == datamodule.train_batch_size
    
    # We should get complete batches up to the dataset size
    expected_total_samples = (datamodule.dataset.train_size // datamodule.train_batch_size) * datamodule.train_batch_size
    assert len(all_indices) == expected_total_samples
    
    # Verify that indices are within bounds of original dataset
    assert all(0 <= idx < datamodule.dataset.train_size for idx in all_indices)
    
    # Since shuffle is True, verify that we're getting shuffled indices
    assert sorted(all_indices) != all_indices  # not in order
    assert len(set(all_indices)) == len(all_indices)  # no repeats in first epoch

def test_train_dataloader_multiple_epochs(datamodule):
    """Test that StatefulDataset provides correct samples across epochs."""
    datamodule.setup('fit')
    
    # Get first epoch
    first_epoch_indices = []
    train_loader = datamodule.train_dataloader()
    for batch in train_loader:
        first_epoch_indices.extend(batch['indices'].tolist())
    
    # Create new datamodule with consumed_samples = dataset_size
    # This should give us samples from the second epoch
    new_datamodule = CodonFMDataModule(
        dataset=lambda seed: IndexTrackingDataset(seed, train_size=datamodule.dataset.train_size),
        seed=42,
        world_size=1,
        train_iters=datamodule.train_iters,
        collate_fn=collate_fn,
        train_batch_size=4,
        shuffle=True
    )
    new_datamodule.init_consumed_samples = datamodule.dataset.train_size 
    new_datamodule.setup('fit')
    
    # Get second epoch
    second_epoch_indices = []
    train_loader = new_datamodule.train_dataloader()
    for batch in train_loader:
        second_epoch_indices.extend(batch['indices'].tolist())
    

    assert len(first_epoch_indices) == len(second_epoch_indices)
    assert len(set(first_epoch_indices)) == len(first_epoch_indices)
    remaining_samples = (
        new_datamodule.train_iters * new_datamodule.global_batch_size
        - new_datamodule.init_consumed_samples
    )
    if remaining_samples >= datamodule.dataset.train_size:
        # We managed to consume (at least) one *full* epoch → expect all unique.
        assert len(set(second_epoch_indices)) == len(second_epoch_indices)
    
    # 3. For datasets that are an exact multiple of the batch size we should see
    #    *all* indices in the epoch.  Otherwise we only get full batches up to
    #    ``floor(train_size / batch_size) * batch_size``.
    if datamodule.dataset.train_size % datamodule.train_batch_size == 0:
        assert sorted(first_epoch_indices) == list(range(datamodule.dataset.train_size))

        if remaining_samples >= datamodule.dataset.train_size:
            assert sorted(second_epoch_indices) == list(range(datamodule.dataset.train_size))
    
    # 4. Ensure the two epochs have different shuffle orders
    assert first_epoch_indices != second_epoch_indices


def test_train_uses_stateful_dataset_and_disables_shuffle():
    """Keep shuffling inside StatefulDataset, not in the DataLoader sampler."""
    from torch.utils.data import TensorDataset
    from torch.utils.data.sampler import SequentialSampler

    from src.data.stateful_dataset import StatefulDataset

    class TinyProvider:
        def get_train(self, process_item=None):
            return TensorDataset(torch.arange(10))

        def get_validation(self, process_item=None):
            return TensorDataset(torch.arange(5))

        def get_test(self, process_item=None):
            return TensorDataset(torch.arange(7))

    dm = CodonFMDataModule(
        dataset=lambda seed: TinyProvider(),
        seed=42,
        world_size=1,
        train_iters=5,
        collate_fn=lambda batch: batch,
        train_batch_size=4,
        val_batch_size=2,
        shuffle=True,
        num_workers=0,
    )

    dm.setup('fit')
    train_dl = dm.train_dataloader()

    assert isinstance(train_dl.dataset, StatefulDataset)
    # DataLoader does not expose shuffle directly; the sampler reflects its setting.
    assert isinstance(train_dl.sampler, SequentialSampler)


def test_consumed_samples_resumption(datamodule):
    """Test that resuming from consumed samples maintains proper indexing."""
    datamodule.setup('fit')
    
    # Get initial sequence of indices
    initial_indices = []
    train_loader = datamodule.train_dataloader()
    for i, batch in enumerate(train_loader):
        if i >= 2:  # Get first 2 batches
            break
        initial_indices.extend(batch['indices'].tolist())
    
    # Create new datamodule with consumed samples
    consumed_samples = len(initial_indices)
    new_datamodule = CodonFMDataModule(
        dataset=lambda seed: IndexTrackingDataset(seed, train_size=datamodule.dataset.train_size),
        seed=42,
        world_size=1,
        train_iters=datamodule.train_iters,
        collate_fn=collate_fn,
        train_batch_size=4,
        shuffle=True
    )
    new_datamodule.init_consumed_samples = consumed_samples
    new_datamodule.setup('fit')
    
    # Get next batch from new datamodule
    resumed_loader = new_datamodule.train_dataloader()
    resumed_batch = next(iter(resumed_loader))
    resumed_indices = resumed_batch['indices'].tolist()
    
    # Since we're using StatefulDataset with shuffling, we can't guarantee exact indices
    # but we can verify they're within bounds and the batch size is correct
    assert len(resumed_indices) == datamodule.train_batch_size  # Should always be full batch due to drop_last=True
    assert all(0 <= idx < datamodule.dataset.train_size for idx in resumed_indices)


def test_half_epoch_transition_resumption(datamodule):
    """Resume from half way through an epoch and verify correct continuation
    into the next epoch.
    """

    datamodule.setup('fit')

    # Reference indices for a complete first epoch
    reference_indices = []
    for batch in datamodule.train_dataloader():
        reference_indices.extend(batch['indices'].tolist())

    batches_per_epoch = len(reference_indices) // datamodule.train_batch_size
    # Resume after half the epoch (rounded down to full batch)
    resume_batches = batches_per_epoch // 2
    consumed_samples = resume_batches * datamodule.train_batch_size

    new_datamodule = CodonFMDataModule(
        dataset=lambda seed: IndexTrackingDataset(seed, train_size=datamodule.dataset.train_size),
        seed=42,
        world_size=1,
        train_iters=datamodule.train_iters,
        collate_fn=collate_fn,
        train_batch_size=datamodule.train_batch_size,
        shuffle=True
    )

    state_dict = {
        'consumed_samples': consumed_samples,
        'global_step': resume_batches
    }
    new_datamodule.load_state_dict(state_dict)
    new_datamodule.setup('fit')

    # How many batches are left in the current epoch?
    samples_remaining_in_epoch1 = len(reference_indices) - consumed_samples

    # Collect the remaining batches of epoch 1 *plus* two batches of epoch 2
    batches_to_collect = (samples_remaining_in_epoch1 // datamodule.train_batch_size) + 2

    resumed_indices = []
    for i, batch in enumerate(new_datamodule.train_dataloader()):
        if i >= batches_to_collect:
            break
        resumed_indices.extend(batch['indices'].tolist())

    # Split into tail of epoch 1 and head of epoch 2
    epoch1_end = resumed_indices[:samples_remaining_in_epoch1]
    epoch2_start = resumed_indices[samples_remaining_in_epoch1:]

    # ---- Assertions for end of epoch 1 ----
    assert len(epoch1_end) == samples_remaining_in_epoch1
    assert len(set(epoch1_end)) == len(epoch1_end)
    position_in_epoch = consumed_samples % datamodule.dataset.train_size
    expected_epoch1_end = reference_indices[position_in_epoch:position_in_epoch + samples_remaining_in_epoch1]
    assert epoch1_end == expected_epoch1_end

    # ---- Assertions for start of epoch 2 ----
    assert len(epoch2_start) == 2 * datamodule.train_batch_size
    assert len(set(epoch2_start)) == len(epoch2_start)
    epoch2_corresponding = reference_indices[:len(epoch2_start)]
    assert epoch2_start != epoch2_corresponding


def test_two_epoch_dataloader_calls(datamodule):
    """Ensure that successive calls to ``train_dataloader`` respect the number
    of already-consumed samples via ``trainer.global_step`` so that the second
    call begins at the start of the *next* epoch (with its own shuffle).
    """

    datamodule.setup('fit')
    # Attach a dummy trainer to drive global-step increment.
    DummyTrainer = type("DummyTrainer", (), {})
    datamodule.trainer = DummyTrainer()
    datamodule.trainer.global_step = 0

    # --------------------------- First epoch ---------------------------
    epoch1_indices = []
    for batch in datamodule.train_dataloader():
        epoch1_indices.extend(batch['indices'].tolist())

    batches_per_epoch = len(epoch1_indices) // datamodule.train_batch_size

    # Update global_step to reflect consumed batches (what lightning does).
    datamodule.trainer.global_step += batches_per_epoch

    # --------------------------- Second epoch --------------------------
    epoch2_indices = []
    for batch in datamodule.train_dataloader():
        epoch2_indices.extend(batch['indices'].tolist())

    expected_samples_per_epoch = (
        datamodule.dataset.train_size // datamodule.train_batch_size
    ) * datamodule.train_batch_size
    assert len(epoch1_indices) == expected_samples_per_epoch
    assert len(epoch2_indices) == expected_samples_per_epoch
    # Shuffle order between the two epochs should differ.
    assert epoch1_indices != epoch2_indices

@pytest.mark.skipif(
    (not torch.distributed.is_available()) or (int(os.environ.get("WORLD_SIZE", "1")) < 2),
    reason="requires distributed launcher with WORLD_SIZE>=2",
)
def test_distributed_indices(datamodule):
    """Test indexing behavior in a distributed setting."""
    import torch.distributed as dist
    
    # FIXME: this test takes a very long time to run
    
    # If CUDA available, ensure device 0 is used for this rank
    if torch.cuda.is_available():
        torch.cuda.set_device(0)
    
    try:
        datamodule.world_size = 2
        datamodule.setup('fit')
        train_loader = datamodule.train_dataloader()
        
        # Collect indices from this rank
        rank_indices = []
        for batch in train_loader:
            rank_indices.extend(batch['indices'].tolist())
            assert len(batch['indices'].tolist()) == datamodule.train_batch_size

        
        # In distributed mode, each rank gets half of the dataset
        # Since drop_last=True, we'll get complete batches up to half the dataset size
        expected_samples_per_rank = ((datamodule.dataset.train_size // 2) // 
                                   datamodule.train_batch_size * datamodule.train_batch_size)
        assert len(rank_indices) == expected_samples_per_rank
        
        # Verify indices are within bounds
        assert all(0 <= idx < datamodule.dataset.train_size for idx in rank_indices)
    
    finally:
        if dist.is_initialized():
            dist.destroy_process_group()


def test_validation_dataloader_without_internal_logger(datamodule):
    """Release dataloaders must not depend on the internal OneLogger callback."""
    datamodule.setup("fit")

    batch = next(iter(datamodule.val_dataloader()))

    assert set(batch["split"]) == {"val"}
