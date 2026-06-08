# AISBench Installation

## Prerequisites

Python 3.10, 3.11, or 3.12 required (not 3.9 or 3.13+). Check:

```bash
python3 --version
```

## Install

Ask the user: **where do you want to clone the AISBench repo?**

```bash
git clone https://github.com/AISBench/benchmark.git $TARGET_DIR
cd $TARGET_DIR
pip3 install -e ./ --use-pep517
pip3 install -r requirements/api.txt
pip3 install -r requirements/extra.txt
```

**Optional extras:**

| Extra | When to install |
| :--- | :--- |
| `requirements/hf_vl_dependency.txt` | HuggingFace VLM / vLLM offline VL inference |
| `requirements/datasets/bfcl_dependencies.txt --no-deps` | BFCL function-calling benchmark |
| `requirements/datasets/ocrbench_v2.txt` | OCRBench_v2 dataset |

## Verify

```bash
ais_bench -h
pip show ais_bench_benchmark
```

The `Editable project location` field is the root used for all config paths.
