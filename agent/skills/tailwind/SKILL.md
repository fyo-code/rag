---
name: tailwind
description: Tailwind CSS patterns for building beautiful, responsive UIs. Covers utility classes, custom configurations, and design systems.
---

# Tailwind CSS Patterns

## Responsive Design

### Mobile-First Breakpoints
```html
<!-- Mobile first: base styles apply to all, then override for larger screens -->
<div class="
  p-4 text-sm           <!-- Mobile (all) -->
  md:p-6 md:text-base   <!-- Tablet (768px+) -->
  lg:p-8 lg:text-lg     <!-- Desktop (1024px+) -->
">
  Content
</div>
```

### Common Breakpoints
| Prefix | Min Width | Description |
|--------|-----------|-------------|
| (none) | 0px | Mobile |
| `sm:` | 640px | Large phone |
| `md:` | 768px | Tablet |
| `lg:` | 1024px | Desktop |
| `xl:` | 1280px | Large desktop |
| `2xl:` | 1536px | Extra large |

---

## Layout Patterns

### Flexbox
```html
<!-- Centered container -->
<div class="flex items-center justify-center min-h-screen">
  <div>Centered content</div>
</div>

<!-- Responsive navbar -->
<nav class="flex flex-col md:flex-row items-center justify-between p-4">
  <div class="logo">Brand</div>
  <div class="flex gap-4">Links</div>
</nav>
```

### Grid
```html
<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <div>Card 1</div>
  <div>Card 2</div>
  <div>Card 3</div>
</div>

<!-- Dashboard layout -->
<div class="grid grid-cols-12 gap-4">
  <aside class="col-span-12 md:col-span-3">Sidebar</aside>
  <main class="col-span-12 md:col-span-9">Content</main>
</div>
```

---

## Component Patterns

### Card
```html
<div class="
  bg-white dark:bg-gray-800 
  rounded-lg shadow-md 
  p-6 
  border border-gray-200 dark:border-gray-700
  hover:shadow-lg transition-shadow
">
  <h3 class="text-lg font-semibold mb-2">Title</h3>
  <p class="text-gray-600 dark:text-gray-300">Description</p>
</div>
```

### Button Variants
```html
<!-- Primary -->
<button class="
  px-4 py-2 rounded-lg font-medium
  bg-blue-600 text-white
  hover:bg-blue-700 
  focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
  transition-colors
">
  Primary
</button>

<!-- Secondary -->
<button class="
  px-4 py-2 rounded-lg font-medium
  bg-gray-100 text-gray-900
  hover:bg-gray-200
  dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600
  transition-colors
">
  Secondary
</button>

<!-- Ghost -->
<button class="
  px-4 py-2 rounded-lg font-medium
  text-blue-600 
  hover:bg-blue-50
  dark:text-blue-400 dark:hover:bg-blue-900/20
  transition-colors
">
  Ghost
</button>
```

### Input
```html
<input 
  type="text"
  class="
    w-full px-4 py-2 rounded-lg
    border border-gray-300 dark:border-gray-600
    bg-white dark:bg-gray-800
    text-gray-900 dark:text-white
    placeholder-gray-500
    focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20
    transition-colors
  "
  placeholder="Enter text..."
/>
```

---

## Dark Mode

```html
<!-- Dark mode with class strategy -->
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
  <h1 class="text-gray-900 dark:text-white">Title</h1>
  <p class="text-gray-600 dark:text-gray-400">Description</p>
</div>
```

```js
// tailwind.config.js
module.exports = {
  darkMode: 'class', // or 'media' for system preference
}
```

---

## Animations

```html
<!-- Hover effects -->
<div class="hover:scale-105 transition-transform duration-200">
  Scales on hover
</div>

<!-- Fade in on scroll (with JS) -->
<div class="opacity-0 animate-fade-in">
  Fades in
</div>

<!-- Spinner -->
<div class="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full" />
```

```js
// tailwind.config.js - custom animation
module.exports = {
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
}
```

---

## Best Practices

### ✅ DO
- Use mobile-first responsive design
- Group related utilities logically
- Use design tokens (colors, spacing)
- Leverage dark mode properly
- Extract common patterns to components

### ❌ DON'T
- Repeat the same utility groups everywhere
- Use arbitrary values when tokens exist
- Forget hover/focus states
- Skip dark mode support
- Use too many custom classes
