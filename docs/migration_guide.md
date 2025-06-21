# Migration Guide: v0.1.0 to v1.1.0

This guide helps existing Meta Agent users migrate from the old `generate` command workflow to the new simplified `create` command workflow.

## Quick Migration

### Old Command (Deprecated)
```bash
meta-agent generate --spec-file agent_spec.yaml
```

### New Command (Recommended)
```bash
meta-agent create --spec-file agent_spec.yaml
```

## Key Changes

### 1. Primary Command Change
- **Old**: `meta-agent generate` was the primary command
- **New**: `meta-agent create` is now the primary command
- **Status**: `generate` still works but is deprecated

### 2. Natural Language Input (New!)
Instead of writing YAML/JSON files, you can now describe agents in plain English:

```bash
# New capability - no spec file needed!
meta-agent create --spec-text "Create a calculator agent that adds two numbers"
```

### 3. Interactive Mode (New!)
Run without arguments for guided agent creation:

```bash
meta-agent create  # Opens editor with prompts
```

### 4. Specification Preview (New!)
See what specification is generated from your natural language:

```bash
meta-agent create --spec-text "your description" --show-spec
```

## Migration Strategies

### Strategy 1: Drop-in Replacement
Simply replace `generate` with `create`:

```bash
# Before
meta-agent generate --spec-file my_agent.yaml --metric cost,tokens

# After  
meta-agent create --spec-file my_agent.yaml --metric cost,tokens
```

### Strategy 2: Convert to Natural Language
Convert your YAML specifications to natural language descriptions:

```yaml
# Old agent_spec.yaml
task_description: |
  Create an agent that validates email addresses
inputs:
  email: str
outputs:
  is_valid: bool
  error_message: str
constraints:
  - Must check format and domain
```

```bash
# New approach
meta-agent create --spec-text "Create an email validator that checks format and domain existence, returning validation status and error messages"
```

### Strategy 3: Hybrid Approach
Use natural language for new agents, keep YAML for complex existing specifications:

```bash
# For new simple agents
meta-agent create --spec-text "Create a document summarizer"

# For existing complex agents
meta-agent create --spec-file complex_agent.yaml
```

## Feature Mapping

| Old Feature | New Feature | Notes |
|-------------|-------------|-------|
| `meta-agent generate --spec-file` | `meta-agent create --spec-file` | Direct replacement |
| `meta-agent generate --spec-text` | `meta-agent create --spec-text` | Now supports natural language |
| Manual YAML writing | Interactive mode (`meta-agent create`) | Much easier! |
| N/A | `--show-spec` flag | Preview generated specs |
| N/A | Enhanced error messages | Better troubleshooting |
| N/A | Retry logic | More reliable |

## Breaking Changes

### 1. Primary Command
- **Impact**: Scripts using `meta-agent generate` still work but get deprecation notices
- **Action**: Update scripts to use `meta-agent create`

### 2. Help Text Updates
- **Impact**: Help messages now emphasize natural language input
- **Action**: No action needed - informational only

### 3. Error Message Format
- **Impact**: Error messages are more detailed and actionable
- **Action**: Update any error parsing logic if you have automated scripts

## No Breaking Changes

The following still work exactly the same:
- All YAML/JSON specification formats
- All command-line flags (`--metric`, `--spec-file`, etc.)
- All telemetry and dashboard commands
- All template commands
- All tool management commands

## Recommended Migration Steps

### For Individual Users
1. Try the new interactive mode: `meta-agent create`
2. Experiment with natural language: `meta-agent create --spec-text "..."`
3. Use `--show-spec` to understand how your descriptions translate to specifications
4. Update your bookmarks/aliases to use `create` instead of `generate`

### For Teams/Organizations
1. Update documentation and training materials
2. Update CI/CD scripts to use `meta-agent create`
3. Consider moving simple agents to natural language descriptions
4. Keep complex agents as YAML files for now
5. Gradually adopt new features as team becomes comfortable

### For Script Authors
1. Replace `meta-agent generate` with `meta-agent create` in scripts
2. Add error handling for the new error message formats
3. Consider adding `--show-spec` for debugging
4. Test with `--debug` flag for detailed logging

## Troubleshooting Migration Issues

### Issue: "Command not found" errors
**Solution**: Ensure you're using Meta Agent v1.1.0+
```bash
pip install --upgrade meta-agent-cli
meta-agent --version
```

### Issue: Different behavior with same spec files
**Solution**: The `create` command has enhanced validation. Use `--debug` to see details:
```bash
meta-agent create --spec-file your_spec.yaml --debug
```

### Issue: Natural language not generating expected specification  
**Solution**: Use `--show-spec` to preview and refine:
```bash
meta-agent create --spec-text "your description" --show-spec
```

### Issue: Missing features from old workflow
**Solution**: All old features are still available. Check the help:
```bash
meta-agent create --help
```

## Getting Help

If you encounter issues during migration:

1. Check the [usage examples](usage_examples.md) for patterns
2. Use `--debug` flag for detailed error information
3. Try `--show-spec` to understand spec generation
4. Consult the [GitHub Issues](https://github.com/DannyMac180/meta-agent/issues) for known issues
5. Open a new issue if you find a bug or need help

## Feedback

We'd love to hear about your migration experience! Please:
- Share feedback in [GitHub Discussions](https://github.com/DannyMac180/meta-agent/discussions)
- Report any issues or unexpected behavior
- Suggest improvements to the migration process
