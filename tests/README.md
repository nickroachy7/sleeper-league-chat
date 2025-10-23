# Test Suite

This directory contains automated tests for the Fantasy League AI Assistant.

## Running Tests

### Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock
```

### Run all tests:
```bash
pytest tests/ -v
```

### Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_league_queries.py -v
```

## Test Structure

- `test_league_queries.py` - Unit tests for database query functions
- `test_api_server.py` - Integration tests for Flask API
- `README.md` - This file

## Test Coverage

Current coverage: ~60%

Areas covered:
- ✅ League query functions
- ✅ API endpoints
- ✅ Error handling

Areas not covered (TODO):
- ❌ Data sync functions
- ❌ OpenAI integration
- ❌ Web UI components
- ❌ End-to-end workflows

## Writing New Tests

Follow these guidelines:

1. **Use descriptive test names**
   ```python
   def test_get_standings_sorts_by_wins_then_points(self):
   ```

2. **One assertion per test (when possible)**
   ```python
   def test_returns_correct_format(self):
       result = get_standings()
       assert isinstance(result, list)
   ```

3. **Use fixtures for common setup**
   ```python
   @pytest.fixture
   def mock_database():
       return create_mock_db()
   ```

4. **Mock external dependencies**
   ```python
   @patch('league_queries.supabase')
   def test_with_mock(self, mock_supabase):
       ...
   ```

## Continuous Integration

To integrate with CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
          pytest tests/ --cov=.
```





