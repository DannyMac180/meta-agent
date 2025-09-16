# @metaagent/tools-code

Secure containerized JavaScript code interpreter for the MetaAgent platform.

## Features

- **Docker-based Isolation**: All code executes in secure, isolated containers
- **Resource Limits**: Configurable memory, CPU, and timeout constraints  
- **Network Isolation**: Network access disabled by default
- **Package Management**: Allow-list based npm package installation
- **Output Protection**: Size limits and truncation handling
- **Security First**: Non-root execution, capability dropping, filesystem restrictions

## Quick Start

```bash
# Build the Docker image
pnpm docker:build

# Run tests
pnpm test

# Basic usage
import { codeTool } from "@metaagent/tools-code";

const result = await codeTool.execute({
  code: "console.log('Hello World!'); Math.sqrt(16);",
  timeoutMs: 5000,
  memMb: 128
});
```

## API Reference

### CodeTool.execute(input)

Execute JavaScript code in a secure container.

**Parameters:**
- `code` (string): JavaScript code to execute (max 100KB)
- `packages?` (string[]): NPM packages to install (must be allow-listed)
- `timeoutMs?` (number): Execution timeout in milliseconds (1000-300000, default: 8000)
- `memMb?` (number): Memory limit in MB (64-1024, default: 256)  
- `network?` (boolean): Enable network access (default: false)

**Returns:** `CodeExecutionResult`
- `success` (boolean): Whether execution succeeded
- `exitCode?` (number): Process exit code
- `stdout` (string): Standard output (truncated at 50KB)
- `stderr` (string): Standard error (truncated at 25KB)
- `executionTimeMs` (number): Actual execution time
- `error?` (string): Error message if execution failed
- `truncated?` (object): Indicates if output was truncated

## Security Model

### Container Security
- Base: Node.js 18 Alpine (minimal attack surface)
- User: Non-root execution (UID 1001)
- Network: Isolated by default (`--network=none`)
- Filesystem: Read-only with limited temp space
- Capabilities: All dropped (`--cap-drop=ALL`)

### Resource Limits
- Memory: 64MB-1GB (default: 256MB), no swap
- CPU: 0.5 core maximum
- Processes: 32 maximum
- File descriptors: 256 maximum
- Execution time: 1-300 seconds (default: 8)

### Package Security
- Only allow-listed packages can be installed
- Dangerous core modules blocked (`fs`, `child_process`, `net`, etc.)
- Package name validation prevents injection attacks
- Installation timeout prevents hanging

### Default Allowed Packages
- lodash, moment, uuid, axios, cheerio, csv-parser
- date-fns, ramda, validator, colors, chalk, debug

## Configuration

Set environment variables in `.env`:

```bash
CODE_TOOL_IMAGE=metaagent-code-sandbox:latest
CODE_TOOL_MAX_CONCURRENT=10
CODE_TOOL_DEFAULT_TIMEOUT_MS=8000
CODE_TOOL_DEFAULT_MEMORY_MB=256
```

## Docker Setup

The tool requires Docker to be running. Build the sandbox image:

```bash
cd packages/tools/code
pnpm docker:build
```

This creates the `metaagent-code-sandbox:latest` image used for code execution.

## Examples

### Basic Execution
```ts
const result = await codeTool.execute({
  code: "console.log('Hello'); 2 + 2;"
});
// result.stdout: "Hello\n"
// result.success: true
```

### With Packages
```ts
const result = await codeTool.execute({
  code: "const _ = require('lodash'); console.log(_.isEmpty({}));",
  packages: ["lodash"],
  timeoutMs: 15000
});
```

### Error Handling
```ts
const result = await codeTool.execute({
  code: "throw new Error('test error');"
});
// result.success: false
// result.stderr: Contains error details
```

### Custom Tool Instance
```ts
import { CodeTool } from "@metaagent/tools-code";

const customTool = new CodeTool({
  imageTag: "my-custom-sandbox:latest",
  allowedPackages: ["lodash", "moment", "my-package"]
});

const result = await customTool.execute({
  code: "// your code here"
});
```

## Testing

```bash
# Run all tests
pnpm test

# Run specific test files
pnpm test security.test.ts
pnpm test executor.test.ts

# Watch mode
pnpm test:watch
```

**Note**: Tests will show failures when Docker is not available, but the validation logic and API structure are still tested.

## Development

### Project Structure
```
packages/tools/code/
├── src/
│   ├── types.ts        # TypeScript interfaces
│   ├── executor.ts     # Docker execution engine  
│   ├── tool.ts        # Main tool interface
│   └── index.ts       # Public exports
├── docker/
│   ├── Dockerfile.nodejs      # Container definition
│   └── sandbox-entrypoint.js  # Container entry point
├── test/
│   ├── security.test.ts       # Security tests
│   ├── executor.test.ts       # Executor tests
│   └── tool.test.ts          # Tool interface tests
└── package.json
```

### Adding New Allowed Packages

```ts
import { codeTool } from "@metaagent/tools-code";

codeTool.addAllowedPackages(["new-package", "another-package"]);
```

Or create a custom instance:

```ts
const customTool = new CodeTool({
  allowedPackages: ["lodash", "moment", "my-custom-package"]
});
```

## Troubleshooting

### Docker Issues
- Ensure Docker daemon is running
- Check if the sandbox image exists: `docker images | grep metaagent-code-sandbox`
- Rebuild image: `pnpm docker:build`

### Permission Issues
- Code tool requires Docker socket access
- Ensure proper user permissions for Docker

### Memory/Timeout Issues
- Adjust `memMb` and `timeoutMs` parameters
- Monitor container resource usage
- Check Docker daemon resource limits

## Contributing

1. Run tests: `pnpm test`
2. Build Docker image: `pnpm docker:build`
3. Test with real Docker environment for integration tests
4. Update documentation for API changes
5. Follow security-first principles in all changes
