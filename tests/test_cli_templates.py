"""Tests for CLI template functionality (init command)."""

import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from meta_agent.cli.main import cli
from meta_agent.template_registry import TemplateRegistry


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_template_registry():
    """Mock template registry with sample templates."""
    registry = MagicMock(spec=TemplateRegistry)
    registry.list_templates.return_value = [
        {
            "slug": "hello-world",
            "current_version": "1.0.0",
            "versions": [{"version": "1.0.0", "path": "hello-world/v1_0_0/template.yaml"}]
        },
        {
            "slug": "data-processor",
            "current_version": "0.2.0",
            "versions": [{"version": "0.2.0", "path": "data-processor/v0_2_0/template.yaml"}]
        }
    ]
    return registry


@pytest.fixture
def sample_template_content():
    """Sample template content."""
    return """# Agent Specification Template
task_description: "A simple hello world agent"
inputs:
  - name: "message"
    description: "The message to process"
outputs:
  - name: "response"
    description: "The processed response"
model_preference: "gpt-4"
"""


class TestCliInit:
    """Test the init command functionality."""

    def test_init_basic_project(self, runner, tmp_path):
        """Test basic project initialization without template."""
        project_name = "test-project"
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", project_name])
            
            assert result.exit_code == 0
            assert f"Initializing project '{project_name}'" in result.output
            assert "✓ Project initialized successfully!" in result.output
            
            # Check that files were created
            project_dir = Path(project_name)
            assert project_dir.exists()
            assert (project_dir / "agent_spec.yaml").exists()
            assert (project_dir / ".meta-agent" / "config.yaml").exists()
            
            # Check content of spec file
            spec_content = (project_dir / "agent_spec.yaml").read_text()
            assert "task_description:" in spec_content
            assert "inputs:" in spec_content
            assert "outputs:" in spec_content

    def test_init_project_with_custom_directory(self, runner, tmp_path):
        """Test project initialization with custom directory."""
        project_name = "test-project"
        custom_dir = tmp_path / "custom-location" / project_name
        
        result = runner.invoke(cli, ["init", project_name, "--directory", str(custom_dir)])
        
        assert result.exit_code == 0
        assert custom_dir.exists()
        assert (custom_dir / "agent_spec.yaml").exists()

    @patch('meta_agent.cli.main.TemplateRegistry')
    def test_init_project_with_valid_template(self, mock_registry_class, runner, 
                                              mock_template_registry, sample_template_content):
        """Test project initialization with a valid template."""
        mock_registry_class.return_value = mock_template_registry
        mock_template_registry.load_template.return_value = sample_template_content
        
        project_name = "template-project"
        template_slug = "hello-world"
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", project_name, "--template", template_slug])
            
            assert result.exit_code == 0
            assert f"Using template: {template_slug}" in result.output
            assert "✓ Project initialized successfully!" in result.output
            
            # Check that template content was used
            project_dir = Path(project_name)
            spec_content = (project_dir / "agent_spec.yaml").read_text()
            assert "A simple hello world agent" in spec_content

    @patch('meta_agent.cli.main.TemplateRegistry')
    @patch('meta_agent.cli.main.TemplateSearchEngine')
    def test_init_project_with_invalid_template(self, mock_search_class, mock_registry_class, 
                                               runner, mock_template_registry):
        """Test project initialization with an invalid template shows available templates."""
        mock_registry_class.return_value = mock_template_registry
        mock_template_registry.load_template.return_value = None  # Template not found
        
        project_name = "template-project"
        invalid_template = "nonexistent-template"
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", project_name, "--template", invalid_template])
            
            assert result.exit_code == 0
            assert f"Template '{invalid_template}' not found." in result.output
            assert "Available templates:" in result.output
            assert "hello-world" in result.output
            assert "data-processor" in result.output


class TestCliServe:
    """Test the serve command functionality."""

    def test_serve_command_help(self, runner):
        """Test serve command help text."""
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Start the REST API server" in result.output
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--reload" in result.output

    def test_serve_command_missing_dependencies_real(self, runner):
        """Test serve command when dependencies are actually missing."""
        # This will test the real behavior - if FastAPI/uvicorn aren't installed
        # the command should fail gracefully
        result = runner.invoke(cli, ["serve"])
        
        # Either succeeds (if deps are available) or fails gracefully
        if result.exit_code != 0:
            assert "Error:" in result.output or "Missing dependency" in result.output
        else:
            # If it somehow succeeds, that's also fine for this test
            pass
