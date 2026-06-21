import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export function FeatureUnavailablePage({ feature }: { feature: string }) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-lg py-16 text-center">
      <h1 className="text-2xl font-semibold text-neutral-900">
        {t("feature_not_available") || "Feature not available"}
      </h1>
      <p className="mt-2 text-neutral-600">
        {t("feature_not_available_desc") ||
          `Your subscription does not include the "${feature}" module. Contact your administrator to upgrade.`}
      </p>
      <Link
        to="/dashboard"
        className="mt-6 inline-block rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
      >
        {t("back_to_dashboard") || "Back to dashboard"}
      </Link>
    </div>
  );
}
