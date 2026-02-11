---
name: nextjs
description: Next.js 14+ App Router patterns for building modern React applications. Covers Server Components, Server Actions, routing, and performance optimization.
---

# Next.js App Router Patterns

## Project Structure

```
app/
├── layout.tsx           # Root layout
├── page.tsx             # Home page
├── globals.css          # Global styles
├── (auth)/              # Route group (no URL segment)
│   ├── login/page.tsx
│   └── register/page.tsx
├── dashboard/
│   ├── layout.tsx       # Dashboard layout
│   ├── page.tsx         # /dashboard
│   └── [id]/page.tsx    # /dashboard/:id
├── api/
│   └── route.ts         # API routes
└── components/
    ├── ui/              # Reusable UI components
    └── features/        # Feature-specific components
```

---

## Server vs Client Components

### Server Components (Default)
```tsx
// app/users/page.tsx
// Server Component by default

async function UsersPage() {
  // Fetch directly in component
  const users = await fetch('http://api.example.com/users').then(r => r.json());
  
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

export default UsersPage;
```

### Client Components
```tsx
'use client'

import { useState } from 'react'

export function Counter() {
  const [count, setCount] = useState(0)
  
  return (
    <button onClick={() => setCount(c => c + 1)}>
      Count: {count}
    </button>
  )
}
```

### When to Use Each
| Use Case | Server | Client |
|----------|--------|--------|
| Data fetching | ✅ | ⚠️ |
| Direct API access | ✅ | ❌ |
| useState, useEffect | ❌ | ✅ |
| Browser APIs | ❌ | ✅ |
| Event handlers | ❌ | ✅ |

---

## Server Actions

```tsx
// app/actions.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function createUser(formData: FormData) {
  const name = formData.get('name') as string
  const email = formData.get('email') as string
  
  await db.user.create({ data: { name, email } })
  
  revalidatePath('/users')
}

// app/users/new/page.tsx
import { createUser } from '../actions'

export default function NewUserPage() {
  return (
    <form action={createUser}>
      <input name="name" required />
      <input name="email" type="email" required />
      <button type="submit">Create User</button>
    </form>
  )
}
```

---

## Data Fetching Patterns

### Parallel Fetching
```tsx
async function Dashboard() {
  // Fetch in parallel
  const [users, posts, stats] = await Promise.all([
    getUsers(),
    getPosts(),
    getStats()
  ])
  
  return (
    <>
      <UserList users={users} />
      <PostList posts={posts} />
      <StatsCard stats={stats} />
    </>
  )
}
```

### With Suspense
```tsx
import { Suspense } from 'react'

async function SlowComponent() {
  const data = await slowFetch()
  return <div>{data}</div>
}

export default function Page() {
  return (
    <>
      <FastContent />
      <Suspense fallback={<Loading />}>
        <SlowComponent />
      </Suspense>
    </>
  )
}
```

---

## API Integration with FastAPI

```tsx
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchFromApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  
  return res.json()
}

// Usage in Server Component
async function UsersPage() {
  const users = await fetchFromApi<User[]>('/api/users')
  return <UserList users={users} />
}
```

---

## Layouts and Templates

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        {children}
      </main>
    </div>
  )
}
```

---

## Best Practices

### ✅ DO
- Use Server Components by default
- Fetch data in Server Components
- Use Server Actions for mutations
- Implement proper loading states
- Use `next/image` for images
- Colocate components with pages

### ❌ DON'T
- Add 'use client' unnecessarily
- Fetch in Client Components when Server works
- Skip error boundaries
- Use `any` types
- Ignore TypeScript errors
