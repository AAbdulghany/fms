# Tailwind CSS — Knowledge Hub

> Learn Tailwind by studying the FMS codebase.

---

## 1. Tailwind Setup

### Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0f766e',
      },
    },
  },
  plugins: [],
}
```

### Usage in CSS

```css
/* src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## 2. Common Classes

### Layout

```html
<!-- Container -->
<div className="container mx-auto px-4">

<!-- Flex -->
<div className="flex items-center justify-between">

<!-- Grid -->
<div className="grid grid-cols-4 gap-4">
<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
```

### Spacing

```html
<!-- Margin -->
<div className="m-4">        <!-- all -->
<div className="mx-4">       <!-- horizontal -->
<div className="my-4">       <!-- vertical -->
<div className="mt-4">        <!-- top -->
<div className="mb-4">        <!-- bottom -->
<div className="ml-4">        <!-- left -->
<div className="mr-4">        <!-- right -->

<!-- Padding -->
<div className="p-4">
<div className="px-4 py-2">
```

### Sizing

```html
<!-- Width -->
<div className="w-full w-64 w-1/2">

<!-- Height -->
<div className="h-64 h-screen">

<!-- Min/Max -->
<div className="min-h-screen max-w-md">
```

---

## 3. Colors & Typography

### Text Colors

```html
<!-- Text -->
<p className="text-gray-500">
<p className="text-primary">
<p className="text-red-500">
<p className="text-green-500">
```

### Background Colors

```html
<div className="bg-white bg-gray-50 bg-gray-100 bg-primary">
```

### Text Sizes

```html
<p className="text-xs">   <!-- 12px -->
<p className="text-sm">   <!-- 14px -->
<p className="text-base">  <!-- 16px -->
<p className="text-lg">   <!-- 18px -->
<p className="text-xl">   <!-- 20px -->
<p className="text-2xl">  <!-- 24px -->
```

### Font Weight

```html
<p className="font-normal">
<p className="font-medium">
<p className="font-semibold">
<p className="font-bold">
```

---

## 4. Component Patterns

### Card

```tsx
export function StatsCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-semibold mt-2">{value}</p>
    </div>
  );
}
```

### Button

```tsx
export function Button({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### Input

```tsx
export function Input({ value, onChange, placeholder }: Props) {
  return (
    <input
      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
    />
  );
}
```

### Badge

```tsx
function StatusBadge({ status }: { status: string }) {
  const colors = {
    open: 'bg-green-100 text-green-800',
    in_progress: 'bg-blue-100 text-blue-800',
    closed: 'bg-gray-100 text-gray-800',
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs ${colors[status] || colors.open}`}>
      {status}
    </span>
  );
}
```

---

## 5. Responsive Design

### Breakpoints

```html
<!-- Mobile first -->
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">

<!-- Hidden on mobile, block on md -->
<div className="hidden md:block">

<!-- Show on mobile, hide on lg -->
<div className="block lg:hidden">
```

### Responsive Navigation

```tsx
const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

return (
  <div>
    {/* Mobile menu button */}
    <button 
      className="md:hidden"
      onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
    >
      Menu
    </button>
    
    {/* Desktop nav */}
    <nav className="hidden md:flex">
      {/* ... */}
    </nav>
  </div>
);
```

---

## 6. RTL Support (Important for FMS)

### Direction

```html
<!-- Set in root element -->
<html dir="rtl" lang="ar">

<!-- Or dynamically -->
<div dir={locale === 'ar' ? 'rtl' : 'ltr'}>
```

### Logical Properties

```html
<!-- Instead of margin-left, use margin-start -->
<div className="ms-4">    <!-- margin-start -->
<div className="me-4">    <!-- margin-end -->
<div className="ps-4">    <!-- padding-start -->
<div className="pe-4">    <!-- padding-end -->
```

---

## 7. FMS Examples

### Work Order Card

```tsx
function WorkOrderCard({ workOrder }: { workOrder: WorkOrder }) {
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition p-6">
      <div className="flex justify-between items-start">
        <h3 className="font-semibold text-lg">{workOrder.title}</h3>
        <StatusBadge status={workOrder.status} />
      </div>
      
      <p className="text-gray-500 mt-2">{workOrder.description}</p>
      
      <div className="flex items-center mt-4 text-sm text-gray-500">
        <span>{workOrder.company_name}</span>
        <span className="mx-2">•</span>
        <span>{workOrder.site_name}</span>
      </div>
    </div>
  );
}
```

### Sidebar

```tsx
function Sidebar() {
  return (
    <aside className="fixed right-0 top-0 w-64 h-screen bg-white border-r border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-8">
        <h1 className="text-xl font-bold text-primary">NexTask</h1>
      </div>
      
      <nav className="space-y-2">
        <a href="/dashboard" className="block px-4 py-2 rounded hover:bg-gray-100">
          Dashboard
        </a>
        <a href="/work-orders" className="block px-4 py-2 rounded hover:bg-gray-100">
          Work Orders
        </a>
      </nav>
    </aside>
  );
}
```

---

## 8. Practice Exercises

### Exercise 1: Create a Table

```tsx
function Table({ data }: { data: User[] }) {
  return (
    <table className="w-full">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Name</th>
          <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Email</th>
          <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Role</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-200">
        {data.map(user => (
          <tr key={user.id} className="hover:bg-gray-50">
            <td className="px-4 py-3">{user.full_name}</td>
            <td className="px-4 py-3">{user.email}</td>
            <td className="px-4 py-3">{user.role}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### Exercise 2: Create a Modal

```tsx
function Modal({ isOpen, onClose, children }: Props) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <button onClick={onClose} className="absolute left-4 top-4">
          ✕
        </button>
        {children}
      </div>
    </div>
  );
}
```

---

## References

- [Tailwind Docs](https://tailwindcss.com/docs/)
- [FMS Tailwind Config](tailwind.config.js)
- [FMS Styles](src/styles/)