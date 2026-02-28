import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from huggingface_hub import get_token

AVAILABLE_QUANTS = ["q4_0", "q4_k_m", "q8_0", "f16", "bf16"]
DEFAULT_QUANT = "q4_k_m"

@dataclass
class SystemSpecs:
    ram_gb: float
    arch: str
    chip: str
    cores: int
    platform_name: str  # "macOS", "Windows", "Linux"

# ---------------------------------------------------------------------------
#  macOS helpers
# ---------------------------------------------------------------------------

def _sysctl(key: str) -> str | None:
    try:
        out = subprocess.run(
            ["sysctl", "-n", key],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() if out.returncode == 0 and out.stdout else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def get_mac_specs() -> SystemSpecs | None:
    if sys.platform != "darwin":
        return None
    ram_bytes: int | None = None
    memsize = _sysctl("hw.memsize")
    if memsize:
        try:
            ram_bytes = int(memsize)
        except ValueError:
            pass
    ram_gb = (ram_bytes / (1024**3)) if ram_bytes else 0.0
    arch = platform.machine() or "unknown"
    chip = _sysctl("machdep.cpu.brand_string") or (
        "Apple Silicon" if arch == "arm64" else "Intel"
    )
    cores_str = _sysctl("hw.ncpu")
    cores = int(cores_str) if cores_str and cores_str.isdigit() else 0

    return SystemSpecs(ram_gb=ram_gb, arch=arch, chip=chip, cores=cores, platform_name="macOS")

# ---------------------------------------------------------------------------
#  Windows helpers
# ---------------------------------------------------------------------------

def _wmic(alias: str, field: str) -> str | None:
    """Query a WMI value via `wmic` when available.

    Note: `wmic` is deprecated on recent Windows versions and may be missing.
    This helper returns None if `wmic` is unavailable or the query fails.
    """
    try:
        out = subprocess.run(
            ["wmic", alias, "get", field, "/value"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0 or not out.stdout:
            return None
        for line in out.stdout.splitlines():
            if "=" in line:
                return line.split("=", 1)[1].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return None

def get_windows_specs() -> SystemSpecs | None:
    if sys.platform != "win32":
        return None

    # RAM
    ram_bytes_str = _wmic("OS", "TotalVisibleMemorySize")
    try:
        ram_gb = int(ram_bytes_str) / (1024**2) if ram_bytes_str else 0.0
    except (ValueError, TypeError):
        ram_gb = 0.0

    arch = platform.machine() or "unknown"

    # CPU name
    chip = _wmic("CPU", "Name") or platform.processor() or "Unknown CPU"

    # Core count
    cores_str = _wmic("CPU", "NumberOfLogicalProcessors")
    try:
        cores = int(cores_str) if cores_str else 0
    except (ValueError, TypeError):
        cores = 0

    return SystemSpecs(ram_gb=ram_gb, arch=arch, chip=chip, cores=cores, platform_name="Windows")

# ---------------------------------------------------------------------------
#  Linux helpers
# ---------------------------------------------------------------------------

def get_linux_specs() -> SystemSpecs | None:
    if sys.platform != "linux":
        return None

    # RAM from /proc/meminfo
    ram_gb = 0.0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    ram_gb = int(parts[1]) / (1024**2)  # kB -> GB
                    break
    except (OSError, ValueError, IndexError):
        pass

    arch = platform.machine() or "unknown"

    # CPU name from /proc/cpuinfo
    chip = "Unknown CPU"
    cores = 0
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name") and chip == "Unknown CPU":
                    chip = line.split(":", 1)[1].strip()
                if line.startswith("processor"):
                    cores += 1
    except OSError:
        pass

    return SystemSpecs(ram_gb=ram_gb, arch=arch, chip=chip, cores=cores, platform_name="Linux")

# ---------------------------------------------------------------------------
#  Unified dispatcher
# ---------------------------------------------------------------------------

def get_system_specs() -> SystemSpecs | None:
    """Detect hardware specs on the current platform."""
    if sys.platform == "darwin":
        return get_mac_specs()
    elif sys.platform == "win32":
        return get_windows_specs()
    elif sys.platform == "linux":
        return get_linux_specs()
    return None

def recommend_quant(specs: SystemSpecs) -> tuple[str, str]:
    ram = specs.ram_gb
    if ram <= 0:
        return "q4_k_m", "Could not detect RAM; defaulting to q4_k_m (good balance of quality and size)."

    if ram <= 10:
        return (
            "q4_0",
            f"Your system has {ram:.0f} GB RAM. q4_0 uses ~2 GB so you have room for context and other apps.",
        )
    if ram <= 16:
        return (
            "q4_k_m",
            f"Your system has {ram:.0f} GB RAM. q4_k_m gives the best quality/size balance and leaves headroom.",
        )
    if ram <= 24:
        return (
            "q8_0",
            f"Your system has {ram:.0f} GB RAM. q8_0 is the safe default; you can override with bf16 for higher quality.",
        )
    if ram <= 32:
        return (
            "bf16",
            f"Your system has {ram:.0f} GB RAM. bf16 fits comfortably and gives near-full quality.",
        )
    return (
        "f16",
        f"Your system has {ram:.0f} GB RAM. f16 recommended.",
    )

def check_specs() -> None:
    """Verify basic prerequisites."""
    if not shutil.which("python3") and not shutil.which("python"):
        print("Python is required.", file=sys.stderr)
        raise SystemExit(1)

def print_specs_and_recommendation() -> None:
    check_specs()
    specs = get_system_specs()
    if not specs:
        print("Could not detect system specs. Supported platforms: macOS, Windows, Linux.", file=sys.stderr)
        raise SystemExit(1)

    quant, reason = recommend_quant(specs)
    print(
        f"{specs.platform_name}: {specs.chip} | {specs.ram_gb:.1f} GB RAM | {specs.arch} | {specs.cores} cores"
    )
    print()
    print(f"Recommended quantization: {quant}")
    print(f"Reason: {reason}")
    print()
    print("Available Tiny Aya GGUF versions on Hugging Face: " + ", ".join(AVAILABLE_QUANTS))

def check_hf_auth() -> None:
    token = get_token()
    if token and token.strip():
        return
    print("You are not logged in to Hugging Face. Login is required to download the model.", file=sys.stderr)
    print(file=sys.stderr)
    print("To authenticate:", file=sys.stderr)
    print("  1. Get a token: https://huggingface.co/settings/tokens", file=sys.stderr)
    print("  2. Run in your terminal:", file=sys.stderr)
    print("     hf auth login", file=sys.stderr)
    print("  3. Paste the token when prompted (or set HF_TOKEN=your_token)", file=sys.stderr)
    print(file=sys.stderr)
    raise SystemExit(1)

def prompt_quant(specs_quant: str, reason: str) -> str:
    print("Default quantization: q4_k_m")
    print()
    print(f"Based on your system we recommend: {specs_quant}")
    print(f"Reason: {reason}")
    print()
    print("Options:")
    print("  [Y] Use recommended (" + specs_quant + ")")
    print("  [n] Use default (q4_k_m)")
    print("  Or type a quant to override: " + ", ".join(AVAILABLE_QUANTS))
    if not sys.stdin.isatty():
        print("No TTY; using recommended.", file=sys.stderr)
        return specs_quant
    try:
        raw = input("Choice [Y/n or quant]: ").strip().lower()
    except EOFError:
        print("No input received; using recommended.", file=sys.stderr)
        return specs_quant
    except KeyboardInterrupt:
        print("\nInterrupted; using recommended.", file=sys.stderr)
        return specs_quant
    if not raw or raw == "y" or raw == "yes":
        return specs_quant
    if raw == "n" or raw == "no":
        return DEFAULT_QUANT
    if raw in AVAILABLE_QUANTS:
        return raw
    for q in AVAILABLE_QUANTS:
        if q.replace("_", "") == raw.replace("_", ""):
            return q
    print(f"Unknown '{raw}'; using recommended ({specs_quant}).", file=sys.stderr)
    return specs_quant
