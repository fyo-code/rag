---
name: typescript
description: TypeScript patterns and best practices for type-safe JavaScript development. Covers types, generics, and common patterns.
---

# TypeScript Patterns

## Core Types

### Basic Types
```typescript
// Primitives
const name: string = "John"
const age: number = 30
const isActive: boolean = true

// Arrays
const items: string[] = ["a", "b", "c"]
const numbers: Array<number> = [1, 2, 3]

// Objects
interface User {
  id: number
  name: string
  email: string
  role?: "admin" | "user"  // Optional with union
}

// Type alias
type ID = string | number
```

### Function Types
```typescript
// Function type
type Callback = (value: string) => void

// Generic function
function first<T>(arr: T[]): T | undefined {
  return arr[0]
}

// Async function
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`)
  return res.json()
}
```

---

## Common Patterns

### Utility Types
```typescript
// Partial - make all properties optional
type PartialUser = Partial<User>

// Required - make all properties required
type RequiredUser = Required<User>

// Pick - select specific properties
type UserPreview = Pick<User, "id" | "name">

// Omit - exclude specific properties
type UserWithoutId = Omit<User, "id">

// Record - object with specific key/value types
type UserRoles = Record<string, "admin" | "user" | "guest">
```

### Discriminated Unions
```typescript
type Result<T> = 
  | { success: true; data: T }
  | { success: false; error: string }

function handleResult<T>(result: Result<T>) {
  if (result.success) {
    console.log(result.data)  // TypeScript knows data exists
  } else {
    console.log(result.error)  // TypeScript knows error exists
  }
}
```

### Type Guards
```typescript
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === "object" &&
    obj !== null &&
    "id" in obj &&
    "name" in obj
  )
}

function processData(data: unknown) {
  if (isUser(data)) {
    console.log(data.name)  // TypeScript knows it's User
  }
}
```

---

## Generics

### Generic Constraints
```typescript
interface HasId {
  id: string | number
}

function findById<T extends HasId>(items: T[], id: T["id"]): T | undefined {
  return items.find(item => item.id === id)
}
```

### Generic Components (React)
```typescript
interface ListProps<T> {
  items: T[]
  renderItem: (item: T) => React.ReactNode
}

function List<T>({ items, renderItem }: ListProps<T>) {
  return <ul>{items.map(renderItem)}</ul>
}

// Usage
<List 
  items={users} 
  renderItem={(user) => <li>{user.name}</li>} 
/>
```

---

## API Types

### Request/Response Types
```typescript
interface ApiResponse<T> {
  data: T
  status: number
  message: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

async function fetchUsers(): Promise<PaginatedResponse<User>> {
  const res = await fetch("/api/users")
  return res.json()
}
```

### Zod for Runtime Validation
```typescript
import { z } from "zod"

const UserSchema = z.object({
  id: z.number(),
  name: z.string().min(2),
  email: z.string().email(),
})

type User = z.infer<typeof UserSchema>

function validateUser(data: unknown): User {
  return UserSchema.parse(data)
}
```

---

## Best Practices

### ✅ DO
- Enable strict mode in tsconfig
- Use interfaces for objects, types for unions
- Prefer `unknown` over `any`
- Use type guards for runtime checks
- Leverage utility types

### ❌ DON'T
- Use `any` without justification
- Ignore TypeScript errors with `@ts-ignore`
- Use type assertions (`as`) carelessly
- Forget null/undefined checks
- Over-complicate types

### Strict tsconfig
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```
