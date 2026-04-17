export type UserRole = 
  | "super_admin" 
  | "company_admin" 
  | "client_admin" 
  | "site_manager" 
  | "technician";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  company_id?: string;
  is_active: boolean;
}

export type WorkOrderStatus =
  | "created"
  | "assigned"
  | "in_progress"
  | "on_hold"
  | "completed"
  | "verified"
  | "cancelled"
  | "closed";

export interface WorkOrder {
  id: string;
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
  opened_at: string;
  closed_at: string | null;
}

export interface PaginatedWorkOrders {
  data: WorkOrder[];
  meta: { page: number; page_size: number; total: number };
}

export interface MaintenanceReport {
  id: string;
  work_order_id: string;
  template_id: string;
  template_version: number;
  answers_json: Record<string, unknown>;
  status: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  schema_json: Record<string, unknown>;
}

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

export interface Company {
  id: string;
  name: string;
  code: string;
  contact_email: string;
  contact_phone?: string;
  status: "active" | "inactive" | "suspended";
  sites_count?: number;
  active_wo_count?: number;
  created_at: string;
}

export interface Site {
  id: string;
  company_id: string;
  company_name?: string;
  name: string;
  address: string;
  city: string;
  country: string;
  timezone: string;
  status: "active" | "inactive";
  asset_count?: number;
  active_wo_count?: number;
  qr_code?: string;
}

export type AssetLifecycleStatus = "active" | "warning" | "end_of_life" | "replaced";

export interface Asset {
  id: string;
  asset_id: string;
  site_id: string;
  site_name?: string;
  company_id: string;
  company_name?: string;
  type: string;
  category: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  installation_date: string;
  expected_lifespan_years: number;
  lifecycle_status: AssetLifecycleStatus;
  age_years: number;
  lifespan_percentage: number;
  repair_count: number;
  last_maintenance_date?: string;
  location_path?: string;
  replacement_wo_id?: string;
}

export interface AssetLifecycleEvent {
  id: string;
  asset_id: string;
  event_type: "installation" | "maintenance" | "repair" | "major_repair" | "replacement";
  date: string;
  work_order_id?: string;
  cost_sar?: string;
  description?: string;
}

export interface Employee {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  company_id?: string;
  assigned_sites?: string[];
  status: "active" | "inactive";
  last_login?: string;
  created_at: string;
}

export interface DashboardStats {
  companies_count?: number;
  active_wo_count: number;
  pending_invoices_amount?: string;
  technicians_count?: number;
  my_tasks_count?: number;
  in_progress_count?: number;
  completed_week_count?: number;
  sites_count?: number;
  assets_count?: number;
  overdue_maintenance_count?: number;
  assets_at_eol_count?: number;
}
