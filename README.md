# Guide to set up Tiny Aya locally and run it

**Cross-platform (macOS, Windows, Linux).** This CLI installs Tiny Aya GGUF from Hugging Face, picks a quantization based on your system specs, and runs an OpenAI-compatible API locally.

**Prerequisite:** The API runs the `llama-server` binary from [llama.cpp](https://github.com/ggml-org/llama.cpp). If it's not installed, `aya-cli serve` will attempt to auto-install it:
- **macOS**: via Homebrew (`brew install llama.cpp`)
- **Windows**: via winget (`winget install ggml-org.llama.cpp`)
- **Linux**: manual install required (see [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases))

## 1. Create and activate a virtual environment

From the project root:

**macOS / Linux:**
```bash
uv venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
uv venv
.venv\Scripts\Activate.ps1
```

## 2. Install the CLI and dependencies

With the venv activated:

```bash
uv pip install -e .
```

This installs `aya-cli` and its dependencies: `huggingface_hub` and `typer`.

## 3. Log in to Hugging Face (required for download)

Tiny Aya is downloaded from Hugging Face. You must be logged in before running `aya-cli install`:

1. Get a token: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Run: `hf auth login` and paste the token when prompted  

## 4. Check your system specs and recommended quantization (optional)

To see your hardware specs and which quantization is recommended:

```bash
aya-cli specs
```

This prints RAM, CPU, architecture, and the suggested quant (`q4_0`, `q4_k_m`, `q8_0`, `f16`, `bf16`) with a short reason.

## 5. Download the model

```bash
aya-cli install
```

- The CLI detects your system specs and recommends a quantization.
- **Model:** You choose one of four Tiny Aya variants: **global**, **earth**, **fire**, or **water** (interactive prompt or `--model` / `-m`). Default is **global**.
- **Quantization:** It detects your system's RAM and recommends a quantization (default is **q4_k_m**). You can: accept **[Y]**, use default **[n]**, or type a quant (e.g. `q8_0`) to override.

**Examples:**

- Interactive (model then quant): `aya-cli install`
- Pick model and quant from CLI: `aya-cli install --model earth --quant q8_0` or `aya-cli install -m fire -q q4_k_m`
- Only override quant: `aya-cli install --quant q8_0`

**Config & model paths:**
- **macOS / Linux:** `~/.config/aya-assist/config.json` and `~/.config/aya-assist/model/`
- **Windows:** `%LOCALAPPDATA%\aya-assist\config.json` and `%LOCALAPPDATA%\aya-assist\model\`

You can install multiple variants; `aya-cli serve` lets you pick which one to run.

## 6. Start the OpenAI-compatible API

```bash
aya-cli serve
```

The API is at **http://localhost:8000/v1**. Chat UI: http://localhost:8000. Press Ctrl+C to stop.

**Server:** `aya-cli serve` runs the `llama-server` binary from [llama.cpp](https://github.com/ggml-org/llama.cpp). If `llama-server` is not on your PATH, the CLI will attempt auto-install:
- **macOS**: `brew install llama.cpp`
- **Windows**: `winget install ggml-org.llama.cpp`

If auto-install fails, install llama.cpp manually or [build from source](https://github.com/ggml-org/llama.cpp).

---

## Quick reference

| Step              | Command |
|-------------------|--------|
| Install llama.cpp (macOS) | `brew install llama.cpp` |
| Install llama.cpp (Windows) | `winget install ggml-org.llama.cpp` |
| Create venv       | `uv venv` |
| Activate venv (macOS/Linux) | `source .venv/bin/activate` |
| Activate venv (Windows) | `.venv\Scripts\Activate.ps1` |
| Install CLI       | `pip install -e .` |
| Log in to HF      | `hf auth login` |
| Show specs + recommendation | `aya-cli specs` |
| Download model    | `aya-cli install` · or `aya-cli install -m earth -q q8_0` |
| Run API           | `aya-cli serve` |

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Cohere
