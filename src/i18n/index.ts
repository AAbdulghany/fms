import i18n from "i18next";
import { initReactI18next } from "react-i18next";

export type AppLocale = "ar" | "en";

const localeLoaders: Record<AppLocale, () => Promise<{ default: Record<string, string> }>> = {
  ar: () => import("./locales/ar.json"),
  en: () => import("./locales/en.json"),
};

const loaded = new Set<AppLocale>();

function readInitialLocale(): AppLocale {
  try {
    const stored = localStorage.getItem("app_lang");
    return stored === "en" || stored === "ar" ? stored : "ar";
  } catch {
    return "ar";
  }
}

/** Load a locale JSON chunk once and register it with i18next. */
export async function ensureLocale(lng: AppLocale): Promise<void> {
  if (loaded.has(lng)) return;
  const mod = await localeLoaders[lng]();
  const data =
    (mod as { default?: Record<string, string> }).default ??
    (mod as unknown as Record<string, string>);
  i18n.addResourceBundle(lng, "translation", data, true, true);
  loaded.add(lng);
}

/**
 * Boot i18n with only the active language in the main graph.
 * The other locale is fetched when the user switches language.
 */
export const i18nReady: Promise<typeof i18n> = (async () => {
  const lng = readInitialLocale();
  const mod = await localeLoaders[lng]();
  const data = mod.default ?? mod;

  await i18n.use(initReactI18next).init({
    resources: { [lng]: { translation: data } },
    lng,
    // Avoid pulling the other locale until switch; missing keys stay as keys.
    fallbackLng: false,
    interpolation: { escapeValue: false },
    partialBundledLanguages: true,
  });
  loaded.add(lng);
  return i18n;
})();

export default i18n;
