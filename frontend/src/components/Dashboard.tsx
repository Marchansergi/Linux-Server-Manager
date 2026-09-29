import { api } from "../api";
import type { CurrentUser } from "../types";
import { useDashboardData } from "../useDashboardData";

import Card from "./Card";
import CpuCard from "./CpuCard";
import MemoryCard from "./MemoryCard";
import StorageCard from "./StorageCard";
import SystemInfoCard from "./SystemInfoCard";

interface DashboardProps {
  user: CurrentUser;
  onSignedOut: () => void;
}

export default function Dashboard({ user, onSignedOut }: DashboardProps) {
  const { info, cpu, memory, storage } = useDashboardData(onSignedOut);

  async function signOut() {
    try {
      await api.logout();
    } finally {
      onSignedOut();
    }
  }

  return (
    <>
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <h1 className="font-semibold">
            Linux Server Manager
            {info.data && (
              <span className="ml-2 font-normal text-slate-500 dark:text-slate-400">
                {info.data.hostname}
              </span>
            )}
          </h1>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-500 dark:text-slate-400">{user.username}</span>
            <button
              type="button"
              onClick={() => void signOut()}
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto grid max-w-6xl gap-4 px-4 py-6 lg:grid-cols-2">
        <div className="lg:col-span-2">
          <Card title="System" error={info.error} loading={!info.data}>
            {info.data && <SystemInfoCard info={info.data} />}
          </Card>
        </div>
        <Card title="CPU" error={cpu.error} loading={!cpu.data}>
          {cpu.data && <CpuCard cpu={cpu.data} />}
        </Card>
        <Card title="Memory" error={memory.error} loading={!memory.data}>
          {memory.data && <MemoryCard memory={memory.data} />}
        </Card>
        <div className="lg:col-span-2">
          <Card title="Storage" error={storage.error} loading={!storage.data}>
            {storage.data && <StorageCard storage={storage.data} />}
          </Card>
        </div>
      </main>
    </>
  );
}
