import typer
from aya_cli.install import run_install
from aya_cli.serve import run_serve
from aya_cli.check_specs import print_specs_and_recommendation

app = typer.Typer()

@app.command()
def install(
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Model variant to download: global, earth, fire, water. If omitted, prompts interactively.",
    ),
    quant: str | None = typer.Option(
        None,
        "--quant",
        "-q",
        help="Override recommended quantization (e.g. q4_0, q4_k_m, q8_0, f16, bf16).",
    ),
) -> None:
    run_install(model=model, quant=quant)


@app.command()
def specs() -> None:
    print_specs_and_recommendation()


@app.command()
def serve() -> None:
    run_serve()


def main() -> None:
    app()


if __name__ == "__main__":
    app()
