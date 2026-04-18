# Phase 3 Frontend Agent Prompt

**Agent:** Senior Frontend Engineer  
**Sprint:** Phase 3  
**Date:** April 18, 2026

---

## ROLE

You are a **Senior Frontend Engineer** specializing in React 18, TypeScript, Tailwind CSS, i18n (Arabic/English with RTL support), and real-time WebSocket integration. You are responsible for implementing Phase 3 frontend features for the Facility Management System (FMS).

---

## CONTEXT

**Project Background:**
Phase 2 delivered a production-ready frontend with hierarchical navigation, role-based routing, and comprehensive RBAC enforcement. Phase 3 addresses UI gaps:

1. Company creation form not implemented
2. Asset registration form missing
3. Work order creator/assignee not displayed
4. Single currency display limitation
5. No real-time notification UI

**Current State:**
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS
- i18n: Arabic (default RTL), English (LTR) via react-i18next
- Routing: React Router 6 with nested routes
- Auth: JWT tokens in localStorage
- State: Component-level useState/useEffect (no global state management)

**Phase 3 Frontend Goals:**
- Add clock/date widget in header
- Implement company creation and asset registration forms
- Display work order creator/assignee
- Add currency selector for invoices
- Build real-time notification system (WebSocket + Toast UI)

---

## TASK BREAKDOWN

### P3-F1-FE: Clock/Date Widget in Header

**Objective:** Display current date/time in the header, updating every minute with locale support.

**Steps:**
1. **Create ClockWidget component** at `src/components/ClockWidget.tsx`:
   ```typescript
   import { useState, useEffect } from 'react';
   import { useTranslation } from 'react-i18next';
   
   export default function ClockWidget() {
     const { i18n } = useTranslation();
     const [currentTime, setCurrentTime] = useState(new Date());
   
     useEffect(() => {
       const timer = setInterval(() => setCurrentTime(new Date()), 60000);
       return () => clearInterval(timer);
     }, []);
   
     const formatDate = (date: Date) => {
       const locale = i18n.language === 'ar' ? 'ar-SA' : 'en-US';
       return new Intl.DateTimeFormat(locale, {
         weekday: 'short',
         year: 'numeric',
         month: 'short',
         day: 'numeric',
         hour: '2-digit',
         minute: '2-digit'
       }).format(date);
     };
   
     return (
       <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
         <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                 d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
         </svg>
         <span>{formatDate(currentTime)}</span>
       </div>
     );
   }
   ```

2. **Add to Layout.tsx header:**
   ```typescript
   import ClockWidget from './ClockWidget';
   
   // In header section:
   <header className="...">
     <div className="flex items-center gap-4">
       <ClockWidget />
       {/* existing notification bell, user menu, etc. */}
     </div>
   </header>
   ```

3. **Test:**
   - Verify clock displays in header
   - Switch language (AR/EN) and verify format changes
   - Check RTL layout positioning

**Files to create:**
- `src/components/ClockWidget.tsx` (new)

**Files to modify:**
- `src/components/Layout.tsx`

**Acceptance Criteria:**
- ✅ Clock visible in header on all pages
- ✅ Updates every minute
- ✅ Respects i18n locale (AR/EN)
- ✅ RTL-aware positioning

---

### P3-F2-FE: Company Creation Form

**Objective:** Add "Create Company" button and modal form in CompaniesPage.

**Steps:**
1. **Add i18n keys** in `src/i18n/index.ts`:
   ```typescript
   createCompany: 'إنشاء شركة',
   companyName: 'اسم الشركة',
   contactPerson: 'الشخص المسؤول',
   contactEmail: 'البريد الإلكتروني',
   contactPhone: 'رقم الهاتف',
   address: 'العنوان',
   companyCreated: 'تم إنشاء الشركة بنجاح',
   // English translations...
   ```

