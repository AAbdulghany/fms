/**
 * Header back walks the page tree, not the browser history.
 * A detail page returns to its list. A list returns to the dashboard.
 */
export function shellParentPath(pathname: string): string | null {
  const path = pathname.replace(/\/+$/, "") || "/";
  if (path === "/" || path === "/dashboard") return null;

  if (path === "/assets/maintenance-calendar") return "/assets";
  if (/^\/assets\/[^/]+$/.test(path)) return "/assets";
  if (/^\/companies\/[^/]+$/.test(path)) return "/companies";
  if (/^\/sites\/[^/]+$/.test(path)) return "/companies";
  if (/^\/work-orders\/[^/]+$/.test(path)) return "/work-orders";
  if (/^\/invoices\/[^/]+$/.test(path)) return "/invoices";

  return "/dashboard";
}
