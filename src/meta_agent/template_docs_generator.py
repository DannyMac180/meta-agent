"""Automated documentation generator for agent templates."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .template_schema import TemplateMetadata, TemplateCategory, TemplateComplexity
from .template_registry import TemplateRegistry

logger = logging.getLogger(__name__)


class TemplateDocsGenerator:
    """Generate Markdown documentation cards for agent templates."""

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        """Initialize the documentation generator.

        Args:
            registry: Template registry instance. If None, creates a new one.
        """
        self.registry = registry or TemplateRegistry()

    def generate_card(
        self, metadata: TemplateMetadata, sample_usage: Optional[str] = None
    ) -> str:
        """Generate a Markdown documentation card for a template.

        Args:
            metadata: Template metadata containing all documentation fields
            sample_usage: Optional sample invocation or usage example

        Returns:
            Formatted Markdown card as a string
        """
        # Build complexity and category badges
        complexity_badge = self._format_badge(
            "Complexity",
            metadata.complexity.value,
            self._get_complexity_color(metadata.complexity),
        )
        category_badge = self._format_badge(
            "Category",
            metadata.category.value,
            self._get_category_color(metadata.category),
        )

        # Build tools and guardrails sections
        tools_section = self._format_list_section("Tools", metadata.tools)
        guardrails_section = self._format_list_section(
            "Guardrails", metadata.guardrails
        )

        # Build requirements section
        requirements = []
        if metadata.requires_structured_outputs:
            requirements.append("Structured outputs support")
        if metadata.requires_web_search:
            requirements.append("Web search capability")
        requirements_section = (
            self._format_list_section("Requirements", requirements)
            if requirements
            else ""
        )

        # Build optional metadata
        optional_metadata = []
        if metadata.eval_score is not None:
            optional_metadata.append(f"**Evaluation Score:** {metadata.eval_score:.2f}")
        if metadata.cost_estimate is not None:
            optional_metadata.append(
                f"**Estimated Cost:** ${metadata.cost_estimate:.4f} per run"
            )
        if metadata.tokens_per_run is not None:
            optional_metadata.append(
                f"**Token Usage:** ~{metadata.tokens_per_run:,} tokens per run"
            )
        if metadata.last_test_passed:
            optional_metadata.append(f"**Last Tested:** {metadata.last_test_passed}")

        optional_section = "\n".join(optional_metadata)
        if optional_section:
            optional_section = f"\n## Performance Metrics\n\n{optional_section}\n"

        # Build tags section
        tags_section = ""
        if metadata.tags:
            tags = " ".join([f"`{tag}`" for tag in metadata.tags])
            tags_section = f"\n**Tags:** {tags}\n"

        # Build sample usage section
        sample_section = ""
        if sample_usage:
            sample_section = f"""
## Sample Usage

```yaml
{sample_usage}
```
"""

        # Generate the complete card
        card = f"""# {metadata.title}

{complexity_badge} {category_badge}

{metadata.description}

## Overview

**Intended Use:** {metadata.intended_use}

**Author:** {metadata.created_by}  
**Version:** {metadata.semver}  
**Model Preference:** {metadata.model_pref}

{tags_section}

## Input/Output Contract

**Input:** {metadata.io_contract.input}

**Output:** {metadata.io_contract.output}

{tools_section}

{guardrails_section}

{requirements_section}{optional_section}{sample_section}

