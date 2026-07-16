# Meta Export — Human-in-the-Loop Design

> Defines four levels of human involvement for obtaining Facebook Page Insights data from Meta Business Suite, states which levels are implemented now, and sets the minimum safety conditions for any future exploration of assisted levels.

> Related docs: `meta-business-suite-export-compliance-research.md` (compliance analysis), `export-matrix-chimcut.md` (which files to export).

---

## 1. The four levels

| Level | Name | Who performs the export | Who performs the import | Implemented now? |
|---|---|---|---|---|
| 1 | Manual export | User | User (manual upload) | Yes |
| 2 | Manual export + watched folder | User | Script (auto-detect + import) | Yes |
| 3 | Human-confirmed UI assist | User (each click), assistant (guidance) | User / assistant | No — design/research only |
| 4 | Unattended browser automation | Bot | Bot | No — prohibited |

---

## 2. Level 1 — Manual export

**Description**: The user does everything.

### Workflow

1. User opens Meta Business Suite in their own browser.
2. User selects the Page, navigates to Insights → Content / Overview.
3. User clicks Export, chooses CSV/XLSX and date range.
4. File downloads to the user's machine.
5. User opens the dashboard → `/imports` → uploads the file.
6. App parses, previews, and lets the user confirm column mapping.
7. App imports the data.

### Characteristics

- No automation of any Meta surface.
- No filesystem watching.
- Fully compliant — uses only the official Export button.
- Highest friction: the user must export and upload for every period.

### Status

**Implemented now.** This is the default path and the baseline against which all other levels are compared.

---

## 3. Level 2 — Manual export + watched folder

**Description**: The user still performs the export manually, but a local script watches a folder and auto-imports any new file.

### Workflow

1. User opens Meta Business Suite and exports as in Level 1.
2. The file lands in a watched directory (default `~/Downloads`, or `META_EXPORTS_WATCH_DIR`).
3. The watcher script (`scripts/watch-meta-exports.ts`, optional) detects a new file matching the export pattern (`*.csv`, `*.xlsx`, name containing "insights"/"facebook"/"meta").
4. The script waits for the file size to stabilize (download complete).
5. The script copies the file into `/imports/incoming` or calls the local import API.
6. App parses, previews, and imports.

### Characteristics

- The user still performs the only Meta-facing action (the manual Export click).
- The script only reads the local filesystem — it never touches Meta, never logs in, never stores cookies.
- Reduces friction by removing the manual upload step.
- Off by default; enabled by setting `META_EXPORTS_WATCH_DIR` and `META_EXPORTS_AUTO_IMPORT`.

### Configuration

```bash
META_EXPORTS_WATCH_DIR=         # path to watch (default: ~/Downloads)
META_EXPORTS_AUTO_IMPORT=false  # true = import immediately on detect; false = copy to /imports/incoming only
```

### Status

**Implemented now** (as an optional script, off by default). This is the recommended convenience layer.

---

## 4. Level 3 — Human-confirmed UI assist

**Description**: The user is logged in to Meta Business Suite in their own browser. An assistant (e.g. an MCP-driven browser or a guided tool) helps the user navigate the export flow, but the user performs every click themselves and confirms each step.

### Intended workflow (concept only)

1. User is already logged in to Meta Business Suite in a real, non-headless browser.
2. User opens the Insights/Export page themselves.
3. Assistant suggests the next action (e.g. "click Export", "choose Performance preset", "set date range to this month").
4. User performs the action.
5. Assistant waits for the user to confirm the action completed.
6. Repeat until the file is downloaded.
7. Level 2 watcher imports the file.

### Why this level is not implemented

- Even though the user performs every click, an assistant observing or guiding interaction with the live Meta UI still introduces ToS exposure — see `meta-business-suite-export-compliance-research.md` section 6.
- The compliance posture is ambiguous: it is less risky than full automation, but it is not clearly authorized by Meta's terms.
- Engineering complexity is non-trivial (step synchronization, confirmation UI, failure recovery) for marginal benefit over Level 2.

### Status

**Design / research only. Not implemented.** Do not build this without a separate, explicit decision and a review of the minimum conditions below.

### Minimum conditions if explored later

If Level 3 is ever revisited, **all** of the following conditions must hold simultaneously. Violating any one disqualifies the approach.

1. **User must be logged in** — the assistant never authenticates; the user's own logged-in session is used.
2. **User opens the export page themselves** — the assistant does not navigate to Meta or to the Insights page on the user's behalf.
3. **User confirms each action** — every click, selection, and download is performed by the user and confirmed before the assistant proceeds.
4. **No headless mode** — the browser must be a visible, interactive window; headless mode is forbidden.
5. **No session storage** — the assistant must not persist, cache, or replay Meta cookies or session tokens.
6. **No scheduled runs** — the assistant may not be triggered by a timer or cron; it only runs when the user explicitly starts it for a single export.
7. **No batch loops** — the assistant handles one export at a time; looping across pages or periods is forbidden.
8. **Must have a stop switch** — the user must be able to halt the assistant at any step; the assistant must not continue unattended.
9. **Local only** — the assistant runs on the user's local machine; no cloud, no remote execution, no shared sessions.
10. **Must not claim "compliant"** — even with all conditions met, the implementation must not be labeled or marketed as compliant; it remains a gray-area research tool.

---

## 5. Level 4 — Unattended browser automation

**Description**: A bot does everything — logs in, navigates, exports, downloads, imports — without human involvement per run.

### Why this level is prohibited

- Violates Meta Terms of Service: "You may not access or collect data from our Products using automated means (without our prior permission)." — https://www.facebook.com/terms/
- Violates Meta Platform Terms — https://developers.facebook.com/terms/dfc_platform_terms/
- Violates Automated Data Collection Terms — https://www.facebook.com/legal/automated_data_collection_terms
- High risk of permanent account suspension.
- Requires bypassing 2FA/captcha and storing credentials/sessions, each of which is independently disqualifying.
- The official sanctioned automation path is the Graph API (`read_insights`), not browser automation.

### Status

**Prohibited.** Not implemented, not designed, not researched further. The compliant equivalent is the Graph API after Business Verification (see compliance research doc, method 5).

---

## 6. Conclusion

| Level | Decision | Rationale |
|---|---|---|
| 1 — Manual export | **Implement now** | Fully compliant, baseline path, already available. |
| 2 — Manual export + watched folder | **Implement now** | Adds filesystem-only convenience; no Meta-facing automation; off by default. |
| 3 — Human-confirmed UI assist | **Design / research only** | Ambiguous compliance, non-trivial complexity, marginal benefit; not implemented. |
| 4 — Unattended browser automation | **Prohibited** | Violates Meta ToS and Platform Terms; high account risk. |

### Principles enforced by this design

- The only Meta-facing action in any implemented level is a manual click by the user on the official Export button.
- No implemented level authenticates to Meta, stores Meta credentials, stores Meta cookies, bypasses 2FA, or scrapes the Meta UI.
- The watched-folder importer (Level 2) operates exclusively on the local filesystem and only on files the user has already downloaded.
- Any future move toward Level 3 requires all ten minimum conditions to be satisfied and must not be described as compliant.
- Level 4 is permanently out of scope; the sanctioned automation path is the Graph API.
