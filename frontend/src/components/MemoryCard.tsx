import { formatBytes, formatPercent } from "../format";
import type { MemoryStats } from "../types";

import UsageBar from "./UsageBar";

function UsageRow(props: { label: string; used: number; total: number; percent: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="font-medium">{props.label}</span>
        <span className="text-slate-500 dark:text-slate-400">
          {formatBytes(props.used)} / {formatBytes(props.total)} ({formatPercent(props.percent)})
        </span>
      </div>
      <UsageBar label={`${props.label} usage`} percent={props.percent} />
    </div>
  );
}

export default function MemoryCard({ memory }: { memory: MemoryStats }) {
  return (
    <div className="space-y-4">
      <UsageRow
        label="RAM"
        used={memory.used_bytes}
        total={memory.total_bytes}
        percent={memory.percent}
      />
      <p className="text-xs text-slate-500 dark:text-slate-400">
        {formatBytes(memory.available_bytes)} available (cache and buffers count as available)
      </p>
      {memory.swap.total_bytes > 0 ? (
        <UsageRow
          label="Swap"
          used={memory.swap.used_bytes}
          total={memory.swap.total_bytes}
          percent={memory.swap.percent}
        />
      ) : (
        <p className="text-sm text-slate-500 dark:text-slate-400">No swap configured</p>
      )}
    </div>
  );
}
