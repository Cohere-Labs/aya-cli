# Guide to set up Tiny Aya locally and run it

**Mac only.** This CLI installs Tiny Aya GGUF from Hugging Face, picks a quantization based on your Mac’s specs, and runs an OpenAI-compatible API locally.

**Prerequisite (optional):** The API runs the `llama-server` binary from [llama.cpp](https://github.com/ggml-org/llama.cpp). If it’s not installed, `aya-cli serve` will automatically run `brew install llama.cpp` on macOS when Homebrew is available. You can also install it yourself beforehand: `brew install llama.cpp`.

## 1. Create and activate a virtual environment

From the project root (`tiny-aya/`):

```bash
uv venv
source .venv/bin/activate
```

## 2. Install the CLI and dependencies

With the venv activated:

```bash
uv pip install -e .
```

This installs `aya-cli` and its dependencies: `huggingface_hub`, `llama-cpp-python[server]`, and `typer`.

## 3. Log in to Hugging Face (required for download)

Tiny Aya is downloaded from Hugging Face. You must be logged in before running `aya-cli install`:

1. Get a token: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Run: `hf auth login` and paste the token when prompted  

## 4. Check your Mac specs and recommended quantization (optional)

To see your Mac’s hardware and which quantization is recommended:

```bash
aya-cli specs
```

This prints RAM, chip, and the suggested quant (`q4_0`, `q4_k_m`, `q8_0`, `f16`, `bf16`) with a short reason.

## 5. Download the model

```bash
aya-cli install
```

- The CLI checks that you’re on macOS and logged in to Hugging Face.
- **Model:** You choose one of four Tiny Aya variants: **global**, **earth**, **fire**, or **water** (interactive prompt or `--model` / `-m`). Default is **global**.
- **Quantization:** It then detects your Mac’s RAM and recommends a quantization (default is **q4_k_m**). You can: accept **[Y]**, use default **[n]**, or type a quant (e.g. `q8_0`) to override.

**Examples:**

- Interactive (model then quant): `aya-cli install`
- Pick model and quant from CLI: `aya-cli install --model earth --quant q8_0` or `aya-cli install -m fire -q q4_k_m`
- Only override quant: `aya-cli install --quant q8_0`

Models are saved under `~/.config/aya-assist/model/` and paths are stored in `~/.config/aya-assist/config.json`. You can install multiple variants; `aya-cli serve` lets you pick which one to run.

## 6. Start the OpenAI-compatible API

```bash
aya-cli serve
```

The API is at **http://localhost:8000/v1**. Chat UI: http://localhost:8000. Press Ctrl+C to stop.

**Server:** `aya-cli serve` runs the `llama-server` binary from [llama.cpp](https://github.com/ggml-org/llama.cpp). If `llama-server` is not on your PATH, the CLI will **auto-install** it via Homebrew on macOS (when `brew` is available). You can also install it yourself before running serve:

```bash
brew install llama.cpp
```

If Homebrew isn’t installed or the auto-install fails, install llama.cpp manually or [build from source](https://github.com/ggml-org/llama.cpp).

---

## Quick reference

| Step              | Command |
|-------------------|--------|
| (Optional) Install llama.cpp | `brew install llama.cpp` — or auto-installed on first `aya-cli serve` |
| Create venv       | `uv venv` |
| Activate venv     | `source .venv/bin/activate` |
| Install CLI       | `pip install -e .` |
| Log in to HF      | `hf auth login` |
| Show Mac + recommendation | `aya-cli specs` |
| Download model    | `aya-cli install` · or `aya-cli install -m earth -q q8_0` |
| Run API           | `aya-cli serve` |

**Paths:** Config: `~/.config/aya-assist/config.json`, models: `~/.config/aya-assist/model/`.

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Cohere
