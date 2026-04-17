import { useTranslation } from "react-i18next";

interface TagBadgeProps {
  tag: string;
}

const tagColors: Record<string, string> = {
  preventive: "bg-blue-100 text-blue-700",
  corrective: "bg-orange-100 text-orange-700",
  protective: "bg-purple-100 text-purple-700",
};

export function TagBadge({ tag }: TagBadgeProps) {
  const { t } = useTranslation();
  const colorClass = tagColors[tag] || "bg-neutral-100 text-neutral-700";
  
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}>
      {t(tag)}
    </span>
  );
}
