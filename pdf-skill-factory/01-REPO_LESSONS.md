# File 1 — REPO_LESSONS.md

> Bài học thiết kế rút từ 20 repo/paper. Format theo brief mục 3.1.
> Mỗi repo trả lời câu hỏi: **"Nó dạy ta điều gì để xây PDF Skill tự cải thiện?"**

## Nhóm A — Skill Library / Lifelong Learning

### 1. Voyager (MineDojo/Voyager)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/MineDojo/Voyager |
| Pattern học được | Skill library + automatic curriculum. Skill = `{name, code, description}` lưu flat, **retrieve bằng embedding similarity** (embed description, so cosine với query task). Verified-skills mới được persist (code chạy không lỗi). Curriculum controller đề xuất "task hữu ích kế tiếp" dựa state hiện tại. |
| Áp dụng cho PDF Skill | Skill `pdf-evidence` chia thành sub-skill: `ClassifyPDF`, `OCRDecision`, `ExtractEvidence`, `ExtractTable`, `AnswerWithCitation`, `CompareDocuments`, `DetectMissingEvidence`, `RefineAnswer`. Mỗi sub-skill có description rõ để curriculum/future-GEPA retrieve đúng khi gặp loại PDF mới. |
| Không áp dụng / rủi ro | Voyager validate chỉ "có chạy" không "chạy tốt" — skill kém generalize vẫn bị cache. Embedding retrieve có thể fetch skill superficial-similar nhưng sai. Library không giới hạn → bloat. |
| Cần eval bằng | Regression suite + bảng metric (DEFINITION_OF_DONE.md) trước khi promote sub-skill; prune skill cũ khi metric tụt. |

## Nhóm B — Reflection / Self-improvement

### 2. Reflexion (noahshinn/reflexion)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/noahshinn/reflexion |
| Pattern học được | **Self-reflection → verbal feedback → episodic memory → next trial**. Evaluator ra reward → reflection model biến reward thành verbal critique ("đã thử X, đánh giá là sai vì Y") → critique append vào memory, inject vào context của trial kế tiếp. Phân biệt với retry: memory **kiên trì qua các trial độc lập**, không phải re-sample cùng prompt. |
| Áp dụng cho PDF Skill | Mỗi failure (thiếu citation, sai trang, bỏ bảng, hallucinate) → reflection ngắn ("page 12 không chứa quote X — verify quote tồn tại verbatim trước khi cite") → lưu vào `skill_memory.json` theo doc-type → re-inject cho PDF cùng loại ở run kế tiếp. |
| Không áp dụng / rủi ro | Memory của Reflexion per-task-instance, clear giữa task khác nhau → phải có versioning layer riêng để cải thiện cumulatively. Evaluator sai → feedback sai → retry tệ hơn. |
| Cần eval bằng | A/B: same PDF chạy 2 trial, trial 2 có memory trial 1 — đo metric improvement. |

### 3. Self-Refine (madaan/self-refine)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/madaan/self-refine |
| Pattern học được | Ba prompt tách bạch: **Init (sinh output) → Feedback (cùng LLM chấm theo rubric nhiều chiều) → Iterate (tái sinh dùng feedback)**. Lặp đến stop criterion. Critic cụ thể vì chấm từng dimension riêng (vd 4/5 ease, 5/5 relevance). Trong task (within-run), không training. |
| Áp dụng cho PDF Skill | Khi lỗi cheap-detectable + local-fixable trong cùng câu trả lời (vd "table cells không khớp → regenerate chỉ table") → chạy Feedback/Iterate trong-loop với rubric `{citation_present, page_correct, no_hallucination, table_complete}`. Promote cross-version memory (Voyager/Reflexion style) chỉ khi cùng dimension fail lặp lại nhiều run. |
| Không áp dụng / rủi ro | Cùng LLM vừa generate vừa critique → blind spot. Feedback drift, loop oscillate không hội tụ. Tối ưu output hiện tại, không tích lũy nếu thiếu save-to-memory. |
| Cần eval bằng | Metric trước/sau iterate loop; dừng nếu iterate quá 3 lần không improve. |

