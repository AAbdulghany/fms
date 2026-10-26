import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch, setTokens, getAccessToken, resolveApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { isPlatformStaff } from "@/lib/roles";
import { applyLanguage, getStoredLanguage } from "@/lib/language";
import type { User } from "@/lib/types";
import { OrbitLogo } from "@/shared/components/OrbitLogo";

const DEMO_SUFFIX = import.meta.env.VITE_DEMO_PASSWORD_SUFFIX ?? "123";

function formatLoginError(err: unknown, t: (key: string) => string, lang: string): string {
  return resolveApiError(err, t, lang, t("login_error_generic"));
}

export function LoginPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { setUser, refresh } = useAuth();
  const [identifier, setIdentifier] = useState("super@demo.com");
  const [password, setPassword] = useState(`super${DEMO_SUFFIX}`);
  const [error, setError] = useState<string | null>(null);
  const [signInOpen, setSignInOpen] = useState(false);

  useEffect(() => {
    void applyLanguage(getStoredLanguage(), i18n);
  }, [i18n]);

  useEffect(() => {
    if (getAccessToken()) navigate("/", { replace: true });
  }, [navigate]);

  const toggleLang = () => {
    const next = i18n.language === "ar" ? "en" : "ar";
    void applyLanguage(next, i18n);
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
      // Tokens first, then load full /users/me (includes subscription features for nav).
      setTokens(res.access_token, res.refresh_token);
      setUser(res.user);
      const me = (await refresh()) ?? res.user;
      // Prefer persisted UI language over user profile locale
      await applyLanguage(getStoredLanguage(), i18n);
      if (res.must_change_password) {
        navigate("/profile?must_change=1", { replace: true });
      } else if (isPlatformStaff(me)) {
        navigate("/platform/maintenance-companies", { replace: true });
      } else {
        navigate("/", { replace: true });
      }
    } catch (err) {
      setError(formatLoginError(err, t, i18n.language));
    }
  }

  const fieldClass =
    "w-full rounded-xl border border-neutral-200 bg-neutral-0 px-4 py-3 text-base text-neutral-900 outline-none focus:border-primary-500";

  return (
    <div className="relative h-full min-h-0 bg-primary-900 max-lg:overflow-hidden lg:flex lg:min-h-dvh lg:bg-neutral-50">
      <section className="relative flex h-full flex-col items-center justify-center bg-primary-900 px-8 text-center text-neutral-50 lg:hidden">
        <button
          type="button"
          className="absolute end-4 top-4 rounded-full bg-neutral-0/10 px-3 py-1.5 text-sm font-semibold text-neutral-50"
          onClick={toggleLang}
        >
          {i18n.language === "ar" ? "EN" : "عربي"}
        </button>
        <OrbitLogo showWordmark={false} iconSize={168} tone="onDark" />
        <p className="mt-3 font-['Syne'] text-3xl font-bold tracking-[0.18em] text-neutral-50">ORBIT</p>
        <p className="mt-2 font-['Syne'] text-xl font-bold text-neutral-50">{t("login_maintain")}</p>
        <p className="font-['Syne'] text-xl font-bold text-secondary-500">{t("login_orbit_line")}</p>
        <button
          type="button"
          className={`mt-10 w-full max-w-xs rounded-xl bg-secondary-500 py-3.5 font-['Syne'] text-lg font-bold text-neutral-900 ${
            signInOpen ? "invisible" : ""
          }`}
          onClick={() => setSignInOpen(true)}
        >
          {t("login")}
        </button>
      </section>

      <section className="hidden items-center justify-center bg-primary-900 px-12 py-12 text-center text-neutral-50 lg:flex lg:w-[42%] lg:shrink-0">
        <div className="flex flex-col items-center gap-3">
          <OrbitLogo showWordmark={false} iconSize={168} tone="onDark" />
          <p className="font-['Syne'] text-3xl font-bold tracking-[0.18em] text-neutral-50">ORBIT</p>
          <p className="font-['Syne'] text-xl font-bold text-neutral-50">{t("login_maintain")}</p>
          <p className="font-['Syne'] text-xl font-bold text-secondary-500">{t("login_orbit_line")}</p>
        </div>
      </section>
      <div className="hidden bg-secondary-500 lg:block lg:w-1.5 lg:shrink-0" aria-hidden />

      <div
        className={`pointer-events-none absolute inset-0 z-10 bg-primary-900 opacity-60 lg:hidden ${
          signInOpen ? "" : "hidden"
        }`}
        aria-hidden
      />

      <section
        className={`${
          signInOpen ? "flex" : "hidden"
        } absolute inset-0 z-20 items-center justify-center px-5 lg:static lg:z-auto lg:flex lg:min-h-dvh lg:flex-1 lg:bg-neutral-50 lg:px-16 lg:py-10`}
        onClick={() => {
          if (signInOpen) setSignInOpen(false);
        }}
      >
        <form
          onSubmit={onSubmit}
          onClick={(event) => event.stopPropagation()}
          className="w-full max-w-md space-y-5 rounded-2xl bg-neutral-0 p-6 shadow-xl lg:rounded-none lg:bg-transparent lg:p-0 lg:shadow-none"
        >

          <div className="flex items-center justify-between gap-4">
            <h1 className="font-['Syne'] text-4xl font-bold text-neutral-900">{t("login")}</h1>
            <button
              type="button"
              className="rounded-full bg-neutral-100 px-3 py-1.5 text-sm font-semibold text-neutral-700"
              onClick={toggleLang}
            >
              {i18n.language === "ar" ? "EN" : "عربي"}
            </button>
          </div>
          {error && (
            <p role="alert" className="rounded-xl bg-error-light px-3 py-2 text-sm text-error-dark">
              {error}
            </p>
          )}
          <div>
            <label htmlFor="login-identifier" className="mb-2 block text-sm font-semibold text-neutral-500">
              {t("login_identifier")}
            </label>
            <input
              id="login-identifier"
              className={fieldClass}
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoComplete="username"
            />
          </div>
          <div>
            <label htmlFor="login-password" className="mb-2 block text-sm font-semibold text-neutral-500">
              {t("password")}
            </label>
            <input
              id="login-password"
              className={fieldClass}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-xl bg-secondary-500 py-3.5 font-['Syne'] text-lg font-bold text-neutral-900 hover:bg-secondary-600"
          >
            {t("login")}
          </button>
          <p className="text-xs text-neutral-500">
            {t("login_demo_accounts")}
            <br />
            {t("login_demo_password_pattern", { suffix: DEMO_SUFFIX })}
          </p>
        </form>
      </section>
    </div>
  );
}
