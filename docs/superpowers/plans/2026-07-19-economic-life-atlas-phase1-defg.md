# Economic Life Atlas — Phase 1 (Sub-phases D/E/F/G) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans or subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Dựng các component chính (ProjectCard/StatsPanel/Theses/Questions/Misconceptions/Credits), tạo 8 trang con, deploy master portal lên Vercel.

**Architecture:** App Router Next.js static export đã scaffold ở ABC. Mỗi trang là server component import từ `content/` qua loaders ở `lib/`. Components tương tác (filter/expand) là client components.

**Tech Stack:** Đã setup (Next 15.5, TS strict, Tailwind v3, Framer 11, Recharts 2, Zod 3.23, Vitest, Playwright).

**Branch:** `economic-life-atlas` (đang ở đó).

**Reference:** spec `docs/superpowers/specs/2026-07-19-economic-life-atlas-phase1-design.md` phần 5.

---

## Sub-phase D — Components chính (Tasks D1-D6)

### Task D1: UI primitives (Badge, Button, Card, Tooltip)

**Files:**
- Create: `components/ui/Badge.tsx`, `components/ui/Button.tsx`, `components/ui/Card.tsx`, `components/ui/Tooltip.tsx`

- [ ] **Step 1: Badge** — variant (production/review/local/unavailable), default size sm
- [ ] **Step 2: Button** — variant (primary teal / outline navy / disabled), as link hoặc button
- [ ] **Step 3: Card** — wrapper paper với border + hover lift
- [ ] **Step 4: Tooltip** — title attribute native + custom styled nếu cần
- [ ] **Step 5: Commit** `feat(atlas): UI primitives — Badge/Button/Card/Tooltip (Phase 1d)`

### Task D2: ProjectCard + ProjectGallery

**Files:**
- Create: `components/project-gallery/ProjectCard.tsx`, `components/project-gallery/ProjectGallery.tsx`
- Test: `tests/components/ProjectCard.test.tsx`

**Spec (5.3):**
- Card có: cover SVG (chưa cần, tạm dùng gradient placeholder), module badge (M01-M04), status badge (production=teal, local=muted), title (serif), subtitle, stats row (chapters/sources/claims/charts/interactions/case_studies), nút "Mở nghiên cứu" (link external nếu có URL)
- Tất cả 4 module giờ đều production → nút luôn enabled, mở `target=_blank rel=noopener noreferrer`

- [ ] **Step 1: TDD test** ProjectCard render đủ field, nút external có target=_blank
- [ ] **Step 2: ProjectCard component**
- [ ] **Step 3: ProjectGallery** map qua `getProjectsSorted()`
- [ ] **Step 4: Test pass + commit** `feat(atlas): ProjectCard + ProjectGallery (Phase 1d)`

### Task D3: StatsPanel (Recharts)

**Files:**
- Create: `components/research-stats/StatsPanel.tsx`
- Test: `tests/components/StatsPanel.test.tsx`

**Spec (5.4):** Hiển thị tổng modules/chapters/sources/claims/charts/interactions/case_studies + bar chart Recharts phân rã theo module. Mỗi metric có tooltip.

- [ ] **Step 1: TDD test** verify total số đúng (217 sources, 327 claims v.v.)
- [ ] **Step 2: StatsPanel component** — number cards + Recharts BarChart
- [ ] **Step 3: Test pass + commit** `feat(atlas): StatsPanel với Recharts bar chart (Phase 1d)`

### Task D4: SynthesisTheses list

**Files:**
- Create: `components/theses/SynthesisTheses.tsx`

**Spec (5.5):** 10 thesis dạng list, mỗi entry: số thứ tự (mono teal), nội dung (serif), tag layer (chip), tag module.

- [ ] **Step 1: Component** render từ `theses` loader
- [ ] **Step 2: Commit** `feat(atlas): SynthesisTheses list 10 luận điểm (Phase 1d)`

### Task D5: QuestionsList + MisconceptionsGrid (client components có filter)

**Files:**
- Create: `components/questions/QuestionsList.tsx`, `components/misconceptions/MisconceptionsGrid.tsx`
- Test: `tests/components/QuestionsList.test.tsx`, `tests/components/MisconceptionsGrid.test.tsx`

**Spec (5.6, 5.7):**
- QuestionsList: filter bar 6 chip nhóm, grid câu hỏi, mỗi câu có module/concept tag
- MisconceptionsGrid: filter 9 tag, grid 16 card expand/collapse, mỗi card 7 trường

- [ ] **Step 1: TDD test** filter hoạt động + expand/collapse
- [ ] **Step 2: QuestionsList 'use client'** với useState filter
- [ ] **Step 3: MisconceptionsGrid 'use client'** với useState filter + expand
- [ ] **Step 4: Test pass + commit** `feat(atlas): QuestionsList + MisconceptionsGrid với filter (Phase 1d)`

### Task D6: CreditsRole + ComingSoon

**Files:**
- Create: `components/credits/CreditsRole.tsx`, `components/placeholders/ComingSoon.tsx`

**Spec (5.8, 5.9):**
- CreditsRole: 3 cột Human/SOL/GLM + feedback loop SVG
- ComingSoon: component cho /map /journey placeholder

