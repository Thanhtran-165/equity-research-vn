import Link from "next/link";
import { Shield } from "lucide-react";

export const metadata = {
  title: "Privacy Policy · Facebook Page Graph Dashboard",
  description: "Privacy Policy for Facebook Page Graph Dashboard",
};

export default function PrivacyPage() {
  return (
    <article className="prose prose-slate max-w-3xl mx-auto dark:prose-invert animate-fade-in">
      <header className="mb-8 not-prose">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-300 flex items-center justify-center">
            <Shield className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-semibold m-0">Privacy Policy</h1>
        </div>
        <p className="text-sm text-muted">
          Facebook Page Graph Dashboard · Last updated {new Date().toISOString().slice(0, 10)}
        </p>
      </header>

      <section>
        <h2>Overview</h2>
        <p>
          Facebook Page Graph Dashboard (&ldquo;the app&rdquo;) is an internal analytics tool that
          helps Page administrators monitor the organic performance of Facebook Pages they manage.
          This policy explains what data we collect, why we collect it, how long we keep it, and
          how you can request deletion.
        </p>
        <p>
          The app only accesses Facebook Pages that the authenticated user manages. It does not
          access Pages of other users, does not run advertising campaigns, and does not use the
          Meta Marketing API.
        </p>
      </section>

      <section>
        <h2>What data we collect</h2>
        <p>When you connect a Facebook Page to the app, we collect the following data:</p>
        <ul>
          <li><strong>Page identity</strong>: Facebook Page ID and Page name.</li>
          <li><strong>Post metadata</strong>: post message, created time, permalink URL, post type (text, photo, video, link).</li>
          <li><strong>Public engagement counts</strong>: reactions count, comments count, shares count.</li>
          <li>
            <strong>Page and Post Insights</strong> (only when permission is granted):
            reach (<code>post_impressions_unique</code>), impressions (<code>post_impressions</code>),
            engaged users (<code>post_engaged_users</code>), and clicks (<code>post_clicks</code>).
          </li>
          <li><strong>Video metrics</strong> (when available): video views and related metrics for video and Reels posts.</li>
          <li><strong>Page comments</strong>: comment text, author, created time, and engagement counts — only when moderation features are enabled.</li>
          <li><strong>Follower snapshots</strong>: follower count and fan count captured at each sync.</li>
        </ul>
      </section>

      <section>
        <h2>Why we collect data</h2>
        <ul>
          <li><strong>Page analytics</strong>: to compute engagement rate, posting cadence, and topic performance.</li>
          <li><strong>Content performance reporting</strong>: to identify top-performing posts by reach, comments, and engagement.</li>
          <li><strong>Organic Page performance monitoring</strong>: to track follower growth and engagement trends over time.</li>
          <li><strong>Comment moderation support</strong>: to surface spam, sensitive keywords, and comments requiring manual review.</li>
          <li><strong>Weekly and monthly reports</strong>: to summarize Page performance for Page admins.</li>
        </ul>
      </section>

      <section>
        <h2>Data sharing</h2>
        <ul>
          <li>We <strong>do not sell</strong> user data.</li>
          <li>We <strong>do not share</strong> Page data with third parties.</li>
          <li>Data is used <strong>only for Pages managed by the authenticated user</strong>. The app does not access, store, or transmit data from Pages the user does not manage.</li>
        </ul>
      </section>

      <section>
        <h2>Data retention</h2>
        <ul>
          <li>Data is retained only as long as needed for analytics and reporting purposes.</li>
          <li>Post metadata, insights snapshots, and generated reports are kept until the Page is disconnected or the user requests deletion.</li>
          <li>You can request deletion of all data associated with your Page at any time. See our <Link href="/data-deletion">Data Deletion Instructions</Link>.</li>
        </ul>
      </section>

      <section>
        <h2>User rights</h2>
        <ul>
          <li>You have the right to request access to the data the app holds about your Page.</li>
          <li>You have the right to request correction of inaccurate data.</li>
          <li>You have the right to request deletion of all data associated with your connected Page.</li>
        </ul>
      </section>

      <section>
        <h2>Contact</h2>
        <p>
          For any privacy-related questions or requests, contact us at{" "}
          <a href="mailto:stevetransg@gmail.com">stevetransg@gmail.com</a>.
        </p>
      </section>

      <section>
        <h2>Data deletion</h2>
        <p>
          To request deletion of your Page data, follow our{" "}
          <Link href="/data-deletion">Data Deletion Instructions</Link>.
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
