import type { Severity } from "@/lib/types";
import { severityLabel, severityColor } from "@/lib/format";

export function SeverityBadge({ severity }: { severity: Severity }) {
  const color = severityColor(severity);
  return (
    <span
      className="rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-widest"
      style={{ color, borderColor: color, backgroundColor: `${color}14` }}
    >
      {severityLabel(severity)}
    </span>
  );
}