## Nhóm C — Prompt / Program Optimization

### 4. DSPy (stanfordnlp/dspy)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/stanfordnlp/dspy |
| Pattern học được | **Signature (input→output typed) → Module (Predict/ChainOfThought/ReAct) → Metric → Teleprompter (Bootstrap/MIPRO/GEPA)**. Tách "chương trình làm gì" (signature) khỏi "prompt thế nào" (optimized). Metric là tín hiệu tối ưu duy nhất — không hand-tune prompt string. |
| Áp dụng cho PDF Skill | Mỗi sub-skill là Signature: `ClassifyPDF(doc)->doc_type`, `ExtractEvidence(question, doc)->list[quote_with_page]`, `ExtractTable(page)->table_json`, `AnswerWithCitation(question, evidence)->answer_with_citations`, `CompareDocuments(a,b)->differences`, `DetectMissingEvidence(...)->report`, `RefineAnswer(answer, critique)->refined`, `GenerateEvalCases(doc)->examples`, `UpdateSkillInstruction(failures, current)->new`. Mỗi module mô tả ở `scaffolding/modules/`. |
| Không áp dụng / rủi ro | Overfit trainset dưới teleprompter aggressive. Metric LLM-based có thể bị game. Bootstrap cần labeled set (PDF scarce). Compile đắt. |
| Cần eval bằng | Hold-out valset; metric trên valset, không trainset. |

### 5. GEPA (gepa-ai/gepa → `dspy.GEPA`, arXiv 2507.19457)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/gepa-ai/gepa; dspy.ai/api/optimizers/GEPA/overview |
| Pattern học được | **Genetic-Pareto**: chọn candidate từ Pareto frontier (xuất sắc theo subset khác nhau) → execute trên minibatch (full trace) → **reflect** (reflection LM đọc trace: error/logprob/failed-parse) → **mutate** component targeted → **accept** nếu improve frontier. Đổi mới: **Actionable Side Information** — evaluator trả **text feedback không chỉ scalar reward** ("bảng p.4 bị miss vì parser tách cột"). Gradient-free, API-only. Vượt GRPO với 35× ít rollout. |
| Áp dụng cho PDF Skill | (Roadmap v0.7) Build sub-skill dạng DSPy module → chạy `dspy.GEPA(auto='medium')` với metric `{score, feedback}` (feedback narrate failure cụ thể) → evolve instruction `ClassifyPDF`/`ExtractEvidence`/`AnswerWithCitation`. Release version mới chỉ nếu improve Pareto trên held-out regression. |
| Không áp dụng / rủi ro | Overfit valset nếu val≈train. Bị giới hạn bởi reflection LM. Pareto pool có thể giữ candidate mediocre tốn cost. |
| Cần eval bằng | Pareto frontier trên valset; so sánh với baseline trước khi release. |

### 6. TextGrad (zou-group/textgrad, Nature 2024)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/zou-group/textgrad |
| Pattern học được | **Autograd engine với gradient = ngôn ngữ feedback LLM**. `Variable(value, role, requires_grad=True)`, `TextLoss(instruction)`, `loss.backward()` (LLM sản critique vào `.grad`), `TGD.step()` rewrite variable từ gradient. Critic useful vì loss **anti-vague**: "Evaluate… Do not attempt to solve it yourself, only identify errors. Be super concise." → gradient thành surgical diff, không rewrite. |
| Áp dụng cho PDF Skill | `citation_policy` và `extraction_instruction` là `requires_grad=True`. Mỗi wrong-citation/missed-table → `.grad` text → `TGD.step()` rewrite rule. Tốt cho edit fine-grained (siết citation rule) — GEPA overkill ở đây. |
| Không áp dụng / rủi ro | Local/greedy, có thể oscillate/drift không acceptance test (GEPA có Pareto gate). Textual gradient vague nếu loss không chặt. |
| Cần eval bằng | Acceptance: phải pass regression set trước khi commit patched rule. |

## Nhóm D — Evaluation / Benchmark

