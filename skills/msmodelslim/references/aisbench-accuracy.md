# AISBench Accuracy Evaluation Guide

AISBench evaluates model accuracy by sending requests to a running vLLM service and comparing outputs against reference answers.

---

## Prerequisite: vLLM Service

```bash
vllm serve /path/to/model --host 0.0.0.0 --port 8080 --served-model-name DeepSeek-R1
```

Verify: `curl http://<host>:<port>/v1/models`

---

## Step 1 — Locate AISBench

```bash
pip show ais_bench_benchmark
```

If not found, follow [aisbench-install.md](aisbench-install.md). Use `Editable project location` as `$LOCATION`.

---

## Step 2 — Choose a Dataset

Ask the user which benchmark to run. List available datasets:

```bash
ls $LOCATION/ais_bench/benchmark/configs/datasets/
```

Prefer `chat_prompt` variants (e.g. `gsm8k_gen_4_shot_cot_chat_prompt`). Place dataset files under `$LOCATION/ais_bench/datasets/`.

---

## Step 3 — Configure Model and Dataset

```bash
ais_bench --models vllm_api_general_chat --datasets gsm8k_gen_4_shot_cot_chat_prompt --search
```

Edit the printed model config (`.py` file). Key fields:

```python
models = [dict(
    type=VLLMCustomAPIChat,
    model="DeepSeek-R1",
    host_ip="localhost",
    host_port=8080,
    max_out_len=512,
    batch_size=4,
    generation_kwargs=dict(temperature=0, top_p=0.95),
)]
```

---

## Step 4 — Run

```bash
ais_bench --models vllm_api_general_chat --datasets gsm8k_gen_4_shot_cot_chat_prompt --debug
```

Results saved under `outputs/default/<timestamp>/`:
- `summary/` — final accuracy scores
- `predictions/` — raw model outputs (JSON)
- `results/` — per-sample evaluation scores

---

## Multi-Task / Resume

```bash
# Multi-task
ais_bench --models vllm_api_general_chat vllm_api_stream_chat \
          --datasets gsm8k_gen aime2024_gen

# Resume interrupted run
ais_bench --models vllm_api_general_chat --datasets gsm8k_gen --reuse 20250628_151326

# Re-evaluate without re-running inference
ais_bench --models vllm_api_general_chat --datasets gsm8k_gen --mode eval --reuse 20250628_151326
```

---

## Troubleshooting

- **Truncated output**: raise `max_out_len`; check vLLM `--max-model-len`
- **Wrong answer format**: add `pred_postprocessor=dict(type=extract_non_reasoning_content)` (strips `<think>` tags)
- **Failed requests**: check `predictions/.../gsm8k_failed.json`; reduce `batch_size` if OOM
