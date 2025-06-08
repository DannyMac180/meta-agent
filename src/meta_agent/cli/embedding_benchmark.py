"""CLI commands for embedding model benchmarking."""

import click


@click.command()
@click.option(
    "--models",
    multiple=True,
    help="Specific models to benchmark (e.g., 'openai:text-embedding-3-small')",
)
@click.option(
    "--save/--no-save",
    default=True,
    help="Save benchmark results to file",
)
def benchmark_embeddings(models, save):
    """Run embedding model benchmarks for template retrieval."""
    from ..embedding_benchmark import TemplateBenchmarkRunner
    from ..embedding_models import EmbeddingModelSelector

    runner = TemplateBenchmarkRunner()

    if models:
        # Parse specified models
        model_instances = []
        selector = EmbeddingModelSelector()
        for model_name in models:
            try:
                model = selector.get_model_by_name(model_name)
                model_instances.append(model)
                click.echo(f"Added model: {model_name}")
            except Exception as e:
                click.echo(f"Failed to load model {model_name}: {e}", err=True)

        if not model_instances:
            click.echo("No valid models specified, using defaults", err=True)
            model_instances = None
    else:
        model_instances = None

    click.echo("Running embedding model benchmark...")

    try:
        results = runner.run_benchmark(models=model_instances, save_results=save)
        runner.print_results(results)

        if save:
            click.echo(f"\nResults saved to: {runner.results_dir}")

    except Exception as e:
        click.echo(f"Benchmark failed: {e}", err=True)
        raise


if __name__ == "__main__":
    benchmark_embeddings()
