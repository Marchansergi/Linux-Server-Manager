import { formatUptime } from "../format";
import type { SystemInfo } from "../types";

import Stat from "./Stat";

export default function SystemInfoCard({ info }: { info: SystemInfo }) {
  return (
    <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <Stat label="Hostname" value={info.hostname} />
      <Stat label="Operating system" value={info.os_name ?? "Unknown"} />
      <Stat label="Kernel" value={info.kernel} />
      <Stat label="Architecture" value={info.architecture} />
      <Stat label="Uptime" value={formatUptime(info.uptime_seconds)} />
      <Stat label="Booted" value={new Date(info.boot_time).toLocaleString()} />
    </dl>
  );
}
