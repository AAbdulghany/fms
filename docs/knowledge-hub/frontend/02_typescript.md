# TypeScript — Knowledge Hub

> Learn TypeScript by studying the FMS codebase.

---

## 1. TypeScript Basics

### Primitive Types

```typescript
// Strings, numbers, booleans
let name: string = 'John';
let age: number = 30;
let active: boolean = true;

// Arrays
let names: string[] = ['John', 'Jane'];
let ages: Array<number> = [30, 25];

// Objects
let user: { name: string; age: number } = {
  name: 'John',
  age: 30
};
```

### Type Aliases

```typescript
// Simple alias
type UserRole = 'super_admin' | 'company_admin' | 'client_admin' | 'site_manager' | 'technician' | 'manager';

// Interface
interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

// Extending interfaces
interface AdminUser extends User {
  permissions: string[];
}
```

---

## 2. FMS Type Examples

### Enums as Types

```typescript
// Work order status
export type WorkOrderStatus =
  | 'created'
  | 'assigned'
  | 'in_progress'
  | 'on_hold'
  | 'completed'
  | 'verified'
  | 'cancelled'
  | 'closed';

// Asset lifecycle
export type AssetLifecycleStatus = 'active' | 'warning' | 'end_of_life' | 'replaced';
```

### API Types

```typescript
// API response wrapper
export interface PaginatedWorkOrders {
  data: WorkOrder[];
  meta: { page: number; page_size: number; total: number };
}

// Work order type
export interface WorkOrder {
  id: string;
  tenant_id?: string;
  client_id: string;
  site_id: string;
  asset_id: string | null;
  source: string;
  category: string;
  urgency: string;
  status: WorkOrderStatus;
  title: string;
  description: string;
  template_id: string | null;
  assignee_user_id: string | null;
  creator?: WorkOrderUserBrief | null;
  assignee?: WorkOrderUserBrief | null;
  company_name?: string | null;
  site_name?: string | null;
  tags?: string[];
  opened_at: string;
  closed_at: string | null;
}
```

### Nested Types

```typescript
// Related user type
export interface WorkOrderUserBrief {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

// Invoice with line items
export interface Invoice {
  id: string;
  client_id: string;
  work_order_id: string;
  number: string;
  status: string;
  subtotal_sar: string;
  tax_sar: string;
  total_sar: string;
  currency: string;
  line_items: Array<{
    line_type: string;
    description: string;
    quantity: string;
    unit_price_sar: string;
    amount_sar: string;
  }>;
}
```

---

## 3. Function Types

### Function Signatures

```typescript
// Basic function
function add(a: number, b: number): number {
  return a + b;
}

// Arrow function
const add = (a: number, b: number): number => a + b;

// Optional parameters
function createUser(name: string, email?: string): User {
  return { name, email: email ?? '' };
}

// Default parameters
function createUser(name: string, role: UserRole = 'technician'): User {
  return { name, role };
}
```

### Generic Functions

```typescript
// Generic type
function getById<T>(id: string): Promise<T> {
  return fetch(`/api/v1/${id}`).then(res => res.json());
}

// Usage
const user = await getById<User>('user-123');
const wo = await getById<WorkOrder>('wo-123');
```

---

## 4. React + TypeScript

### Component Props

```typescript
interface Props {
  workOrder: WorkOrder;
  onUpdate?: (id: string, data: Partial<WorkOrder>) => void;
}

export function WorkOrderCard({ workOrder, onUpdate }: Props) {
  return (
    <div>
      <h3>{workOrder.title}</h3>
      <span>{workOrder.status}</span>
    </div>
  );
}
```

### useState with Types

```typescript
// Simple state
const [users, setUsers] = useState<User[]>([]);

// With null type
const [currentUser, setCurrentUser] = useState<User | null>(null);

// Complex state
const [state, setState] = useState<{
  data: WorkOrder[];
  loading: boolean;
  error: string | null;
}>({
  data: [],
  loading: false,
  error: null
});
```

### useEffect Types

```typescript
import { useEffect } from 'react';

// Effect with cleanup
useEffect(() => {
  const subscription = subscribe(id);
  return () => subscription.unsubscribe();
}, [id]);
```

---

## 5. API Client Types

### API Function Signatures

```typescript
// src/lib/api.ts
import { WorkOrder, PaginatedWorkOrders } from './types';

interface ListParams {
  page?: number;
  page_size?: number;
  status?: string;
}

export async function getWorkOrders(params?: ListParams): Promise<PaginatedWorkOrders> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.status) searchParams.set('status', params.status);
  
  const response = await fetch(`/api/v1/work-orders?${searchParams}`);
  return response.json();
}

export async function createWorkOrder(data: Partial<WorkOrder>): Promise<WorkOrder> {
  const response = await fetch('/api/v1/work-orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}
```

---

## 6. Utility Types

### Partial & Required

```typescript
// Make all optional
type PartialUser = Partial<User>;

// Make all required
type RequiredUser = Required<User>;
```

### Pick & Omit

```typescript
// Select specific fields
type UserBrief = Pick<User, 'id' | 'email' | 'full_name'>;

// Exclude specific fields
type UserWithoutId = Omit<User, 'id'>;
```

### Record

```typescript
// Object with string keys
type UserMap = Record<string, User>;
// { [key: string]: User }

// Usage
const usersById: UserMap = {
  'user-1': { id: 'user-1', email: '...', ... },
  'user-2': { id: 'user-2', email: '...', ... },
};
```

---

## 7. Practice Exercises

### Exercise 1: Define a Type

Create a type for notifications:

```typescript
export interface Notification {
  id: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

export type NotificationList = Notification[];
```

### Exercise 2: Create Generic Fetch

```typescript
async function fetchList<T>(endpoint: string, params?: Record<string, string>): Promise<T[]> {
  const searchParams = new URLSearchParams(params);
  const response = await fetch(`${endpoint}?${searchParams}`);
  const data = await response.json();
  return data.data;
}

// Usage
const users = await fetchList<User>('/api/v1/users');
```

---

## References

- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [FMS Types](src/lib/types.ts)