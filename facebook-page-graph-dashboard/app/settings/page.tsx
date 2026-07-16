"use client";

import { useEffect, useState } from "react";
import {
  Settings as SettingsIcon,
  CheckCircle2,
  XCircle,
  AlertCircle,
  KeyRound,
  ExternalLink,
  Beaker,
  FileCheck,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import { SuccessPill, DangerPill, WarningPill } from "@/components/ui/StatusPill";

interface EnvInfo {
  apiVersion: string;
  hasPageId: boolean;
  pageId: string;
  hasPageToken: boolean;
  pageTokenMasked: string;
  hasUserToken: boolean;
  userTokenMasked: string;
}

interface ApiError {
  code?: string;
  message: string;
  details?: any;
}

const REQUIRED_PERMISSIONS = [
  { name: "pages_show_list", desc: "Hiển thị danh sách Page bạn quản lý" },
  { name: "pages_read_engagement", desc: "Đọc comment, reaction công khai" },
  { name: "read_insights", desc: "Đọc reach thật (post_impressions_unique). LƯU Ý: permission này được cấp nhưng Graph API vẫn chặn metric khi App ở Development mode — cần App Review hoặc Live mode để có reach thật cho mọi loại post. MVP dùng fallback video_views + public engagement." },
  { name: "pages_read_user_content", desc: "Đọc nội dung bài viết" },
  { name: "pages_manage_engagement", desc: "Moderation comment (hide/reply)" },
];

export default function SettingsPage() {
  const [env, setEnv] = useState<EnvInfo | null>(null);
  const [envLoading, setEnvLoading] = useState(true);
  const [envError, setEnvError] = useState<ApiError | null>(null);

  const [pageTest, setPageTest] = useState<null | { loading: boolean; data: any; error: ApiError | null }>(null);
  const [accounts, setAccounts] = useState<null | { loading: boolean; data: any; error: ApiError | null }>(null);
  const [tokenScopes, setTokenScopes] = useState<string[] | null>(null);

  async function loadEnv() {
    setEnvLoading(true);
    setEnvError(null);
    try {
      const r = await fetch("/api/env").then((x) => x.json());
      if (r.ok) setEnv(r.data);
      else setEnvError(r.error);
    } catch (e: any) {
      setEnvError({ message: e?.message ?? String(e) });
    } finally {
      setEnvLoading(false);
    }
  }

  useEffect(() => {
    loadEnv();
  }, []);

  async function testPage() {
    setPageTest({ loading: true, data: null, error: null });
    try {
      const r = await fetch("/api/fb/page").then((x) => x.json());
      if (r.ok) {
        setPageTest({ loading: false, data: r.data, error: null });
        // Lấy scopes qua debug_token (qua endpoint public)
        try {
          const dbg = await fetch("/api/fb/page").then((x) => x.json());
          void dbg;
        } catch {}
      } else {
        setPageTest({ loading: false, data: null, error: r.error });
      }
    } catch (e: any) {
      setPageTest({ loading: false, data: null, error: { message: e?.message ?? String(e) } });
    }
  }

  async function getAccounts() {
    setAccounts({ loading: true, data: null, error: null });
    try {
      const r = await fetch("/api/fb/accounts").then((x) => x.json());
      if (r.ok) setAccounts({ loading: false, data: r.data, error: null });
      else setAccounts({ loading: false, data: null, error: r.error });
    } catch (e: any) {
      setAccounts({ loading: false, data: null, error: { message: e?.message ?? String(e) } });
    }
  }

  return (
    <>
      <PageHeader
        title="Cài đặt"
        subtitle="Cấu hình Facebook Graph API · kiểm tra token & permission"
        icon={<SettingsIcon className="w-5 h-5" />}
      />

      {/* Config status */}
      <section className="card p-5 mb-4">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <KeyRound className="w-4 h-4" /> Trạng thái cấu hình
        </h2>
        {envLoading && <div className="skeleton h-24 w-full" />}
        {envError && <ErrorBox title="Không đọc được env" error={envError} />}
        {env && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <ConfigRow label="FB_API_VERSION" value={env.apiVersion} ok />
              <ConfigRow label="FB_PAGE_ID" value={env.hasPageId ? env.pageId : "(chưa set)"} ok={env.hasPageId} />
              <ConfigRow
                label="FB_PAGE_ACCESS_TOKEN"
                value={env.hasPageToken ? env.pageTokenMasked : "(chưa set)"}
                ok={env.hasPageToken}
              />
              <ConfigRow
                label="FB_USER_ACCESS_TOKEN"
                value={env.hasUserToken ? env.userTokenMasked : "(optional)"}
                ok={env.hasUserToken}
                optional
              />
            </div>
            <div className="mt-4 flex gap-2 flex-wrap">
              <button onClick={testPage} className="btn-primary">
                <Beaker className="w-4 h-4" /> Test Page Token
              </button>
              <button
                onClick={getAccounts}
                disabled={!env.hasUserToken}
                className="btn-secondary disabled:cursor-not-allowed"
                title={!env.hasUserToken ? "Cần FB_USER_ACCESS_TOKEN" : ""}
              >
                Get Accounts Helper
              </button>
            </div>
          </>
        )}
      </section>

      {/* Permission checklist */}
      <section className="card p-5 mb-4">
        <h2 className="font-semibold mb-1">Permission cần thiết</h2>
        <p className="text-xs text-muted mb-3">
          Cấp trong Graph API Explorer → Generate Access Token. <code>read_insights</code> có thể
          không có effect nếu App chưa qua App Review hoặc ở Development mode (chỉ hoạt động với tester).
        </p>
        <ul className="space-y-2">
          {REQUIRED_PERMISSIONS.map((p) => {
            const granted = tokenScopes?.includes(p.name);
            const isReadInsights = p.name === "read_insights";
            return (
              <li key={p.name} className="flex items-start gap-2.5 text-sm">
                <div className="mt-0.5 shrink-0">
                  {granted === true ? (
                    <CheckCircle2 className="w-4 h-4 text-success-600" />
                  ) : granted === false ? (
                    <XCircle className="w-4 h-4 text-danger-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-muted" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <code className="text-xs font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                      {p.name}
                    </code>
                    {granted === true && <SuccessPill>đã cấp</SuccessPill>}
                    {granted === false && <DangerPill>thiếu</DangerPill>}
                    {granted == null && isReadInsights && <WarningPill>test bằng sync</WarningPill>}
                  </div>
                  <div className="text-xs text-muted mt-0.5">{p.desc}</div>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      {/* 5 loại metricSource */}
      <section className="card p-5 mb-4">
        <h2 className="font-semibold mb-1">5 loại metricSource</h2>
        <p className="text-xs text-muted mb-3">
          Mỗi post được gán 1 giá trị <code className="font-mono text-xs">metricSource</code> dựa trên
          <strong> sự tồn tại</strong> của dữ liệu (không phải giá trị &gt; 0). Một post có 0 reactions
          nhưng API trả field hợp lệ vẫn là <code className="font-mono text-xs">facebook_public_metrics</code>.
        </p>
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>metricSource</th>
                <th>Ý nghĩa</th>
                <th>Dùng tính ER?</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code className="text-xs">facebook_graph_api_insights</code></td>
                <td className="text-xs">Reach thật (<code>post_impressions_unique</code>). Cần App Review.</td>
                <td><span className="badge-low">✓ Có</span></td>
              </tr>
              <tr>
                <td><code className="text-xs">facebook_video_metric</code></td>
                <td className="text-xs">Video views (<code>post_video_views</code>). Metric thật cho video/reel.</td>
                <td><span className="badge-neutral">Không</span></td>
              </tr>
              <tr>
                <td><code className="text-xs">facebook_public_metrics</code></td>
                <td className="text-xs">Reactions + comments + shares (field summary). <strong>Không phải reach</strong>.</td>
                <td><span className="badge-neutral">Không</span></td>
              </tr>
              <tr>
                <td>
                  <code className="text-xs">public_engagement_proxy</code>
                  <span className="ml-2 badge-medium">deprecated</span>
                </td>
                <td className="text-xs">Alias cũ của <code>facebook_public_metrics</code>. Backward-compat, không dùng cho sync mới.</td>
                <td><span className="badge-neutral">Không</span></td>
              </tr>
              <tr>
                <td><code className="text-xs">unavailable</code></td>
                <td className="text-xs">Không có metric nào trả về (lỗi API hoặc post bị xoá).</td>
                <td><span className="badge-neutral">Không</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Meta App Review Links */}
      <section className="card p-5 mb-4">
        <h2 className="font-semibold mb-1 flex items-center gap-2">
          <FileCheck className="w-4 h-4" /> Meta App Review Links
        </h2>
        <p className="text-xs text-muted mb-3">
          Các URL bạn cần copy vào Meta Developer Dashboard khi submit App Review.
        </p>

        {(() => {
          const appUrl = process.env.NEXT_PUBLIC_APP_URL;
          const isLocal = !appUrl || appUrl.includes("localhost") || appUrl.includes("127.0.0.1");
          const privacyUrl = appUrl ? `${appUrl}/privacy` : "/privacy";
          const deletionUrl = appUrl ? `${appUrl}/data-deletion` : "/data-deletion";
          const termsUrl = appUrl ? `${appUrl}/terms` : "/terms";
          return (
            <>
              {isLocal && (
                <div className="mb-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30">
                  <p className="text-xs text-amber-800 dark:text-amber-400 m-0">
                    <strong>⚠️ Localhost warning:</strong> Meta App Review yêu cầu <strong>public HTTPS URL</strong>,
                    không chấp nhận <code>localhost</code>. Hãy deploy app lên production (Vercel/Cloudflare/etc.)
                    rồi set <code>NEXT_PUBLIC_APP_URL</code> trong <code>.env.local</code> trước khi nộp review.
                  </p>
                </div>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex items-start justify-between gap-3 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60">
                  <div className="min-w-0">
                    <div className="text-xs text-muted uppercase tracking-wide">Privacy Policy URL</div>
                    <code className="text-xs break-all">{privacyUrl}</code>
                  </div>
                  <a href="/privacy" target="_blank" className="btn-secondary !py-1 !px-2 shrink-0">
                    <ExternalLink className="w-3 h-3" /> Mở
                  </a>
                </div>

                <div className="flex items-start justify-between gap-3 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60">
                  <div className="min-w-0">
                    <div className="text-xs text-muted uppercase tracking-wide">Data Deletion Instructions URL</div>
                    <code className="text-xs break-all">{deletionUrl}</code>
                  </div>
                  <a href="/data-deletion" target="_blank" className="btn-secondary !py-1 !px-2 shrink-0">
                    <ExternalLink className="w-3 h-3" /> Mở
                  </a>
                </div>

                <div className="flex items-start justify-between gap-3 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60">
                  <div className="min-w-0">
                    <div className="text-xs text-muted uppercase tracking-wide">Terms of Service URL (optional)</div>
                    <code className="text-xs break-all">{termsUrl}</code>
                  </div>
                  <a href="/terms" target="_blank" className="btn-secondary !py-1 !px-2 shrink-0">
                    <ExternalLink className="w-3 h-3" /> Mở
                  </a>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2 text-xs">
                <div className="flex items-start gap-2">
                  <span className="text-muted w-40 shrink-0">App Category recommend:</span>
                  <span><strong>Business</strong> (hoặc Productivity / Utilities &amp; Tools)</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-muted w-40 shrink-0">App Icon requirement:</span>
                  <span><strong>1024 × 1024</strong> PNG hoặc JPG</span>
                </div>
              </div>
            </>
          );
        })()}
      </section>

      {/* Test result */}
      {pageTest && (
        <section className="card p-5 mb-4">
          <h2 className="font-semibold mb-2">Test Page Token</h2>
          {pageTest.loading && <div className="text-sm text-muted">Đang gọi /api/fb/page…</div>}
          {pageTest.error && <ErrorBox error={pageTest.error} />}
          {pageTest.data && (
            <>
              <div className="flex items-center gap-2 mb-2">
                <SuccessPill>Thành công</SuccessPill>
                <span className="text-sm">Page: <strong>{pageTest.data.name}</strong></span>
              </div>
              <pre className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg text-xs overflow-x-auto">
{JSON.stringify(pageTest.data, null, 2)}
              </pre>
            </>
          )}
        </section>
      )}

      {accounts && (
        <section className="card p-5 mb-4">
          <h2 className="font-semibold mb-2">Danh sách Page (helper)</h2>
          {accounts.loading && <div className="text-sm text-muted">Đang gọi /api/fb/accounts…</div>}
          {accounts.error && <ErrorBox error={accounts.error} />}
          {accounts.data && (
            <>
              <p className="text-xs text-muted mb-2">
                Token đã được mask. Copy <code>id</code> và <code>access_token</code> của Page cần
                dùng vào <code>.env.local</code>.
              </p>
              <pre className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg text-xs overflow-x-auto">
{JSON.stringify(accounts.data, null, 2)}
              </pre>
            </>
          )}
        </section>
      )}

      {/* Setup guide */}
      <section className="card p-5">
        <h2 className="font-semibold mb-2">Hướng dẫn lấy Page Access Token</h2>
        <ol className="list-decimal list-inside text-sm text-slate-700 dark:text-slate-200 space-y-1.5">
          <li>
            Vào{" "}
            <a
              className="text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center gap-0.5"
              href="https://developers.facebook.com/tools/explorer/"
              target="_blank"
              rel="noreferrer"
            >
              Meta Graph API Explorer <ExternalLink className="w-3 h-3" />
            </a>
          </li>
          <li>Chọn Meta App của bạn.</li>
          <li>
            Add 5 permission:{" "}
            <code className="text-xs">pages_show_list, pages_read_engagement, read_insights,
            pages_read_user_content, pages_manage_engagement</code>
          </li>
          <li>Generate Access Token (User Token).</li>
          <li>
            Gọi{" "}
            <code className="text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
              me/accounts?fields=id,name,access_token,tasks
            </code>
          </li>
          <li>Copy <code>id</code> và <code>access_token</code> của Page cần theo dõi.</li>
          <li>
            Dán vào <code>.env.local</code>:
            <pre className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-lg text-xs mt-1">
{`FB_PAGE_ID=<id>
FB_PAGE_ACCESS_TOKEN=<page_token>
FB_USER_ACCESS_TOKEN=<user_token_optional>`}
            </pre>
          </li>
          <li>Khởi động lại <code>npm run dev</code>.</li>
        </ol>
        <p className="text-xs text-danger-600 dark:text-danger-400 mt-3 flex items-start gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>KHÔNG bao giờ paste token vào chat hoặc commit lên git. Token chỉ nằm trong <code>.env.local</code>.</span>
        </p>
      </section>
    </>
  );
}

function ConfigRow({
  label,
  value,
  ok,
  optional,
}: {
  label: string;
  value: React.ReactNode;
  ok?: boolean;
  optional?: boolean;
}) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 py-2.5 gap-2">
      <div className="text-muted font-mono text-xs">{label}</div>
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-slate-800 dark:text-slate-100 truncate font-mono text-xs">{value}</span>
        {ok === true && <SuccessPill />}
        {ok === false && !optional && <DangerPill>thiếu</DangerPill>}
        {ok === false && optional && <WarningPill>optional</WarningPill>}
      </div>
    </div>
  );
}
