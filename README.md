# Meta Agent 🤖

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/meta-agent.svg)](https://pypi.org/project/meta-agent/)

**Generate fully-functional AI agents from natural language specifications in minutes.**

Meta Agent is a Python CLI tool that automatically produces production-ready OpenAI-powered agents complete with code, tests, and guardrails from simple English descriptions.

## 🚀 Quick Start

### Installation

```bash
pip install meta-agent
```

### Create Your First Agent

```bash
# Initialize a new project
meta-agent init my-calculator --template hello-world

# Generate an agent from specification
meta-agent generate --spec-file agent_spec.yaml
```

### Example Specification

```yaml
task_description: |
  Create a calculator agent that can perform basic arithmetic operations.
  The agent should handle addition, subtraction, multiplication, and division.
inputs:
  operation: str  # "+", "-", "*", "/"
  num1: float
  num2: float
outputs:
  result: float
constraints:
  - Must validate division by zero
  - Should handle floating point precision
```

## ✨ Key Features

- **🎯 Natural Language Input**: Describe what you want in plain English
- **⚡ Instant Generation**: Get working agents in minutes, not hours
- **🛡️ Built-in Safety**: Automatic guardrails and validation
- **🧪 Test Generation**: Unit tests created automatically
- **📊 Telemetry**: Built-in monitoring and metrics
- **🔧 Extensible**: Template system for custom patterns

## 🎯 Perfect For

- **AI Engineers** building production agents quickly
- **Solutions Architects** integrating AI into workflows  
- **Rapid Prototypers** who need demo-ready agents fast
- **Hobbyists** exploring AI without deep coding expertise

## 📖 Documentation

### Core Commands

```bash
# Initialize new project
meta-agent init <project-name> [--template <template-name>]

# Generate agent from spec
meta-agent generate --spec-file <path> [--metric cost,tokens,latency]

# Manage templates
meta-agent templates list
meta-agent templates docs

# View telemetry
meta-agent dashboard
meta-agent export --format json
```

### Input Formats

Meta Agent supports multiple input formats:

**YAML File:**
```bash
meta-agent generate --spec-file my_agent.yaml
```

**JSON File:**
```bash
meta-agent generate --spec-file my_agent.json
```

**Direct Text:**
```bash
meta-agent generate --spec-text "Create an agent that summarizes documents"
```

### Project Structure

```
my-project/
├── .meta-agent/
│   └── config.yaml          # Project configuration
├── agent_spec.yaml          # Agent specification
└── generated/              # Generated agent code
    ├── agent.py
    ├── tests/
    └── guardrails/
```

## 🏗️ Architecture

Meta Agent uses a sophisticated orchestration system:

- **Planning Engine**: Decomposes specifications into tasks
- **Sub-Agent Manager**: Coordinates specialized agents
- **Tool Designer**: Generates custom tools and functions
- **Guardrail Designer**: Creates safety and validation logic
- **Template System**: Reusable patterns and best practices

## 🔧 Development

### Requirements

- Python 3.11+
- OpenAI API key (for LLM functionality)

### Setup

```bash
# Clone repository
git clone https://github.com/DannyMac180/meta-agent.git
cd meta-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[test]"

# Run tests
pytest

# Run linting
ruff check .
pyright
```

## 📊 Examples

### Data Processing Agent

```yaml
task_description: |
  Create an agent that processes CSV files and generates summary reports.
inputs:
  csv_file: str
  columns_to_analyze: list[str]
outputs:
  summary_report: dict
  charts: list[str]
```

### Web Scraping Agent

```yaml
task_description: |
  Build an agent that scrapes product information from e-commerce websites.
inputs:
  website_url: str
  product_selectors: dict
outputs:
  product_data: list[dict]
constraints:
  - Must respect robots.txt
  - Rate limit to 1 request per second
```

## 🔒 Environment Variables

```bash
# Required for LLM functionality
export OPENAI_API_KEY="your-api-key-here"

# Optional: Custom OpenAI base URL
export OPENAI_BASE_URL="https://your-proxy.com/v1"

# Optional: Enable debug logging
export META_AGENT_DEBUG=true
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the [OpenAI SDK](https://github.com/openai/openai-python)
- Inspired by the growing need for rapid AI agent development
- Thanks to the open-source community for foundational tools

## 📞 Support

- **Documentation**: [Full documentation](https://meta-agent.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/DannyMac180/meta-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DannyMac180/meta-agent/discussions)

---

**Made with ❤️ by developers, for developers building the AI-powered future.**