"""Template mixing and inheritance utilities."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import BaseLoader, Environment, TemplateNotFound

from .template_registry import TemplateRegistry


def _split_name(name: str) -> Tuple[str, str]:
    """Split ``slug@version`` into components."""
    if "@" in name:
        slug, version = name.split("@", 1)
    else:
        slug, version = name, "latest"
    return slug, version


class _RegistryLoader(BaseLoader):
    """Jinja loader that pulls templates from a :class:`TemplateRegistry`."""

    def __init__(self, registry: TemplateRegistry) -> None:
        self.registry = registry

    def get_source(self, environment: Environment, template: str) -> str:
        slug, version = _split_name(template)
        source = self.registry.load_template(slug, version)
        if source is None:
            raise TemplateNotFound(template)
        return source


class TemplateMixer:
    """Render templates that extend or include other templates."""

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self.registry = registry or TemplateRegistry()
        self.env = Environment(loader=_RegistryLoader(self.registry))

    def render(
        self,
        slug: str,
        *,
        version: str = "latest",
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a template and all of its dependencies."""
        name = slug if version == "latest" else f"{slug}@{version}"
        template = self.env.get_template(name)
        return template.render(**(context or {}))

    def dependency_graph(
        self, slug: str, *, version: str = "latest"
    ) -> Dict[str, List[str]]:
        """Return a mapping of template to templates it references via ``extends`` or ``include``."""

        visited: Dict[str, List[str]] = {}
        pattern = re.compile(r"{%\s*(?:extends|include)\s+'([^']+)'")

        def _walk(name: str) -> None:
            if name in visited:
                return
            s, v = _split_name(name)
            source = self.registry.load_template(s, v) or ""
            deps = pattern.findall(source)
            visited[name] = deps
            for dep in deps:
                _walk(dep)

        root = slug if version == "latest" else f"{slug}@{version}"
        _walk(root)
        return visited
