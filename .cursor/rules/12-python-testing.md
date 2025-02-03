---
description: "Python testing standards and requirements"
globs:
  - "tests/**/*.py"
  - "tests/data/**/*"
  - "tests/fixtures/**/*"
version: 1.0.0
status: Active
---

# Python Testing Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the testing standards, practices, and requirements for Python code. It ensures comprehensive test coverage, consistent test organization, and proper test execution across the project. For Python style and documentation standards, see `10-python-style.md`.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Test Organization](#test-organization)
- [Test Types](#test-types)
- [Test Configuration](#test-configuration)
- [Coverage Requirements](#coverage-requirements)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)
- [Dependencies](#dependencies)

## Test Organization
### Directory Structure
```
tests/
├── unit/               # Unit tests
│   ├── test_module1.py
│   └── test_module2.py
├── integration/        # Integration tests
│   ├── test_feature1.py
│   └── test_feature2.py
├── e2e/               # End-to-end tests
│   └── test_flows.py
├── performance/       # Performance tests
│   └── test_perf.py
├── fixtures/          # Test fixtures
│   └── data.json
└── conftest.py        # Shared fixtures
```

### Test File Patterns
- Test files must be in appropriate directories
- Each source file should have corresponding test file
- Fixtures should be in fixtures directory or conftest.py
- Data files should be in tests/data directory

## Test Types
### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Fast execution
- High isolation
- Comprehensive edge cases

### Integration Tests
- Test component interactions
- Limited mocking
- Database interactions
- API integrations
- Service communications

### End-to-End Tests
- Test complete workflows
- Real external services
- UI interactions
- API sequences
- Data flow validation

### Performance Tests
- Response time benchmarks
- Load testing
- Stress testing
- Resource utilization
- Scalability validation

## Test Configuration
### Required Plugins
- pytest-cov: Coverage reporting
- pytest-asyncio: Async support
- pytest-xdist: Parallel testing
- pytest-timeout: Test timeouts
- pytest-randomly: Random ordering

### Pytest Configuration
```ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test* *Test
python_functions = test_* *_test
addopts =
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --randomly-seed=1234
    --timeout=300
    -v
```

### Test Markers
- @pytest.mark.unit: Unit tests
- @pytest.mark.integration: Integration tests
- @pytest.mark.e2e: End-to-end tests
- @pytest.mark.performance: Performance tests
- @pytest.mark.slow: Slow tests
- @pytest.mark.network: Network-dependent tests
- @pytest.mark.database: Database-dependent tests

## Coverage Requirements
### Thresholds
- Unit Tests: 90% minimum
- Integration Tests: 80% minimum
- Total Coverage: 85% minimum

### Coverage Types
- Branch coverage
- Statement coverage
- Function coverage
- Class coverage

### Reporting
- HTML reports required
- Console summary required
- Coverage trends tracked
- Failed thresholds block merge
- Reports archived in CI/CD

## Mandatory Constraints
### MUST
- Write tests for all code changes
- Organize tests by type
- Use appropriate markers
- Meet coverage thresholds
- Maintain test isolation
- Mock external dependencies
- Clean up test resources
- Handle edge cases
- Include regression tests
- Follow AAA pattern
- Use fixtures effectively
- Run full test suite
- Document test purpose
- Verify error cases

### MUST NOT
- Skip tests without reason
- Leave tests incomplete
- Mix test types
- Share test state
- Use hardcoded paths
- Leave resources uncleaned
- Ignore failed tests
- Skip coverage reports
- Use deprecated fixtures
- Break test isolation
- Commit failing tests
- Skip error testing

## Advisory Guidelines
### SHOULD
- Write tests first (TDD)
- Keep tests focused
- Use meaningful test data
- Document complex setups
- Monitor test performance
- Update test data regularly
- Verify mock behaviors
- Track coverage trends
- Review test quality
- Automate test runs

### RECOMMENDED
- Regular test cleanup
- Performance profiling
- Security testing
- Load testing
- API testing
- UI testing
- Database testing
- Cache testing
- Error path testing
- Boundary testing

## Exception Clauses
Test exceptions allowed when:
- Complex integration required
- External service unavailable
- Performance impact too high
- Security constraints
- Legacy system limitations
- Third-party limitations
- Resource constraints
- Time-sensitive releases

## Examples
### Good Test Structure
```python
import pytest
from unittest.mock import Mock
from myapp.user import UserManager, DatabaseError

@pytest.fixture
def mock_db():
    """Provides a mocked database connection."""
    db = Mock()
    db.query.return_value = {"id": 123, "name": "Test User"}
    return db

@pytest.fixture
def user_manager(mock_db):
    """Provides a UserManager with mocked database."""
    return UserManager(db_connection=mock_db)

class TestUserManager:
    """Tests for UserManager functionality."""

    def test_get_user_success(self, user_manager):
        """Test successful user retrieval."""
        # Arrange
        user_id = 123

        # Act
        user = user_manager.get_user(user_id)

        # Assert
        assert user is not None
        assert user["name"] == "Test User"

    def test_get_user_error(self, user_manager, mock_db):
        """Test database error handling."""
        # Arrange
        mock_db.query.side_effect = DatabaseError("Connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError):
            user_manager.get_user(123)

@pytest.mark.integration
def test_user_creation_flow(client):
    """Integration test for user creation workflow."""
    # Arrange
    user_data = {"name": "New User", "email": "test@example.com"}

    # Act
    response = client.post("/users", json=user_data)

    # Assert
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["name"] == user_data["name"]
    assert created_user["email"] == user_data["email"]
```

### Bad Test Structure
```python
def test_user():  # Too vague, no clear purpose
    manager = UserManager(db_connection=None)  # Bad setup
    assert manager.get_user(1)  # Insufficient assertions

def test_database():  # Mixed concerns
    db = Database()
    user = User()
    # No cleanup, shared state
    db.connect()
    user.save()
```

## Migration Notes
- Update test directory structure
- Add missing test types
- Implement new markers
- Update configuration
- Fix coverage gaps
- Separate test types properly

## Dependencies
- 10-python-style.md (Style and documentation standards)
- 11-python-typing.md (Type hint requirements)
- 40-error-handling.md (Error handling standards)
- 41-logging.md (Logging standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined test organization
- Added test types
- Set coverage requirements
- Added comprehensive examples
- Removed style overlaps
- Enhanced test patterns
