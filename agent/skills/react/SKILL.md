---
name: react
description: React patterns and best practices for building maintainable components. Covers hooks, state management, and component design.
---

# React Patterns & Best Practices

## Component Patterns

### Function Components
```tsx
interface UserCardProps {
  user: User
  onEdit?: (id: string) => void
}

export function UserCard({ user, onEdit }: UserCardProps) {
  return (
    <div className="card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      {onEdit && (
        <button onClick={() => onEdit(user.id)}>Edit</button>
      )}
    </div>
  )
}
```

### Custom Hooks
```tsx
function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue
    const stored = localStorage.getItem(key)
    return stored ? JSON.parse(stored) : initialValue
  })

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value))
  }, [key, value])

  return [value, setValue] as const
}

// Usage
const [theme, setTheme] = useLocalStorage('theme', 'light')
```

---

## State Management

### useState for Local State
```tsx
const [count, setCount] = useState(0)
const [user, setUser] = useState<User | null>(null)

// Update based on previous state
setCount(prev => prev + 1)

// Update object
setUser(prev => prev ? { ...prev, name: 'New Name' } : null)
```

### useReducer for Complex State
```tsx
type State = { count: number; step: number }
type Action = 
  | { type: 'increment' }
  | { type: 'decrement' }
  | { type: 'setStep'; payload: number }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + state.step }
    case 'decrement':
      return { ...state, count: state.count - state.step }
    case 'setStep':
      return { ...state, step: action.payload }
    default:
      return state
  }
}

const [state, dispatch] = useReducer(reducer, { count: 0, step: 1 })
```

### Context for Shared State
```tsx
interface ThemeContextType {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  
  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')
  
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
```

---

## Data Fetching

### With TanStack Query
```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => fetch('/api/users').then(r => r.json()),
  })
}

function useCreateUser() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (user: UserCreate) => 
      fetch('/api/users', {
        method: 'POST',
        body: JSON.stringify(user)
      }).then(r => r.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    }
  })
}
```

---

## Performance Optimization

### React.memo for Expensive Components
```tsx
const ExpensiveList = React.memo(function ExpensiveList({ items }: { items: Item[] }) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  )
})
```

### useCallback and useMemo
```tsx
// useCallback for event handlers passed to children
const handleClick = useCallback((id: string) => {
  setSelected(id)
}, [])

// useMemo for expensive computations
const sortedItems = useMemo(() => {
  return [...items].sort((a, b) => a.name.localeCompare(b.name))
}, [items])
```

---

## Error Handling

```tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

// Usage
<ErrorBoundary fallback={<ErrorMessage />}>
  <RiskyComponent />
</ErrorBoundary>
```

---

## Best Practices

### ✅ DO
- Use TypeScript strictly (no `any`)
- Keep components small and focused
- Lift state only when necessary
- Use hooks for reusable logic
- Handle loading/error states
- Test critical components

### ❌ DON'T
- Mutate state directly
- Use index as key (unless stable)
- Overuse useMemo/useCallback
- Put async in useEffect without cleanup
- Ignore TypeScript errors
