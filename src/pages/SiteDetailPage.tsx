import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";

export default function SiteDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold text-neutral-900">
        {t("sites")} - {id}
      </h1>
      <div className="rounded-lg bg-neutral-0 p-8 text-center shadow-sm">
        <p className="text-neutral-600">Site detail page - To be implemented</p>
      </div>
    </div>
  );
}
