"""Forward-model interface for the data-assimilation pipeline.

Every supported model implements this surface; the engines (`python/enkf.py`,
`python/pf.py`) and the orchestrator (`main.py`) call models *only* through it, so a
new model is added by writing a class with these methods and registering it in
`models/__init__.py` — with no engine changes.

Methods take the pipeline's `args` / `raw` dicts (the same ones the engines already
pass around), so a model is a thin, mostly-stateless adapter over its run mechanics.
"""

from abc import ABC, abstractmethod


class Model(ABC):
    #: registry key — the value of `-m/--model` and the arg-file "model" field.
    name: str = ""

    # --- runtime config -----------------------------------------------------
    @abstractmethod
    def run_config(self):
        """Dict of runtime knobs merged into the engine's run args (e.g. Docker image/version)."""

    # --- input readiness / instance setup -----------------------------------
    @abstractmethod
    def standard_inputs_ready(self, standard_inputs): ...
    @abstractmethod
    def instances_ready(self, ensemble_base, n_members): ...
    @abstractmethod
    def copy_standard_inputs(self, raw): ...

    # --- per-window run machinery -------------------------------------------
    @abstractmethod
    def start_containers(self, args, max_workers=None): ...
    @abstractmethod
    def stop_containers(self, args): ...
    @abstractmethod
    def run_window(self, window_start, window_end, args, max_workers=None): ...

    # --- state / output IO --------------------------------------------------
    @abstractmethod
    def read_ref_date(self, ensemble_base): ...
    @abstractmethod
    def model_output_depths(self, ensemble_base): ...
    @abstractmethod
    def load_T(self, ensemble_dir, args): ...
    @abstractmethod
    def clear_member_outputs(self, ensemble_base, member_ids, results_dir): ...
    @abstractmethod
    def accumulate_mean(self, member_ids, args): ...
    @abstractmethod
    def read_snapshot_T(self, member_id, args): ...
    @abstractmethod
    def write_snapshot_T(self, member_id, T_new, args): ...
