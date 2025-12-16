# PyOpen2300 Test Suite

This directory contains the test suite for PyOpen2300.

## Structure

```
tests/
├── __init__.py
├── conftest.py              Pytest configuration and fixtures
├── README.md                This file
│
├── unit/                    Unit tests (fast, isolated)
│   ├── test_constants.py
│   ├── test_config.py
│   └── test_weatherstation.py
│
├── integration/             Integration tests (slower, realistic)
│   └── test_config_loading.py
│
└── mocks/                   Mock hardware for testing
    └── (future: mock serial devices)
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Run with markers
pytest -m unit
pytest -m integration
```

### Run Specific Test Files

```bash
pytest tests/unit/test_config.py
pytest tests/unit/test_weatherstation.py
```

### Run Specific Tests

```bash
pytest tests/unit/test_config.py::TestConfig::test_default_values
```

### Coverage Report

```bash
# Generate coverage report
pytest --cov=pyopen2300 --cov-report=html

# View report
open htmlcov/index.html
```

## Test Markers

Tests are organized with markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.hardware` - Tests requiring actual hardware
- `@pytest.mark.mock` - Tests using mocked hardware

Run specific markers:

```bash
pytest -m unit
pytest -m "not slow"
```

## Writing Tests

### Unit Tests

Test individual functions/classes in isolation:

```python
def test_function_name():
    result = my_function(input)
    assert result == expected
```

### Integration Tests

Test multiple components working together:

```python
def test_config_loads_and_validates(temp_config_file):
    config = Config(temp_config_file)
    assert config.is_valid()
```

### Using Fixtures

Common test fixtures are defined in `conftest.py`:

```python
def test_with_config(temp_config_file):
    # temp_config_file is automatically created and cleaned up
    config = Config(temp_config_file)
    assert config.log_level > 0
```

## Continuous Integration

Tests are designed to run without hardware. Hardware-dependent tests use mocks.

### CI Command

```bash
pytest -v --cov=pyopen2300 --cov-report=term-missing
```

## Test Coverage Goals

- **Core modules**: >90% coverage
- **CLI tools**: >70% coverage (hardware mocking complex)
- **Overall**: >80% coverage

## Adding New Tests

1. Create test file: `test_<module>.py`
2. Import module to test
3. Create test class: `class Test<Feature>`
4. Add test methods: `def test_<specific_behavior>()`
5. Use fixtures from conftest.py
6. Add markers if needed
7. Run tests to verify

Example:

```python
# tests/unit/test_new_feature.py
import pytest
from pyopen2300.new_module import NewClass

class TestNewClass:
    def test_basic_functionality(self):
        obj = NewClass()
        assert obj.method() == expected_result
    
    def test_with_fixture(self, temp_config_file):
        obj = NewClass(temp_config_file)
        assert obj.is_valid()
```

## Troubleshooting

### Import Errors

Make sure package is installed in development mode:

```bash
pip install -e .
```

### Serial Port Tests

Tests don't require actual serial ports - they use mocks. If you see serial errors, check that mocks are properly configured.

### Coverage Not Generated

Install coverage dependencies:

```bash
pip install pytest-cov coverage
```

## Future Enhancements

- [ ] Mock serial device for hardware simulation
- [ ] Performance benchmarks
- [ ] Database integration tests (PostgreSQL, SQLite)
- [ ] Network request mocking (Weather Underground)
- [ ] CLI command testing
- [ ] Stress tests for serial communication

