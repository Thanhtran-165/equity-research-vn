"use client";

import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { X } from "lucide-react";
import { useSync } from "./SyncContext";

interface Props {
  children: React.ReactNode;
}

function formatLastSync(date: Date | null): string | null {
  if (!date) return null;
  const diff = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diff < 60) return `Sync cách đây ${diff}s`;
  if (diff < 3600) return `Sync cách đây ${Math.floor(diff / 60)} phút`;
  return `Sync lúc ${date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}`;
}

export default function AppShell({ children }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { syncing, lastSyncAt, triggerSync } = useSync();
  const [tick, setTick] = useState(0);

  // Re-render lastSyncLabel mỗi 30s để refresh "cách đây X phút"
  useEffect(() => {
    const i = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(i);
  }, []);
  void tick; // mark used

  // Lấy pageName/followers từ API (1 lần)
  const [pageInfo, setPageInfo] = useState<{ name?: string; followers?: number }>({});
  useEffect(() => {
    fetch("/api/fb/dashboard")
      .then((r) => r.json())
      .then((r) => {
        if (r.ok && r.data?.page) {
          setPageInfo({
            name: r.data.page.pageName,
            followers: r.data.followers,
          });
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <Sidebar
        pageName={pageInfo.name}
        followers={pageInfo.followers}
      />

      {/* Mobile sidebar drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="absolute left-0 top-0 bottom-0 w-64 bg-white dark:bg-slate-900 shadow-xl animate-slide-in-right">
            <button
              className="absolute top-3 right-3 btn-icon z-10"
              onClick={() => setMobileNavOpen(false)}
              aria-label="Đóng menu"
            >
              <X className="w-5 h-5" />
            </button>
            <MobileNav onClose={() => setMobileNavOpen(false)} />
          </div>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        <Topbar
          onSync={triggerSync}
          syncing={syncing}
          lastSyncLabel={formatLastSync(lastSyncAt)}
          onOpenMobileNav={() => setMobileNavOpen(true)}
        />
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

function MobileNav({ onClose }: { onClose: () => void }) {
  // Render nav đơn giản cho mobile (tránh duplicate state)
  return (
    <div className="w-64 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col">
      <div className="h-14 flex items-center gap-2 px-4 border-b border-slate-200 dark:border-slate-800">
        <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center font-semibold text-sm">
          f
        </div>
        <div className="font-semibold text-sm">Page Dashboard</div>
      </div>
      <nav className="flex-1 p-2 space-y-0.5" onClick={onClose}>
        {[
          { href: "/dashboard", label: "Dashboard" },
          { href: "/video-dashboard", label: "Video" },
          { href: "/posts", label: "Bài viết" },
          { href: "/comments", label: "Moderation" },
          { href: "/public-benchmark", label: "Benchmark công khai" },
          { href: "/internal-benchmark", label: "Benchmark nội bộ" },
          { href: "/imports", label: "Imports" },
          { href: "/reports", label: "Báo cáo" },
          { href: "/settings", label: "Cài đặt" },
        ].map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="block px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            {item.label}
          </a>
        ))}
      </nav>
    </div>
  );
}
