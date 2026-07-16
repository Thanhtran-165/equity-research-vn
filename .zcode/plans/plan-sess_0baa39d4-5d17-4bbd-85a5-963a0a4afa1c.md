# Plan: Hợp nhất 2 dự án → 1 frontend-polish tự sở hữu (Option B)

## Mục tiêu
Biến `frontend-polish` từ "bộ não điều phối 2 dự án" → **1 dự án tự sở hữu hoàn toàn**. Chọn lọc ~20 skill giá trị nhất, viết lại bằng **1 giọng duy nhất** (Việt framing + Anh technical), nội địa hóa nguyên lý Emil làm **lớp nền craft** áp dụng cho mọi skill. Bỏ dispatch/vendor, không còn phụ thuộc upstream.

## Phân tích đã làm (đũa cơ sở cho plan)
- **MengTo triage:** từ ~97 skill → chọn **15** (7 principle + 8 recipe). Cắt: mood skins (~20, chỉ là palette copy-paste), motion trùng (8→2: gsap + animation-systems, cắt 6 biến thể scroll), 3D/WebGL (8→0, niche heavy-dep), taste trùng (6→1: high-end-visual-design), codex operational (18→2: optimize + verify).
- **Emil extraction:** ra **15 luật cross-cutting** (frequency gate, easing law, duration law, physicality law, GPU law, interruptibility law, spring law, velocity law, gesture law, spatial consistency, asymmetric timing, a11y law, cohesion law, + polish tactical). Ma trận trùng lặp cho thấy: STANDARDS.md = 100% subset emil → drop; spring/gesture canonical = apple (đầy đủ nhất); a11y canonical = apple (3 tín hiệu vs 1). Phần unique của emil: easing curves, duration table, scale(0) ban, Sonner 6 principles, review format. Phần unique của apple: velocity handoff math, momentum projection, rubber-band formula, materials, typography.
- **Glossary** (animation-vocabulary): giữ làm reference riêng (mục đích khác — naming không phải building, ~80 định nghĩa không phải rule actionable).

## Cấu trúc kết quả (19 skill + 2 reference)

```
frontend-polish/
├── SKILL.md                    # rewrite — workflow mới, không còn routing-vendor
├── skills/                     # ← MỚI: tự sở hữu, 1 giọng
│   ├── craft/                  # 5 — lớp nền triết lý + luật (Emil nội địa hóa + MengTo taste)
│   │   ├── animation-laws.md       (15 luật consolidated từ emil+apple — load trước mọi motion)
│   │   ├── apple-motion.md         (spring/gesture/material/typography — phần unique của apple)
│   │   ├── review-checklist.md     (10 standards + escalation triggers + output format)
│   │   ├── beloved-components.md   (6 nguyên tắc Sonner + cohesion/personality)
│   │   └── taste-guardrail.md      (anti-generic taste — từ high-end-visual-design)
│   ├── layout/                 # 3
│   │   ├── editorial-tech.md       (dashboard/editorial layout — recipe)
│   │   ├── conversion-pages.md     (landing + pricing gộp — structure/CRO principle)
│   │   └── tailwindcss.md          (CSS framework conventions — foundation)
│   ├── motion/                 # 2
│   │   ├── gsap.md                 (timeline/ScrollTrigger/stagger + pitfalls — subsumes 6 scroll variants)
│   │   └── animation-systems.md    (product-grade motion principles — easing/duration/choreography)
│   ├── visual/                 # 5
│   │   ├── shadows.md              (layered elevation — universal, high-impact)
│   │   ├── border-gradient.md      (premium gradient edges)
│   │   ├── blur-masking.md         (progressive-blur + alpha-masking gộp — edge fades/gradient blur)
│   │   ├── marquee.md              (seamless infinite marquee — logo cloud)
│   │   └── materials.md            (skeuomorphic + glass gộp — tactile/translucent surfaces)
│   ├── audit/                  # 3
│   │   ├── optimize-animations.md  (perf axis — rAF/memory-leak/GPU, complement craft)
│   │   ├── verify-grade5.md        (verify-and-report plain language)
│   │   └── redesign.md             (audit existing site → upgrade to premium)
│   └── assets/                 # 1
│       └── images.md              (Unsplash sourcing + aspect-ratio guidance)
├── references/                 # 2
│   ├── catalog.md              # rewrite — 19 skill, routing matrix mới
│   └── animation-glossary.md   # ← MỚI: từ animation-vocabulary (term→description, naming reference)
├── agents/openai.yaml          # giữ nguyên
├── README.md                   # update — bỏ phần submodule, giải thích cấu trúc mới
└── .gitignore                  # giữ nguyên
```

**Không còn:** `vendor/`, `.gitmodules`, 77+4 skill external, progressive-dispatch-via-catalog.

