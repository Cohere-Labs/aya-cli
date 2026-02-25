import sys
from pathlib import Path

from aya_cli.config import CONFIG_DIR, get_models_list, load_config

def check_models() -> None:
    if not CONFIG_DIR.exists():
        print(f"Config directory not found: {CONFIG_DIR}. Run `aya-cli install` first.", file=sys.stderr)
        raise SystemExit(1)

    config = load_config()
    models = get_models_list(config) if config else []
    if not models:
        print("No model path in config. Run `aya-cli install` first.", file=sys.stderr)
        raise SystemExit(1)

    existing = [m for m in models if Path(m["model_path"]).exists()]
    if not existing:
        print("No installed model file found. Run `aya-cli install` again.", file=sys.stderr)
        raise SystemExit(1)

    for m in existing:
        print(f"Model: {m.get('quant', '')} — {m['model_path']}")

def main() -> None:
    check_models()

if __name__ == "__main__":
    main()
