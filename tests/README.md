# Test Suite

Comprehensive test coverage for the GitOps ML Infrastructure Demo.

## Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── test_inference.py    # Unit tests for ML sentiment analysis
├── test_api.py          # Integration tests for FastAPI endpoints
└── test_dashboard.py    # Integration tests for Flask dashboard
```

## Running Tests

### Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/ -v -m unit

# API tests only
pytest tests/ -v -m api

# Dashboard tests only
pytest tests/ -v -m dashboard

# Inference tests only
pytest tests/ -v -m inference
```

### Run with Coverage

```bash
pytest tests/ -v --cov=app/ml-inference --cov=scripts --cov-report=term-missing
```

## Test Categories

| Marker | Description |
|--------|-------------|
| `unit` | Fast unit tests with no external dependencies |
| `integration` | Tests requiring external services |
| `api` | FastAPI endpoint tests |
| `dashboard` | Flask dashboard tests |
| `inference` | ML inference logic tests |

## Coverage Goals

- Minimum: 70%
- Target: 80%

## CI/CD Integration

Tests run automatically in the GitHub Actions workflow:

1. **Unit Test Job**: Runs all pytest tests before deployment
2. **Health Check Job**: Runs integration tests on deployed services

The deploy job only proceeds if unit tests pass.
