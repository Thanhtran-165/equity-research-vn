"use client";

import { createContext, useCallback, useContext, useState } from "react";

interface SyncContextValue {
  syncing: boolean;
  lastSyncAt: Date | null;
  lastSyncResult: any | null;
  triggerSync: () => Promise<void>;
  /** Pages có thể subscribe để biết khi sync xong → refetch data */
  syncNonce: number;
}

const SyncContext = createContext<SyncContextValue | null>(null);

export function useSync() {
  const ctx = useContext(SyncContext);
  if (!ctx) {
    // Fallback an toàn nếu gọi ngoài provider
    return {
      syncing: false,
      lastSyncAt: null,
      lastSyncResult: null,
      triggerSync: async () => {},
      syncNonce: 0,
    } as SyncContextValue;
  }
  return ctx;
}

export function SyncProvider({ children }: { children: React.ReactNode }) {
  const [syncing, setSyncing] = useState(false);
  const [lastSyncAt, setLastSyncAt] = useState<Date | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<any | null>(null);
  const [syncNonce, setSyncNonce] = useState(0);

  const triggerSync = useCallback(async () => {
    setSyncing(true);
    try {
      const r = await fetch("/api/fb/sync", { method: "POST" }).then((x) => x.json());
      setLastSyncResult(r);
      setLastSyncAt(new Date());
      setSyncNonce((n) => n + 1);
      return r;
    } finally {
      setSyncing(false);
    }
  }, []);

  return (
    <SyncContext.Provider
      value={{ syncing, lastSyncAt, lastSyncResult, triggerSync, syncNonce }}
    >
      {children}
    </SyncContext.Provider>
  );
}
