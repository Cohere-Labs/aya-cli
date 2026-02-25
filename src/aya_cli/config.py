import json
from pathlib import Path

CONFIG_DIR = Path("~/.config/aya-assist").expanduser()
MODELS_DIR = CONFIG_DIR / "model"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_PORT = 8000

AVAILABLE_MODELS = {
    "global": "CohereLabs/tiny-aya-global-GGUF",
    "earth": "CohereLabs/tiny-aya-earth-GGUF",
    "fire": "CohereLabs/tiny-aya-fire-GGUF",
    "water": "CohereLabs/tiny-aya-water-GGUF",
}
MODEL_SLUGS = list(AVAILABLE_MODELS.keys())
DEFAULT_MODEL = "global"
DEFAULT_N_CTX = 4096
DEFAULT_N_GPU_LAYERS = 99

def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None

def get_models_list(config: dict) -> list[dict]:
    """Return list of model entries; support old single-model config."""
    if not config:
        return []
    if "models" in config and isinstance(config["models"], list):
        return config["models"]
    if config.get("model_path"):
        return [{"model_path": config["model_path"], "quant": config.get("quant", ""), "repo_id": config.get("repo_id", "")}]
    return []

def get_server_opts(config: dict) -> dict:
    """Return port, n_ctx, n_gpu_layers from config or defaults."""
    return {
        "port": config.get("port", DEFAULT_PORT) if config else DEFAULT_PORT,
        "n_ctx": config.get("n_ctx", DEFAULT_N_CTX) if config else DEFAULT_N_CTX,
        "n_gpu_layers": config.get("n_gpu_layers", DEFAULT_N_GPU_LAYERS) if config else DEFAULT_N_GPU_LAYERS,
    }

def save_config(data: dict) -> None:
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
