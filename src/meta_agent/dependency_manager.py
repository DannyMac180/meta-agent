"""Collect and pin dependencies for generated agent bundles."""

from __future__ import annotations

import hashlib
from typing import Iterable, List, Dict, Tuple, Optional, Mapping, cast
import importlib.metadata as metadata


class DependencyManager:
    """Resolve package dependencies and gather metadata."""

    def _extract_license(self, dist: metadata.Distribution) -> str:
        """Return the license string for a distribution."""
        meta = cast(Mapping[str, str], dist.metadata)
        license_header = meta.get("License")
        if license_header:
            return license_header.strip()
        for classifier in dist.metadata.get_all("Classifier") or []:
            if "License" in classifier:
                part = classifier.split("::")[-1].strip()
                return part.removesuffix("License").strip()
        return ""
      
    def _collect_recursive(
        self,
        package: str,
        pinned: Dict[str, str],
        licenses: Dict[str, str],
        visited: set[str],
        include_hashes: bool,
        hashes: Optional[Dict[str, str]],
    ) -> None:
        if package in visited:
            return
        visited.add(package)
        try:
            dist = metadata.distribution(package)
        except metadata.PackageNotFoundError:
            return

        meta = cast(Mapping[str, str], dist.metadata)
        name = meta.get("Name", package)
        version = dist.version
        pinned[name] = version
        licenses[name] = self._extract_license(dist)

        if include_hashes and hashes is not None:
            # Use hash of RECORD contents if available, else hash of version
            record = dist.read_text("RECORD")
            if record is not None:
                digest = hashlib.sha256(record.encode("utf-8")).hexdigest()
            else:
                digest = hashlib.sha256(version.encode("utf-8")).hexdigest()
            hashes[name] = digest

        for req in dist.requires or []:
            req_name = req.split(";")[0].strip().split()[0]
            req_name = req_name.split("[")[0]
            if req_name:
                self._collect_recursive(
                    req_name, pinned, licenses, visited, include_hashes, hashes
                )

    def resolve(
        self, packages: Iterable[str], include_hashes: bool = False
    ) -> Tuple[List[str], Dict[str, str], Optional[Dict[str, str]]]:
        """Return pinned requirements and license info for ``packages``."""

        pinned: Dict[str, str] = {}
        licenses: Dict[str, str] = {}
        hashes: Optional[Dict[str, str]] = {} if include_hashes else None
        visited: set[str] = set()

        for pkg in packages:
            base = pkg.split("==")[0].split(">=")[0].split("<")[0]
            base = base.split("[")[0]
            self._collect_recursive(
                base, pinned, licenses, visited, include_hashes, hashes
            )

        reqs = [f"{name}=={ver}" for name, ver in sorted(pinned.items())]
        return reqs, licenses, hashes
