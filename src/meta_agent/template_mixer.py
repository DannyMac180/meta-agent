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

        def _render_source(source: str) -> str:
            # handle extends directive
            match = re.search(r"{%\s*extends\s+'([^']+)'\s*%}", source)
            if match:
                parent_slug = match.group(1)
                parent = self.registry.load_template(parent_slug, version) or ""
                source = source.replace(match.group(0), "")
                base = _render_source(parent)
                block_re = re.compile(
                    r"{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}", re.S
                )
                parent_blocks = {n: c for n, c in block_re.findall(base)}
                child_blocks = {n: c for n, c in block_re.findall(source)}
                for name, content in parent_blocks.items():
                    if name in child_blocks:
                        child = child_blocks[name].replace("{{ super() }}", content)
                        pattern = (
                            r"{%\s*block\s+"
                            + re.escape(name)
                            + r"\s*%}.*?{%\s*endblock\s*%}"
                        )
                        base = re.sub(pattern, child, base, flags=re.S)
                source = base
            # handle include directive
            include_re = re.compile(r"{%\s*include\s+'([^']+)'\s*%}")

            def _replace_include(m: re.Match[str]) -> str:
                inc = self.registry.load_template(m.group(1), version) or ""
                return _render_source(inc)

            source = include_re.sub(_replace_include, source)
            return source

        raw = self.registry.load_template(slug, version) or ""
        processed = _render_source(raw)
        template = self.env.from_string(processed)
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
