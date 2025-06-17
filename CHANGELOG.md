# Changelog

All notable changes to Meta Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-17

### Added
- Initial release of Meta Agent
- CLI tool for generating AI agents from natural language specifications
- Support for YAML, JSON, and text input formats
- Template system with hello-world template
- Agent orchestration system with planning engine
- Tool designer for generating custom tools
- Guardrail designer for safety and validation
- Telemetry system with built-in monitoring
- Project initialization and management
- Comprehensive test suite
- Docker support for sandboxed execution

### Architecture
- Modular design with sub-agent pattern
- Local agents stub replacing openai-agents dependency
- OpenAI SDK integration for LLM functionality
- Template-based code generation
- Built-in error handling and fallbacks

### CLI Commands
- `meta-agent generate` - Generate agents from specifications
- `meta-agent init` - Initialize new projects
- `meta-agent templates` - Manage and document templates
- `meta-agent dashboard` - View telemetry data
- `meta-agent export` - Export telemetry data
- `meta-agent tool` - Manage tools
- `meta-agent serve` - Start REST API server

### Documentation
- Comprehensive README with examples
- CLI help system
- Architecture documentation
- Template documentation generator

### Dependencies
- Python 3.11+ support
- OpenAI SDK 1.80+ (without openai-agents dependency)
- Modern Python tooling (pytest, ruff, pyright)
- Minimal external dependencies for better compatibility

[0.1.0]: https://github.com/yourusername/meta-agent/releases/tag/v0.1.0