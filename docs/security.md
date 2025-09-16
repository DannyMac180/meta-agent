# Security

## Code Interpreter Security

The code interpreter tool provides secure JavaScript execution through containerized isolation:

### Container Security
- **Base Image**: Node.js 18 Alpine (minimal attack surface)
- **Non-root Execution**: All code runs as UID 1001 (sandbox user)  
- **Network Isolation**: `--network=none` by default, optional allow-list override
- **Filesystem**: Read-only root filesystem with limited temp directories
- **Capabilities**: All Linux capabilities dropped (`--cap-drop=ALL`)

### Resource Limits
- **Memory**: Configurable (64MB-1GB), default 256MB, no swap
- **CPU**: Limited to 0.5 core
- **Processes**: Max 32 processes per container  
- **File Descriptors**: Max 256 open files
- **Disk**: 100MB temp space, 50MB app directory
- **Timeout**: Configurable (1-300 seconds), default 8 seconds

### Package Security
- **Allow-list Validation**: Only pre-approved packages can be installed
- **Name Validation**: Strict regex validation prevents injection
- **Dangerous Packages Blocked**: Core modules like `fs`, `child_process`, `net` blocked
- **Installation Timeout**: Package installation limited to 30 seconds

### Output Protection
- **Size Limits**: stdout limited to 50KB, stderr to 25KB  
- **Truncation Indicators**: Clear indication when output is truncated
- **No Secrets**: Container has no access to host secrets or environment

### Container Lifecycle
- **Unique Containers**: Each execution gets fresh container with random ID
- **Automatic Cleanup**: Containers removed after execution or timeout
- **Process Isolation**: dumb-init prevents zombie processes
- **Graceful Shutdown**: SIGTERM/SIGINT handled for clean exits

### Runtime Monitoring
- **Execution Tracking**: All running containers tracked and manageable
- **Timeout Enforcement**: Hard container kill after timeout + 5s grace period
- **Resource Monitoring**: Memory and CPU usage constrained by Docker
- **Audit Logging**: All executions logged with security context

## Egress Allow-List

The MetaAgent platform enforces strict network security through an egress allow-list that controls which external hosts can be accessed by tools and services.

### Configuration

All external HTTP requests are controlled by the `ALLOW_HTTP_HOSTS` environment variable:

```bash
# JSON array format (preferred)
ALLOW_HTTP_HOSTS='["api.openai.com", "google.serper.dev", "*.example.com"]'

# Comma-separated format (fallback)
ALLOW_HTTP_HOSTS="api.openai.com,google.serper.dev,*.example.com"
```

### Host Patterns

The allow-list supports the following patterns:

- **Exact match**: `api.openai.com` - matches only that specific host
- **Wildcard subdomain**: `*.example.com` - matches any subdomain of example.com
  - ✅ `api.example.com`
  - ✅ `service.api.example.com`
  - ❌ `example.com` (doesn't match the root domain)
  - ❌ `malicious-example.com` (doesn't match the pattern)

### Required Hosts by Tool

Different tools require specific hosts to be allow-listed:

#### HTTP Tool
- User-defined: Any hosts your agents need to access

#### Web Search Tool
- `google.serper.dev` - for Serper API search results

#### Vector Tool
- `api.openai.com` - for OpenAI embedding API

### Validation

The system validates the allow-list configuration on service startup:

- **Empty allow-list**: Logs warning, blocks all external requests
- **Invalid JSON**: Falls back to comma-separated parsing
- **Malformed patterns**: Rejects configuration with helpful error messages

### Security Logging

All blocked requests are logged for security monitoring:

```
[SECURITY] Blocked HTTP request to disallowed host: malicious.com (GET https://malicious.com/api)
```

### Testing

Run security tests to validate allow-list enforcement:

```bash
# HTTP tool security tests
pnpm --filter @metaagent/tools-http test security

# Runner service integration tests  
pnpm --filter @metaagent/services-runner test security.integration

# All security-related tests
pnpm test -- security
```

### Deployment Considerations

#### Production
- Use minimal allow-list with only required hosts
- Monitor blocked request logs for security threats
- Regularly audit and update allowed hosts

#### Development
- Include development/testing hosts as needed
- Use `.env.local` for local overrides
- Avoid wildcards in production when possible

#### Docker
- Configure allow-list via environment variables
- Consider network-level restrictions for additional security
- Use separate configurations per service if needed

### Troubleshooting

#### "Blocked host" Errors
1. Check the current `ALLOW_HTTP_HOSTS` configuration
2. Add the required host to the allow-list
3. Restart the service to pick up changes
4. Verify the host pattern matches correctly

#### Configuration Issues
1. Validate JSON syntax if using array format
2. Check for trailing commas or quotes
3. Ensure wildcard patterns are correct
4. Review startup logs for validation warnings

#### Testing Allow-List Rules
Use the HTTP tool to test host access:

```bash
curl -X POST http://localhost:3102/tools/http \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "method": "GET"}'
```

Expected responses:
- **Allowed host**: HTTP response or network error
- **Blocked host**: `400` error with "Blocked host" message
