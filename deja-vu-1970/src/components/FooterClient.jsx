"use client";
import { useLang } from "./LangProvider.jsx";

export default function FooterClient() {
  const { t } = useLang();
  return (
    <>
      <p>
        <strong>{t("brand")}</strong>
        {t("footer_tagline")}
        <a href="/about">{t("footer_sources_label")}</a>.
      </p>
      <p>
        {t("footer_sources_pre")}
        <a href="/sources">{t("footer_sources_link")}</a>
      </p>
    </>
  );
}
