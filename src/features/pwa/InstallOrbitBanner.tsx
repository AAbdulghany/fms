import { useTranslation } from "react-i18next";
import { usePwaInstall } from "@/features/pwa/usePwaInstall";

export function InstallOrbitBanner() {
  const { t } = useTranslation();
  const { visible, mode, dismiss, promptInstall, canPrompt } = usePwaInstall();

  if (!visible || !mode) return null;

  return (
    <div
      className="fixed inset-x-0 bottom-14 z-50 border-t border-primary-200 bg-neutral-0 p-3 shadow-[0_-4px_16px_rgba(28,25,23,0.08)] lg:hidden"
      role="dialog"
      aria-label={t("pwa_install_title")}
    >
      <div className="mx-auto flex max-w-lg items-start gap-3">
        <img
          src="/icons/icon-192.png"
          alt=""
          width={40}
          height={40}
          className="mt-0.5 h-10 w-10 shrink-0 rounded-lg"
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-neutral-900">{t("pwa_install_title")}</p>
          <p className="mt-0.5 text-xs text-neutral-600">
            {mode === "ios" ? t("pwa_install_ios_hint") : t("pwa_install_body")}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {mode === "chromium" && canPrompt && (
              <button
                type="button"
                className="rounded-md bg-primary-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-primary-600"
                onClick={() => void promptInstall()}
              >
                {t("pwa_install_cta")}
              </button>
            )}
            <button
              type="button"
              className="rounded-md border border-neutral-300 px-3 py-1.5 text-xs text-neutral-700 hover:bg-neutral-100"
              onClick={dismiss}
            >
              {t("pwa_install_dismiss")}
            </button>
          </div>
        </div>
        <button
          type="button"
          className="shrink-0 rounded-md p-1 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-800"
          onClick={dismiss}
          aria-label={t("close")}
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
