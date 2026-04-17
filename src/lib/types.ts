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
