import { useTranslation } from "react-i18next";

type Props = {
  open: boolean;
  title: string;
  username: string;
  email: string;
  initialPassword: string;
  extraLines?: { label: string; value: string }[];
  onClose: () => void;
};

export function ProvisionCredentialsModal({
  open,
  title,
  username,
  email,
  initialPassword,
  extraLines,
  onClose,
}: Props) {
  const { t } = useTranslation();
  if (!open) return null;

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <h2 className="mb-2 text-lg font-bold text-neutral-900">{title}</h2>
        <p className="mb-4 text-sm text-neutral-600">{t("provision_credentials_hint")}</p>
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-neutral-500">{t("username")}</dt>
            <dd className="flex items-center gap-2 font-mono text-neutral-900">
              {username}
              <button type="button" className="text-primary-600 hover:underline" onClick={() => copy(username)}>
                {t("copy")}
              </button>
            </dd>
          </div>
          <div>
            <dt className="text-neutral-500">{t("email")}</dt>
            <dd className="flex items-center gap-2 break-all font-mono text-xs text-neutral-800">
              {email}
              <button type="button" className="shrink-0 text-primary-600 hover:underline" onClick={() => copy(email)}>
                {t("copy")}
              </button>
            </dd>
          </div>
          <div>
            <dt className="text-neutral-500">{t("initial_password")}</dt>
            <dd className="flex items-center gap-2 font-mono text-neutral-900">
              {initialPassword}
              <button type="button" className="text-primary-600 hover:underline" onClick={() => copy(initialPassword)}>
                {t("copy")}
              </button>
            </dd>
          </div>
          {extraLines?.map((line) => (
            <div key={line.label}>
              <dt className="text-neutral-500">{line.label}</dt>
              <dd className="font-mono text-neutral-900">{line.value}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            onClick={onClose}
          >
            {t("confirm")}
          </button>
        </div>
      </div>
    </div>
  );
}