### 7. RAGAS (explodinggradients/ragas)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/explodinggradients/ragas |
| Pattern học được | Metric RAG: **Faithfulness** (decompose answer → verify mỗi claim supported by context; = supported/total), **Answer Relevancy** (trả lời có đúng input không), **Context Precision** (relevant chunk rank cao), **Context Recall** (gold answer attributable to retrieved context). Hook cho citation-by-page: **IDBasedContextPrecision** — mỗi chunk có `id` (page number), verify cited page rank top. |
| Áp dụng cho PDF Skill | Faithfulness + Answer Relevancy áp trực tiếp. IDBasedContextPrecision → page-citation verifier. Phải custom thêm: **table-fidelity** (header/units/period), **abstention** (được reward khi evidence thiếu). |
| Không áp dụng / rủi ro | RAGAS không có metric table-structure. Không verify natively cited page chứa evidence thật (chỉ rank). |
| Cần eval bằng | Custom metric: page-accuracy (page có trong evidence set), table-fidelity (cell compare). |

### 8. DeepEval (confident-ai/deepeval)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/confident-ai/deepeval |
| Pattern học được | **pytest-style LLM unit test**. `LLMTestCase(actual_output, retrieval_context)`. Metric: Faithfulness, AnswerRelevancy, **Hallucination** (LLM-judge actual vs context). Mỗi bug → fixture → `assert_test(case, [Faithfulness(threshold=0.9), Hallucination(threshold=0)])`. Suite chỉ tăng — bug đã fix không bao giờ tái diễn. |
| Áp dụng cho PDF Skill | Mỗi lỗi trong `06-FAILURE_MODES.md` → pytest case trong `scaffolding/tests/test_regression.py`. Regression green = gate bắt buộc trước bump version (DEFINITION_OF_DONE.md). |
| Không áp dụng / rủi ro | LLM-judge cost; metric phụ thuộc quality LLM-judge. |
| Cần eval bằng | CI gate: pytest 100% xanh trước release. |

### 9. OpenAI Evals (openai/evals)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/openai/evals |
| Pattern học được | Eval = **eval.yaml (task + model + dataset) → run → collect observations → score** (model-graded hoặc rule-based). Mỗi run logged theo version → so sánh head-to-head. Rubric cho cited answer: rule-based (page-in-evidence) + model-graded (faithful). Cho abstained: dataset có explicit "unanswerable" item, abstention đúng = 1.0, hallucinate = 0. |
| Áp dụng cho PDF Skill | Fixture `case.json` = eval item. `eval_runner.py` = mini-eval-harness. So sánh metric distribution giữa version — block bump nếu regression quá tolerance. |
| Không áp dụng / rủi ro | Dataset nghiêng nếu thiếu "unanswerable" item (PDF Skill PHẢI có). |
| Cần eval bằng | Fixture có cả answerable + unanswerable item; metric report có cột abstention_accuracy. |

## Nhóm E — Coding Agent / Skill Writer

### 10. OpenHands (All-Hands-AI/OpenHands, ex OpenDevin)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/All-Hands-AI/OpenHands |
| Pattern học được | **Sandboxed runtime**: agent đề xuất action (edit/run/observe) → execute trong sandbox → observe → lặp. Role chuyên biệt: coder viết code, reviewer critique, loop đóng bằng chạy test. **Human approval ở boundary**: agent đề xuất, sandbox execute, checkpoint (PR/approval) gate promotion. |
| Áp dụng cho PDF Skill | Vai trò trong factory: Researcher (đọc repo, ra rule) → Coder (viết skill) → Critic (review) → Evaluator (chạy eval, đọc failure) → Version-bumper (gated). Human approval ở giữa "evaluator green" và "version bump" (xem RUNBOOK.md Phase 8). |
| Không áp dụng / rủi ro | Sandbox overhead; agent có thể viết code sai vòng lặp dài. |
| Cần eval bằng | Mỗi agent role có output schema; checkpoint có review bởi role khác hoặc human. |

### 11. OpenAI Agents SDK (openai-agents-python)

