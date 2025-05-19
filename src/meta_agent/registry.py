import importlib
import json
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from packaging.version import parse as parse_version

logger = logging.getLogger(__name__)

GENERATED_TOOLS_BASE_DIR_NAME = "generated_tools"
METADATA_FILE_NAME = "metadata.json"
TOOL_CODE_FILE_NAME = "tool.py"


@dataclass
class GeneratedTool:
    """Represents a generated tool's source code and metadata."""

    name: str
    description: str
    code: str  # The Python code for the tool
    specification: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """
    Manages the registration, loading, and discovery of dynamically generated tools.
    """

    def __init__(self, base_dir: Union[str, Path] = "src/meta_agent"):
        self.base_dir = Path(base_dir)
        if not self.base_dir.is_absolute():
            current_file_dir = Path(__file__).parent
            self.base_dir = current_file_dir
        self.tools_dir = self.base_dir / GENERATED_TOOLS_BASE_DIR_NAME
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        (self.tools_dir / "__init__.py").touch(exist_ok=True)

    def _get_tool_version_dir(
        self, tool_name_sanitized: str, version_sanitized: str
    ) -> Path:
        return self.tools_dir / tool_name_sanitized / version_sanitized

    def _get_tool_package_dir(self, tool_name_sanitized: str) -> Path:
        return self.tools_dir / tool_name_sanitized

    def register(self, tool: GeneratedTool, version: str = "0.1.0") -> Optional[str]:
        tool_name_sanitized = tool.name.replace("-", "_").replace(" ", "_").lower()
        version_sanitized = "v" + version.replace(".", "_")
        tool_package_dir = self._get_tool_package_dir(tool_name_sanitized)
        tool_version_dir = self._get_tool_version_dir(
            tool_name_sanitized, version_sanitized
        )
        if tool_version_dir.exists():
            logger.warning(
                f"Tool '{tool.name}' version '{version}' already exists at {tool_version_dir}. Overwriting."
            )
        try:
            # Ensure all parent directories exist and are Python packages
            tool_version_dir.parent.parent.mkdir(parents=True, exist_ok=True)
            (tool_version_dir.parent.parent / "__init__.py").touch(exist_ok=True)
            tool_version_dir.parent.mkdir(exist_ok=True)
            (tool_version_dir.parent / "__init__.py").touch(exist_ok=True)
            tool_version_dir.mkdir(exist_ok=True)
            (tool_version_dir / "__init__.py").touch(exist_ok=True)

            # Create the tool code file
            tool_code_path = tool_version_dir / TOOL_CODE_FILE_NAME
            with open(tool_code_path, "w", encoding="utf-8") as f:
                f.write(tool.code)
            # Construct module path relative to tools_dir
            module_import_path = f"{GENERATED_TOOLS_BASE_DIR_NAME}.{tool_name_sanitized}.{version_sanitized}.tool"
            metadata = {
                "name": tool.name,
                "original_name": tool.name,
                "sanitized_name": tool_name_sanitized,
                "version": version,
                "sanitized_version": version_sanitized,
                "description": tool.description,
                "specification": tool.specification,
                "module_path": module_import_path,
            }
            metadata_path = tool_version_dir / METADATA_FILE_NAME
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            logger.info(
                f"Tool '{tool.name}' version '{version}' registered successfully at {tool_version_dir}"
            )
            return module_import_path
        except IOError as e:
            logger.error(
                f"Failed to register tool '{tool.name}' version '{version}': {e}"
            )
            if tool_version_dir.exists():
                shutil.rmtree(tool_version_dir)
            return None

    def _get_latest_version(self, tool_name_sanitized: str) -> Optional[str]:
        tool_package_dir = self._get_tool_package_dir(tool_name_sanitized)
        if not tool_package_dir.exists():
            return None
        versions = []
        for version_name_dir in tool_package_dir.iterdir():
            metadata_path = version_name_dir / METADATA_FILE_NAME
            if (
                version_name_dir.is_dir()
                and (version_name_dir / "__init__.py").exists()
                and metadata_path.exists()
            ):
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    if "version" in metadata:
                        versions.append(metadata["version"])
                except (IOError, json.JSONDecodeError):
                    logger.warning(f"Could not read metadata from {metadata_path}")
                    continue
        if not versions:
            return None
        latest_version_str = sorted(versions, key=parse_version, reverse=True)[0]
        return latest_version_str

    def load(self, tool_name: str, version: str = "latest") -> Optional[Any]:
        tool_name_sanitized = tool_name.replace("-", "_").replace(" ", "_").lower()
        if version == "latest":
            actual_version_str = self._get_latest_version(tool_name_sanitized)
            if not actual_version_str:
                logger.error(
                    f"No versions found for tool '{tool_name}'. Cannot load 'latest'."
                )
                return None
        else:
            actual_version_str = version
        version_sanitized = "v" + actual_version_str.replace(".", "_")
        metadata = self.get_tool_metadata(tool_name, actual_version_str)
        tool_code_file = (
            self._get_tool_version_dir(tool_name_sanitized, version_sanitized)
            / TOOL_CODE_FILE_NAME
        )
        if not tool_code_file.exists():
            logger.error(
                f"Tool code file not found for '{tool_name}' v{actual_version_str} at {tool_code_file}"
            )
            return None

        # Get metadata to get the module path
        metadata = self.get_tool_metadata(tool_name, actual_version_str)
        if not metadata or "module_path" not in metadata:
            logger.error(
                f"No metadata found for tool '{tool_name}' version '{actual_version_str}'"
            )
            return None

        module_full_path = metadata["module_path"]

        importlib.invalidate_caches()  # Ensure import system sees new files
        original_sys_path = sys.path[:]
        path_added_to_sys = False
        try:
            # Add the base directory to sys.path
            if str(self.base_dir) not in sys.path:
                sys.path.insert(0, str(self.base_dir))
                path_added_to_sys = True
                importlib.invalidate_caches()  # Ensure import system sees new files after sys.path change

            # Ensure generated_tools namespace covers this base directory
            pkg_name = GENERATED_TOOLS_BASE_DIR_NAME
            pkg_path = str(self.tools_dir)
            if pkg_name in sys.modules:
                pkg = sys.modules[pkg_name]
                if hasattr(pkg, "__path__") and pkg_path not in pkg.__path__:
                    pkg.__path__.append(pkg_path)
            else:
                spec = importlib.util.spec_from_file_location(
                    pkg_name, self.tools_dir / "__init__.py"
                )
                pkg = importlib.util.module_from_spec(spec)
                sys.modules[pkg_name] = pkg
                pkg.__path__ = [pkg_path]
                if spec and spec.loader:
                    spec.loader.exec_module(pkg)

            logger.info(f"[DIAGNOSTIC] Attempting to import: {module_full_path}")
            logger.info(f"[DIAGNOSTIC] Current sys.path: {sys.path}")
            tool_module = importlib.import_module(module_full_path)

            # Prefer a get_tool_instance factory if available
            factory = getattr(tool_module, "get_tool_instance", None)
            if callable(factory):
                tool_instance = factory()
                setattr(tool_instance, "get_tool_instance", factory)
                setattr(tool_instance, "__name__", tool_module.__name__)
                logger.info(
                    f"Tool '{tool_name}' version '{actual_version_str}' loaded successfully from {module_full_path} via factory"
                )
                return tool_instance

            # Fallback to a class named after the sanitized tool name or with 'Tool' suffix
            tool_class = getattr(tool_module, tool_name_sanitized, None)
            if not tool_class:
                camel = "".join(
                    part.capitalize() for part in tool_name_sanitized.split("_")
                )
                tool_class = getattr(tool_module, f"{camel}Tool", None) or getattr(
                    tool_module, camel, None
                )

            if tool_class:
                tool_instance = tool_class()
                logger.info(
                    f"Tool '{tool_name}' version '{actual_version_str}' loaded successfully from {module_full_path}"
                )
                return tool_instance
            else:
                logger.error(
                    f"Tool class not found in module '{module_full_path}' for '{tool_name}'"
                )
                return None
        except ImportError as e:
            logger.error(
                f"Failed to import tool '{tool_name}' version '{actual_version_str}' from {module_full_path}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading tool '{tool_name}' version '{actual_version_str}': {e}"
            )
            return None
        finally:
            if path_added_to_sys:
                sys.path = original_sys_path
                importlib.invalidate_caches()  # Ensure import system sees new files after sys.path restoration
                # Consider importlib.invalidate_caches() here if needed after sys.path restoration

    def list_tools(self) -> List[Dict[str, Any]]:
        available_tools = []
        if not self.tools_dir.exists():
            return available_tools
        for tool_name_dir in self.tools_dir.iterdir():
            if tool_name_dir.is_dir() and (tool_name_dir / "__init__.py").exists():
                tool_name_sanitized = tool_name_dir.name
                versions_data = []
                original_tool_name_display = tool_name_sanitized
                for version_dir in tool_name_dir.iterdir():
                    metadata_path = version_dir / METADATA_FILE_NAME
                    if (
                        version_dir.is_dir()
                        and (version_dir / "__init__.py").exists()
                        and metadata_path.exists()
                    ):
                        try:
                            with open(metadata_path, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                            versions_data.append(
                                {
                                    "version": metadata.get("version"),
                                    "sanitized_version": metadata.get(
                                        "sanitized_version"
                                    ),
                                    "description": metadata.get("description"),
                                    "module_path": metadata.get("module_path"),
                                    "specification": metadata.get("specification", {}),
                                }
                            )
                            if "original_name" in metadata:
                                original_tool_name_display = metadata["original_name"]
                        except (IOError, json.JSONDecodeError) as e:
                            logger.warning(
                                f"Could not read metadata for {version_dir}: {e}"
                            )
                if versions_data:
                    versions_data.sort(
                        key=lambda v: parse_version(v["version"]), reverse=True
                    )
                    available_tools.append(
                        {
                            "name": original_tool_name_display,
                            "sanitized_name": tool_name_sanitized,
                            "versions": versions_data,
                        }
                    )
        return available_tools

    def get_tool_metadata(
        self, tool_name: str, version: str = "latest"
    ) -> Optional[Dict[str, Any]]:
        tool_name_sanitized = tool_name.replace("-", "_").replace(" ", "_").lower()
        if version == "latest":
            actual_version_str = self._get_latest_version(tool_name_sanitized)
            if not actual_version_str:
                logger.warning(
                    f"No versions found for tool '{tool_name}'. Cannot get metadata for 'latest'."
                )
                return None
        else:
            actual_version_str = version
        version_sanitized = "v" + actual_version_str.replace(".", "_")
        metadata_path = (
            self._get_tool_version_dir(tool_name_sanitized, version_sanitized)
            / METADATA_FILE_NAME
        )
        if not metadata_path.exists():
            logger.warning(
                f"Metadata file not found for tool '{tool_name}' version '{actual_version_str}' at {metadata_path}"
            )
            return None
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(
                f"Error reading metadata for tool '{tool_name}' version '{actual_version_str}': {e}"
            )
            return None

    def unregister(self, tool_name: str, version: Optional[str] = None) -> bool:
        tool_name_sanitized = tool_name.replace("-", "_").replace(" ", "_").lower()
        tool_package_dir = self._get_tool_package_dir(tool_name_sanitized)
        if not tool_package_dir.exists():
            logger.warning(
                f"Tool '{tool_name}' (directory {tool_package_dir}) not found for unregistration."
            )
            return False
        if version:
            actual_version_str = version
            version_sanitized = "v" + actual_version_str.replace(".", "_")
            tool_version_dir = self._get_tool_version_dir(
                tool_name_sanitized, version_sanitized
            )
            if tool_version_dir.exists():
                try:
                    shutil.rmtree(tool_version_dir)
                    logger.info(
                        f"Unregistered tool '{tool_name}' version '{actual_version_str}'."
                    )
                    remaining_items = [
                        item
                        for item in tool_package_dir.iterdir()
                        if item.name != "__init__.py"
                    ]
                    if not remaining_items:
                        logger.info(
                            f"Parent directory for '{tool_name}' is empty, removing {tool_package_dir}."
                        )
                        shutil.rmtree(tool_package_dir)
                    return True
                except OSError as e:
                    logger.error(
                        f"Error unregistering tool '{tool_name}' version '{actual_version_str}': {e}"
                    )
                    return False
            else:
                logger.warning(
                    f"Tool '{tool_name}' version '{actual_version_str}' not found for unregistration at {tool_version_dir}."
                )
                return False
        else:
            try:
                shutil.rmtree(tool_package_dir)
                logger.info(
                    f"Unregistered all versions of tool '{tool_name}' by removing {tool_package_dir}."
                )
                return True
            except OSError as e:
                logger.error(
                    f"Error unregistering all versions of tool '{tool_name}': {e}"
                )
                return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"Added {src_path} to sys.path")
    registry = ToolRegistry()
    print(f"Using tools directory: {registry.tools_dir.resolve()}")
    if registry.tools_dir.exists():
        print(f"Cleaning up existing tools directory: {registry.tools_dir}")
        for item in registry.tools_dir.iterdir():
            if item.name != "__init__.py":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    sample_tool_code = """
# Dynamically loaded tool code
import logging
tool_logger = logging.getLogger(__name__)

def greet(name: str) -> str:
    tool_logger.info(f"Greet function called with {name}")
    return f"Hello, {name}!"

class GreeterTool:
    def __init__(self, salutation="Hello"):
        self.salutation = salutation
        tool_logger.info(f"GreeterTool initialized with {self.salutation}")

    def run(self, name: str) -> str:
        tool_logger.info(f"GreeterTool.run called with {name}")
        return f"{self.salutation}, {name} from GreeterTool!"

def get_tool_instance(): # A common entry point convention
    tool_logger.info("get_tool_instance called")
    return GreeterTool(salutation="Greetings")
"""
    tool_spec = {
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Name to greet"}},
        },
        "output_schema": {"type": "string", "description": "A greeting message"},
    }
    my_tool = GeneratedTool(
        name="MyExampleGreeter",
        description="A simple greeter tool for testing.",
        code=sample_tool_code,
        specification=tool_spec,
    )
    print("\n--- Registering Tool ---")
    module_path_v1 = registry.register(my_tool, version="0.1.0")
    if module_path_v1:
        print(f"Registered MyExampleGreeter v0.1.0 at module: {module_path_v1}")
    my_tool_v2_code = sample_tool_code.replace("GreeterTool!", "GreeterTool V2!")
    my_tool_v2 = GeneratedTool(
        name="MyExampleGreeter",
        description="V2 of greeter.",
        code=my_tool_v2_code,
        specification=tool_spec,
    )
    module_path_v2 = registry.register(my_tool_v2, version="0.2.0")
    if module_path_v2:
        print(f"Registered MyExampleGreeter v0.2.0 at module: {module_path_v2}")
    print("\n--- Listing Tools ---")
    tools_list = registry.list_tools()
    print(json.dumps(tools_list, indent=2))
    assert any(
        t["name"] == "MyExampleGreeter" for t in tools_list
    ), "MyExampleGreeter not found in list"
    print("\n--- Loading Tool v0.1.0 ---")
    loaded_tool_module_v1 = registry.load("MyExampleGreeter", version="0.1.0")
    assert loaded_tool_module_v1 is not None, "Failed to load MyExampleGreeter v0.1.0"
    if loaded_tool_module_v1:
        if hasattr(loaded_tool_module_v1, "get_tool_instance"):
            greeter_instance_v1 = loaded_tool_module_v1.get_tool_instance()
            result_v1 = greeter_instance_v1.run("Alice")
            print(f"v0.1.0 output: {result_v1}")
            assert "Greetings, Alice from GreeterTool!" in result_v1
        else:
            print("v0.1.0 module does not have get_tool_instance")
    print("\n--- Loading Latest Tool (should be v0.2.0) ---")
    latest_tool_module = registry.load("MyExampleGreeter", version="latest")
    assert latest_tool_module is not None, "Failed to load latest MyExampleGreeter"
    if latest_tool_module:
        if hasattr(latest_tool_module, "get_tool_instance"):
            latest_greeter_instance = latest_tool_module.get_tool_instance()
            result_latest = latest_greeter_instance.run("Bob")
            print(f"Latest output: {result_latest}")
            assert "Greetings, Bob from GreeterTool V2!" in result_latest
        else:
            print("Latest module does not have get_tool_instance")
    print("\n--- Getting Metadata for v0.1.0 ---")
    metadata_v1 = registry.get_tool_metadata("MyExampleGreeter", "0.1.0")
    if metadata_v1:
        print(json.dumps(metadata_v1, indent=2))
        assert metadata_v1["version"] == "0.1.0"
    print("\n--- Unregistering Tool v0.1.0 ---")
    unreg_v1_success = registry.unregister("MyExampleGreeter", version="0.1.0")
    assert unreg_v1_success, "Failed to unregister v0.1.0"
    tools_list_after_unregister_v1 = registry.list_tools()
    print(
        "List after unregistering v0.1.0:",
        json.dumps(tools_list_after_unregister_v1, indent=2),
    )
    my_greeter_info = next(
        (t for t in tools_list_after_unregister_v1 if t["name"] == "MyExampleGreeter"),
        None,
    )
    if my_greeter_info:
        assert not any(
            v["version"] == "0.1.0" for v in my_greeter_info["versions"]
        ), "v0.1.0 still found"
        assert any(
            v["version"] == "0.2.0" for v in my_greeter_info["versions"]
        ), "v0.2.0 not found"
    else:
        pass
    print("\n--- Unregistering All Versions of MyExampleGreeter ---")
    unreg_all_success = registry.unregister("MyExampleGreeter")
    assert unreg_all_success, "Failed to unregister all versions of MyExampleGreeter"
    tools_list_after_full_unregister = registry.list_tools()
    print(
        "List after unregistering all:",
        json.dumps(tools_list_after_full_unregister, indent=2),
    )
    assert not any(
        t["name"] == "MyExampleGreeter" for t in tools_list_after_full_unregister
    ), "MyExampleGreeter still found after full unregistration"
    print("\nTool Registry example script finished successfully.")
