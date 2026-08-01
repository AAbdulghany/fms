export interface ObservationFieldDef {
  id: string;
  type: "text" | "textarea" | "checklist";
  label: string;
  options?: string[];
  required?: boolean;
  rows?: number;
}

const DEFAULT_OBSERVATION_FIELDS: ObservationFieldDef[] = [
  {
    id: "overall_condition",
    type: "checklist",
    label: "Overall condition",
    options: ["Good", "Fair", "Poor", "Critical"],
    required: true,
  },
  {
    id: "findings_defects",
    type: "textarea",
    label: "Findings / defects",
    rows: 5,
    required: true,
  },
];

export function resolveEffectiveReportSchema(
  schema: Record<string, unknown> | null | undefined,
  assetCategory?: string | null
): Record<string, unknown> {
  if (!schema) return { sections: [] };
  const effective = structuredClone(schema);
  const byCat = (effective.observations_by_category ?? {}) as Record<string, ObservationFieldDef[]>;
  const key = (assetCategory ?? "").trim();
  const fields =
    (key && byCat[key]) || byCat._default || DEFAULT_OBSERVATION_FIELDS;
  const sections = (effective.sections ?? []) as Array<Record<string, unknown>>;
  const obs = sections.find((s) => s.id === "sec_observations");
  if (obs) {
    obs.fields = structuredClone(fields);
  } else {
    sections.push({
      id: "sec_observations",
      title: "Observations",
      category_variant: true,
      fields: structuredClone(fields),
    });
    effective.sections = sections;
  }
  return effective;
}