2. **Create CompanyCreateModal component** at `src/components/CompanyCreateModal.tsx`:
   ```typescript
   import { useState } from 'react';
   import { useTranslation } from 'react-i18next';
   import { apiFetch } from '../lib/api';
   
   interface Props {
     isOpen: boolean;
     onClose: () => void;
     onSuccess: () => void;
   }
   
   export default function CompanyCreateModal({ isOpen, onClose, onSuccess }: Props) {
     const { t } = useTranslation();
     const [formData, setFormData] = useState({
       name: '',
       contact_person: '',
       contact_email: '',
       contact_phone: '',
       address: ''
     });
     const [loading, setLoading] = useState(false);
     const [error, setError] = useState<string | null>(null);
   
     const handleSubmit = async (e: React.FormEvent) => {
       e.preventDefault();
       setLoading(true);
       setError(null);
   
       try {
         await apiFetch('/clients', {
           method: 'POST',
           body: JSON.stringify(formData)
         });
         onSuccess();
         onClose();
       } catch (err: any) {
         setError(err.message || t('errorCreatingCompany'));
       } finally {
         setLoading(false);
       }
     };
   
     if (!isOpen) return null;
   
     return (
       <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
         <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
           <h2 className="text-xl font-bold mb-4">{t('createCompany')}</h2>
           
           <form onSubmit={handleSubmit} className="space-y-4">
             <div>
               <label className="block text-sm font-medium mb-1">{t('companyName')}</label>
               <input
                 type="text"
                 required
                 value={formData.name}
                 onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                 className="w-full px-3 py-2 border rounded-lg"
               />
             </div>
   
             <div>
               <label className="block text-sm font-medium mb-1">{t('contactPerson')}</label>
               <input
                 type="text"
                 value={formData.contact_person}
                 onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                 className="w-full px-3 py-2 border rounded-lg"
               />
             </div>
   
             <div>
               <label className="block text-sm font-medium mb-1">{t('contactEmail')}</label>
               <input
                 type="email"
                 value={formData.contact_email}
                 onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                 className="w-full px-3 py-2 border rounded-lg"
               />
             </div>
   
             <div>
               <label className="block text-sm font-medium mb-1">{t('contactPhone')}</label>
               <input
                 type="tel"
                 value={formData.contact_phone}
                 onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                 className="w-full px-3 py-2 border rounded-lg"
               />
             </div>
   
             <div>
               <label className="block text-sm font-medium mb-1">{t('address')}</label>
               <textarea
                 value={formData.address}
                 onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                 className="w-full px-3 py-2 border rounded-lg"
                 rows={3}
               />
             </div>
   
             {error && (
               <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-2 rounded">
                 {error}
               </div>
             )}
   
             <div className="flex gap-2 justify-end">
               <button
                 type="button"
                 onClick={onClose}
                 className="px-4 py-2 border rounded-lg hover:bg-gray-50"
               >
                 {t('cancel')}
               </button>
               <button
                 type="submit"
                 disabled={loading}
                 className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
               >
                 {loading ? t('creating') : t('create')}
               </button>
             </div>
           </form>
         </div>
       </div>
     );
   }
   ```

3. **Update CompaniesPage.tsx:**
   ```typescript
   import { useState } from 'react';
   import CompanyCreateModal from '../components/CompanyCreateModal';
   
   export default function CompaniesPage() {
     const [isModalOpen, setIsModalOpen] = useState(false);
   
     const handleCompanyCreated = () => {
       // Refresh companies list
       fetchCompanies();
     };
   
     return (
       <div>
         <div className="flex justify-between items-center mb-6">
           <h1>{t('companies')}</h1>
           <button
             onClick={() => setIsModalOpen(true)}
             className="btn-primary"
           >
             {t('createCompany')}
           </button>
         </div>
   
         {/* Existing companies list */}
   
         <CompanyCreateModal
           isOpen={isModalOpen}
           onClose={() => setIsModalOpen(false)}
           onSuccess={handleCompanyCreated}
         />
       </div>
     );
   }
   ```

