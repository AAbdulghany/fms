/** Canonical TanStack Query keys — keep paths stable for invalidateQueries. */
export const queryKeys = {
  me: ["users", "me"] as const,
  dashboardSummary: ["dashboard", "summary"] as const,
  workOrdersRecent: (pageSize: number) => ["work-orders", "recent", pageSize] as const,
  invoices: ["invoices"] as const,
  clients: (includeArchived: boolean) => ["clients", { includeArchived }] as const,
};