- [ ] **Step 1: Components**
- [ ] **Step 2: Commit** `feat(atlas): CreditsRole + ComingSoon (Phase 1d)`

---

## Sub-phase E — Pages (Tasks E1-E9)

### Task E1: Home page đầy đủ

**Files:**
- Modify: `app/page.tsx`

- [ ] Hero + ProjectGallery preview + StatsPanel + SynthesisTheses preview + link tới pages
- [ ] **Commit** `feat(atlas): home page đầy đủ (Phase 1e)`

### Task E2: /projects page

- [ ] Hero nhỏ + ProjectGallery đầy đủ
- [ ] **Commit** `feat(atlas): /projects page (Phase 1e)`

### Task E3: /questions page

- [ ] Hero nhỏ + QuestionsList
- [ ] **Commit** `feat(atlas): /questions page (Phase 1e)`

### Task E4: /misconceptions page

- [ ] Hero nhỏ + MisconceptionsGrid
- [ ] **Commit** `feat(atlas): /misconceptions page (Phase 1e)`

### Task E5: /credits page

- [ ] Hero nhỏ + CreditsRole
- [ ] **Commit** `feat(atlas): /credits page (Phase 1e)`

### Task E6: /methodology page

- [ ] Hero nhỏ + research steps + source hierarchy + claim statuses + limits (từ methodology.json)
- [ ] Note Gate 3: worklog/token placeholder thẳng thắn hiển thị
- [ ] **Commit** `feat(atlas): /methodology page (Phase 1e)`

### Task E7: /sources page

- [ ] Hero nhỏ + sources tổng + by_module breakdown + glossary list (30 terms)
- [ ] **Commit** `feat(atlas): /sources page (Phase 1e)`

### Task E8: /map + /journey stubs với ComingSoon

- [ ] /map: ComingSoon phase="Phase 2" — Knowledge Constellation
- [ ] /journey: ComingSoon phase="Phase 3" — Research Journey Timeline
- [ ] **Commit** `feat(atlas): /map + /journey placeholder pages (Phase 1e)`

### Task E9: Khôi phục build vào validate + verify build

- [ ] Edit package.json `validate` thêm lại `&& npm run build`
- [ ] Chạy `npm run validate` phải full green
- [ ] Verify `out/index.html` + các trang con `out/projects/index.html` v.v.
- [ ] **Commit** `chore(atlas): khôi phục build vào validate chain (Phase 1e)`

---

## Sub-phase F — Tests bổ sung (Tasks F1-F3)

### Task F1: Component tests còn thiếu

- [ ] ProjectGallery.test.tsx, StatsPanel.test.tsx, SynthesisTheses.test.tsx, CreditsRole.test.tsx
- [ ] **Commit** `test(atlas): component tests Phase 1f`

### Task F2: E2E tests Playwright

**Files:**
- Create: `tests/e2e/navigation.spec.ts`, `gallery.spec.ts`, `questions.spec.ts`, `misconceptions.spec.ts`, `accessibility.spec.ts`, `mobile.spec.ts`

- [ ] 8 routes HTTP 200
- [ ] Gallery 4 card, M01-M04 link external đúng URL
- [ ] Questions filter nhóm
- [ ] Misconceptions filter tag + expand
- [ ] Mobile 390px viewport
- [ ] **Commit** `test(atlas): Playwright E2E suite (Phase 1f)`

### Task F3: Final `npm run validate` full green

- [ ] Chạy validate, phải pass
- [ ] **Commit** nếu có fix

---

## Sub-phase G — Deploy Vercel (Tasks G1-G3)

### Task G1: Vercel project setup

- [ ] `cd economic-life-atlas && npx vercel link` (hoặc tạo project mới nếu chưa có)
- [ ] Project name: `economic-life-atlas`
- [ ] **Commit** `.vercel/project.json` nếu có

### Task G2: Deploy production

- [ ] `npx vercel --prod`
- [ ] Verify URL `economic-life-atlas.vercel.app` HTTP 200
- [ ] Verify 4 module link external hoạt động
- [ ] Nếu tên trùng → chọn biến thể, báo URL thực

### Task G3: Final report

- [ ] Tạo `economic-life-atlas/README.md` với URL, deploy status, commit hash
- [ ] Tạo `economic-life-atlas/CHANGELOG.md` Phase 1 entry
- [ ] **Commit** `docs(atlas): README + CHANGELOG Phase 1 complete (Phase 1g)`

---

## Definition of Done — Phase 1

Sau D-G,portal phải đáp ứng 14 điều kiện spec phần 9.

**Self-Review**: plan ngắn hơn ABC vì spec đã rõ + nhiều tasks là "tạo component đơn giản từ loader có sẵn". Implementation details đưa vào subagent prompt thay vì lặp ở plan.

**Execution note**: User chỉ thị continuous end-to-end, không dừng báo cáo. Tôi sẽ dispatch 2-3 implementer subagents liên tục (D1-D6 chung 1 subagent, E1-E9 chung 1 subagent, F1-G3 chung 1 subagent cuối).
