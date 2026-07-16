"use client";

import { useState, useEffect, useCallback } from "react";
import { UserPlus, Trash2, ChevronDown, ChevronUp, Check, AlertTriangle } from "lucide-react";

interface Peer {
  id: number;
  name: string;
  canonicalUrl: string;
  benchmarkRole: string;
  isOwnPage: boolean;
  category: string | null;
  scaleBand: string | null;
  notes: string | null;
  _count?: { posts: number };
}

const CATEGORIES = [
  { value: "stock_market", label: "Chứng khoán" },
  { value: "gold_usd", label: "Vàng / USD" },
  { value: "real_estate", label: "Bất động sản" },
  { value: "macro_economics", label: "Vĩ mô" },
  { value: "banking_rates", label: "Lãi suất / Ngân hàng" },
  { value: "social_commentary", label: "Bình luận xã hội" },
  { value: "other", label: "Khác" },
];

const ROLES = [
  { value: "core_peer", label: "Core Peer (so sánh trực tiếp)" },
  { value: "watchlist", label: "Watchlist (theo dõi)" },
  { value: "topic_reference", label: "Topic Reference (tham chiếu)" },
];

export default function AddPeerPanel() {
  const [expanded, setExpanded] = useState(false);
  const [peers, setPeers] = useState<Peer[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  const [form, setForm] = useState({
    name: "",
    canonicalUrl: "",
    category: "stock_market",
    benchmarkRole: "core_peer",
    notes: "",
  });

  const loadPeers = useCallback(async () => {
    try {
      const r = await fetch("/api/public-benchmark/pages").then((x) => x.json());
      if (r.ok) {
        setPeers((r.data?.pages ?? []).filter((p: Peer) => !p.isOwnPage));
      }
    } catch {
      // Silent
    }
  }, []);

  useEffect(() => { loadPeers(); }, [loadPeers]);

  async function handleAdd() {
    if (!form.name.trim() || !form.canonicalUrl.trim()) {
      setResult({ ok: false, message: "Tên trang và URL là bắt buộc" });
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const r = await fetch("/api/public-benchmark/peers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      }).then((x) => x.json());

      if (r.ok) {
        setResult({ ok: true, message: `Đã thêm: ${r.data?.page?.name ?? form.name}` });
        setForm({ name: "", canonicalUrl: "", category: "stock_market", benchmarkRole: "core_peer", notes: "" });
        loadPeers();
      } else {
        setResult({ ok: false, message: r.data?.error || r.error?.message || "Lỗi" });
      }
    } catch (e) {
      setResult({ ok: false, message: e instanceof Error ? e.message : "Lỗi kết nối" });
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number, name: string) {
    if (!confirm(`Xóa "${name}" khỏi benchmark? Dữ liệu bài viết sẽ bị xóa.`)) return;

    try {
      const r = await fetch(`/api/public-benchmark/peers/${id}`, { method: "DELETE" }).then((x) => x.json());
      if (r.ok) {
        setResult({ ok: true, message: `Đã xóa: ${name}` });
        loadPeers();
      } else {
        setResult({ ok: false, message: r.data?.error || "Không xóa được" });
      }
    } catch {
      setResult({ ok: false, message: "Lỗi kết nối" });
    }
  }

  async function handleRoleChange(id: number, role: string) {
    try {
      await fetch(`/api/public-benchmark/peers/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ benchmarkRole: role }),
      });
      loadPeers();
    } catch {
      // Silent
    }
  }

  return (
    <div className="glass-card p-5 mb-5 border-emerald-500/30">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between mb-0"
      >
        <div className="flex items-center gap-2">
          <UserPlus className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold">Quản lý Peer</h2>
          <span className="text-xs text-muted">({peers.length} trang)</span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-muted" /> : <ChevronDown className="w-4 h-4 text-muted" />}
      </button>

      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Add form */}
          <div className="bg-slate-800/30 rounded-lg p-4 space-y-3">
            <div className="text-sm font-medium text-emerald-400">Thêm trang mới</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted block mb-1">Tên trang *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="VD: CafeF, Bò và Gấu..."
                  className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-1">Facebook URL *</label>
                <input
                  type="text"
                  value={form.canonicalUrl}
                  onChange={(e) => setForm({ ...form, canonicalUrl: e.target.value })}
                  placeholder="facebook.com/..."
                  className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-1">Chủ đề</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
                >
                  {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted block mb-1">Vai trò</label>
                <select
                  value={form.benchmarkRole}
                  onChange={(e) => setForm({ ...form, benchmarkRole: e.target.value })}
                  className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
                >
                  {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Ghi chú (tùy chọn)</label>
              <input
                type="text"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="VD: 563K followers, chuyên phân tích..."
                className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
              />
            </div>
            <button
              onClick={handleAdd}
              disabled={loading}
              className="btn-primary text-sm px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
            >
              <UserPlus className="w-4 h-4" />
              {loading ? "Đang thêm..." : "Thêm trang"}
            </button>
          </div>

          {/* Result message */}
          {result && (
            <div className={`text-sm p-2 rounded flex items-center gap-2 ${
              result.ok ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
            }`}>
              {result.ok ? <Check className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              {result.message}
            </div>
          )}

          {/* Peer list */}
          <div>
            <div className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
              Danh sách Peer ({peers.length})
            </div>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {peers.length === 0 ? (
                <div className="text-sm text-muted p-2">Chưa có peer nào.</div>
              ) : (
                peers.map((peer) => (
                  <div key={peer.id} className="flex items-center gap-2 py-2 px-2 border-b border-slate-800/50 hover:bg-slate-800/30 rounded">
                    <div className="flex-1 min-w-0">
                      <a href={peer.canonicalUrl} target="_blank" rel="noopener noreferrer" className="text-sm text-cyan-400 hover:underline truncate block">
                        {peer.name}
                      </a>
                      <div className="text-xs text-muted">
                        {peer.category ?? "—"} · {peer._count?.posts ?? 0} posts · {peer.scaleBand ?? "?"}
                      </div>
                    </div>
                    <select
                      value={peer.benchmarkRole}
                      onChange={(e) => handleRoleChange(peer.id, e.target.value)}
                      className="text-xs bg-slate-800 border border-slate-700 rounded px-1 py-1"
                    >
                      <option value="core_peer">Core</option>
                      <option value="watchlist">Watchlist</option>
                      <option value="topic_reference">Reference</option>
                      <option value="extended_creator_peer">Extended</option>
                      <option value="institutional_reference">Institutional</option>
                    </select>
                    <button
                      onClick={() => handleDelete(peer.id, peer.name)}
                      className="text-rose-400 hover:text-rose-300 p-1"
                      title="Xóa"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