| Trường | Giá trị |
|---------|---------|
| Repo | github.com/openai/openai-agents-python |
| Pattern học được | Ba pattern load-bearing: **Handoffs** (agent delegate qua `on_handoff` callback, filter `input_type`), **Guardrails** (input guardrail trước khi agent act; output guardrail trước khi answer — đây là chỗ enforcement citation + abstention), **Tracing** (record LLM/tool/handoff/guardrail event — auditable). |
| Áp dụng cho PDF Skill | Output guardrail ở mỗi boundary: claim phải cite page trong evidence; no-evidence → phải abstain. Tracing → mỗi quyết định (tại sao classify thế, tại sao cite page đó) auditable cho self-improvement. |
| Không áp dụng / rủi ro | Phức tạp hơn workflow tuyến tính nếu scope nhỏ. |
| Cần eval bằng | Trace sample để xác nhận guardrail fires đúng; failure → regression case. |

## Nhóm F — PDF Tools (DOMAIN KNOWLEDGE, không lõi kiến trúc)

Mỗi tool: 1 dòng tốt nhất / fail / rule → policy.

| # | Tool | Best at | Fails at | Rule đưa vào `references/parsers.md` |
|---|------|---------|----------|--------------------------------------|
| 12 | RAGFlow/DeepDoc | RAG + layout + TSR table chunking | Rotated/merged cells mis-parse | DLR+TSR khi có bảng; auto-correct rotation |
| 13 | Docling | Born-digital structured → JSON | Multi-col scan, dense table | Ưu tiên cho born-digital; emit structured không flat |
| 14 | Marker | PDF→Markdown text-heavy fidelity | Compute nặng, scan degraded | Preserve page anchor để cite |
| 15 | MinerU | Formula/table-heavy + OCR | Doc lớn, edge-case formula | Route scan qua OCR pipeline |
| 16 | PyMuPDF4LLM | Markdown nhanh born-digital | Scan (cần OCR upstream) | Fast path digital; scan→OCR first |
| 17 | PaddleOCR | Scan OCR đa ngữ (VN+80) | Layout phức tạp không có layout module | Scan → OCR; multilingual cho non-Latin |
| 18 | Surya | Layout + reading order + table 90+ ngôn ngữ | Cần GPU; script hiếm | Respect reading order trước extract |
| 19 | Camelot | Bảng (lattice→stream) | Chỉ bảng; stream fail merged cell | Bảng → Camelot lattice first, stream fallback |
| 20 | pdfplumber | Char-level inspection, debug | Chậm doc lớn; heuristic break layout | Diagnostic + fallback + char-verify citation |

> v0.1 chỉ cài `pdfplumber` + `pypdf`. Các tool còn lại được **mô tả trong policy** để agent biết khi nào đề xuất user dùng, nhưng không cài trong scaffolding.

---

## SYNTHESIS — Top 5 pattern compose thành 1 loop

```
Task → Run Skill → Evaluate → Critique → Update Skill → Regression → Version Release
```

1. **DSPy (Signature/Module/Metric/Teleprompter)** — skeleton. Mỗi sub-skill là typed signature; metric là chân lý tối ưu.
2. **Voyager (skill library + embedding retrieve + curriculum)** — memory/registry layer: sub-skill có description, retrieve theo doc-type, curriculum đề xuất sub-skill mới khi family PDF fail lặp.
3. **Reflexion (verbal feedback → episodic memory)** — short-term, instance-typed: mỗi lỗi → lesson ngắn, re-inject cho run kế tiếp cùng doc-type.
4. **Self-Refine + TextGrad (in-task critique, anti-vague critic)** — within-run fix cho defect cheap-fixable; promote cross-version chỉ khi cùng dimension fail lặp.
5. **GEPA (dspy.GEPA, Pareto + ASI)** — driver cho "Update Skill → Regression → Version": evolve instruction từ eval failure, release version mới chỉ nếu improve Pareto trên held-out regression set.

**Phân tầng**: Reflexion + Self-Refine = "improve this run". Voyager + GEPA + DSPy = "improve this skill across runs".
