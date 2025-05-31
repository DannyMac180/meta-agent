from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys

_src = Path(__file__).resolve().parent.parent / "src" / "meta_agent" / "__init__.py"
_spec = spec_from_file_location(
    "meta_agent", _src, submodule_search_locations=[str(_src.parent)]
)
_module = module_from_spec(_spec)
sys.modules[__name__] = _module
_spec.loader.exec_module(_module)  # type: ignore
for k, v in _module.__dict__.items():
    globals()[k] = v
