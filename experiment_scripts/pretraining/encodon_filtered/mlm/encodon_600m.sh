#!/bin/bash
set -ex

: "${WANDB_PROJECT:?Set WANDB_PROJECT to your WandB project name}"
: "${WANDB_ENTITY:?Set WANDB_ENTITY to your WandB entity name}"

# - hyperparameters
learning_rate=7.5e-5
num_nodes=16
num_gpus=8
train_batch_size=8
val_batch_size=8
effective_batch_size=$((train_batch_size * num_gpus * num_nodes))
num_workers=12

exp_name="encodon_600m_latest_${learning_rate}_${effective_batch_size}_nopathogen"

# - run
python -m src.runner pretrain \
    --exp_name "$exp_name" \
    --model_name encodon_600m \
    --data_path /data/ncbi/processed_unfiltered/ \
    --process_item mlm_memmap \
    --dataset_name CodonMemmapDataset \
    --lr $learning_rate \
    --num_gpus $num_gpus \
    --num_nodes $num_nodes \
    --train_batch_size $train_batch_size \
    --val_batch_size $val_batch_size \
    --num_workers $num_workers \
    --bf16 \
    --split_name_prefix nopathogen \
    --taxid_exclusion_file /data/ncbi/taxids_to_remove.json \
    --checkpoints_dir /results/checkpoints/${exp_name} \
    --enable_wandb \
    --project_name "$WANDB_PROJECT" \
    --entity "$WANDB_ENTITY"
