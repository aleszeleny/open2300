# Testing Guide for PyOpen2300

## Overview

PyOpen2300 includes a comprehensive test suite to ensure code quality and reliability.

## Quick Start

```bash
# Install test dependencies
cd python-implementation
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=pyopen2300 --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Organization

### Directory Structure

```
tests/
├── unit/              Fast, isolated tests of individual components
├── integration/       Tests of multiple components working together
├── mocks/            Mock hardware and external dependencies
└── conftest.py       Shared fixtures and configuration
```

### Test Categories

**Unit Tests** (`tests/unit/`)
- Test individual functions and classes
- Fast execution (< 1 second total)
- No external dependencies
- High isolation using mocks

**Integration Tests** (`tests/integration/`)
- Test multiple components together
- Realistic scenarios
- May be slower
- Use test fixtures

## Running Tests

### Basic Commands

```bash
# All tests
pytest

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show print statements
pytest -s
```

### Selective Testing

```bash
# Specific directory
pytest tests/unit/

# Specific file
pytest tests/unit/test_config.py

# Specific test class
pytest tests/unit/test_config.py::TestConfig

# Specific test method
pytest tests/unit/test_config.py::TestConfig::test_default_values

# By marker
pytest -m unit
pytest -m "not slow"
```

### Coverage Analysis

```bash
# Generate coverage report
pytest --cov=pyopen2300

# HTML report
pytest --cov=pyopen2300 --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=pyopen2300 --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=pyopen2300 --cov-fail-under=80
```

## Test Fixtures

Common fixtures are available in `conftest.py`:

### temp_config_file
Creates a temporary configuration file with test settings.

```python
def test_config_loading(temp_config_file):
    config = Config(temp_config_file)
    assert config.log_level == 1
```

### mock_serial
Provides a mocked serial device.

```python
def test_serial_communication(mock_serial):
    mock_serial.read.return_value = b'\x02'
    # Test code using mock_serial
```

### mock_weather_data
Sample weather data for testing.

```python
def test_data_processing(mock_weather_data):
    temp = mock_weather_data['temperature_outdoor']
    assert temp == 18.3
```

## Writing Tests

### Test Structure

```python
import pytest
from pyopen2300.module import MyClass

class TestMyClass:
    """Test MyClass functionality"""
    
    def test_basic_creation(self):
        """Test basic object creation"""
        obj = MyClass()
        assert obj is not None
    
    def test_with_fixture(self, temp_config_file):
        """Test using a fixture"""
        obj = MyClass(temp_config_file)
        assert obj.is_valid()
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """Test that takes a long time"""
        result = obj.slow_method()
        assert result == expected
```

### Best Practices

1. **One assertion per test** (when possible)
   ```python
   def test_temperature_celsius():
       temp = get_temperature(CELSIUS)
       assert temp == 22.5
   
   def test_temperature_fahrenheit():
       temp = get_temperature(FAHRENHEIT)
       assert temp == 72.5
   ```

2. **Use descriptive names**
   ```python
   # Good
   def test_config_loads_from_valid_file():
   
   # Bad
   def test_config1():
   ```

3. **Test edge cases**
   ```python
   def test_temperature_at_zero():
       assert get_temperature(0) == -30.0
   
   def test_temperature_at_maximum():
       assert get_temperature(0xFF) == 225.5
   ```

4. **Use pytest.approx for floats**
   ```python
   assert value == pytest.approx(22.5, rel=1e-2)
   ```

5. **Test exceptions**
   ```python
   def test_invalid_config_raises_error():
       with pytest.raises(FileNotFoundError):
           Config('/nonexistent/file')
   ```

## Mocking

### Mocking Serial Devices

```python
from unittest.mock import Mock, patch

@patch('pyopen2300.serial_comm.serial.Serial')
def test_serial_read(mock_serial_class):
    mock_device = Mock()
    mock_device.read.return_value = b'\x02'
    mock_serial_class.return_value = mock_device
    
    # Your test code here
```

### Mocking Weather Station

```python
@patch('pyopen2300.weatherstation.SerialDevice')
def test_weather_station(mock_serial_class):
    ws = WeatherStation('/dev/ttyS0')
    # Configure mock behavior
    ws.device.read_safe.return_value = bytes([0x50, 0x52])
    
    temp = ws.temperature_indoor()
    assert temp == pytest.approx(22.5)
```

## Continuous Integration

### CI Configuration

```yaml
# Example .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements-test.txt
      - run: pip install -e .
      - run: pytest --cov=pyopen2300 --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Core modules (config, constants) | >95% |
| Protocol (weatherstation) | >90% |
| Serial communication | >85% |
| CLI tools | >70% |
| Overall | >80% |

## Debugging Tests

### Run with debugging

```bash
# Drop into pdb on failure
pytest --pdb

# Drop into pdb on first failure
pytest -x --pdb

# Show local variables on failure
pytest --showlocals
```

### Print debugging

```bash
# Show print statements
pytest -s

# More verbose
pytest -vv
```

### Specific test with output

```bash
pytest tests/unit/test_config.py::TestConfig::test_default_values -v -s
```

## Performance Testing

### Timing Tests

```bash
# Show slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

### Benchmark Tests

```python
import time

@pytest.mark.slow
def test_performance():
    start = time.time()
    result = expensive_operation()
    duration = time.time() - start
    assert duration < 1.0  # Should complete in <1 second
```

## Test Markers Reference

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Slow test
@pytest.mark.hardware      # Requires hardware
@pytest.mark.mock          # Uses mocked hardware
```

Run by marker:

```bash
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
pytest -m "not slow"        # Skip slow tests
pytest -m "unit and not slow"  # Unit tests that are fast
```

## Troubleshooting

### Tests not found

```bash
# Check test discovery
pytest --collect-only

# Ensure package installed
pip install -e .
```

### Import errors

```bash
# Install in development mode
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

### Serial port errors

Tests should not require actual serial ports. If you see serial errors:
1. Check that mocks are properly configured
2. Ensure pyserial is installed: `pip install pyserial`
3. Tests use mocked serial devices by default

### Coverage not working

```bash
# Install coverage tools
pip install pytest-cov coverage

# Run with explicit coverage
pytest --cov=pyopen2300 --cov-report=term
```

## Adding New Tests

1. **Create test file** in appropriate directory
2. **Import modules** to test
3. **Write test class** with descriptive name
4. **Add test methods** starting with `test_`
5. **Use fixtures** from conftest.py
6. **Add markers** if needed
7. **Run tests** to verify
8. **Check coverage** to ensure adequate testing

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Python Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Summary

✅ Comprehensive test suite
✅ Unit and integration tests  
✅ No hardware required (mocked)  
✅ Coverage reporting  
✅ CI/CD ready  
✅ Well documented  

Run tests regularly during development to catch issues early!

