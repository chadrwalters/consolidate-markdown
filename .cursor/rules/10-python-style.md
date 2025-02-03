---
description: "Python code style and formatting requirements"
globs:
  - "src/**/*.py"
  - "tests/**/*.py"
version: 1.0.0
status: Active
---

# Python Style Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the Python coding style requirements and formatting standards. It ensures consistent code quality, readability, and maintainability across all Python files in the project. For type hinting requirements, see `11-python-typing.md`.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Style Requirements](#style-requirements)
- [Formatting Standards](#formatting-standards)
- [Documentation Standards](#documentation-standards)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)
- [Dependencies](#dependencies)

## Style Requirements
### Code Organization
- One class per file (with exceptions)
- Logical function grouping
- Clear module structure
- Consistent import ordering
- Standard section ordering

### Naming Conventions
- Classes: PascalCase
- Functions: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private members: _prefix

### Import Structure
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Blank line between groups

### Error Handling
- Use specific except clauses
- Handle errors at appropriate level
- Log exceptions properly
- Clean up resources in finally
- Document error conditions

## Formatting Standards
### Line Length
- Maximum: 88 characters (Black default)
- Docstrings: 72 characters
- Comments: 72 characters
- Imports: One per line

### Whitespace
- 4 spaces for indentation
- No tabs
- Two blank lines before classes
- One blank line before functions
- No trailing whitespace

### String Formatting
- f-strings preferred
- Multi-line strings indented
- Consistent quote usage (single for internal, double for docstrings)
- String concatenation style

### Comments
- Complete sentences
- Proper capitalization
- Meaningful content
- Updated with code
- Clear purpose

## Documentation Standards
### Module Documentation
```python
"""Module purpose and description.

Detailed explanation of module functionality.
Usage examples and important notes.
"""
```

### Class Documentation
```python
class ExampleClass:
    """Class purpose and behavior.

    Detailed explanation of class functionality.
    Usage examples and important notes.

    Attributes:
        attr_name: Description of attribute
    """
```

### Function Documentation
```python
def example_function(param1, param2):
    """Short description of function purpose.

    Detailed explanation of function behavior.
    Usage examples and edge cases.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ErrorType: Description of error conditions
    """
```

## Mandatory Constraints
### MUST
- Follow Black formatting
- Write clear docstrings
- Follow naming conventions
- Order imports correctly
- Maintain line length limits
- Use consistent indentation
- Document public interfaces
- Handle exceptions properly
- Follow PEP 8 guidelines
- Use proper string formatting
- Write meaningful comments

### MUST NOT
- Mix naming styles
- Leave docstrings empty
- Exceed line length
- Use inconsistent formatting
- Leave TODOs without tickets
- Mix string formats
- Use bare except
- Skip error handling
- Leave code uncommented
- Use deprecated features
- Mix indentation styles

## Advisory Guidelines
### SHOULD
- Use descriptive names
- Keep functions focused
- Limit function length
- Group related code
- Document complex logic
- Handle edge cases
- Write unit tests
- Use constants
- Follow patterns
- Review code regularly

### RECOMMENDED
- Code reviews
- Style checking
- Documentation updates
- Regular refactoring
- Performance profiling
- Test coverage
- Error logging
- Pattern matching
- Context managers
- Automated formatting

## Exception Clauses
Style exceptions allowed when:
- Required by external library
- Needed for compatibility
- Improves readability
- Handles special cases
- Documented clearly

## Examples
### Good Style Example
```python
"""User management module for handling user operations.

This module provides a clean interface for user CRUD operations
and related functionality.
"""
from typing import Optional  # Standard lib imports first

import requests  # Third-party imports second

from myapp.db import Database  # Local imports last
from myapp.logging import logger


class UserManager:
    """Manages user operations and state.

    Provides a high-level interface for user management operations
    including creation, retrieval, updates, and deletion.

    Attributes:
        db: Database connection instance
        cache_timeout: Cache timeout in seconds
    """

    def __init__(self, db_connection: Database, cache_timeout: int = 300) -> None:
        self._db = db_connection
        self._cache_timeout = cache_timeout

    def get_user(self, user_id: int) -> Optional[dict]:
        """Retrieves user by ID.

        Attempts to fetch user from cache first, then falls back to
        database if not found.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User data dictionary or None if not found

        Raises:
            DatabaseError: If database connection fails
        """
        try:
            return self._db.query(f"SELECT * FROM users WHERE id = {user_id}")
        except DatabaseError as e:
            logger.error(f"Failed to retrieve user {user_id}: {e}")
            raise
```

### Bad Style Example
```python
# No module docstring
import random
from myapp.db import Database  # Incorrect import order
from datetime import datetime
import requests

# No class docstring
class user_manager:  # Incorrect naming
    def __init__(self,db,timeout=300):  # Poor spacing
        self.db=db  # Poor spacing
        self.timeout=timeout

    # No function docstring
    def get(self,id):  # Poor naming
        try:
            return self.db.query("SELECT * FROM users WHERE id = "+str(id))  # Poor string formatting
        except:  # Bare except
            print(f"Error getting user {id}")  # Print instead of logging
```

## Migration Notes
- Update existing code to new style
- Improve documentation
- Fix formatting issues
- Handle exceptions properly
- Add missing docstrings

## Dependencies
- 02-base.md (Base formatting requirements)
- 11-python-typing.md (Type hint requirements)
- 40-error-handling.md (Error handling standards)
- 41-logging.md (Logging standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined style requirements
- Set formatting standards
- Added documentation standards
- Removed typing content (moved to 11-python-typing.md)
- Added comprehensive examples
