import { formatPercent } from "../format";

const WARNING_PERCENT = 75;
const CRITICAL_PERCENT = 90;

function barColor(percent: number): string {
  if (percent >= CRITICAL_PERCENT) return "bg-red-600";
  if (percent >= WARNING_PERCENT) return "bg-amber-500";
  return "bg-teal-600";
}

export default function UsageBar({ label, percent }: { label: string; percent: number }) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
      title={`${label}: ${formatPercent(percent)}`}
    >
      <div className={`h-full ${barColor(clamped)}`} style={{ width: `${clamped}%` }} />
    </div>
  );
}
