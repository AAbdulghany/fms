import type { i18n as I18nInstance } from "i18next";
import { ensureLocale, type AppLocale } from "@/i18n";

export type AppLanguage = AppLocale;

export function getStoredLanguage(): AppLanguage {
  const stored = localStorage.getItem("app_lang");
  return stored === "en" || stored === "ar" ? stored : "ar";
}

/** Apply UI language and persist to localStorage (survives logout/login). */
export async function applyLanguage(lang: AppLanguage, i18n: I18nInstance): Promise<void> {
  await ensureLocale(lang);
  await i18n.changeLanguage(lang);
  localStorage.setItem("app_lang", lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.body.className = lang === "ar" ? "fms-page font-body-ar" : "fms-page font-body-en";
}
