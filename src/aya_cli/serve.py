import subprocess
import shutil
import sys
from pathlib import Path
from aya_cli.config import get_models_list, get_server_opts, load_config
from aya_cli.check_specs import check_specs


def _install_llama_via_brew() -> str | None:
    if not shutil.which("brew"):
        return None
    print("llama-server not found. Installing via Homebrew (brew install llama.cpp)...", file=sys.stderr)
    result = subprocess.run(
        ["brew", "install", "llama.cpp"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        return None
    out = subprocess.run(
        ["brew", "--prefix", "llama.cpp"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if out.returncode != 0 or not out.stdout:
        return shutil.which("llama-server")
    prefix = out.stdout.strip()
    path = Path(prefix) / "bin" / "llama-server"
    return str(path) if path.exists() else shutil.which("llama-server")


def _resolve_llama_server() -> str | None:
    path = shutil.which("llama-server")
    if path:
        return path
    if sys.platform == "darwin":
        path = _install_llama_via_brew()
        if path:
            return path
    return None

def run_serve() -> None:
    check_specs()
    config = load_config()
    models = get_models_list(config) if config else []
    existing = [m for m in models if Path(m["model_path"]).exists()]
    if not existing:
        print("Run `aya-cli install` first, or no installed model found.", file=sys.stderr)
        raise SystemExit(1)

    if len(existing) == 1:
        chosen = existing[0]
    else:
        print("Multiple models installed. Select one to run:")
        for i, m in enumerate(existing, 1):
            print(f"  {i}. {m.get('quant', '')} — {m['model_path']}")
        if not sys.stdin.isatty():
            chosen = existing[0]
            print("No TTY; using first model.", file=sys.stderr)
        else:
            while True:
                raw = input("Choice (1–{}): ".format(len(existing))).strip()
                if raw.isdigit() and 1 <= int(raw) <= len(existing):
                    chosen = existing[int(raw) - 1]
                    break
                print("Invalid choice.", file=sys.stderr)

    model_path = chosen["model_path"]
    opts = get_server_opts(config)
    port = opts["port"]
    n_ctx = opts["n_ctx"]
    n_gpu_layers = opts["n_gpu_layers"]

    llama_server = _resolve_llama_server()
    if not llama_server:
        print(
            "llama-server not found. Install with: brew install llama.cpp\n"
            "Or build from source: https://github.com/ggml-org/llama.cpp",
            file=sys.stderr,
        )
        raise SystemExit(1)

    cmd = [
        llama_server,
        "-m",
        model_path,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--ctx-size",
        str(n_ctx),
        "-ngl",
        str(n_gpu_layers),
    ]
    print(f"OpenAI-compatible API: http://0.0.0.0:{port}/v1 (accessible on your local network)")
    print("Press Ctrl+C to stop.")
    subprocess.run(cmd)
