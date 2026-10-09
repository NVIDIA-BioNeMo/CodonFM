# Data Scripts

This directory contains scripts and notebooks for downloading, curating, preprocessing, and validating datasets used for CodonFM training and evaluation.

## Directory Structure

```
data_scripts/
├── process_gtf.py
├── download_preprocess_codonbert_bench.py
├── preprocess_validation.py
├── check_codon_frequency.py
├── ncbi_memmap_dataset_batched.py
└── data_curation/
    ├── download_cds_clean.ipynb
    ├── allseq_clustering_for_splits.ipynb
    └── taxids_to_remove_bac.json
```

## End-to-End Workflow

The scripts follow a pipeline with this general data flow:

```
1. Download & clean NCBI CDS data          (data_curation/download_cds_clean.ipynb)
       ↓  grouped CSV files per organism class
2. Convert to memory-mapped datasets       (ncbi_memmap_dataset_batched.py)
       ↓  memmap arrays + metadata
3. Cluster for train/val/test   (data_curation/allseq_clustering_for_splits.ipynb)
       ↓  cluster index file
4. Compute codon frequency statistics      (check_codon_frequency.py)

── Separately ──
5. Download benchmark datasets             (download_preprocess_codonbert_bench.py)
       ↓
6. Standardize & validate benchmarks       (preprocess_validation.py)
```

## Scripts

### `process_gtf.py`

Converts GENCODE GTF files into protein-coding transcript annotations (TSV) and transcript/exon BED files. Run with `--gtf-files` and optionally `--output-dir`.

### `data_curation/download_cds_clean.ipynb`

Main entry point for obtaining training data. Downloads NCBI RefSeq CDS sequences, filters by taxonomy, validates sequences (divisible-by-3 length, valid translation, no premature stop codons), removes duplicates, and writes grouped CSV files per organism class (e.g., `bacteria.csv`, `Primates.csv`).

### `ncbi_memmap_dataset_batched.py`

Converts the grouped CSV files into memory-mapped datasets suitable for training. Tokenizes CDS sequences using the project tokenizer, processes files in parallel, and chunks output by token count (default 1B tokens per chunk). Produces `sequences_chunk*.mmap`, `index_chunk*.mmap`, and `metadata.json`.

### `data_curation/allseq_clustering_for_splits.ipynb`

Creates sequence-similarity-based train/val/test splits. Translates CDS to amino acid sequences, clusters them with MMseqs2 (50% identity, 90% coverage), and outputs `allSeqClusterIdx.npy` mapping each sequence to a cluster ID.

### `check_codon_frequency.py`

Computes per-organism-group codon usage statistics from the processed memmap datasets. Filters out specified taxonomy IDs and writes frequency counts to JSON.

### `download_preprocess_codonbert_bench.py`

Downloads CodonBERT benchmark datasets from GitHub (CoV_Vaccine_Degradation, E.Coli_proteins, Fungal_expression, MLOS, Tc-Riboswitches, mRFP_Expression, mRNA_Stability). Supports downloading all datasets or a specific one.

### `preprocess_validation.py`

Standardizes and validates DNA sequence variant data from the benchmark datasets. Normalizes column names, handles multiple input formats, calculates codon positions, validates sequences, and adds unique IDs.

## Dependencies

- **Python packages**: pandas, polars, numpy, BioPython, requests
- **External tools**: [MMseqs2](https://github.com/soedinglab/MMseqs2) (for clustering in `allseq_clustering_for_splits.ipynb`)
- **Internal**: Tokenizer from `src/tokenizer/tokenizer.py`
