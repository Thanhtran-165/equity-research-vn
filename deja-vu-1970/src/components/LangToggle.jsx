"use client";
import { useEffect, useState } from "react";
import { useLang } from "./LangProvider.jsx";

export default function LangToggle() {
  const { lang, setLang } = useLang();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  const toggle = () => setLang(lang === "vi" ? "en" : "vi");
  if (!mounted) return <button className="theme-toggle no-print" aria-label="Toggle language">·</button>;
  return (
    <button
      className="theme-toggle no-print"
      onClick={toggle}
      aria-label="Toggle language"
      title={lang === "vi" ? "Chuyển sang English" : "Switch to Tiếng Việt"}
    >
      {lang === "vi" ? "🇻🇳 VI" : "🇺🇸 EN"}
    </button>
  );
}
