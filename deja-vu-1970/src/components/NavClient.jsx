"use client";
import { useLang } from "./LangProvider.jsx";

const NAV = [
  { href: "/", key: "nav_overview" },
  { href: "/timeline", key: "nav_timeline" },
  { href: "/scorecard", key: "nav_scorecard" },
  { href: "/commodities", key: "nav_commodities" },
  { href: "/chapters", key: "nav_chapters" },
  { href: "/claims", label: { vi: "Trích dẫn", en: "Claims" } },
  { href: "/sources", key: "nav_sources" },
  { href: "/about", key: "nav_about" },
];

export default function NavClient() {
  const { t, lang } = useLang();
  return (
    <>
      <a href="/" className="brand">
        <span className="brand-mark">D</span>
        <span>{t("brand")}</span>
      </a>
      <nav className="nav-links">
        {NAV.map((n) => <a key={n.href} href={n.href}>{n.key ? t(n.key) : (n.label ? n.label[lang] : n.href)}</a>)}
      </nav>
    </>
  );
}
