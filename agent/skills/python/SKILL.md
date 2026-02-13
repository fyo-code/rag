---
name: python-patterns
description: Python development patterns and best practices for modern Python 3.11+ applications. Covers type hints, async programming, Pydantic, and clean code principles.
---

# Python Patterns & Best Practices

## Core Principles

### Type Hints Everywhere
```python
from typing import Optional, List, Dict, Any
from datetime import datetime

def process_data(
    items: List[Dict[str, Any]],
    limit: Optional[int] = None
) -> List[str]:
    """Process items and return results."""
    ...
```

### Pydantic for Validation
```python
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    email: str = Field(..., description="User email")
    name: str = Field(..., min_length=2)
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
```

### Async by Default for I/O
```python
import asyncio
import httpx

async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async def fetch_all(urls: List[str]) -> List[dict]:
    return await asyncio.gather(*[fetch_data(url) for url in urls])
```

---

## Project Structure

```
project/
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point
│   ├── config.py             # Configuration
│   ├── dependencies.py       # Dependency injection
│   ├── models/               # Pydantic/DB models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   └── user_service.py
│   ├── repositories/         # Data access
│   │   ├── __init__.py
│   │   └── user_repository.py
│   └── api/                  # API routes
│       ├── __init__.py
│       └── routes/
│           └── users.py
├── tests/
│   ├── __init__.py
│   └── test_users.py
├── pyproject.toml
└── requirements.txt
```

---

## Error Handling

```python
from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: T) -> 'Result[T]':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'Result[T]':
        return cls(success=False, error=error)
```

---

## Testing Patterns

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_create_user(mock_db):
    service = UserService(db=mock_db)
    result = await service.create_user({"email": "test@example.com"})
    assert result.success
```

---

## Best Practices

### ✅ DO
- Use type hints for all public functions
- Prefer `async/await` for I/O operations
- Use Pydantic for data validation
- Write docstrings for public APIs
- Use `pathlib.Path` instead of `os.path`
- Use context managers for resources

### ❌ DON'T
- Use `Any` without good reason
- Block the event loop with sync I/O
- Catch bare `Exception`
- Use mutable default arguments
- Use global state
