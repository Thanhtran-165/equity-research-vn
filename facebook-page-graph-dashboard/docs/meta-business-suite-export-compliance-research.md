# Meta Business Suite Export — Compliance Research

> Objective: determine which methods of obtaining Facebook Page Insights data are compliant with Meta's Terms of Service and Platform Terms, and which automation paths are safe to implement now versus prohibited.

> Status: Research only. This document does not authorize any implementation. Any automation beyond manual export + watched folder must be approved separately.

---

## 1. Official sources consulted

| # | Source | URL | Relevance |
|---|---|---|---|
| 1 | Export Help — "Export your Page's insights data" | https://www.facebook.com/help/972879969525875 | Official manual export path for Page Insights |
| 2 | Ads Manager Export | https://www.facebook.com/business/help/205067636197240 | Export for Ads data (not organic Insights) |
| 3 | Automated Data Collection Terms | https://www.facebook.com/legal/automated_data_collection_terms | Legal terms governing automated collection |
| 4 | Meta Platform Terms (DFC) | https://developers.facebook.com/terms/dfc_platform_terms/ | Developer platform obligations |
| 5 | Meta Terms of Service | https://www.facebook.com/terms/ | General user ToS — "You may not access or collect data from our Products using automated means (without our prior permission)" |
| 6 | Automated Data Collection dev docs | https://developers.facebook.com/documentation/development/terms-and-policies/automated-data-collection | Developer guidance on automated collection |

---

## 2. Official export path (manual)

This is the **official, Meta-provided** flow. The user performs every step themselves; no automation touches Meta's surfaces.

1. Open **Meta Business Suite**: https://business.facebook.com/latest/
2. Select the Page (e.g. "Chim Cút").
3. Left menu → **Insights** → **Overview** or **Content**.
4. Choose a time range (7 / 28 / 90 days).
5. Click **Export** (top-right, down-arrow / export icon).
6. Choose:
   - Data type: Overview / Content / Audience.
   - Format: CSV or XLSX (depending on UI version).
   - Date range.
7. Click **Export** → Meta generates the file → it downloads to the user's machine.

> Note: The Meta Business Suite UI may change over time and by language (English / Tiếng Việt). Some accounts may not see the Export button, or may see only CSV.

**Compliance status**: Fully compliant. The user is using a feature Meta ships for this exact purpose.

---

## 3. Scheduled export

**Status**: Not confirmed from official Meta documentation.

- No official scheduled export for organic Page Insights was found in Meta Business Suite (as of 2026-07).
- Meta Ads Manager supports scheduled email reports, but only for **Ads** data, not organic Page Insights.
- Some Enterprise accounts may have "Automated Insights" dashboards, but these do not export to CSV on a schedule.

**Conclusion**: There is no confirmed official scheduled export for organic Page Insights. Manual export remains the only confirmed official path.

---

## 4. Email report

**Status**: Not confirmed.

- No scheduled email report for organic Page Insights was found in official Meta documentation.
- Email reports exist for Ads, not for organic Page Insights.

**Conclusion**: Not implementable at this time. If Meta adds this feature later, it could be consumed via Gmail OAuth (scope `gmail.readonly`) reading attachments from `@facebookmail.com`, but that depends on a feature Meta has not confirmed.

---

## 5. Graph API `read_insights`

**Status**: Future — currently blocked by Business Verification.

- This is the standard, sanctioned automation path for Page Insights.
- The app's App Review for `read_insights` Advanced Access is blocked because the owner is an individual without a verified legal entity.
- After Business Verification is complete → request `read_insights` Advanced Access → use `/page-id/insights` and `/post-id/insights`.
- This path is fully compliant because it uses Meta's official developer API under the Platform Terms.

**Compliance status**: Compliant once access is granted. Not available in the current phase.

---

## 6. Compliance analysis of browser automation

Browser automation (Playwright, Selenium, headless browsers, MCP-driven browsers) against the live Meta Business Suite UI is evaluated against three governing documents:

1. **Meta Terms of Service** — https://www.facebook.com/terms/
   - "You may not access or collect data from our Products using automated means (without our prior permission)."
2. **Meta Platform Terms** — https://developers.facebook.com/terms/dfc_platform_terms/
   - Prohibits automated queries against Meta surfaces outside the official APIs.
3. **Automated Data Collection Terms** — https://www.facebook.com/legal/automated_data_collection_terms
   - Governs and restricts automated collection from Meta Products.

### Findings

- Automating the Meta Business Suite UI (clicking Export programmatically, navigating pages headlessly, reusing cookies/sessions to drive a logged-in session) constitutes "accessing or collecting data from our Products using automated means" under the Meta Terms of Service.
- Scraping the UI violates the Platform Terms, which require data to be obtained through the official Graph API.
- Even with the user's own session and consent, the risk of account suspension is high and the activity itself is not authorized by Meta.
- Storing cookies/sessions to replay login is a credential-handling risk on top of the ToS issue.

