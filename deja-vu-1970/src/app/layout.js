// src/app/layout.js — root layout
import "../styles/globals.css";
import ThemeToggle from "../components/ThemeToggle.jsx";
import LangToggle from "../components/LangToggle.jsx";
import NavClient from "../components/NavClient.jsx";
import { LangProvider } from "../components/LangProvider.jsx";
import { DICTIONARY } from "../data/i18n.mjs";

export const metadata = {
  title: "Déjà Vu 1970–1980? | So sánh vĩ mô lịch sử",
  description: "So sánh định lượng giữa chế độ kinh tế-tài chính 1965–1985 và 2020–hiện tại: địa chính trị, lạm phát, hàng hóa, nợ, chính sách tiền tệ, AI và hành vi tài sản. Bilingual VI/EN.",
  openGraph: {
    title: "Déjà Vu 1970–1980?",
    description: "Hôm nay có phải phiên bản mới của thập niên 1970? So sánh định lượng 16 chiều và 12+ hàng hóa. Bilingual VI/EN.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <script dangerouslySetInnerHTML={{ __html: `
          // Apply persisted language before paint to avoid flash.
          try {
            var l = localStorage.getItem('dejavu-lang') || 'vi';
            document.documentElement.lang = l;
          } catch (e) {}
        `}} />
      </head>
      <body>
        <LangProvider dictionary={DICTIONARY}>
          <header className="site-header no-print">
            <div className="site-header-inner">
              <NavClient />
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <LangToggle />
                <ThemeToggle />
              </div>
            </div>
          </header>
          <main>{children}</main>
          <footer className="site-footer">
            <div className="container">
              <FooterContent />
            </div>
          </footer>
        </LangProvider>
      </body>
    </html>
  );
}

// Client wrapper for nav so it can use the lang context.
import NavClientImpl from "../components/NavClient.jsx";
function FooterContent() {
  // Use a small client component to render localized footer.
  return <FooterClient />;
}

import FooterClient from "../components/FooterClient.jsx";
