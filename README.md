# Meta Agent 🤖

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/meta-agent.svg)](https://pypi.org/project/meta-agent/)

**Generate fully-functional AI agents from natural language descriptions in minutes.**

Meta Agent is a Python CLI tool that automatically produces production-ready OpenAI-powered agents complete with code, tests, and guardrails from simple English descriptions. Just describe what you want your agent to do, and Meta Agent handles the rest.

## 🚀 Quick Start

### Installation

```bash
pip install meta-agent
```

### Create Your First Agent

```bash
# Simplest way - interactive mode (recommended for new users)
meta-agent create

# Or provide your description directly
meta-agent create --spec-text "Create a calculator agent that can perform basic arithmetic operations"

# Initialize a new project with templates (optional)
meta-agent init my-calculator --template hello-world
```

### Natural Language Specifications

Instead of complex YAML files, simply describe what you want in plain English:

```bash
# Interactive mode - just run this and describe your agent when prompted
meta-agent create

# Simple text description
meta-agent create --spec-text "Create a calculator agent that performs basic math operations"

# More detailed specification
meta-agent create --spec-text "Build an agent that analyzes customer feedback, 
  categorizes it by sentiment (positive/negative/neutral), 
  and generates summary reports with key insights"
```

### Optional: Traditional YAML Format

For advanced users, YAML specifications are still supported:

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

- **🎯 Natural Language Input**: Describe what you want in plain English - no YAML required
- **💬 Interactive Mode**: Just run `meta-agent create` and get guided prompts
- **⚡ Instant Generation**: Get working agents in minutes, not hours
- **🛡️ Built-in Safety**: Automatic guardrails and validation generated
- **🧪 Test Generation**: Comprehensive unit tests created automatically
- **🔧 Tool Creation**: Custom tools generated automatically when needed
- **📊 Telemetry**: Built-in monitoring and metrics
- **👀 Specification Preview**: See generated specs with `--show-spec`
- **🔒 Privacy**: `--no-sensitive-logs` flag for secure environments

## 🎯 Perfect For

- **AI Engineers** building production agents quickly without YAML complexity
- **Solutions Architects** integrating AI into workflows with natural language specs
- **Rapid Prototypers** who need demo-ready agents from simple descriptions
- **Hobbyists** exploring AI without deep coding or specification writing expertise
- **Product Managers** who can describe features in plain English

## 📖 Documentation

### Core Commands

```bash
# Create agent (primary command)
meta-agent create                                    # Interactive mode (recommended)
meta-agent create --spec-text "description"         # Direct text input
meta-agent create --spec-file path/to/spec.yaml     # File input (advanced)
meta-agent create --show-spec --spec-text "..."     # Preview generated spec
meta-agent create --debug --spec-text "..."         # Debug mode with detailed logging

# Initialize new project
meta-agent init <project-name> [--template <template-name>]

# Privacy and security
meta-agent create --no-sensitive-logs --spec-text "..." # Secure logging

# Legacy command (deprecated but still works)
meta-agent generate --spec-file <path> [--metric cost,tokens,latency]

# Manage templates
meta-agent templates list
meta-agent templates docs

# View telemetry
meta-agent dashboard
meta-agent export --format json
```

### Input Formats

Meta Agent supports multiple input formats, with natural language being the primary method:

**Natural Language (Recommended):**
```bash
meta-agent create --spec-text "Create an agent that summarizes documents and extracts key insights"
```

**Interactive Mode (Recommended for beginners):**
```bash
meta-agent create  # Prompts you to describe your agent in your own words
```

**YAML File:**
```bash
meta-agent create --spec-file my_agent.yaml
```

**JSON File:**
```bash
meta-agent create --spec-file my_agent.json
```

**Preview Generated Specification:**
```bash
meta-agent create --spec-text "your description" --show-spec
```

### What Actually Happens

When you run `meta-agent create`, here's what happens automatically:

1. **📝 You describe your agent** in plain English (interactive prompt or `--spec-text`)
2. **🔍 Intelligent parsing** extracts structure (inputs, outputs, constraints) from your description  
3. **📋 Planning** breaks down the work into tasks and identifies required tools
4. **🔧 Tool generation** creates any custom tools your agent needs
5. **🛡️ Guardrail creation** adds safety and validation logic
6. **🧪 Test generation** creates comprehensive unit tests
7. **✅ Complete agent** ready to use with code, tests, and documentation

All of this happens automatically - no YAML editing, no complex configuration required!

### Before vs After

**❌ Old Way (Complex):**
```bash
# 1. Create YAML specification file manually
# 2. Learn YAML syntax and structure  
# 3. Figure out all the required fields
# 4. Run: meta-agent generate --spec-file my_spec.yaml
# 5. Debug YAML errors and iterate
```

**✅ New Way (Simple):**
```bash
# 1. Run: meta-agent create
# 2. Describe what you want in plain English
# 3. Done! Working agent with tests and guardrails
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

**Natural Language:**
```bash
meta-agent create --spec-text "Create an agent that processes CSV files, 
analyzes specified columns, and generates summary reports with charts"
```

**Traditional YAML (Optional):**
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

**Natural Language:**
```bash
meta-agent create --spec-text "Build an agent that scrapes product information 
from e-commerce websites, respects robots.txt, and limits requests to 1 per second"
```

**Traditional YAML (Optional):**
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