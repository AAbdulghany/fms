import { useTranslation } from "react-i18next";
import { QRCodeSVG } from "qrcode.react";

type Props = {
  open: boolean;
  siteId: string;
  siteName: string;
  onClose: () => void;
};

export function SiteQRModal({ open, siteId, siteName, onClose }: Props) {
  const { t } = useTranslation();

  if (!open) return null;

  const deepLink = `${window.location.origin}/sites/${siteId}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-neutral-900">{t("qr_code")}</h2>
            <p className="mt-0.5 text-sm text-neutral-600">{siteName}</p>
          </div>
          <button
            type="button"
            className="rounded-md p-1 text-neutral-400 hover:text-neutral-600"
            onClick={onClose}
            aria-label={t("close")}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex justify-center rounded-lg border border-neutral-200 bg-white p-6">
          <QRCodeSVG
            value={deepLink}
            size={200}
            level="M"
            includeMargin={false}
          />
        </div>

        <p className="mt-3 break-all text-center text-xs text-neutral-500">{deepLink}</p>

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-50"
            onClick={() => {
              void navigator.clipboard.writeText(deepLink);
            }}
          >
            {t("copy_link")}
          </button>
          <button
            type="button"
            className="rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
            onClick={onClose}
          >
            {t("close")}
          </button>
        </div>
      </div>
    </div>
  );
}