## Nguyên tắc viết mỗi skill file
- **1 giọng duy nhất** — Việt framing/hướng dẫn (như SKILL.md hiện tại) + Anh technical (code, easing values, CSS, terms).
- **Mỗi skill tự chứa** — frontmatter (`name`/`description`/`Use when`) + nội dung. Không bắt buộc phải đi đọc Emil/MengTo gốc nữa.
- **Lớp nền craft áp dụng toàn cục** — `craft/animation-laws.md` chứa 15 luật; mọi skill `motion/` và `visual/` tham chiếu "tuân thủ animation-laws" thay vì lặp lại.
- **Deduplicate theo ma trận trùng lặp** — spring/gesture lấy từ apple (đầy đủ nhất); easing/duration/scale(0)/review-format lấy từ emil; a11y lấy apple's 3-signal version; STANDARDS.md drop hoàn toàn.
- **Progressive disclosure giữ nguyên** — catalog.md vẫn là entry (~2K tokens), mỗi skill load khi cần.
- **Attribution** — mỗi skill có footnote nguồn gốc: " distilled from [Emil/MengTo] (MIT)". Top-level ATTRIBUTION note trong README.

## Workflow mới của SKILL.md
1. **Định loại output** — dashboard/landing/portfolio/app UI. Nếu user mô tả cảm giác → tra `animation-glossary.md`.
2. **Load lớp nền craft** — **luôn** đọc `craft/animation-laws.md` trước khi chạm motion. Đây là điểm khác biệt cốt lõi vs layout cũ: luật animation là đường ray toàn cục, không phải 1 skill tùy chọn.
3. **Chọn 3-5 skill** từ catalog theo routing matrix.
4. **Áp dụng** — chỉ đổi 1-2 thứ/lần, giữ logic/data, chỉ chạm presentation. Tuân thủ animation-laws cho mọi motion.
5. **Verify** — chạy `audit/verify-grade5.md` + (nếu có animation) `audit/optimize-animations.md`.

## Routing matrix mới (trong SKILL.md)
| Loại output | skill gợi ý |
|---|---|
| Dashboard tài chính / báo cáo | editorial-tech, shadows, tailwindcss, taste-guardrail |
| Landing/conversion SaaS | conversion-pages, border-gradient, marquee, taste-guardrail |
| Portfolio/storytelling | gsap, animation-systems, blur-masking, taste-guardrail |
| App UI / dashboard sản phẩm | editorial-tech, shadows, materials, animation-systems |
| Có animation (luôn) | **animation-laws** (bắt buộc) + animation-systems + gsap |
| Audit motion craft | review-checklist + animation-laws + optimize-animations |
| Redesign existing | redesign + taste-guardrail + review-checklist |

## Thứ tự thực thi (full batch, 1 commit)
1. **Tạo `skills/` tree** — viết 19 skill file theo taxonomy (craft → layout → motion → visual → audit → assets). Mỗi file distilled từ nguồn đã phân tích, deduplicate, 1 giọng.
2. **Tạo `references/animation-glossary.md`** — port glossary từ animation-vocabulary (80+ term → description).
3. **Rewrite `references/catalog.md`** — 19 skill mới, format bảng cùng kiểu, routing matrix mới.
4. **Rewrite `SKILL.md`** — workflow mới, routing matrix mới, bỏ mọi ref tới vendor/MengTo/Emil dispatch.
5. **Update `README.md`** — cấu trúc mới, bỏ phần submodule, thêm ATTRIBUTION section.
6. **Remove `vendor/` + `.gitmodules`** — `git rm` + `git submodule deinit`.
7. **Commit + push** — 1 commit "feat: consolidate into self-owned 19-skill skill (drop vendor dispatch)".

## Verify
- `ls -R skills/` → đủ 19 file ở đúng taxonomy.
- `grep -r "vendor/" SKILL.md references/` → 0 ref cũ.
- `grep -r "MengTo\|emilkowalski" SKILL.md` → chỉ còn attribution context, không còn dispatch.
- Mỗi skill file có frontmatter đầy đủ + attribution footer.
- Catalog.md list đúng 19 skill, load path `skills/<cat>/<name>.md` resolve.
- `git status` clean sau commit; remote update.

## Đổi lại (trade-off đã chấp nhận)
- **Mất đồng bộ upstream** — MengTo/Emil update thì không auto vào. Bù lại: focus, ownership, mạch lạc, 1 giọng. Coi đây là "fork có chủ ý" — bạn chủ động chọn phiên hiện tại.
- **Phải bảo trì nội dung** — nếu phát hiện gap, tự viết thêm/bổ sung skill. Không còn `git submodule update`.
- **Attribution** — ghi rõ nguồn MIT trong mỗi skill + README. Tôn trọng license, không claim là author gốc.
- **1 commit lớn** — khó rollback từng phần, nhưng kết quả cuối gọn, testable ngay (verify trong bước verify).