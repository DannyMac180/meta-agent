# Meta Agent Usage Examples

This document shows examples of the new simplified workflow for creating agents with Meta Agent.

## Primary Workflow: Natural Language Input

### Simple Example
```bash
meta-agent create --spec-text "Create a calculator agent that performs basic math operations"
```

### Complex Example
```bash
meta-agent create --spec-text "Build an agent that analyzes customer feedback from CSV files, 
categorizes sentiment as positive/negative/neutral, identifies key themes, 
and generates detailed reports with charts and actionable insights"
```

### Interactive Mode
```bash
meta-agent create
```
This opens an editor with guided prompts:
```
# Describe your agent here
# What should your agent do?

# What inputs will it need?

# What outputs should it produce?

# Any specific requirements?
```

## Advanced Features

### Preview Generated Specification
```bash
meta-agent create --spec-text "Create a document summarizer agent" --show-spec
```

This will show the generated YAML specification before creating the agent:
```yaml
task_description: |
  Create a document summarizer agent that can analyze text documents and generate concise summaries.
inputs:
  document_text: str
  max_summary_length: int
outputs:
  summary: str
  key_points: list[str]
```

### Traditional YAML Input (Still Supported)
```bash
meta-agent create --spec-file my_agent.yaml
```

### Debug Mode
```bash
meta-agent create --spec-text "your description" --debug
```

## Common Natural Language Patterns

### Data Processing Agents
- "Process CSV files and generate reports"
- "Analyze sales data and identify trends"
- "Clean and validate customer data"

### Analysis Agents
- "Analyze customer feedback sentiment"
- "Extract key insights from survey responses"
- "Categorize support tickets by priority"

### Content Agents
- "Summarize long documents"
- "Generate product descriptions from specifications"
- "Create marketing copy from product features"

### Utility Agents
- "Validate email addresses and phone numbers"
- "Convert file formats and compress images"
- "Schedule tasks and send reminders"

## Migration from Old Workflow

### Before (v0.1.0)
```bash
# Create YAML specification file
cat > agent_spec.yaml << EOF
task_description: "Create a calculator agent"
inputs:
  num1: int
  num2: int
outputs:
  result: int
EOF

# Generate agent
meta-agent generate --spec-file agent_spec.yaml
```

### After (v1.1.0+)
```bash
# One simple command
meta-agent create --spec-text "Create a calculator agent that adds two numbers"

# Or interactive mode
meta-agent create
```

## Best Practices

1. **Be Specific**: Include details about inputs, outputs, and requirements
   - Good: "Create an email validator that checks format and domain existence"
   - Better: "Create an email validator that checks format, verifies domain exists, and flags disposable email providers"

2. **Mention Constraints**: Include important limitations or requirements
   - "Create a web scraper that respects robots.txt and rate limits to 1 request per second"

3. **Specify Output Format**: Be clear about what the agent should produce
   - "Generate a summary report with charts, key metrics, and actionable recommendations"

4. **Use Preview Mode**: Use `--show-spec` to verify the generated specification
   - `meta-agent create --spec-text "your description" --show-spec`

5. **Iterate**: Start simple and refine based on the generated specification
   - First: "Create a document analyzer"
   - Refined: "Create a document analyzer that extracts entities, sentiment, and key topics from text files"
