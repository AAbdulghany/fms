import { useState } from "react";
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
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  if (!open) return null;

  async function copy(key: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey((cur) => (cur === key ? null : cur)), 2000);
    } catch {
      /* ignore — user can still select the text */
    }
  }

  const allText = [
    `Username: ${username}`,
    `Email: ${email}`,
    `Password: ${initialPassword}`,
    ...(extraLines ?? []).map((line) => `${line.label}: ${line.value}`),
  ].join("\n");

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <h2 className="mb-2 text-lg font-bold text-neutral-900">{title}</h2>
        <p className="mb-4 text-sm text-neutral-600">{t("provision_credentials_hint")}</p>
        <dl className="space-y-3 text-sm">
          <CredentialRow
            label={t("username")}
            value={username}
            copied={copiedKey === "username"}
            copiedLabel={t("copied")}
            copyLabel={t("copy")}
            onCopy={() => void copy("username", username)}
          />
          <CredentialRow
            label={t("email")}
            value={email}
            copied={copiedKey === "email"}
            copiedLabel={t("copied")}
            copyLabel={t("copy")}
            onCopy={() => void copy("email", email)}
          />
          <CredentialRow
            label={t("initial_password")}
            value={initialPassword}
            copied={copiedKey === "password"}
            copiedLabel={t("copied")}
            copyLabel={t("copy")}
            onCopy={() => void copy("password", initialPassword)}
            emphasize
            testId="credentials-password"
          />
          {extraLines?.map((line) => (
            <div key={line.label}>
              <dt className="text-neutral-500">{line.label}</dt>
              <dd className="font-mono text-neutral-900">{line.value}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-6 flex flex-wrap items-center justify-end gap-2">
          <button
            type="button"
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm text-neutral-800 hover:bg-neutral-50"
            onClick={() => void copy("all", allText)}
            data-testid="credentials-copy-all"
          >
            {copiedKey === "all" ? t("copied") : t("copy_all") || "Copy all"}
          </button>
          <button
            type="button"
            data-testid="credentials-confirm"
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

function CredentialRow({
  label,
  value,
  copied,
  copiedLabel,
  copyLabel,
  onCopy,
  emphasize,
  testId,
}: {
  label: string;
  value: string;
  copied: boolean;
  copiedLabel: string;
  copyLabel: string;
  onCopy: () => void;
  emphasize?: boolean;
  testId?: string;
}) {
  return (
    <div>
      <dt className="text-neutral-500">{label}</dt>
      <dd className="mt-1 flex items-center gap-2">
        <input
          readOnly
          value={value}
          data-testid={testId}
          onFocus={(e) => e.currentTarget.select()}
          onClick={(e) => e.currentTarget.select()}
          className={`min-w-0 flex-1 rounded-md border px-2 py-1.5 font-mono text-sm text-neutral-900 ${
            emphasize ? "border-primary-300 bg-primary-50" : "border-neutral-200 bg-neutral-50"
          }`}
        />
        <button
          type="button"
          className="shrink-0 rounded-md border border-neutral-300 px-2.5 py-1.5 text-xs font-medium text-primary-700 hover:bg-primary-50"
          onClick={onCopy}
        >
          {copied ? copiedLabel : copyLabel}
        </button>
      </dd>
    </div>
  );
}