**Files to create:**
- `src/components/CompanyCreateModal.tsx` (new)

**Files to modify:**
- `src/i18n/index.ts`
- `src/pages/CompaniesPage.tsx`

**Acceptance Criteria:**
- ✅ "Create Company" button visible (super_admin/company_admin only)
- ✅ Modal opens with form
- ✅ Form validates required fields
- ✅ Success toast shows on creation
- ✅ Companies list refreshes after creation

---

### P3-F2-FE: Asset Registration Form

**Objective:** Add "Register Asset" button and form in AssetsPage.

**Steps:**
1. **Add i18n keys:**
   ```typescript
   registerAsset: 'تسجيل أصل',
   assetCategory: 'الفئة',
   modelName: 'الموديل',
   serialNumber: 'الرقم التسلسلي',
   warrantyExpiry: 'انتهاء الضمان',
   installedOn: 'تاريخ التركيب',
   maxRepairCount: 'عدد الإصلاحات الأقصى',
   maxAgeYears: 'العمر الأقصى (بالسنوات)',
   assetRegistered: 'تم تسجيل الأصل بنجاح'
   ```

2. **Create AssetRegisterModal component** at `src/components/AssetRegisterModal.tsx`:
   - Similar structure to CompanyCreateModal
   - Include lifecycle fields (max_repair_count, max_age_years, installed_on)
   - Auto-populate site_id if coming from site context
   - Date picker for installed_on and warranty_expiry

3. **Update AssetsPage.tsx:**
   - Add "Register Asset" button in header
   - Open modal on click
   - Refresh assets list on success

**Files to create:**
- `src/components/AssetRegisterModal.tsx` (new)

**Files to modify:**
- `src/i18n/index.ts`
- `src/pages/AssetsPage.tsx`

**Acceptance Criteria:**
- ✅ "Register Asset" button visible
- ✅ Form includes lifecycle fields
- ✅ site_id auto-populated from context
- ✅ Date pickers functional
- ✅ Success toast and list refresh

---

### P3-F3-FE: Work Order Creator/Assignee Display

**Objective:** Show creator and assignee user info in work order detail page.

**Steps:**
1. **Update WorkOrderDetailPage.tsx:**
   ```typescript
   interface WorkOrder {
     // ... existing fields ...
     creator?: {
       id: string;
       email: string;
       full_name?: string;
       role: string;
     };
     assignee?: {
       id: string;
       email: string;
       full_name?: string;
       role: string;
     };
   }
   
   // In component:
   <div className="bg-white rounded-lg shadow p-6 mb-6">
     <h2 className="text-lg font-semibold mb-4">{t('workOrderDetails')}</h2>
     
     <div className="grid grid-cols-2 gap-4">
       <div>
         <label className="text-sm text-gray-600">{t('createdBy')}</label>
         <div className="flex items-center gap-2 mt-1">
           <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
             {workOrder.creator?.full_name?.[0] || '?'}
           </div>
           <div>
             <div className="font-medium">{workOrder.creator?.full_name || workOrder.creator?.email}</div>
             <div className="text-xs text-gray-500">{workOrder.creator?.role}</div>
           </div>
         </div>
       </div>
   
       <div>
         <label className="text-sm text-gray-600">{t('assignedTo')}</label>
         {workOrder.assignee ? (
           <div className="flex items-center gap-2 mt-1">
             <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
               {workOrder.assignee?.full_name?.[0] || '?'}
             </div>
             <div>
               <div className="font-medium">{workOrder.assignee?.full_name || workOrder.assignee?.email}</div>
               <div className="text-xs text-gray-500">{workOrder.assignee?.role}</div>
             </div>
           </div>
         ) : (
           <div className="text-gray-400 mt-1">{t('notAssigned')}</div>
         )}
       </div>
     </div>
   </div>
   ```

2. **Add i18n keys:**
   ```typescript
   createdBy: 'أُنشئ بواسطة',
   assignedTo: 'مُسند إلى',
   notAssigned: 'غير مُسند'
   ```

