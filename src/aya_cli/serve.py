import subprocess
import shutil
import sys
from pathlib import Path
from aya_cli.config import get_models_list, get_server_opts, load_config
from aya_cli.check_specs import check_specs

# ---------------------------------------------------------------------------
#  Auto-install helpers (per-platform)
# ---------------------------------------------------------------------------

def _install_llama_via_brew() -> str | None:
    """Attempt to install llama.cpp via Homebrew (macOS)."""
    if not shutil.which("brew"):
        return None
    print("llama-server not found. Installing via Homebrew (brew install llama.cpp)...", file=sys.stderr)
    try:
        result = subprocess.run(
            ["brew", "install", "llama.cpp"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        print(
            "brew install llama.cpp timed out after 300 seconds. "
            "Please try running the installation manually.",
            file=sys.stderr,
        )
        return None
    if result.returncode != 0:
        return None
    result = subprocess.run(
        ["brew", "--prefix", "llama.cpp"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0 or not result.stdout:
        return shutil.which("llama-server")
    prefix = result.stdout.strip()
    path = Path(prefix) / "bin" / "llama-server"
    return str(path) if path.exists() else shutil.which("llama-server")


def _install_llama_via_winget() -> str | None:
    """Attempt to install llama.cpp via winget (Windows 10/11)."""
    if not shutil.which("winget"):
        return None
    print("llama-server not found. Installing via winget (winget install ggml-org.llama.cpp)...", file=sys.stderr)
    try:
        result = subprocess.run(
            ["winget", "install", "ggml-org.llama.cpp",
             "--accept-source-agreements", "--accept-package-agreements"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        print(
            "winget install timed out after 300 seconds. "
            "Please try running the installation manually.",
            file=sys.stderr,
        )
        return None
    if result.returncode != 0:
        return None
    # winget installs may require a new shell to pick up PATH changes
    path = shutil.which("llama-server") or shutil.which("llama-server.exe")
    if path:
        return path
    print(
        "llama-server was installed but not found on PATH. "
        "Please restart your terminal and try again.",
        file=sys.stderr,
    )
    return None

# ---------------------------------------------------------------------------
#  Resolve llama-server binary
# ---------------------------------------------------------------------------

def _resolve_llama_server() -> str | None:
    """Find or auto-install the llama-server binary."""
    path = shutil.which("llama-server")
    if path:
        return path
    if sys.platform == "darwin":
        path = _install_llama_via_brew()
        if path:
            return path
    elif sys.platform == "win32":
        path = _install_llama_via_winget()
        if path:
            return path
    return None


def _llama_not_found_message() -> str:
    """Return a platform-appropriate error message when llama-server is missing."""
    lines = ["llama-server not found."]
    if sys.platform == "darwin":
        lines.append("  Install with: brew install llama.cpp")
    elif sys.platform == "win32":
        lines.append("  Install with: winget install ggml-org.llama.cpp")
    elif sys.platform == "linux":
        lines.append("  Install from your package manager or build from source.")
    lines.append("  Or build from source: https://github.com/ggml-org/llama.cpp")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
#  Main serve command
# ---------------------------------------------------------------------------

def run_serve() -> None:
    check_specs()
    config = load_config()
    models = get_models_list(config) if config else []
    if not models:
        print("No models configured. Run `aya-cli install` to add a model.", file=sys.stderr)
        raise SystemExit(1)
    existing = [m for m in models if Path(m["model_path"]).exists()]
    if not existing:
        print(
            "Configured models not found on disk. Run `aya-cli install` to reinstall or fix model paths.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if len(existing) == 1:
        chosen = existing[0]
    else:
        if not sys.stdin.isatty():
            chosen = existing[0]
            print("Multiple models installed; no TTY detected. Using first model.", file=sys.stderr)
        else:
            print("Multiple models installed. Select one to run:")
            for i, m in enumerate(existing, 1):
                print(f"  {i}. {m.get('quant', '')} — {m['model_path']}")
            while True:
                try:
                    raw = input("Choice (1–{}): ".format(len(existing))).strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nNo input received; using first model.", file=sys.stderr)
                    chosen = existing[0]
                    break
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
        print(_llama_not_found_message(), file=sys.stderr)
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
    print(f"OpenAI-compatible API: http://localhost:{port}/v1")
    print("Press Ctrl+C to stop.")
    process = subprocess.run(cmd)
    if process.returncode != 0:
        print(
            f"llama-server exited with code {process.returncode}. Check logs above for errors.",
            file=sys.stderr,
        )
        raise SystemExit(process.returncode)
