"""Forward-model registry for the data-assimilation pipeline.

Selected via `main.py -m/--model` (default: simstrat).  For now only Simstrat is
supported, so each entry is just the model's Docker/runtime config — no class
hierarchy needed.  Add a model by adding an entry here; main.py merges the
selected entry into the Python engine's run args (single source of truth for the
model's Docker invocation).
"""

# name -> runtime config the Python engine reads (see functions.build_python_run_args).
MODELS = {
    "simstrat": {
        "simstrat_version": "3.0.4",
        "simstrat_binary":  "/entrypoint.sh",
        "simstrat_workdir": "/simstrat/run",
    },
}


def get_model(name):
    """Return the runtime config for model `name`, or raise with the valid choices."""
    if name not in MODELS:
        raise ValueError(f"unknown model '{name}'; choose from {sorted(MODELS)}")
    return MODELS[name]
