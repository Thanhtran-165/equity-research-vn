// src/app/chapters/[slug]/page.js — server wrapper for static params + client render
import ChapterClient from "./ChapterClient.jsx";
import { CHAPTERS } from "../../../data/chapters.mjs";

export const dynamic = "force-static";
export function generateStaticParams() {
  return CHAPTERS.filter((c) => !c.redirect).map((c) => ({ slug: c.slug }));
}

export default function Page({ params }) {
  return <ChapterClient slug={params.slug} />;
}
