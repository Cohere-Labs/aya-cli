import sys
from pathlib import Path
from huggingface_hub import hf_hub_download
from aya_cli.config import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    MODELS_DIR,
    MODEL_SLUGS,
    DEFAULT_N_CTX,
    DEFAULT_N_GPU_LAYERS,
    DEFAULT_PORT,
    ensure_dirs,
    get_models_list,
    get_server_opts,
    load_config,
    save_config,
)
from aya_cli.check_specs import (
    AVAILABLE_QUANTS,
    check_specs,
    check_hf_auth,
    get_mac_specs,
    prompt_quant,
    recommend_quant,
)

DEFAULT_QUANT = "q4_k_m"

def _prompt_model() -> str:
    print("Available Tiny Aya models:")
    for i, slug in enumerate(MODEL_SLUGS, 1):
        print(f"  {i}. {slug} — {AVAILABLE_MODELS[slug]}")
    print(f"  Default: {DEFAULT_MODEL}")
    if not sys.stdin.isatty():
        print("No TTY; using default model.", file=sys.stderr)
        return DEFAULT_MODEL
    raw = input(f"Choice [1-{len(MODEL_SLUGS)} or slug, Enter for default]: ").strip().lower()
    if not raw:
        return DEFAULT_MODEL
    if raw in MODEL_SLUGS:
        return raw
    try:
        idx = int(raw)
        if 1 <= idx <= len(MODEL_SLUGS):
            return MODEL_SLUGS[idx - 1]
    except ValueError:
        pass
    print(f"Unknown '{raw}'; using default ({DEFAULT_MODEL}).", file=sys.stderr)
    return DEFAULT_MODEL

def run_install(model: str | None = None, quant: str | None = None) -> None:
    ensure_dirs()
    check_specs()
    check_hf_auth()

    if model is not None:
        if model not in MODEL_SLUGS:
            print(
                f"Unknown model '{model}'. Available: {', '.join(MODEL_SLUGS)}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        chosen_model = model
        print(f"Using model: {chosen_model} (from --model)")
    else:
        chosen_model = _prompt_model()
        if chosen_model != DEFAULT_MODEL:
            print(f"Using model: {chosen_model}")

    repo_id = AVAILABLE_MODELS[chosen_model]

    if quant is not None:
        if quant not in AVAILABLE_QUANTS:
            print(
                f"Unknown quant '{quant}'. Available: {', '.join(AVAILABLE_QUANTS)}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        chosen = quant
        print(f"Using quantization: {chosen} (from --quant)")
    else:
        specs = get_mac_specs()
        if specs:
            print(f"Mac: {specs.chip} | {specs.ram_gb:.1f} GB RAM")
            print()
            recommended, reason = recommend_quant(specs)
            chosen = prompt_quant(recommended, reason)
        else:
            print(f"Could not detect Mac specs. Using default: {DEFAULT_QUANT}")
            chosen = DEFAULT_QUANT

    filename = f"tiny-aya-{chosen_model}-{chosen}.gguf"
    path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(MODELS_DIR),
    )
    model_path = str(Path(path).resolve())
    entry = {"model_path": model_path, "quant": chosen, "repo_id": repo_id}

    config = load_config()
    models = get_models_list(config)
    server_opts = get_server_opts(config) if config else {"port": DEFAULT_PORT, "n_ctx": DEFAULT_N_CTX, "n_gpu_layers": DEFAULT_N_GPU_LAYERS}
    if not models:
        server_opts = {"port": DEFAULT_PORT, "n_ctx": DEFAULT_N_CTX, "n_gpu_layers": DEFAULT_N_GPU_LAYERS}
    existing_paths = {m["model_path"] for m in models}
    if model_path not in existing_paths:
        models.append(entry)
    save_config({**server_opts, "models": models})

    print(f"Model saved to: {model_path}")
    print("Run `aya-cli serve` to start the API.")
