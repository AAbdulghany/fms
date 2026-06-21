import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch, setTokens, getAccessToken } from "../lib/api";
import { isPlatformStaff } from "../lib/roles";
import { applyLanguage, getStoredLanguage } from "../lib/language";
import type { User } from "../lib/types";
import { OrbitLogo } from "../components/OrbitLogo";

function formatLoginError(err: unknown, t: (key: string) => string): string {
  if (!(err instanceof Error)) return t("login_error_generic");
  try {
    const j = JSON.parse(err.message) as { detail?: unknown };
    const d = j.detail;
    if (typeof d === "string") {
      const map: Record<string, string> = {
        INVALID_CREDENTIALS: t("login_error_invalid_credentials"),
        USER_INACTIVE: t("login_error_user_inactive"),
        IDENTIFIER_REQUIRED: t("login_error_generic"),
      };
      return map[d] ?? d;
    }
    if (Array.isArray(d) && d[0] && typeof (d[0] as { msg?: string }).msg === "string") {
      return (d[0] as { msg: string }).msg;
    }
  } catch {
    /* not JSON */
  }
  if (err.message.length > 200) return t("login_error_generic");
  return err.message;
}

export function LoginPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("super@demo.com");
  const [password, setPassword] = useState("super123");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    applyLanguage(getStoredLanguage(), i18n);
  }, [i18n]);

  useEffect(() => {
    if (getAccessToken()) navigate("/", { replace: true });
  }, [navigate]);

  const toggleLang = () => {
    const next = i18n.language === "ar" ? "en" : "ar";
    applyLanguage(next, i18n);
  };

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await apiFetch<{
        access_token: string;
        refresh_token: string;
        must_change_password?: boolean;
        user: User;
      }>("/auth/login", { method: "POST", json: { identifier, password } });
      setTokens(res.access_token, res.refresh_token);
      // Prefer persisted UI language over user profile locale
      applyLanguage(getStoredLanguage(), i18n);
      if (res.must_change_password) {
        navigate("/profile?must_change=1", { replace: true });
      } else if (isPlatformStaff(res.user)) {
        navigate("/platform/maintenance-companies", { replace: true });
      } else {
        navigate("/", { replace: true });
      }
    } catch (err) {
      setError(formatLoginError(err, t));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-100 px-4">
      <div className="absolute top-4 right-4">
        <button
          type="button"
          className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
          onClick={toggleLang}
        >
          {i18n.language.toUpperCase()}
        </button>
      </div>
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md space-y-4 rounded-xl border border-neutral-200 bg-neutral-0 p-8 shadow-md"
      >
        <div className="flex flex-col items-center pb-2">
          <OrbitLogo iconSize={40} />
        </div>
        <h1 className="text-center text-xl font-semibold text-neutral-900">{t("login")}</h1>
        {error && (
          <p className="rounded-md bg-error-light px-3 py-2 text-sm text-error-dark">{error}</p>
        )}
        <div>
          <label className="mb-1 block text-sm text-neutral-600">{t("login_identifier")}</label>
          <input
            className="w-full rounded-md border border-neutral-300 px-3 py-2"
            type="text"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            autoComplete="username"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-neutral-600">{t("password")}</label>
          <input
            className="w-full rounded-md border border-neutral-300 px-3 py-2"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        <button
          type="submit"
          className="w-full rounded-md bg-primary-600 py-2 font-medium text-neutral-0 hover:bg-primary-700"
        >
          {t("login")}
        </button>
        <p className="text-center text-xs text-neutral-500">
          super@demo.com / super123 · admin@demo.com / admin123 · tech@demo.com / tech123
        </p>
      </form>
    </div>
  );
}
