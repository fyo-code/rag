---
name: fastapi
description: FastAPI development patterns for building high-performance async APIs with Python. Covers routing, dependency injection, validation, and best practices.
---

# FastAPI Development Patterns

## Core Patterns

### Application Structure
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Route Organization
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_db)
):
    return await user_service.list_users(db, skip, limit)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db = Depends(get_db)
):
    return await user_service.create_user(db, user)
```

---

## Dependency Injection

```python
from fastapi import Depends
from typing import Annotated

async def get_db():
    async with async_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
) -> User:
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401)
    return user

# Type alias for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/me")
async def get_profile(user: CurrentUser):
    return user
```

---

## Pydantic Models

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str = Field(..., description="User email")
    name: str = Field(..., min_length=2)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

---

## Error Handling

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )
```

---

## Database Integration (SQLAlchemy 2.0)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

---

## Best Practices

### ✅ DO
- Use Pydantic for request/response validation
- Use dependency injection for services
- Return proper HTTP status codes
- Document endpoints with docstrings
- Use async for all I/O operations
- Implement proper error handling

### ❌ DON'T
- Put business logic in routes
- Use sync database calls
- Expose internal errors to clients
- Skip input validation
- Hardcode configuration values
