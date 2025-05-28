from __future__ import annotations

import json
import logging
import difflib
from hashlib import sha256
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from packaging.version import parse as parse_version

from .template_schema import TemplateMetadata

logger = logging.getLogger(__name__)

TEMPLATE_LIBRARY_DIR_NAME = "template_library"
TEMPLATE_FILE_NAME = "template.yaml"
METADATA_FILE_NAME = "metadata.json"
MANIFEST_FILE_NAME = "registry.json"


class TemplateRegistry:
    """Manage versioned agent templates."""

    def __init__(self, base_dir: str | Path = "src/meta_agent") -> None:
        self.base_dir = Path(base_dir)
        if not self.base_dir.is_absolute():
            self.base_dir = Path(__file__).parent
        self.templates_dir = self.base_dir / TEMPLATE_LIBRARY_DIR_NAME
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.templates_dir / MANIFEST_FILE_NAME
        if not self.manifest_path.exists():
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_manifest(self) -> Dict[str, Any]:
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            logger.warning("Failed to read template registry manifest. Recreating.")
            return {}

    def _save_manifest(self, manifest: Dict[str, Any]) -> None:
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to write template registry manifest: {e}")

    def register(
        self,
        metadata: TemplateMetadata,
        content: str,
        version: str = "0.1.0",
    ) -> Optional[str]:
        slug = metadata.slug
        slug_sanitized = slug.replace(" ", "_").lower()
        version_sanitized = "v" + version.replace(".", "_")
        version_dir = self.templates_dir / slug_sanitized / version_sanitized
        version_dir.mkdir(parents=True, exist_ok=True)
        template_path = version_dir / TEMPLATE_FILE_NAME
        template_path.write_text(content, encoding="utf-8")
        checksum = sha256(content.encode("utf-8")).hexdigest()
        metadata_dict = (
            metadata.model_dump()
            if hasattr(metadata, "model_dump")
            else metadata.dict()
        )
        meta_data = {
            **metadata_dict,
            "version": version,
            "checksum": checksum,
        }
        with open(version_dir / METADATA_FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)
        manifest = self._load_manifest()
        entry = manifest.setdefault(slug_sanitized, {"versions": {}})
        entry["versions"][version] = {
            "path": f"{slug_sanitized}/{version_sanitized}/{TEMPLATE_FILE_NAME}",
            "checksum": checksum,
            "created_at": datetime.utcnow().isoformat(),
        }
        entry["current_version"] = version
        self._save_manifest(manifest)
        return str(template_path)

    def list_templates(self) -> List[Dict[str, Any]]:
        manifest = self._load_manifest()
        templates = []
        for slug, entry in manifest.items():
            versions = [
                {"version": v, **data}
                for v, data in sorted(
                    entry.get("versions", {}).items(),
                    key=lambda item: parse_version(item[0]),
                    reverse=True,
                )
            ]
            templates.append(
                {
                    "slug": slug,
                    "current_version": entry.get("current_version"),
                    "versions": versions,
                }
            )
        return templates

    def load_template(self, slug: str, version: str = "latest") -> Optional[str]:
        slug_sanitized = slug.replace(" ", "_").lower()
        manifest = self._load_manifest()
        entry = manifest.get(slug_sanitized)
        if not entry:
            return None
        if version == "latest":
            version = entry.get("current_version")
            if not version:
                return None
        version_data = entry.get("versions", {}).get(version)
        if not version_data:
            return None
        template_path = self.templates_dir / version_data["path"]
        if not template_path.exists():
            return None
        return template_path.read_text(encoding="utf-8")

    def diff(self, slug: str, old_version: str, new_version: str) -> str:
        old = self.load_template(slug, old_version) or ""
        new = self.load_template(slug, new_version) or ""
        return "\n".join(
            difflib.unified_diff(
                old.splitlines(),
                new.splitlines(),
                fromfile=old_version,
                tofile=new_version,
                lineterm="",
            )
        )

    def rollback(self, slug: str, version: str) -> bool:
        slug_sanitized = slug.replace(" ", "_").lower()
        manifest = self._load_manifest()
        entry = manifest.get(slug_sanitized)
        if not entry or version not in entry.get("versions", {}):
            return False
        entry["current_version"] = version
        self._save_manifest(manifest)
        return True
