import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import type { Employee, UserRole } from "../lib/types";
import { EmptyState } from "../components/EmptyState";
import { UserRoleBadge } from "../components/UserRoleBadge";

import { ProvisionCredentialsModal } from "../components/ProvisionCredentialsModal";

type UserListApi = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: string;
  client_id?: string | null;
  phone?: string | null;
  last_login_at?: string | null;
};

function mapToEmployee(u: UserListApi): Employee {
  return {
    id: u.id,
    email: u.email,
    full_name: u.full_name,
    role: u.role,
    status: u.status === "active" ? "active" : "inactive",
    company_id: u.client_id ?? undefined,
    phone: u.phone ?? undefined,
    last_login: u.last_login_at ?? undefined,
    created_at: new Date().toISOString(),
  };
}

type AddUserModalProps = {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
};

function AddUserModal({ open, onClose, onCreated }: AddUserModalProps) {
  const { t } = useTranslation();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"company_admin" | "technician">("technician");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creds, setCreds] = useState<{ email: string; username: string; initialPassword: string } | null>(null);

  if (!open) return null;

  if (creds) {
    return (
      <ProvisionCredentialsModal
        open
        title={t("user_created_credentials")}
        username={creds.username}
        email={creds.email}
        initialPassword={creds.initialPassword}
        onClose={() => {
          setCreds(null);
          onClose();
        }}
      />
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body: { full_name: string; email: string; role: string; password?: string } = {
        full_name: fullName.trim(),
        email: email.trim(),
        role,
      };
      if (password.trim()) body.password = password.trim();

      const res = await apiFetch<{
        user: { email: string; username?: string };
        initial_password?: string | null;
      }>("/users", { method: "POST", json: body });

      setFullName("");
      setEmail("");
      setPassword("");
      onCreated();

      if (res.initial_password) {
        setCreds({
          email: res.user.email,
          username: res.user.username ?? res.user.email,
          initialPassword: res.initial_password,
        });
      } else {
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("add_user")}</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("full_name")} *</label>
            <input
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("email")} *</label>
            <input
              required
              type="email"
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">
              {t("password")} ({t("optional")})
            </label>
            <input
              type="password"
              minLength={8}
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("password_auto_generate_hint")}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("role")} *</label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value as "company_admin" | "technician")}
            >
              <option value="technician">{t("role_technician")}</option>
              <option value="company_admin">{t("role_company_admin")}</option>
            </select>
          </div>
          {error && <p className="text-sm text-error-main">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100" onClick={onClose}>
              {t("cancel")}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? t("loading") : t("create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function UsersPage() {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<UserRole | "all">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [addUserOpen, setAddUserOpen] = useState(false);

  const loadEmployees = () => {
    void (async () => {
      try {
        const data = await apiFetch<UserListApi[]>("/users");
        setEmployees(data.map(mapToEmployee));
      } catch (error) {
        console.error("Failed to fetch employees", error);
        setEmployees([]);
      } finally {
        setLoading(false);
      }
    })();
  };

  useEffect(() => {
    loadEmployees();
  }, []);

  const filteredEmployees = employees.filter((employee) => {
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      employee.full_name.toLowerCase().includes(query) ||
      employee.email.toLowerCase().includes(query) ||
      (employee.phone && employee.phone.toLowerCase().includes(query));

    const matchesRole = roleFilter === "all" || employee.role === roleFilter;
    const matchesStatus = statusFilter === "all" || employee.status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold text-neutral-900">{t("employees")}</h1>
        <button
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          onClick={() => setAddUserOpen(true)}
        >
          + {t("add_user")}
        </button>
      </div>

      {/* Filters */}
      {employees.length > 0 && (
        <div className="space-y-4">
          {/* Search */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder={`${t("search")} ${t("employees").toLowerCase()}...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-neutral-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
              />
            </div>
          </div>

          {/* Role & Status Filters */}
          <div className="flex flex-wrap gap-2">
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as UserRole | "all")}
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
            >
              <option value="all">{t("all")} {t("role")}</option>
              <option value="super_admin">{t("role_super_admin")}</option>
              <option value="company_admin">{t("role_company_admin")}</option>
              <option value="client_admin">{t("role_client_admin")}</option>
              <option value="site_manager">{t("role_site_manager")}</option>
              <option value="technician">{t("role_technician")}</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as "all" | "active" | "inactive")}
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
            >
              <option value="all">{t("all")} {t("status")}</option>
              <option value="active">{t("status_active")}</option>
              <option value="inactive">{t("status_inactive")}</option>
            </select>

            {(searchQuery || roleFilter !== "all" || statusFilter !== "all") && (
              <button
                onClick={() => {
                  setSearchQuery("");
                  setRoleFilter("all");
                  setStatusFilter("all");
                }}
                className="rounded-lg border border-neutral-300 bg-neutral-0 px-3 py-1.5 text-sm text-neutral-700 transition-colors hover:bg-neutral-50"
              >
                {t("clear_filters")}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {employees.length === 0 ? (
        <EmptyState
          icon={
            <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
          }
          title={t("no_employees")}
          description="Add your first employee to start assigning work orders."
          action={{
            label: `+ ${t("add_user")}`,
            onClick: () => setAddUserOpen(true),
          }}
        />
      ) : filteredEmployees.length === 0 ? (
        <EmptyState
          icon={
            <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          }
          title={t("no_results")}
          description="Try adjusting your search or filter criteria."
          action={{
            label: t("clear_filters"),
            onClick: () => {
              setSearchQuery("");
              setRoleFilter("all");
              setStatusFilter("all");
            },
          }}
        />
      ) : (
        <>
          {/* Desktop Table */}
          <div className="hidden overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm md:block">
            <table className="w-full">
              <thead className="border-b border-neutral-200 bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("full_name")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("email")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("role")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("status")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("last_login")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {filteredEmployees.map((employee) => (
                  <tr
                    key={employee.id}
                    className="transition-colors hover:bg-neutral-50"
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-neutral-900">{employee.full_name}</div>
                      {employee.phone && (
                        <div className="text-xs text-neutral-500">{employee.phone}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">{employee.email}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <UserRoleBadge role={employee.role} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          employee.status === "active"
                            ? "bg-success-light text-success-dark"
                            : "bg-neutral-200 text-neutral-600"
                        }`}
                      >
                        {employee.status === "active" ? t("status_active") : t("status_inactive")}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-600">
                      {employee.last_login
                        ? new Date(employee.last_login).toLocaleDateString()
                        : "Never"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="grid gap-4 md:hidden">
            {filteredEmployees.map((employee) => (
              <div
                key={employee.id}
                className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm transition-colors hover:border-primary-300"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="text-base font-medium text-neutral-900">{employee.full_name}</div>
                    <div className="text-sm text-neutral-600">{employee.email}</div>
                    {employee.phone && (
                      <div className="text-sm text-neutral-600">{employee.phone}</div>
                    )}
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      employee.status === "active"
                        ? "bg-success-light text-success-dark"
                        : "bg-neutral-200 text-neutral-600"
                    }`}
                  >
                    {employee.status === "active" ? t("status_active") : t("status_inactive")}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <UserRoleBadge role={employee.role} />
                  {employee.last_login && (
                    <span className="text-xs text-neutral-500">
                      {t("last_login")}: {new Date(employee.last_login).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <AddUserModal
        open={addUserOpen}
        onClose={() => setAddUserOpen(false)}
        onCreated={() => loadEmployees()}
      />
    </div>
  );
}
