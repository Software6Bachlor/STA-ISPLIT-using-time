# Run all tests
```bash
pytest
```

# Run with verbose output
```bash
pytest -v
```
# Run with coverage report
```bash
pytest --cov
```
# Run specific test file
```bash
pytest tests/testExample.py
```
# Run specific test function
```bash
pytest tests/testExample.py::testBasicExample
```

# Get coverage report
```bash
pytest --cov=. --cov-branch --cov-report html
```

You should see output like:
```
collected 2 items

tests/testExample.py::testBasicExample PASSED
tests/test_example.py::testStringOperations PASSED

====== 2 passed in 0.02s ======
```
