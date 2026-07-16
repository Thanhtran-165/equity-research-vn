import Link from "next/link";
import { FileText } from "lucide-react";

export const metadata = {
  title: "Terms of Service · Facebook Page Graph Dashboard",
  description: "Terms of Service for Facebook Page Graph Dashboard",
};

export default function TermsPage() {
  return (
    <article className="prose prose-slate max-w-3xl mx-auto dark:prose-invert animate-fade-in">
      <header className="mb-8 not-prose">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-300 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-semibold m-0">Terms of Service</h1>
        </div>
        <p className="text-sm text-muted">
          Facebook Page Graph Dashboard · Last updated {new Date().toISOString().slice(0, 10)}
        </p>
      </header>

      <section>
        <h2>Acceptance of terms</h2>
        <p>
          By connecting a Facebook Page to Facebook Page Graph Dashboard (&ldquo;the app&rdquo;),
          you agree to these Terms of Service. If you do not agree, do not use the app.
        </p>
      </section>

      <section>
        <h2>Description of service</h2>
        <p>
          The app provides organic Page performance analytics, post metadata, engagement metrics,
          optional comment moderation support, and weekly/monthly performance reports for Facebook
          Pages that you manage. The app does not provide advertising, paid promotion, or
          automated posting services.
        </p>
      </section>

      <section>
        <h2>Your responsibilities</h2>
        <ul>
          <li>You may only connect Pages that you own or are authorized to manage.</li>
          <li>You are responsible for keeping your access credentials confidential.</li>
          <li>You agree not to use the app to violate Facebook&rsquo;s Platform Terms or applicable law.</li>
          <li>You agree not to attempt to access data from Pages you do not manage.</li>
        </ul>
      </section>

      <section>
        <h2>Data usage</h2>
        <ul>
          <li>The app only stores data from the Pages you explicitly connect.</li>
          <li>The app does not sell or share Page data with third parties.</li>
          <li>You may request deletion of your Page data at any time. See our{" "}<Link href="/data-deletion">Data Deletion Instructions</Link>.</li>
        </ul>
      </section>

      <section>
        <h2>Disclaimer of warranties</h2>
        <p>
          The app is provided &ldquo;as is&rdquo; without warranties of any kind, either express or
          implied, including but not limited to accuracy, availability, or fitness for a particular
          purpose. Metrics displayed may be delayed, estimated, or incomplete depending on the
          Facebook Graph API.
        </p>
      </section>

      <section>
        <h2>Limitation of liability</h2>
        <p>
          To the maximum extent permitted by law, the app and its operators shall not be liable
          for any indirect, incidental, special, consequential, or punitive damages, or any loss
          of data, arising out of your use of the app.
        </p>
      </section>

      <section>
        <h2>Changes to these terms</h2>
        <p>
          We may update these Terms from time to time. Continued use of the app after changes
          constitutes acceptance of the updated Terms.
        </p>
      </section>

      <section>
        <h2>Contact</h2>
        <p>
          Questions about these Terms can be sent to{" "}
          <a href="mailto:stevetransg@gmail.com">stevetransg@gmail.com</a>.
        </p>
        <p>
          See also our{" "}<Link href="/privacy">Privacy Policy</Link>.
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
