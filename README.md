# CodonFM: Foundation Models for Codon Sequences

CodonFM is a fully open-source suite of foundation models trained directly on codon sequences to learn contextual codon representations and enable downstream codon-aware tasks. We release the entire stack: code, training/finetuning/evaluation scripts, dockerized environments, experiment templates, and pre-trained model weights under an open license for transparent and reproducible use. 

Our primary model family, Encodon, uses masked language modeling over codons with scalable architectures (80M to 1B) and efficient memmapped data pipelines. Public links to the pre-trained checkpoints are here: [80M](https://huggingface.co/nvidia/NV-CodonFM-Encodon-80M-v1), [600M](https://huggingface.co/nvidia/NV-CodonFM-Encodon-600M-v1), [1B](https://huggingface.co/nvidia/NV-CodonFM-Encodon-1B-v1), [1B-Cdwt](https://huggingface.co/nvidia/NV-CodonFM-Encodon-Cdwt-1B-v1). 

The checkpoints can also be found on NGC [here](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/clara/models/nv_codonfm_encodon).

**Release v1.1 security scope:** This branch contains the Encodon model family and the release package and container security updates.

## Methodology and Results

The pre-print of this work with detailed methodology and results can be found [here](https://research.nvidia.com/labs/dbr/assets/data/manuscripts/nv-codonfm-preprint.pdf)

If you like this work please cite it as follows:
```bibtex
@article{codonfm_2025,
author = {Darabi+, Sajad and Cao+, Fan and Naghipourfar+, Mohsen and Rabi, Sara and Sethia, Ankit and Gion, Kyle and Grewal, Jasleen and Cohen, Jonathan and Greenleaf, William and Goodarzi*, Hani and Sundaram*, Laksshman},
title = {{Learning the language of codon translation with CodonFM}},
url = {https://research.nvidia.com/labs/dbr/assets/data/manuscripts/nv-codonfm-preprint.pdf},
year = {2025}
}
```
Note: Sajad Darabi, Fan Cao and Mohsen Naghipourfar are equal contributing first authors.

Corresponding Author: Hani Goodarzi and Laksshman Sundaram

## Accelerated CodonFM
This repository contains the exact code used in the [pre-print](#methodology-and-results). 

An accelerated version of the codebase is available in [BioNeMo Framework Recipes](https://github.com/NVIDIA/bionemo-framework/tree/main/bionemo-recipes/recipes/codonfm_ptl_te), which uses [TransformerEngine](https://github.com/NVIDIA/TransformerEngine) to accelerate training and inference. Accelerated checkpoints are available for all Encodon model variants: [80M](https://huggingface.co/nvidia/NV-CodonFM-Encodon-TE-80M-v1), [600M](https://huggingface.co/nvidia/NV-CodonFM-Encodon-TE-600M-v1), [1B](https://huggingface.co/nvidia/NV-CodonFM-Encodon-TE-1B-v1), [1B-Cdwt](https://huggingface.co/nvidia/NV-CodonFM-Encodon-TE-Cdwt-1B-v1).


## Table of Contents
- [Pre-trained Models](#pre-trained-models)
- [Repository Structure](#repository-structure)
- [Quickstart](#quickstart)
- [Data](#data-)
- [Running Training/Finetuning/Evaluation](#running-trainingfinetuningevaluation)
- [Using Wandb with CodonFM](#using-wandb-with-codonfm)
- [Testing](#testing)
- [License](#license)
- [Contact](#contact)

## Pre-trained Models

The table below summarizes the set of open source pre-trained weights currently made available. All of the training scripts are contained in the directory `experiment_scripts/pretraining/encodon_filtered/`.

Model | Variant | Hidden size | Layers | Heads | Intermediate | Script | Checkpoint
|---|---|---|---|---|---|---|---
Encodon 80M | MLM (random p=0.15) | 1024 | 6 | 8 | 4096 | `mlm/encodon_80m.sh` |  [link](https://huggingface.co/nvidia/NV-CodonFM-Encodon-80M-v1)
Encodon 600M | MLM (random p=0.15) | 2048 | 12 | 16 | 8192 | `mlm/encodon_600m.sh` |  [link](https://huggingface.co/nvidia/NV-CodonFM-Encodon-600M-v1)
Encodon 1B | MLM (random p=0.15) | 2048 | 18 | 16 | 8192 | `mlm/encodon_1b.sh` |  [link](https://huggingface.co/nvidia/NV-CodonFM-Encodon-1B-v1)
Encodon 1B (CDSWT) | MLM (codon frequency-weighted) | 2048 | 18 | 16 | 8192 | `cdswt/encodon_1b.sh` |  [link](https://huggingface.co/nvidia/NV-CodonFM-Encodon-Cdwt-1B-v1)

## Repository Structure
High-level overview (NerdTree-style):

```
codon-fm/
├── src/ — core library and CLI entrypoints
│   ├── runner.py — entry for pretrain/finetune/eval
│   ├── config.py — model/data/trainer configs
│   ├── tasks.py — pretraining/finetuning/eval tasks
│   ├── models/ — model definitions and components
│   ├── data/ — datamodules, datasets, preprocessing
│   │   └── preprocess/ — item level process items
│   ├── inference/ — inference wrappers and prediction definitions
│   ├── tokenizer/ — codon tokenizer and mappings
│   └── utils/ — logging, schedulers, writers, helpers
├── experiment_scripts/ — launch scripts for pre-training
│   └── pretraining/ — Encodon pretraining
├── data_scripts/ — data download and curation tools
├── notebooks/ — analysis and evaluation notebooks
├── pyproject.toml — package metadata, dependencies, and NGC image constraints
├── env.example — sample env vars
└── README.md — repo guide
```

## Quickstart
To run the scripts in this repository, we recommend using the provided Docker setup.

### 1. Clone the repository
```bash
git clone https://github.com/NVIDIA-BioNeMo/CodonFM
cd CodonFM
```
### 2. Docker Setup

The fastest way to get up and running with CodonFM is through the Docker setup below. This is an interactive development environment, you can build and launch a container that mounts your local repository. This allows you to edit code locally and run it inside the container.

To build and launch the development container, simply run the following from the root folder:

```bash
bash run_dev.sh
```

This script will:
1.  Build the development Docker image using the `development` target in the `Dockerfile`.
2.  Pass your user and group IDs to the container to avoid permission issues with mounted files.
3.  Stop and remove any existing container with the same name.
4.  Launch a new container with your local code mounted at `/workspace`, GPU access, isolated networking, a published Jupyter port, and the configured data directories.

You can also customize the data and checkpoint directory paths by passing arguments:
```bash
bash run_dev.sh --data-dir /path/to/your/data --checkpoints-dir /path/to/your/checkpoints
```

You will be dropped into a `bash` shell inside the container as a non-root user.

#### Evaluation Notebooks 📓

A series of notebooks in the `notebooks` directory show zero-shot variant prediction and downstream tasks that train Random Forest regressors on pretrained Encodon embeddings. See a brief overview below:

| Notebook | Description |
|---|---|
| [00-Mutation-Datasets-Preprocessing.ipynb](notebooks/00-Mutation-Datasets-Preprocessing.ipynb) | Prepare and harmonize mutation datasets used across evaluations. |
| [0-Zero-Shot-Mutation-Variant-CancerHotspot.ipynb](notebooks/0-Zero-Shot-Mutation-Variant-CancerHotspot.ipynb) | Zero-shot variant effect scoring on Cancer Hotspots. |
| [1-Zero-Shot-Mutation-Variant-DDD-ASD.ipynb](notebooks/1-Zero-Shot-Mutation-Variant-DDD-ASD.ipynb) | Zero-shot scoring on Deciphering Developmental Disorders (DDD) and autism spectrum disorder (ASD) cohort study, which catalogs genetic mutations linked to rare pediatric and developmental diseases, to evaluate separation of healthy versus disease coh on coding sequence context.|
| [2-Zero-Shot-Mutation-Variant-Clinvar-Alphamissense.ipynb](notebooks/2-Zero-Shot-Mutation-Variant-Clinvar-Alphamissense.ipynb) | Zero-shot evaluation on ClinVar missense variants classifying benign vs. pathogenic |
| [3-Zero-Shot-Mutation-Variant-Clinvar-Synonymous.ipynb](notebooks/3-Zero-Shot-Mutation-Variant-Clinvar-Synonymous.ipynb) | Zero-shot evaluation on ClinVar synonymous variants evaluating how the models separate benign versus pathogenic synonymous mutations.|
| [Encodon riboNN notebook](notebooks/4-EnCodon-Downstream-Task-riboNN.ipynb) | Predicts ribosome profiling signal intensity along coding sequences, evaluating how well models capture translation efficiency and codon-level regulation from sequence context. |
| [Encodon mRFP expression notebook](notebooks/5-EnCodon-Downstream-Task-mRFP-expression.ipynb) | Predicts fluorescent protein expression levels (mRFP) from coding sequences, testing how accurately models capture codon-dependent effects on translation efficiency and protein abundance.|
| [Encodon mRNA stability notebook](notebooks/6-EnCodon-Downstream-Task-mRNA-stability.ipynb) | Predicts mRNA stability from coding sequences evaluating how the models associate codon composition with stability of mRNA.|


### Data 📊

#### Pre-training Dataset

The data curation tools live under `data_scripts/data_curation/`.

- Main entrypoint: open and run `data_scripts/data_curation/download_cds_clean.ipynb`. It documents how to obtain coding sequences (CDS), process metadata, and produce curated outputs.
- Filtering resources: `data_scripts/data_curation/taxids_to_remove_bac.json` lists bacterial taxids to exclude during curation.
- Recommended environment: use the provided dev container (`bash run_dev.sh`), then open the notebook in Jupyter/VS Code and execute the cells.

Outputs from the notebook (cleaned CDS files and metadata tables) can be transformed into training-ready memory-mapped data with `data_scripts/ncbi_memmap_dataset_batched.py`. The resulting files can then be consumed by `CodonMemmapDataset`.

`CodonMemmapDataset` also requires a sequence cluster file, `allSeqClusterIdx.npy`, in the data directory to build train/val/test splits. Generate it with `data_scripts/data_curation/allseq_clustering_for_splits.ipynb` (see [data_scripts/README.md](data_scripts/README.md)).

#### Evaluation Datasets

- mRFP expression and mRNA stability:
  - Open and run the notebooks `notebooks/5-EnCodon-Downstream-Task-mRFP-expression.ipynb` and `notebooks/6-EnCodon-Downstream-Task-mRNA-stability.ipynb`. These notebooks contain cells that download/prepare the datasets and guide you through executing the evaluations end-to-end.
- Mean translation efficiency prediction task:
  - Open and run the notebook `notebooks/4-EnCodon-Downstream-Task-riboNN.ipynb`. It will download/prepare the downstream dataset and guide you through finetuning on this downstream task.
- Synonymous, DDD/ASD, and Cancer Hotspot variant datasets:
  - Follow `notebooks/00-Mutation-Datasets-Preprocessing.ipynb`. This notebook includes a cell that lists the required input files (with expected names/locations) and outlines how to process them into harmonized formats.
  - After preprocessing, use the task-specific notebooks in `notebooks/` (e.g., `0-...CancerHotspot.ipynb` and `1-...DDD-ASD.ipynb`) which consume the harmonized outputs produced by the preprocessing notebook.

### Running Training/Finetuning/Evaluation
The main entry point is available as either `python -m src.runner` or the installed `codon-fm` command. It supports three modes:
#### Pre-training

The explicit scripts used to train the released checkpoints are referenced in [Pre-trained Models](#pre-trained-models)
```bash
python -m src.runner pretrain \
    --out_dir <output_dir> \
    --exp_name <experiment_name> \
    --model_name <model_size> \
    --data_path <path_to_data> \
    --process_item mlm_memmap \
    --dataset_name CodonMemmapDataset \
    --lr <learning_rate> \
    --num_gpus <num_gpus> \
    --num_nodes <num_nodes>
```

Optional path overrides:
```bash
  --out_dir <dir>
  --checkpoints_dir <dir>
  --pretrained_ckpt_path <path>
```

**Available `--process_item` options:**
- `mlm_memmap`: Constructs MLM training examples using memory-mapped data input format.
- `mutation_pred_mlm`: Constructs mutation prediction scoring input for the model using ref/alt/mut pos
- `mutation_pred_likelihood`: Constructs input sentence with alt mutation at input to be scored by the model.
- `codon_sequence`: Constructs a codon sequence that can be inputed into the model.

**Available `--dataset_name` options:**
- `CodonMemmapDataset`: memory-mapped pre-training dataset for Encodon.
- `MutationDataset`: dataset for mutation prediction.
- `CodonBertDataset`: dataset to ingest codon sequences.
**Available `--model_name` options (examples):** `encodon_80m`, `encodon_600m`, `encodon_1b`.

#### Fine-tuning
The publicly available checkpoints can be finetuned using the finetuning options.

**Available finetuning options:**
- `lora`: Fine-tunes low-rank adapters within a pretrained model added to each transformer layer to reduce training cost and memory usage.
- `head_only_random`: Trains a randomly initialized output head while the remainder of the model is kept frozen.
- `head_only_pretrained`: Trains a pretrained output head while the remainder of the model is kept frozen.
- `full`: Fine-tunes all parameters of the model end-to-end

This is an example commandline for running finetuning:

```bash
python -m src.runner finetune \
    --out_dir <output_dir> \
    --exp_name <experiment_name> \
    --model_name <model_size> \
    --pretrained_ckpt_path <path_to_pretrained_checkpoint> \
    --data_path <path_to_data> \
    --process_item <process-item-to-use> \
    --dataset_name <dataset-name> \
    --finetune_strategy <strategy>
```

#### Evaluation
The publicly available checkpoints can be used to launch evaluation runs as well.

**Available tasks**
- `mutation_prediction`: Scores a specified mutation via ref-vs-alt codon log-likelihood ratio.
- `masked_language_modeling`: Predicts masked codon tokens from surrounding sequence context.
- `fitness_prediction`: Estimates sequence fitness as the mean log-likelihood of the sequence as predicted by the model.
- `embedding_prediction`: Extracts encoder CLS embeddings for each input.
- `downstream_prediction`: Uses the downstream cross-attention head for task-specific classification/regression.

This is an example commandline for running evaluation:

```bash
python -m src.runner eval \
    --out_dir <output_dir> \
    --exp_name <experiment_name> \
    --model_name <model_size> \
    --checkpoint_path <path_to_checkpoint> \
    --data_path <path_to_data> \
    --process_item <process-item-to-use> \
    --dataset_name <dataset-name> \
    --task_type <task_type> \
    --predictions_output_dir <output_directory>
```

## Using Wandb with CodonFM

To use Wandb with CodonFM, set your Weights & Biases API key for logging in the .env file:

```bash
# WANDB key (optional; only needed if enabling --enable_wandb)
export WANDB_API_KEY="your_wandb_api_key"
```
You can then source the .env file.

```bash
source .env
```

When launching runs, enable WandB logging by passing `--enable_wandb` with `--project_name` and `--entity`. Without `--enable_wandb`, the runner uses CSV logging; with it, both names are required.

Set your own project and entity values before running a pretraining script:

```bash
export WANDB_PROJECT="your_project_name"
export WANDB_ENTITY="your_entity_name"
```


## Testing

This repository includes a test suite to ensure code quality and functionality. To run the complete test suite:

```bash
# Run all tests
python -m pytest tests/
```

## License

Copyright @ 2025, NVIDIA Corporation. All rights reserved.
The source code is made available under Apache-2.0.
The model weights are made available under the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).

## Contact
Any questions or correspondance should be sent to nv-codonfm@nvidia.com