**Conclusion**: Browser automation against the live Meta Business Suite is **not recommended and must not be implemented**. The only sanctioned automation path is the Graph API (`read_insights`), which is currently blocked.

---

## 7. Compliance matrix

The table below evaluates the 10 methods specified in spec section IV.

| # | Method | Website/Surface | Description | Automation level | Compliance risk | Account risk | Engineering complexity | Recommendation |
|---|---|---|---|---|---|---|---|---|
| 1 | Manual export | Meta Business Suite UI | User opens Insights, clicks Export, downloads CSV/XLSX | None | None | None | Low | **Recommended now** |
| 2 | Manual export + watched folder | Meta Business Suite UI + local filesystem | User exports manually; local script detects new file in Downloads and imports it | Semi (filesystem only) | None | None | Low–Medium | **Recommended now** |
| 3 | Scheduled reminder + watched folder | Local calendar/reminder + filesystem | App reminds user to export on a schedule; watched folder imports the file | Semi (reminder + filesystem) | None | None | Low | **Recommended** |
| 4 | Official scheduled export / email report | Meta Business Suite (if offered) | Meta sends CSV on a schedule or emails a report | High (Meta-side) | None (if Meta-provided) | None | Low | **Conditional / Not confirmed** — feature not confirmed in official Meta docs |
| 5 | Graph API `read_insights` | Graph API | Authorized API call to `/page-id/insights` and `/post-id/insights` | High (API) | None (sanctioned) | None | Low | **Future** — blocked by Business Verification |
| 6 | Human-in-the-loop UI assistant | Meta Business Suite UI (user's live session) | Assistant guides the user step by step; user performs every click; each step confirmed | Low (guidance only) | Medium (UI is still involved) | Medium | Medium | **Research only** |
| 7 | Playwright/MCP on local mock page | Local test page (not Meta) | Browser automation against a local HTML mock to develop/test import UI | High (local only) | None | None | Medium | **Allowed** (does not touch Meta) |
| 8 | Playwright/MCP on Meta Business Suite (real) | Live Meta Business Suite UI | Automated browser drives the real Meta UI to export | Very High | High (ToS violation) | High (ban risk) | High | **Not recommended / do not implement** |
| 9 | Headless browser automation | Live Meta surfaces (headless) | Fully unattended headless bot logs in and exports | Very High | High (ToS + scraping) | High (ban risk) | High | **Prohibited** |
| 10 | Cookie/session reuse | Stored Meta session | Reuse saved cookies/session to drive a logged-in session | Very High | High (ToS + credential storage) | High (ban + credential leak) | Medium | **Prohibited** |

---

## 8. Compliance boundaries

### What NOT to do

- Do not automate login to Meta.
- Do not use username/password to authenticate against Meta.
- Do not store Meta cookies or sessions.
- Do not bypass 2FA or captcha.
- Do not scrape the Meta Business Suite UI (DOM parsing, programmatic clicks, headless navigation).
- Do not run Playwright/Selenium/MCP against the live Meta Business Suite to download CSVs.
- Do not simulate user behavior to evade Meta's anti-bot controls.
- Do not schedule unattended browser runs against Meta.
- Do not batch-loop exports across many pages via the UI.
- Do not claim any browser-automation approach is "compliant" — it is not.

### What IS allowed

- Use the official **Export** button in Meta Business Suite manually.
- Use the official **Graph API `read_insights`** once Advanced Access is granted (after Business Verification).
- Watch a **local filesystem folder** for files the user has already downloaded, and import them.
- Send the user a **scheduled reminder** to perform the export themselves.
- Use Playwright/MCP against a **local mock page** that does not touch Meta, for development and testing of the import UI.
- Process files the user has explicitly exported themselves.

---

## 9. Conclusion

1. **Manual export** is the only confirmed compliant data-acquisition path available right now.
2. **Manual export + watched folder** is the recommended convenience layer — it adds no Meta-facing automation.
3. **Scheduled reminder + watched folder** is the recommended way to reduce friction without automation risk.
4. **Official scheduled export / email report** is not confirmed to exist for organic Page Insights.
5. **Graph API `read_insights`** is the compliant endgame, blocked by Business Verification.
6. **Browser automation against the live Meta Business Suite** (methods 8, 9, 10) violates Meta's Terms of Service and Platform Terms and must not be implemented.
7. **Human-in-the-loop UI assistance** (method 6) is research only — it reduces but does not eliminate ToS exposure and is not implemented in this phase.

### Safety principles applied by this project

- No automated login to Meta.
- No username/password storage.
- No Meta cookie/session storage.
- No 2FA/captcha bypass.
- No scraping of the Meta Business Suite UI.
- No Playwright/Selenium used to download CSVs from Meta.
- No user-behavior simulation to evade controls.
- Only files the user has downloaded themselves are processed.