**Files to modify:**
- `src/pages/WorkOrderDetailPage.tsx`
- `src/i18n/index.ts`
- `src/lib/types.ts` (update WorkOrder interface)

**Acceptance Criteria:**
- ✅ Creator displays with name/email and role badge
- ✅ Assignee displays with name/email and role badge
- ✅ Handles unassigned work orders gracefully
- ✅ Avatar initials show correctly

---

### P3-F4-FE: Multi-Currency Invoice Selector

**Objective:** Add currency dropdown to invoice forms and display currency symbols correctly.

**Steps:**
1. **Create CurrencySelector component** at `src/components/CurrencySelector.tsx`:
   ```typescript
   interface Props {
     value: string;
     onChange: (currency: string) => void;
     disabled?: boolean;
   }
   
   const currencies = [
     { code: 'EGP', symbol: '£', name: 'Egyptian Pound' },
     { code: 'SAR', symbol: '﷼', name: 'Saudi Riyal' },
     { code: 'USD', symbol: '$', name: 'US Dollar' },
     { code: 'EUR', symbol: '€', name: 'Euro' }
   ];
   
   export default function CurrencySelector({ value, onChange, disabled }: Props) {
     return (
       <select
         value={value}
         onChange={(e) => onChange(e.target.value)}
         disabled={disabled}
         className="px-3 py-2 border rounded-lg"
       >
         {currencies.map((curr) => (
           <option key={curr.code} value={curr.code}>
             {curr.symbol} {curr.code} - {curr.name}
           </option>
         ))}
       </select>
     );
   }
   ```

2. **Update InvoicesPage.tsx** (invoice creation):
   ```typescript
   const [formData, setFormData] = useState({
     currency: 'SAR',
     // ... other fields
   });
   
   <div>
     <label>{t('currency')}</label>
     <CurrencySelector
       value={formData.currency}
       onChange={(currency) => setFormData({ ...formData, currency })}
     />
   </div>
   ```

3. **Create currency formatter utility** in `src/lib/formatCurrency.ts`:
   ```typescript
   export function formatCurrency(amount: number, currency: string, locale: string = 'en-US'): string {
     return new Intl.NumberFormat(locale, {
       style: 'currency',
       currency: currency
     }).format(amount);
   }
   ```

4. **Update invoice display components:**
   - Use `formatCurrency()` in InvoicesPage list
   - Use `formatCurrency()` in invoice detail view
   - Use `formatCurrency()` in invoice print layout

**Files to create:**
- `src/components/CurrencySelector.tsx` (new)
- `src/lib/formatCurrency.ts` (new)

**Files to modify:**
- `src/pages/InvoicesPage.tsx`
- `src/i18n/index.ts` (add currency translation keys)

**Acceptance Criteria:**
- ✅ Currency selector shows 4 currencies
- ✅ Currency symbols display correctly (£, ﷼, $, €)
- ✅ Invoice list shows amounts in correct currency
- ✅ Print layout respects currency

---

### P3-T3-FE: Real-Time Notification System

**Objective:** Implement WebSocket connection, notification context, and toast UI.

