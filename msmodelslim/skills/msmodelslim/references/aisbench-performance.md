# AISBench Performance Evaluation Guide

Performance benchmarking measures throughput, latency, and concurrency of a running vLLM service. Differences from accuracy eval:

1. Add `--mode perf`
2. Use **streaming** model backend (`vllm_api_stream_chat`)

---

## Prerequisite: vLLM Service

```bash
vllm serve /path/to/model --host 0.0.0.0 --port 8080 --served-model-name DeepSeek-R1
```

---

## Step 1 — Locate AISBench

```bash
pip show ais_bench_benchmark
```

---

## Step 2 — Choose a Dataset

**Option A: Existing dataset** (same as accuracy eval)

**Option B: Synthetic dataset** (recommended for controlled I/O lengths):

```bash
ais_bench --models vllm_api_stream_chat --datasets synthetic_gen --mode perf
```

Configure `synthetic_config.py`:
```python
synthetic_config = {
    "Type": "string", "RequestCount": 1000,
    "StringConfig": {
        "Input":  {"Method": "uniform", "Params": {"MinValue": 512, "MaxValue": 2048}},
        "Output": {"Method": "uniform", "Params": {"MinValue": 128, "MaxValue": 512}},
    }
}
```

---

## Step 3 — Configure Model Client

```bash
ais_bench --models vllm_api_stream_chat --mode perf --search
```

Edit `vllm_api_stream_chat.py`:

```python
models = [dict(
    type=VLLMCustomAPIChatStream,   # streaming required
    model="DeepSeek-R1",
    host_ip="localhost",
    host_port=8080,
    max_out_len=512,
    batch_size=64,                   # primary variable to sweep
    generation_kwargs=dict(
        temperature=1.0, top_p=1.0,
        ignore_eos=True,             # force full output length
    ),
)]
```

Key differences from accuracy: `type=VLLMCustomAPIChatStream`, `ignore_eos=True`, higher `batch_size`.

---

## Step 4 — Run

```bash
ais_bench --models vllm_api_stream_chat --datasets demo_gsm8k_gen --mode perf --debug

# Smoke test with limited requests
ais_bench --models vllm_api_stream_chat --datasets synthetic_gen --mode perf --num-prompts 100
```

---

## Step 5 — Read Results

Saved under `outputs/default/<timestamp>/performances/<model-abbr>/`:
- `<dataset>.csv` — per-request latency breakdown
- `<dataset>.json` — end-to-end summary metrics
- `<dataset>_plot.html` — concurrency visualization

Key metrics:

| Metric | What it measures |
|--------|-----------------|
| **TTFT** | Time To First Token — prefill latency |
| **TPOT** | Time Per Output Token — decode latency |
| **E2EL** | End-to-End Latency |
| **Output Token Throughput** | decode tokens/s — primary metric |

---

## Concurrency Sweep

```bash
for BS in 1 4 16 64 128 256; do
    sed -i "s/batch_size=.*/batch_size=$BS,/" $LOCATION/.../vllm_api_stream_chat.py
    ais_bench --models vllm_api_stream_chat --datasets synthetic_gen --mode perf --num-prompts 200
done
```
