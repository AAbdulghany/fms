import { useTranslation } from "react-i18next";

export default function CompaniesPage() {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold text-neutral-900">{t("companies")}</h1>
      <div className="rounded-lg bg-neutral-0 p-8 text-center shadow-sm">
        <p className="text-neutral-600">Companies page - To be implemented</p>
      </div>
    </div>
  );
}