---
*Generated from template metadata v{metadata.semver}*
"""
        return card.strip()

    def generate_all_cards(
        self, output_dir: str | Path, include_sample: bool = True
    ) -> List[str]:
        """Generate documentation cards for all registered templates.

        Args:
            output_dir: Directory to save the generated documentation files
            include_sample: Whether to include sample usage in cards

        Returns:
            List of paths to generated documentation files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        templates = self.registry.list_templates()
        generated_files = []

        for template_info in templates:
            slug = template_info["slug"]
            current_version = template_info["current_version"]

            if not current_version:
                logger.warning(f"No current version found for template {slug}")
                continue

            # Load metadata
            metadata = self._load_template_metadata(slug, current_version)
            if not metadata:
                logger.warning(
                    f"Could not load metadata for template {slug} v{current_version}"
                )
                continue

            # Generate sample usage if requested
            sample_usage = None
            if include_sample:
                sample_usage = self._generate_sample_usage(metadata)

            # Generate card
            card_content = self.generate_card(metadata, sample_usage)

            # Save to file
            filename = f"{slug.replace('_', '-')}.md"
            file_path = output_path / filename
            file_path.write_text(card_content, encoding="utf-8")
            generated_files.append(str(file_path))

            logger.info(f"Generated documentation for {metadata.title} -> {filename}")

        return generated_files

    def generate_index(
        self, output_dir: str | Path, cards_dir: Optional[str] = None
    ) -> str:
        """Generate an index file listing all available templates.

        Args:
            output_dir: Directory to save the index file
            cards_dir: Relative path to cards directory for links (default: same as output_dir)

        Returns:
            Path to the generated index file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        templates = self.registry.list_templates()

        # Group templates by category
        by_category: Dict[str, List[Dict[str, Any]]] = {}

        for template_info in templates:
            slug = template_info["slug"]
            current_version = template_info["current_version"]

            if not current_version:
                continue

            metadata = self._load_template_metadata(slug, current_version)
            if not metadata:
                continue

            category = metadata.category.value
            if category not in by_category:
                by_category[category] = []

            by_category[category].append(
                {
                    "metadata": metadata,
                    "slug": slug,
                    "filename": f"{slug.replace('_', '-')}.md",
                }
            )

        # Generate index content
        index_content = "# Template Library\n\n"
        index_content += "This is an automatically generated index of all available agent templates.\n\n"

        for category, templates_in_category in sorted(by_category.items()):
            index_content += f"## {category.title().replace('_', ' ')}\n\n"

            # Sort templates by complexity, then name
            templates_in_category.sort(
                key=lambda x: (x["metadata"].complexity.value, x["metadata"].title)
            )

            for template in templates_in_category:
                metadata = template["metadata"]
                filename = template["filename"]

                # Create relative link
                if cards_dir:
                    link_path = f"{cards_dir}/{filename}"
                else:
                    link_path = filename

                complexity_emoji = self._get_complexity_emoji(metadata.complexity)
                index_content += f"- {complexity_emoji} **[{metadata.title}]({link_path})** - {metadata.description}\n"

            index_content += "\n"

        index_content += f"\n---\n*Generated on {self._get_timestamp()}*\n"

        # Save index file
        index_path = output_path / "README.md"
        index_path.write_text(index_content, encoding="utf-8")

        logger.info(f"Generated template index -> {index_path}")
        return str(index_path)

    def _load_template_metadata(
        self, slug: str, version: str
    ) -> Optional[TemplateMetadata]:
        """Load template metadata from the registry."""
        try:
            # Load metadata from the registry directory structure
            slug_sanitized = slug.replace(" ", "_").lower()
            version_sanitized = "v" + version.replace(".", "_")
            metadata_path = (
                self.registry.templates_dir
                / slug_sanitized
                / version_sanitized
                / "metadata.json"
            )

            if not metadata_path.exists():
                return None

            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)

            return TemplateMetadata(**metadata_dict)
        except Exception as e:
            logger.error(f"Failed to load metadata for {slug} v{version}: {e}")
            return None

    def _generate_sample_usage(self, metadata: TemplateMetadata) -> str:
        """Generate a sample usage example for a template."""
        return f"""# Sample invocation for {metadata.title}
meta-agent init --template {metadata.slug}

# Or use the template directly
spec:
  name: "My Agent"
  template: "{metadata.slug}"
  description: "{metadata.intended_use}"
  model: "{metadata.model_pref}"
"""

    def _format_badge(self, label: str, value: str, color: str) -> str:
        """Format a badge for display."""
        return f"![{label}](https://img.shields.io/badge/{label}-{value.replace(' ', '%20')}-{color})"

    def _format_list_section(self, title: str, items: List[str]) -> str:
        """Format a list section with title."""
        if not items:
            return ""

        formatted_items = "\n".join([f"- `{item}`" for item in items])
        return f"\n## {title}\n\n{formatted_items}\n"

    def _get_complexity_color(self, complexity: TemplateComplexity) -> str:
        """Get color for complexity badge."""
        color_map = {
            TemplateComplexity.BASIC: "green",
            TemplateComplexity.INTERMEDIATE: "yellow",
            TemplateComplexity.ADVANCED: "red",
        }
        return color_map.get(complexity, "grey")

    def _get_category_color(self, category: TemplateCategory) -> str:
        """Get color for category badge."""
        color_map = {
            TemplateCategory.CONVERSATION: "blue",
            TemplateCategory.REASONING: "purple",
            TemplateCategory.CREATIVE: "orange",
            TemplateCategory.DATA_PROCESSING: "lightblue",
            TemplateCategory.INTEGRATION: "darkgreen",
        }
        return color_map.get(category, "grey")

    def _get_complexity_emoji(self, complexity: TemplateComplexity) -> str:
        """Get emoji for complexity level."""
        emoji_map = {
            TemplateComplexity.BASIC: "🟢",
            TemplateComplexity.INTERMEDIATE: "🟡",
            TemplateComplexity.ADVANCED: "🔴",
        }
        return emoji_map.get(complexity, "⚪")

    def _get_timestamp(self) -> str:
        """Get current timestamp for documentation."""
        from datetime import datetime

        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
