"""Tests for template documentation generator."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from meta_agent.template_docs_generator import TemplateDocsGenerator
from meta_agent.template_schema import (
    IOContract,
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
)


@pytest.fixture
def sample_metadata():
    """Create sample template metadata for testing."""
    return TemplateMetadata(
        slug="test-template",
        title="Test Template",
        description="A sample template for testing",
        intended_use="Testing template documentation generation",
        io_contract=IOContract(
            input="Text description of task", output="Structured response with results"
        ),
        tools=["web_search", "file_read"],
        guardrails=["no_personal_data", "safe_browsing"],
        model_pref="gpt-4",
        category=TemplateCategory.REASONING,
        complexity=TemplateComplexity.INTERMEDIATE,
        created_by="test-author",
        semver="1.2.0",
        last_test_passed="2025-01-01T12:00:00Z",
        tags=["automation", "testing"],
        eval_score=0.85,
        cost_estimate=0.0150,
        tokens_per_run=1500,
        requires_structured_outputs=True,
        requires_web_search=True,
    )


@pytest.fixture
def mock_registry():
    """Create a mock template registry."""
    registry = Mock()
    registry.list_templates.return_value = [
        {
            "slug": "test-template",
            "current_version": "1.2.0",
            "versions": [
                {"version": "1.2.0", "path": "test-template/v1_2_0/template.yaml"}
            ],
        },
        {
            "slug": "another-template",
            "current_version": "0.1.0",
            "versions": [
                {"version": "0.1.0", "path": "another-template/v0_1_0/template.yaml"}
            ],
        },
    ]
    return registry


class TestTemplateDocsGenerator:
    """Test suite for TemplateDocsGenerator."""

    def test_init_with_registry(self, mock_registry):
        """Test initialization with provided registry."""
        generator = TemplateDocsGenerator(registry=mock_registry)
        assert generator.registry == mock_registry

    def test_init_without_registry(self):
        """Test initialization without registry creates new one."""
        with patch(
            "meta_agent.template_docs_generator.TemplateRegistry"
        ) as mock_reg_class:
            generator = TemplateDocsGenerator()
            mock_reg_class.assert_called_once()
            assert generator.registry == mock_reg_class.return_value

    def test_generate_card_basic(self, sample_metadata):
        """Test basic card generation with all fields."""
        generator = TemplateDocsGenerator()

        card = generator.generate_card(sample_metadata)

        # Check main sections are present
        assert "# Test Template" in card
        assert "A sample template for testing" in card
        assert "Testing template documentation generation" in card
        assert "test-author" in card
        assert "1.2.0" in card
        assert "gpt-4" in card

        # Check badges
        assert "![Complexity]" in card
        assert "![Category]" in card

        # Check I/O contract
        assert "Text description of task" in card
        assert "Structured response with results" in card

        # Check tools and guardrails
        assert "`web_search`" in card
        assert "`file_read`" in card
        assert "`no_personal_data`" in card
        assert "`safe_browsing`" in card

        # Check requirements
        assert "Structured outputs support" in card
        assert "Web search capability" in card

        # Check performance metrics
        assert "0.85" in card
        assert "$0.0150" in card
        assert "1,500 tokens" in card
        assert "2025-01-01T12:00:00Z" in card

        # Check tags
        assert "`automation`" in card
        assert "`testing`" in card

    def test_generate_card_with_sample_usage(self, sample_metadata):
        """Test card generation with sample usage."""
        generator = TemplateDocsGenerator()
        sample_usage = "meta-agent init --template test-template"

        card = generator.generate_card(sample_metadata, sample_usage)

        assert "## Sample Usage" in card
        assert sample_usage in card

    def test_generate_card_minimal_metadata(self):
        """Test card generation with minimal required metadata."""
        minimal_metadata = TemplateMetadata(
            slug="minimal",
            title="Minimal Template",
            description="Basic template",
            intended_use="Testing minimal requirements",
            io_contract=IOContract(input="Input", output="Output"),
            model_pref="gpt-3.5-turbo",
            category=TemplateCategory.CONVERSATION,
            created_by="author",
            semver="0.1.0",
        )

        generator = TemplateDocsGenerator()
        card = generator.generate_card(minimal_metadata)

        # Should not contain optional sections
        assert "## Tools" not in card
        assert "## Guardrails" not in card
        assert "## Requirements" not in card
        assert "## Performance Metrics" not in card
        assert "**Tags:**" not in card

    def test_generate_all_cards(self, mock_registry, sample_metadata):
        """Test generating cards for all templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = TemplateDocsGenerator(registry=mock_registry)

            # Mock the metadata loading
            with patch.object(generator, "_load_template_metadata") as mock_load:
                mock_load.return_value = sample_metadata

                files = generator.generate_all_cards(temp_dir)

                assert len(files) == 2  # Two templates in mock registry

                # Check files were created
                for file_path in files:
                    assert Path(file_path).exists()
                    content = Path(file_path).read_text()
                    assert "# Test Template" in content

    def test_generate_all_cards_with_missing_metadata(self, mock_registry):
        """Test handling of missing metadata during bulk generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = TemplateDocsGenerator(registry=mock_registry)

            # Mock metadata loading to return None (missing metadata)
            with patch.object(generator, "_load_template_metadata") as mock_load:
                mock_load.return_value = None

                files = generator.generate_all_cards(temp_dir)

                assert len(files) == 0  # No files generated due to missing metadata

    def test_generate_index(self, mock_registry, sample_metadata):
        """Test index generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = TemplateDocsGenerator(registry=mock_registry)

            with patch.object(generator, "_load_template_metadata") as mock_load:
                mock_load.return_value = sample_metadata

                index_path = generator.generate_index(temp_dir)

                assert Path(index_path).exists()
                content = Path(index_path).read_text()

                assert "# Template Library" in content
                assert "## Reasoning" in content  # Category section
                assert "Test Template" in content
                assert "A sample template for testing" in content
                assert "🟡" in content  # Intermediate complexity emoji

    def test_generate_index_with_cards_dir(self, mock_registry, sample_metadata):
        """Test index generation with custom cards directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = TemplateDocsGenerator(registry=mock_registry)

            with patch.object(generator, "_load_template_metadata") as mock_load:
                mock_load.return_value = sample_metadata

                index_path = generator.generate_index(temp_dir, cards_dir="cards")

                content = Path(index_path).read_text()
                assert "](cards/test-template.md)" in content

    def test_load_template_metadata_success(self, mock_registry, sample_metadata):
        """Test successful metadata loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock directory structure
            template_dir = Path(temp_dir) / "test-template" / "v1_2_0"
            template_dir.mkdir(parents=True)

            metadata_file = template_dir / "metadata.json"
            metadata_dict = sample_metadata.model_dump()
            metadata_file.write_text(json.dumps(metadata_dict))

            generator = TemplateDocsGenerator(registry=mock_registry)
            generator.registry.templates_dir = Path(temp_dir)

            result = generator._load_template_metadata("test-template", "1.2.0")

            assert result is not None
            assert result.slug == "test-template"
            assert result.title == "Test Template"

    def test_load_template_metadata_missing_file(self, mock_registry):
        """Test metadata loading with missing file."""
        generator = TemplateDocsGenerator(registry=mock_registry)

        result = generator._load_template_metadata("nonexistent", "1.0.0")

        assert result is None

    def test_generate_sample_usage(self, sample_metadata):
        """Test sample usage generation."""
        generator = TemplateDocsGenerator()

        usage = generator._generate_sample_usage(sample_metadata)

        assert "meta-agent init --template test-template" in usage
        assert "Test Template" in usage
        assert "gpt-4" in usage

    def test_format_badge(self):
        """Test badge formatting."""
        generator = TemplateDocsGenerator()

        badge = generator._format_badge("Test", "Value With Spaces", "blue")

        assert "![Test]" in badge
        assert "Value%20With%20Spaces" in badge
        assert "blue" in badge

    def test_format_list_section_with_items(self):
        """Test list section formatting with items."""
        generator = TemplateDocsGenerator()

        section = generator._format_list_section("Tools", ["tool1", "tool2"])

        assert "## Tools" in section
        assert "- `tool1`" in section
        assert "- `tool2`" in section

    def test_format_list_section_empty(self):
        """Test list section formatting with no items."""
        generator = TemplateDocsGenerator()

        section = generator._format_list_section("Tools", [])

        assert section == ""

    def test_complexity_color_mapping(self):
        """Test complexity color mapping."""
        generator = TemplateDocsGenerator()

        assert generator._get_complexity_color(TemplateComplexity.BASIC) == "green"
        assert (
            generator._get_complexity_color(TemplateComplexity.INTERMEDIATE) == "yellow"
        )
        assert generator._get_complexity_color(TemplateComplexity.ADVANCED) == "red"

    def test_category_color_mapping(self):
        """Test category color mapping."""
        generator = TemplateDocsGenerator()

        assert generator._get_category_color(TemplateCategory.CONVERSATION) == "blue"
        assert generator._get_category_color(TemplateCategory.REASONING) == "purple"
        assert generator._get_category_color(TemplateCategory.CREATIVE) == "orange"
        assert (
            generator._get_category_color(TemplateCategory.DATA_PROCESSING)
            == "lightblue"
        )
        assert (
            generator._get_category_color(TemplateCategory.INTEGRATION) == "darkgreen"
        )

    def test_complexity_emoji_mapping(self):
        """Test complexity emoji mapping."""
        generator = TemplateDocsGenerator()

        assert generator._get_complexity_emoji(TemplateComplexity.BASIC) == "🟢"
        assert generator._get_complexity_emoji(TemplateComplexity.INTERMEDIATE) == "🟡"
        assert generator._get_complexity_emoji(TemplateComplexity.ADVANCED) == "🔴"

    def test_get_timestamp(self):
        """Test timestamp generation."""
        generator = TemplateDocsGenerator()

        timestamp = generator._get_timestamp()

        assert "UTC" in timestamp
        assert len(timestamp.split()) == 3  # YYYY-MM-DD HH:MM:SS UTC
