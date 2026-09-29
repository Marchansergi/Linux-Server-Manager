import { formatPercent } from "../format";
import type { CpuStats } from "../types";

import Stat from "./Stat";
import UsageBar from "./UsageBar";

export default function CpuCard({ cpu }: { cpu: CpuStats }) {
  const cores = [cpu.physical_cores, cpu.logical_cores].map((n) => n ?? "?").join(" / ");
  return (
    <div className="space-y-4">
      <div>
        <p className="mb-1 text-3xl font-semibold">{formatPercent(cpu.usage_percent)}</p>
        <UsageBar label="CPU usage" percent={cpu.usage_percent} />
      </div>
      <dl className="grid grid-cols-3 gap-4">
        <Stat label="Cores (phys / logical)" value={cores} />
        <Stat
          label="Load (1 / 5 / 15 min)"
          value={cpu.load_average?.map((load) => load.toFixed(2)).join(" / ") ?? "N/A"}
        />
        <Stat
          label="Frequency"
          value={cpu.frequency_mhz ? `${(cpu.frequency_mhz / 1000).toFixed(2)} GHz` : "N/A"}
        />
      </dl>
      {cpu.per_core_percent.length > 1 && (
        <ul className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
          {cpu.per_core_percent.map((percent, core) => (
            <li key={core} className="text-xs">
              <span className="text-slate-500 dark:text-slate-400">
                Core {core}: {formatPercent(percent)}
              </span>
              <UsageBar label={`Core ${core} usage`} percent={percent} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
