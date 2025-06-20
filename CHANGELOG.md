# Changelog

All notable changes to Meta Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-06-20

### Added
- **New Primary Command**: `meta-agent create` - Simplified agent creation from natural language
- **Interactive Mode**: Run `meta-agent create` without arguments for guided agent specification
- **Natural Language Processing**: Direct text input with `--spec-text` flag for intuitive agent descriptions
- **Specification Preview**: `--show-spec` flag to preview generated YAML specifications
- **Enhanced Error Handling**: Improved error messages with actionable suggestions
- **Privacy Controls**: `--no-sensitive-logs` flag to exclude sensitive data from traces
- **Retry Logic**: Automatic retry with exponential backoff for transient failures

### Changed
- **Breaking**: Primary workflow now uses `meta-agent create` instead of `meta-agent generate`
- **Enhanced CLI**: Better help text, examples, and user guidance
- **Improved UX**: Interactive editor for specification input with template comments
- **Streamlined Process**: Natural language specifications are now the recommended approach

### Deprecated
- `meta-agent generate` command (still functional but no longer recommended for new users)
- YAML/JSON specification files as primary input method (still supported for advanced use)

### Fixed
- Improved component initialization error handling
- Better network error detection and retry logic
- Enhanced validation error messages with context-specific suggestions

### Migration Guide
- Replace `meta-agent generate --spec-file spec.yaml` with `meta-agent create --spec-file spec.yaml`
- For new agents, prefer `meta-agent create --spec-text "your description"` or interactive `meta-agent create`
- Use `--show-spec` to see the generated specification from natural language input

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

[1.1.0]: https://github.com/DannyMac180/meta-agent/releases/tag/v1.1.0
[0.1.0]: https://github.com/DannyMac180/meta-agent/releases/tag/v0.1.0