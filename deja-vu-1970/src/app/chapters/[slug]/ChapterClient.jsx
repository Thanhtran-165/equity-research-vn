"use client";
import { useLang } from "../../../components/LangProvider.jsx";
import { CHAPTERS } from "../../../data/chapters.mjs";
import { Chapter01 } from "../../../components/ChapterContent.jsx";
import { Chapter03, Chapter04 } from "../../../components/ChapterContent2.jsx";
import { Chapter05, Chapter06 } from "../../../components/ChapterContent3.jsx";
import { Chapters7to18 } from "../../../components/ChapterContent4.jsx";
import { Chapter11, Chapter12, Chapter13, Chapter14, Chapter15, Chapter16, Chapter18 } from "../../../components/ChapterContent5.jsx";
import { useEffect } from "react";
import { useRouter } from "next/navigation.js";

const BODIES = {
  "01": Chapter01,
  "03": Chapter03, "04": Chapter04, "05": Chapter05, "06": Chapter06,
  ...Chapters7to18,
  "11": Chapter11, "12": Chapter12, "13": Chapter13, "14": Chapter14,
  "15": Chapter15, "16": Chapter16, "18": Chapter18,
};

export default function ChapterClient({ slug }) {
  const { lang } = useLang();
  const router = useRouter();
  const chapter = CHAPTERS.find((c) => c.slug === slug);
  useEffect(() => {
    if (chapter?.redirect) router.replace(chapter.redirect);
  }, [chapter, router]);
  if (!chapter) return null;
  if (chapter.redirect) return null;
  const pick = (obj) => (obj && typeof obj === "object" ? (obj[lang] || obj.vi || obj.en) : obj);
  const Body = BODIES[chapter.slug];
  if (!Body) {
    return (
      <div className="container-narrow" style={{paddingTop: 40}}>
        <h1>{lang === "vi" ? `Chương ${chapter.slug}` : `Chapter ${chapter.slug}`}: {pick(chapter.title)}</h1>
        <p>{lang === "vi" ? "Nội dung đang hoàn thiện." : "Content pending population."}</p>
      </div>
    );
  }
  return <Body />;
}
