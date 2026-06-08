# vLLM-Ascend Running & Troubleshooting

Guide for running and debugging vLLM on Ascend NPUs.

**Pre-run check**: Always verify available devices with `npu-smi info`.

______________________________________________________________________

## Phase 1: Offline Validation (Eager Mode)

*Start here. Write an offline inference script with eager mode enabled.*

1. **Get the Model Locally** — See [model-download.md](model-download.md). Record the local path as `$MODEL_PATH`.
2. **Check NPU Availability** — `npu-smi info`
3. **Estimate Parallelism** — Use safetensors to count params, compute TP/EP based on NPU HBM. TP must divide `num_attention_heads` and `num_key_value_heads` evenly.
4. **Write an Offline Script** — Standalone Python with `enforce_eager=True`, `os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"`.
5. **Quantized Model Check** — Set `quantization="ascend"` for quantized models. Do NOT set for bf16/fp16.
6. **Trust Remote Code** — Set `trust_remote_code=True` for custom architectures (Qwen3, DeepSeek, GLM, etc.).

______________________________________________________________________

## Phase 2: Performance Optimization

1. **Disable Eager Mode** — Remove `enforce_eager=True` to activate ACL Graph capture.
2. **Read Model-Specific Docs** — Check `vllm-ascend/docs/source/tutorials/models/` for recommended flags.
3. **Set Graph Capture Sizes** — `cudagraph_capture_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256]`

### Scenario-Based Tuning

| Scenario | Key Parameters |
| :--- | :--- |
| **High Concurrency + Steady** | `--max-num-seqs` ↑, FULL graph mode |
| **Long Context / RAG** | `--gpu-memory-utilization 0.95`, enable quantization |
| **TTFT-Sensitive + Bursty** | `--max-num-seqs` ↓, `--max-num-batched-tokens` with headroom |
| **TPOT-Sensitive** | `--speculative-config` with draft model |
| **Memory-Constrained** | `--gpu-memory-utilization 0.9`→`0.95`, lower `--max-num-seqs` |

______________________________________________________________________

## Phase 3: Online Serving

1. **Ask the user** for `model-served-name` and `port`.
2. **Convert to API server** — Wrap in shell script with `2>&1 | tee` log capture.
3. **Health Check** — `curl http://<host>:<port>/v1/models`
4. **Test Request** — Send a chat/completion curl request.

### Graceful Shutdown

```bash
kill -2 $(pgrep -f "vllm serve")
```
