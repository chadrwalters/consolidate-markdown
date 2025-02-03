---
description: "Python type hinting and type checking requirements"
globs:
  - "src/**/*.py"
  - "tests/**/*.py"
version: 1.0.0
status: Active
---

# Python Type Hinting Rules
Version: 1.0.0
Last Updated: 2024-02-02

## Abstract/Purpose
This rule defines the requirements and standards for Python type hints and type checking. It ensures type safety, code clarity, and proper static type analysis across the project.

## Table of Contents
- [Mandatory Constraints](#mandatory-constraints)
- [Advisory Guidelines](#advisory-guidelines)
- [Type System](#type-system)
- [Type Checking](#type-checking)
- [Exception Clauses](#exception-clauses)
- [Examples](#examples)
- [Migration Notes](#migration-notes)

## Type System
### Basic Types
- Use built-in types (int, str, etc.)
- Use typing module types
- Define custom types when needed
- Use type aliases for clarity
- Document complex types

### Generic Types
- List[T], Dict[K, V], etc.
- Use TypeVar for generics
- Bound type variables
- Covariant/contravariant types
- Generic protocols

### Special Types
- Optional[T] for nullable
- Union[A, B] for multiple types
- Literal for constants
- Final for immutable
- TypeAlias for aliases

### Custom Types
- Define in types.py
- Use descriptive names
- Document constraints
- Include examples
- Test type behavior

## Type Checking
### Mypy Configuration
```toml
[mypy]
python_version = 3.12
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
```

### Type Checking Process
1. Run mypy on all files
2. Address all errors
3. Document exceptions
4. Verify fixes
5. Update stubs if needed

### Stub Files
- Create for external modules
- Match module structure
- Document type behavior
- Include all public APIs
- Test stub accuracy

## Mandatory Constraints
### MUST
- Use type hints for all functions
- Type all parameters
- Type all return values
- Use proper generic types
- Document type behavior
- Run type checker
- Fix type errors
- Create stub files
- Test type compliance
- Update type dependencies
- Follow typing conventions
- Handle optional types

### MUST NOT
- Skip type hints
- Use Any unnecessarily
- Ignore type errors
- Mix typing styles
- Leave stubs incomplete
- Use incorrect generics
- Break type safety
- Bypass type checker
- Use dynamic typing
- Leave types ambiguous
- Skip type tests
- Use deprecated types

## Advisory Guidelines
### SHOULD
- Use descriptive types
- Create type aliases
- Document complex types
- Test edge cases
- Review type coverage
- Update stubs regularly
- Monitor type errors
- Use type guards
- Follow type patterns
- Keep types simple

### RECOMMENDED
- Regular type checks
- Type coverage reports
- Documentation updates
- Stub maintenance
- Pattern matching
- Protocol usage
- Generic constraints
- Type optimization
- Error tracking
- Compliance testing

## Exception Clauses
Type checking exceptions allowed when:
- External library lacks types
- Runtime type checking needed
- Performance critical code
- Complex dynamic behavior
- Explicitly documented

## Examples
```python
from typing import TypeVar, Generic, Optional, List, Dict
from dataclasses import dataclass

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

@dataclass
class Container(Generic[T]):
    """Generic container with type safety.

    Args:
        value: The contained value of type T
        metadata: Optional metadata about the value
    """
    value: T
    metadata: Optional[Dict[str, str]] = None

    def get_value(self) -> T:
        """Retrieves the contained value.

        Returns:
            The value of type T
        """
        return self.value

class Registry(Generic[K, V]):
    """Type-safe registry mapping keys to values.

    Args:
        items: Initial dictionary of items
    """
    def __init__(self, items: Optional[Dict[K, V]] = None) -> None:
        self._items: Dict[K, V] = items or {}

    def get(self, key: K) -> Optional[V]:
        """Get value by key with type safety.

        Args:
            key: The key of type K

        Returns:
            The value of type V if found, None otherwise
        """
        return self._items.get(key)

# Bad Examples
def bad_function(x): # Missing type hints
    return x + 1

def worse_function(x: any): # Incorrect Any usage
    return x.something()
```

## Migration Notes
- Add missing type hints
- Update to new typing syntax
- Create missing stubs
- Fix type errors
- Document type behavior

## Dependencies
- @rule(02-base.md:format_requirements)
- @rule(10-python-style.md:code_standards)

## Changelog
### 1.0.0 (2024-02-02)
- Initial version
- Defined typing requirements
- Added mypy configuration
- Created type examples
