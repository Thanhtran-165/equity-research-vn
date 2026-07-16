"use client";
import { createContext, useContext, useEffect, useState, useCallback } from "react";

// Default to Vietnamese — primary audience is Vietnamese.
// Hydration-safe: server and first client render both use "vi";
// persisted preference is applied in useEffect after mount.
const LangContext = createContext({ lang: "vi", setLang: () => {}, t: (k) => k });

export function LangProvider({ children, dictionary }) {
  const [lang, setLangState] = useState("vi");

  useEffect(() => {
    // Read persisted choice after mount; default to vi.
    try {
      const saved = localStorage.getItem("dejavu-lang");
      if (saved === "en" || saved === "vi") {
        setLangState(saved);
      }
      document.documentElement.lang = (saved === "en" ? "en" : "vi");
    } catch {}
  }, []);

  const setLang = useCallback((next) => {
    setLangState(next);
    try {
      localStorage.setItem("dejavu-lang", next);
      document.documentElement.lang = next === "vi" ? "vi" : "en";
    } catch {}
  }, []);

  const t = useCallback((key) => {
    const entry = dictionary[key];
    if (!entry) return key;
    if (typeof entry === "string") return entry;
    return entry[lang] || entry.en || key;
  }, [lang, dictionary]);

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}

export function pick(obj, lang) {
  if (!obj) return "";
  if (typeof obj === "string") return obj;
  return obj[lang] || obj.vi || obj.en || "";
}
