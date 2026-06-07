# React Basics — Knowledge Hub

> Learn React by studying the FMS codebase.

---

## 1. React Fundamentals

### Component Types

```tsx
// Function Component (preferred)
function DashboardPage() {
  return <div>Dashboard</div>;
}

// With props
interface Props {
  title: string;
  count: number;
}

function StatsCard({ title, count }: Props) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <p>{count}</p>
    </div>
  );
}
```

### JSX Syntax

```tsx
// Basic rendering
return (
  <div className="container">
    <h1>Title</h1>
    {showContent && <p>Content</p>}
    {items.map(item => (
      <div key={item.id}>{item.name}</div>
    ))}
  </div>
);
```

---

## 2. State Management

### useState

```tsx
import { useState } from 'react';

function WorkOrdersPage() {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div>
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      {workOrders.map(wo => (
        <WorkOrderCard key={wo.id} {...wo} />
      ))}
    </div>
  );
}
```

### useEffect

```tsx
import { useEffect } from 'react';

function WorkOrdersPage() {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);

  useEffect(() => {
    // Fetch data on mount
    fetchWorkOrders().then(setWorkOrders);
  }, []); // Empty = run once

  // Or with dependencies
  useEffect(() => {
    fetchWorkOrders(filters).then(setWorkOrders);
  }, [filters]); // Re-run when filters change
}
```

---

## 3. React Router

### Setup

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/work-orders" element={<WorkOrdersPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Dynamic Routes

```tsx
// params
<Route path="/work-orders/:id" element={<WorkOrderDetailPage />} />

// In component
import { useParams } from 'react-router-dom';

function WorkOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  // id is the URL parameter
}
```

### Nested Routes

```tsx
<Route path="/sites" element={<SitesLayout />}>
  <Route index element={<SitesList />} />
  <Route path=":id" element={<SiteDetail />} />
  <Route path=":id/assets" element={<SiteAssets />} />
</Route>
```

---

## 4. Protected Routes

```tsx
// src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface Props {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export function ProtectedRoute({ children, allowedRoles }: Props) {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading...</p>;

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
```

### Usage

```tsx
<Route
  path="/users"
  element={
    <ProtectedRoute allowedRoles={['super_admin', 'company_admin']}>
      <UsersPage />
    </ProtectedRoute>
  }
/>
```

---

## 5. Context

### Creating Context

```tsx
// src/contexts/NotificationContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react';

interface Notification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ContextValue {
  notifications: Notification[];
  addNotification: (message: string, type: Notification['type']) => void;
  removeNotification: (id: string) => void;
}

const NotificationContext = createContext<ContextValue | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = (message: string, type: Notification['type']) => {
    const id = crypto.randomUUID();
    setNotifications(prev => [...prev, { id, message, type }]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <NotificationContext.Provider value={{ notifications, addNotification, removeNotification }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}
```

### Using Context

```tsx
function SomeComponent() {
  const { addNotification } = useNotifications();

  const handleSave = () => {
    addNotification('Saved successfully!', 'success');
  };
}
```

---

## 6. Components Patterns

### List Component

```tsx
interface Props {
  workOrders: WorkOrder[];
}

export function WorkOrderList({ workOrders }: Props) {
  return (
    <div className="space-y-4">
      {workOrders.map(wo => (
        <WorkOrderCard key={wo.id} workOrder={wo} />
      ))}
    </div>
  );
}
```

### Form Component

```tsx
interface Props {
  onSubmit: (data: FormData) => void;
}

export function WorkOrderForm({ onSubmit }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ title, description });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={title}
        onChange={e => setTitle(e.target.value)}
        placeholder="Title"
      />
      <textarea
        value={description}
        onChange={e => setDescription(e.target.value)}
      />
      <button type="submit">Submit</button>
    </form>
  );
}
```

---

## 7. FMS Component Structure

### Layout Component

```tsx
// src/components/Layout.tsx
export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64">
        <Header />
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
```

### Page Component

```tsx
// src/pages/DashboardPage.tsx
export function DashboardPage() {
  const { user } = useAuth();
  const { data: stats } = useDashboardStats();

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="grid grid-cols-4 gap-4">
        <StatsCard title="Total WOs" count={stats.active_wo_count} />
        <StatsCard title="In Progress" count={stats.in_progress_count} />
      </div>
    </div>
  );
}
```

---

## 8. Practice Exercises

### Exercise 1: Create a List Page

```tsx
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);

  useEffect(() => {
    api.getAssets().then(setAssets);
  }, []);

  return (
    <div>
      <h1>Assets</h1>
      <div className="grid grid-cols-3 gap-4">
        {assets.map(asset => (
          <AssetCard key={asset.id} asset={asset} />
        ))}
      </div>
    </div>
  );
}
```

### Exercise 2: Add Filtering

```tsx
export function WorkOrdersPage() {
  const [filter, setFilter] = useState({ status: '' });

  const { data } = useWorkOrders(filter);

  return (
    <div>
      <select
        value={filter.status}
        onChange={e => setFilter({ ...filter, status: e.target.value })}
      >
        <option value="">All</option>
        <option value="open">Open</option>
        <option value="closed">Closed</option>
      </select>
      {/* ... */}
    </div>
  );
}
```

---

## References

- [React Docs](https://react.dev/)
- [FMS Pages](src/pages/)
- [FMS Components](src/components/)