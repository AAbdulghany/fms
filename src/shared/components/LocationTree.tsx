import { useTranslation } from "react-i18next";

export interface LocationTreeNode {
  id: string;
  site_id: string;
  parent_id: string | null;
  name: string;
  location_type: string;
  sort_order: number;
  children: LocationTreeNode[];
}

function NodeRow({
  node,
  depth,
}: {
  node: LocationTreeNode;
  depth: number;
}) {
  const pad = depth * 16;
  return (
    <li className="border-b border-neutral-100 last:border-0">
      <div
        className="flex items-center gap-2 py-2 ps-2 text-sm"
        style={{ paddingInlineStart: `${8 + pad}px` }}
      >
        <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600">
          {node.location_type}
        </span>
        <span className="font-medium text-neutral-900">{node.name}</span>
      </div>
      {node.children?.length > 0 && (
        <ul className="ms-0">
          {node.children.map((c) => (
            <NodeRow key={c.id} node={c} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function LocationTree({ nodes }: { nodes: LocationTreeNode[] }) {
  const { t } = useTranslation();
  if (!nodes.length) {
    return (
      <p className="rounded-lg border border-dashed border-neutral-200 bg-neutral-50 p-6 text-center text-sm text-neutral-600">
        {t("no_locations")}
      </p>
    );
  }
  return (
    <ul className="rounded-lg border border-neutral-200 bg-neutral-0">
      {nodes.map((n) => (
        <NodeRow key={n.id} node={n} depth={0} />
      ))}
    </ul>
  );
}
