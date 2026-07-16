import "./globals.css";
import type { Metadata } from "next";
import React from "react";
import { Inter } from "next/font/google";
import { SyncProvider } from "@/components/layout/SyncContext";
import AppShell from "@/components/layout/AppShell";

const inter = Inter({
  subsets: ["latin", "vietnamese"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Facebook Page Dashboard",
  description:
    "Dashboard theo dõi hiệu suất Fanpage Facebook + moderation + benchmark (Graph API + Prisma).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className={inter.variable} suppressHydrationWarning>
      <head>
        {/* Anti-FOUC: áp dụng dark class trước khi hydrate */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');var d=t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches);if(d)document.documentElement.classList.add('dark');}catch(e){}})();`,
          }}
        />
      </head>
      <body className="font-sans">
        <SyncProvider>
          <AppShell>{children}</AppShell>
        </SyncProvider>
      </body>
    </html>
  );
}
