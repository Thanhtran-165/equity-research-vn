"use client";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState("light");
  useEffect(() => {
    const saved = localStorage.getItem("dejavu-theme") || "light";
    setTheme(saved);
    document.documentElement.setAttribute("data-theme", saved);
    setMounted(true);
  }, []);
  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("dejavu-theme", next);
  };
  if (!mounted) return <button className="theme-toggle no-print" aria-label="Toggle theme">·</button>;
  return (
    <button className="theme-toggle no-print" onClick={toggle} aria-label="Toggle theme">
      {theme === "light" ? "🌙 Tối" : "☀️ Sáng"}
    </button>
  );
}
