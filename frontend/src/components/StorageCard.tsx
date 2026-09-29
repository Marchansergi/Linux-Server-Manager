import { formatBytes, formatPercent } from "../format";
import type { StorageStats } from "../types";

import UsageBar from "./UsageBar";

export default function StorageCard({ storage }: { storage: StorageStats }) {
  if (storage.partitions.length === 0) {
    return <p className="text-sm text-slate-500">No filesystems found</p>;
  }
  return (
    <ul className="space-y-4">
      {storage.partitions.map((partition) => (
        <li key={`${partition.device}:${partition.mountpoint}`}>
          <div className="mb-1 flex flex-wrap justify-between gap-x-4 text-sm">
            <span className="font-medium break-all">
              {partition.mountpoint}{" "}
              <span className="font-normal text-slate-500 dark:text-slate-400">
                {partition.device} · {partition.fstype}
              </span>
            </span>
            <span className="text-slate-500 dark:text-slate-400">
              {formatBytes(partition.used_bytes)} / {formatBytes(partition.total_bytes)} (
              {formatPercent(partition.percent)})
            </span>
          </div>
          <UsageBar label={`${partition.mountpoint} usage`} percent={partition.percent} />
        </li>
      ))}
    </ul>
  );
}
