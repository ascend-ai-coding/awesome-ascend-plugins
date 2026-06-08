# vLLM-Ascend Installation

Install vLLM from source on Ascend NPUs. The core requirement is version-pinning: `vllm-ascend` only works with a specific `vllm` commit.

______________________________________________________________________

## 1. Cleanup

Remove any conflicting installations before starting:

```bash
pip uninstall -y vllm vllm-ascend
```

______________________________________________________________________

## 2. Clone Repositories

Ask the user where they want to clone the repositories before proceeding. Then clone into that directory:

```bash
cd YOUR_DIR
git clone https://github.com/vllm-project/vllm.git
git clone https://github.com/vllm-project/vllm-ascend.git
```

______________________________________________________________________

## 3. Select vllm-ascend Version

Ask the user which version of `vllm-ascend` they want to install. List available tags:

```bash
git -C vllm-ascend tag --sort=-version:refname | head -20
```

- If the user specifies a version, check it out: `git -C vllm-ascend checkout $TAG`
- If the user doesn't know, stay on `main`.

______________________________________________________________________

## 4. Pin vllm to the Commit Expected by vllm-ascend

`vllm-ascend` is built against a specific `vllm` commit:

```bash
grep -r "VLLM_COMMIT\|vllm.*checkout\|vllm.*sha" vllm-ascend/.github/workflows/
cd vllm && git checkout $COMMIT_HASH && cd ..
```

______________________________________________________________________

## 5. Install vllm Core

```bash
cd vllm
VLLM_TARGET_DEVICE=empty pip install -v -e .
cd ..
```

______________________________________________________________________

## 6. Install vllm-ascend Plugin

```bash
cd vllm-ascend
pip install -v -e .
cd ..
```

______________________________________________________________________

## 7. Verify

```bash
pip list | grep vllm
python -c "import vllm; import vllm_ascend; print('OK')"
```
