"""Build deployment caches for ML models and the railway station graph."""
from .ml_models import FreightModels
from .simulation import GRAPH


def main():
    models = FreightModels()
    source = "cache" if models.loaded_from_cache else "training"
    print(
        f"[build] ML models ready from {source}: {models.trained_rows:,} rows",
        flush=True,
    )
    print(f"[build] railway graph ready: {len(GRAPH):,} nodes", flush=True)


if __name__ == "__main__":
    main()
