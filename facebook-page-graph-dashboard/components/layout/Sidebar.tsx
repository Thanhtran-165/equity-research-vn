"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Newspaper,
  MessageSquareWarning,
  BarChart3,
  TrendingUp,
  FileText,
  Settings,
  Upload,
  Video,
  Bell,
} from "lucide-react";
import { useState } from "react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/video-dashboard", label: "Video", icon: Video },
  { href: "/posts", label: "Bài viết", icon: Newspaper },
  { href: "/comments", label: "Moderation", icon: MessageSquareWarning },
  { href: "/internal-benchmark", label: "Benchmark nội bộ", icon: BarChart3 },
  { href: "/benchmark", label: "Đối thủ", icon: TrendingUp },
  { href: "/imports", label: "Imports", icon: Upload },
  { href: "/data-reminders", label: "Nhắc cập nhật", icon: Bell },
  { href: "/reports", label: "Báo cáo", icon: FileText },
  { href: "/settings", label: "Cài đặt", icon: Settings },
];

export default function Sidebar({
  pageName,
  followers,
}: {
  pageName?: string;
  followers?: number;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {/* Mobile overlay backdrop handled in ShellClient */}
      <aside
        className={`
          ${collapsed ? "w-[68px]" : "w-60"}
          hidden md:flex md:flex-col
          shrink-0 h-screen sticky top-0
          bg-bg-1/80 backdrop-blur-xl
          border-r transition-[width] duration-200
          z-20
        `}
        style={{ borderColor: "var(--border-soft)" }}
      >
        {/* Brand */}
        <div className="h-14 flex items-center gap-2 px-4 border-b" style={{ borderColor: "var(--border-soft)" }}>
          <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white font-bold text-sm bg-grad-main shadow-glow">
            f
          </div>
          {!collapsed && (
            <div className="leading-tight overflow-hidden">
              <div className="font-semibold text-sm truncate" style={{ color: "var(--text-main)" }}>Page Dashboard</div>
              <div className="text-[10px] truncate" style={{ color: "var(--text-faint)" }}>Facebook Analytics</div>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto scrollbar-thin">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname?.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={`
                  flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all
                  ${active
                    ? "font-medium"
                    : "hover:bg-white/5"
                  }
                `}
                style={active ? {
                  background: "rgba(168,85,247,0.12)",
                  color: "var(--purple)",
                  boxShadow: "inset 0 0 0 1px rgba(168,85,247,0.2)",
                } : {
                  color: "var(--text-dim)",
                }}
              >
                <Icon className={`w-4 h-4 shrink-0 ${active ? "text-neon-purple" : ""}`} />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Page info footer */}
        {pageName && (
          <div className="p-3 border-t" style={{ borderColor: "var(--border-soft)" }}>
            <div className={`flex items-center gap-2 ${collapsed ? "justify-center" : ""}`}>
              <div className="w-8 h-8 rounded-full text-white flex items-center justify-center text-xs font-bold shrink-0 bg-grad-main">
                {pageName.slice(0, 2).toUpperCase()}
              </div>
              {!collapsed && (
                <div className="leading-tight overflow-hidden">
                  <div className="text-sm font-medium truncate" style={{ color: "var(--text-main)" }}>{pageName}</div>
                  <div className="text-xs" style={{ color: "var(--text-faint)" }}>
                    {followers != null ? followers.toLocaleString("vi-VN") : "—"} followers
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="hidden md:flex items-center justify-center h-8 text-xs border-t"
          style={{ borderColor: "var(--border-soft)", color: "var(--text-faint)" }}
          title={collapsed ? "Mở rộng" : "Thu gọn"}
        >
          {collapsed ? "›" : "‹"}
        </button>
      </aside>
    </>
  );
}
