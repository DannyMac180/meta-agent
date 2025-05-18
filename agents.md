## Testing Instructions
Run the full suite with coverage:

```bash
pytest -v --cov=src/meta_agent tests
```

Run a single test:

```bash
pytest tests/test_agent.py::test_agent
```

Run a single test with coverage:

```bash
pytest -v --cov=src/meta_agent tests/test_agent.py::test_agent
```

## Repo Rules
Check the .windsurfrules file for more information on how to use this repo. Espeically when working with task-master tasks.