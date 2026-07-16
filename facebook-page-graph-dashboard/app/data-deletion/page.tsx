import Link from "next/link";
import { Trash2 } from "lucide-react";

export const metadata = {
  title: "Data Deletion Instructions · Facebook Page Graph Dashboard",
  description: "How to request deletion of your Page data",
};

export default function DataDeletionPage() {
  return (
    <article className="prose prose-slate max-w-3xl mx-auto dark:prose-invert animate-fade-in">
      <header className="mb-8 not-prose">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-danger-50 dark:bg-danger-500/10 text-danger-600 dark:text-danger-500 flex items-center justify-center">
            <Trash2 className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-semibold m-0">Data Deletion Instructions</h1>
        </div>
        <p className="text-sm text-muted">
          Facebook Page Graph Dashboard · Last updated {new Date().toISOString().slice(0, 10)}
        </p>
      </header>

      <section>
        <h2>How to request deletion</h2>
        <p>To request deletion of all data the app holds about your Facebook Page:</p>
        <ol>
          <li>
            Email us at{" "}
            <a href="mailto:stevetransg@gmail.com">stevetransg@gmail.com</a>.
          </li>
          <li>
            Include the <strong>Facebook Page name</strong> or <strong>Page ID</strong> in your
            request, so we can identify the records to delete. You can find the Page ID in the
            app&rsquo;s Settings page after connecting the Page.
          </li>
          <li>
            Optionally include the Facebook user account email associated with the Page to speed
            up verification.
          </li>
        </ol>
      </section>

      <section>
        <h2>What data will be deleted</h2>
        <p>Once a deletion request is verified, we will permanently remove:</p>
        <ul>
          <li><strong>Page connection records</strong>: Page ID, Page name, follower snapshots.</li>
          <li><strong>Synced post metadata</strong>: post IDs, messages, created times, permalink URLs, post types, topic tags.</li>
          <li><strong>Page and post insights snapshots</strong>: reach, impressions, engaged users, clicks, video views, and public engagement metrics.</li>
          <li><strong>Comments stored for moderation</strong>: comment text, author metadata, and moderation status.</li>
          <li><strong>Generated reports</strong>: weekly and monthly performance reports associated with the Page.</li>
          <li><strong>Benchmark and import records</strong>: any competitor benchmark snapshots or CSV import records related to the Page.</li>
        </ul>
      </section>

      <section>
        <h2>Timeline</h2>
        <p>
          We will process deletion requests within a reasonable period, typically{" "}
          <strong>within 7 business days</strong> of receiving a verified request. Once deletion
          is complete, you will receive a confirmation email at the address you provided.
        </p>
      </section>

      <section>
        <h2>Important note about Facebook content</h2>
        <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 not-prose">
          <p className="text-sm text-amber-800 dark:text-amber-400 m-0">
            Deleting data from this app <strong>does not delete</strong> any content from Facebook
            itself. Posts, comments, videos, and other content on your Facebook Page remain
            untouched. This app only deletes the analytics data and snapshots stored locally in
            its own database.
          </p>
        </div>
      </section>

      <section>
        <h2>After deletion</h2>
        <p>
          Once your data is deleted, the app will no longer have any record of your Page. If you
          reconnect the same Page in the future, the app will start collecting data again from
          scratch.
        </p>
      </section>

      <section>
        <h2>Contact</h2>
        <p>
          Questions about deletion or other privacy matters can be sent to{" "}
          <a href="mailto:stevetransg@gmail.com">stevetransg@gmail.com</a>.
        </p>
        <p>
          See also our{" "}
          <Link href="/privacy">Privacy Policy</Link>.
        </p>
      </section>

      <footer className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-800 not-prose text-xs text-muted">
        <p>
          Facebook Page Graph Dashboard is an independent tool and is not affiliated with,
          endorsed by, or sponsored by Meta Platforms, Inc.
        </p>
      </footer>
    </article>
  );
}
