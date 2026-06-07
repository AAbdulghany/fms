import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { apiFetch } from "../lib/api";
import type { User } from "../lib/types";

export function ProfilePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const mustChange = searchParams.get("must_change") === "1";

  const [user, setUser] = useState<User | null>(null);
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const u = await apiFetch<User & { username?: string }>("/users/me");
        setUser(u);
        setFullName(u.full_name);
      } catch (e) {
        setErr(e instanceof Error ? e.message : t("error"));
      } finally {
        setLoading(false);
      }
    })();
  }, [t]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    if (password && password !== confirmPassword) {
      setErr(t("password_mismatch"));
      return;
    }
    if (password && password.length < 6) {
      setErr(t("password_too_short"));
      return;
    }
    setSaving(true);
    try {
      const body: { full_name: string; password?: string } = {
        full_name: fullName.trim(),
      };
      if (password) body.password = password;
      const updated = await apiFetch<User>("/users/me", { method: "PATCH", json: body });
      setUser(updated);
      setPassword("");
      setConfirmPassword("");
      setMsg(t("profile_saved"));
      if (mustChange) {
        navigate("/dashboard", { replace: true });
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[240px] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-2xl font-semibold text-neutral-900">{t("profile")}</h1>

      {mustChange && (
        <p className="rounded-md bg-warning-light px-4 py-3 text-sm text-warning-dark">
          {t("must_change_password_prompt")}
        </p>
      )}

      {msg && <p className="rounded-md bg-success-light px-4 py-3 text-sm text-success-dark">{msg}</p>}
      {err && <p className="rounded-md bg-error-light px-4 py-3 text-sm text-error-dark">{err}</p>}

      <form onSubmit={onSubmit} className="space-y-4 rounded-xl border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <div>
          <label className="mb-1 block text-sm font-medium text-neutral-700">{t("email")}</label>
          <input
            readOnly
            className="w-full rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-600"
            value={user?.email ?? ""}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-neutral-700">{t("username")}</label>
          <input
            readOnly
            className="w-full rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-600"
            value={(user as User & { username?: string })?.username ?? "—"}
          />
          <p className="mt-1 text-xs text-neutral-500">{t("username_readonly_hint")}</p>
        </div>
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
          <label className="mb-1 block text-sm font-medium text-neutral-700">
            {t("new_password")} {mustChange ? "*" : `(${t("optional")})`}
          </label>
          <input
            type="password"
            minLength={6}
            required={mustChange}
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-neutral-700">{t("confirm_password")}</label>
          <input
            type="password"
            minLength={6}
            required={mustChange || Boolean(password)}
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          {!mustChange && (
            <button
              type="button"
              className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100"
              onClick={() => navigate(-1)}
            >
              {t("cancel")}
            </button>
          )}
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? t("loading") : t("save")}
          </button>
        </div>
      </form>
    </div>
  );
}