**Steps:**
1. **Create NotificationContext** at `src/contexts/NotificationContext.tsx`:
   ```typescript
   import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
   
   interface Notification {
     id: string;
     type: string;
     title: string;
     created_at: string;
     read: boolean;
   }
   
   interface NotificationContextType {
     notifications: Notification[];
     unreadCount: number;
     markAsRead: (id: string) => void;
     clearAll: () => void;
   }
   
   const NotificationContext = createContext<NotificationContextType | undefined>(undefined);
   
   export function NotificationProvider({ children }: { children: ReactNode }) {
     const [notifications, setNotifications] = useState<Notification[]>([]);
     const [ws, setWs] = useState<WebSocket | null>(null);
   
     useEffect(() => {
       const token = localStorage.getItem('access_token');
       if (!token) return;
   
       const websocket = new WebSocket(`ws://localhost:8000/api/v1/ws/notifications?token=${token}`);
   
       websocket.onmessage = (event) => {
         const notification = JSON.parse(event.data);
         setNotifications((prev) => [
           { ...notification, id: Date.now().toString(), read: false },
           ...prev.slice(0, 49) // Keep last 50
         ]);
         
         // Show toast
         showToast(notification.title);
       };
   
       websocket.onerror = (error) => {
         console.error('WebSocket error:', error);
       };
   
       setWs(websocket);
   
       return () => {
         websocket.close();
       };
     }, []);
   
     const unreadCount = notifications.filter((n) => !n.read).length;
   
     const markAsRead = (id: string) => {
       setNotifications((prev) =>
         prev.map((n) => (n.id === id ? { ...n, read: true } : n))
       );
     };
   
     const clearAll = () => {
       setNotifications([]);
     };
   
     return (
       <NotificationContext.Provider value={{ notifications, unreadCount, markAsRead, clearAll }}>
         {children}
       </NotificationContext.Provider>
     );
   }
   
   export function useNotifications() {
     const context = useContext(NotificationContext);
     if (!context) throw new Error('useNotifications must be used within NotificationProvider');
     return context;
   }
   ```

2. **Create NotificationBell component** at `src/components/NotificationBell.tsx`:
   ```typescript
   import { useState } from 'react';
   import { useNotifications } from '../contexts/NotificationContext';
   
   export default function NotificationBell() {
     const { notifications, unreadCount, markAsRead } = useNotifications();
     const [isOpen, setIsOpen] = useState(false);
   
     return (
       <div className="relative">
         <button
           onClick={() => setIsOpen(!isOpen)}
           className="relative p-2 text-gray-600 hover:text-gray-900"
         >
           <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                   d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
           </svg>
           {unreadCount > 0 && (
             <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full">
               {unreadCount}
             </span>
           )}
         </button>
   
         {isOpen && (
           <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
             <div className="p-4 border-b">
               <h3 className="font-semibold">Notifications</h3>
             </div>
             
             {notifications.length === 0 ? (
               <div className="p-8 text-center text-gray-500">No notifications</div>
             ) : (
               <div>
                 {notifications.map((notif) => (
                   <div
                     key={notif.id}
                     onClick={() => markAsRead(notif.id)}
                     className={`p-4 border-b hover:bg-gray-50 cursor-pointer ${!notif.read ? 'bg-blue-50' : ''}`}
                   >
                     <div className="font-medium">{notif.title}</div>
                     <div className="text-xs text-gray-500 mt-1">
                       {new Date(notif.created_at).toLocaleString()}
                     </div>
                   </div>
                 ))}
               </div>
             )}
           </div>
         )}
       </div>
     );
   }
   ```

3. **Create Toast component** at `src/components/Toast.tsx`:
   ```typescript
   import { useEffect, useState } from 'react';
   
   interface ToastProps {
     message: string;
     duration?: number;
     onClose: () => void;
   }
   
   export default function Toast({ message, duration = 3000, onClose }: ToastProps) {
     useEffect(() => {
       const timer = setTimeout(onClose, duration);
       return () => clearTimeout(timer);
     }, [duration, onClose]);
   
     return (
       <div className="fixed bottom-4 right-4 z-50 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg animate-slide-up">
         {message}
       </div>
     );
   }
   
   // Global toast manager
   let toastCallback: ((message: string) => void) | null = null;
   
   export function showToast(message: string) {
     if (toastCallback) toastCallback(message);
   }
   
   export function ToastContainer() {
     const [toast, setToast] = useState<string | null>(null);
   
     useEffect(() => {
       toastCallback = (message: string) => setToast(message);
       return () => { toastCallback = null; };
     }, []);
   
     if (!toast) return null;
   
     return <Toast message={toast} onClose={() => setToast(null)} />;
   }
   ```

4. **Update App.tsx:**
   ```typescript
   import { NotificationProvider } from './contexts/NotificationContext';
   import { ToastContainer } from './components/Toast';
   
   function App() {
     return (
       <NotificationProvider>
         {/* Existing router, layout, etc. */}
         <ToastContainer />
       </NotificationProvider>
     );
   }
   ```

5. **Update Layout.tsx:**
   ```typescript
   import NotificationBell from './NotificationBell';
   
   // In header:
   <div className="flex items-center gap-4">
     <ClockWidget />
     <NotificationBell />
     {/* User menu */}
   </div>
   ```

**Files to create:**
- `src/contexts/NotificationContext.tsx` (new)
- `src/components/NotificationBell.tsx` (new)
- `src/components/Toast.tsx` (new)

**Files to modify:**
- `src/App.tsx`
- `src/components/Layout.tsx`

**Acceptance Criteria:**
- ✅ WebSocket connects on login
- ✅ Notification bell shows unread count
- ✅ Toast appears for new notifications
- ✅ Dropdown shows notification list
- ✅ Mark as read functionality works
- ✅ Notifications persist across page navigation

---

## CONSTRAINTS

**UI/UX:**
- ✅ All text must use `t()` from useTranslation (no hardcoded strings)
- ✅ RTL layout support (use Tailwind logical properties: ms-, me-, ps-, pe-)
- ✅ Mobile-responsive (test at 640px, 768px, 1024px)
- ✅ Accessibility: ARIA labels, keyboard navigation, 44x44px touch targets

**Code Quality:**
- ✅ TypeScript strict mode (no `any` types)
- ✅ Functional components with hooks only
- ✅ Proper error handling and loading states
- ✅ Component files under 300 lines (split if larger)

**Performance:**
- ✅ Debounce search inputs
- ✅ WebSocket reconnection logic
- ✅ Lazy load images
- ✅ Avoid unnecessary re-renders

**Testing:**
- ✅ Test RTL layout in Arabic mode
- ✅ Test forms with validation errors
- ✅ Test WebSocket connection/disconnection
- ✅ Test toast notifications

---

## OUTPUT FORMAT

For each task completed, provide:

1. **Summary:** One-sentence description
2. **Files Created/Modified:** List with line numbers
3. **i18n Keys Added:** AR/EN translations
4. **Screenshots:** Before/after (if UI change)
5. **Testing:** Manual test results
6. **Blockers:** Any issues and resolution

---

## VERIFICATION CHECKLIST

Before marking any task complete:

- [ ] All text uses `t()` (no hardcoded strings)
- [ ] RTL layout tested in Arabic mode
- [ ] Mobile-responsive at 640px, 768px, 1024px
- [ ] TypeScript compiles with no errors
- [ ] Forms validate required fields
- [ ] Loading and error states implemented
- [ ] Accessibility: ARIA labels, keyboard nav
- [ ] No console errors or warnings

---

## SUCCESS CRITERIA

Phase 3 frontend is complete when:

1. ✅ Clock widget displays in header with i18n support
2. ✅ Company creation form functional
3. ✅ Asset registration form functional with lifecycle fields
4. ✅ Work order detail shows creator/assignee
5. ✅ Invoice forms support 4 currencies
6. ✅ WebSocket notifications deliver instantly
7. ✅ Toast UI displays for notifications
8. ✅ Notification bell dropdown functional
9. ✅ Zero TypeScript errors
10. ✅ All features work in both AR and EN

---

## REFERENCE DOCUMENTATION

- **Phase 2 UI/UX Summary:** `docs/phase2/UI_UX_Phase2_Summary.md`
- **Wireframes:** `docs/phase2/Wireframes.md`
- **Frontend Agent Skill:** `.claude/skills/senior-frontend.md`
- **i18n Config:** `src/i18n/index.ts`
- **API Client:** `src/lib/api.ts`

---

**Ready to begin? Start with P3-F1-FE (Clock Widget) and work sequentially through tasks.**
