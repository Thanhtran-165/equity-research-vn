# GLM implementation handoff

## Canonical content
Use the five files in `child_rewrites/` and `08_master_report_draft.md` as canonical meaning. Their source-of-truth copies are in `canonical_content/` and are emitted by `build_editorial_package.py`; never patch generated prose directly. GLM may improve sentence rhythm, headings and microcopy in the canonical source, but may not alter any empirical claim, number, limitation or conclusion. Use `14_claim_usage_matrix.json` for every empirical number and `12_chart_briefs.json` for visual work.

## Section order
Child reports follow their individual maps in `06_child_report_section_map.json`. Master report follows `07_master_report_outline.md`. Keep the short answer, limitation box, investor-use boundary and conclusion visible without accordions. Put technical provenance in details/appendix only. Do not flatten the five reports into one repeated template.

## Claim and visual rules
Only listed claim IDs may support empirical statements. Preserve artifact/key/SHA mapping; do not cite HTML as evidence. Never use invalid/historical authority. Implement only chart briefs; no new charts, composite signals, numeric pooling or causal chain. V2 is a conceptual explainer and must not display invented frequencies, probabilities or empirical breadth precedence.

## Mobile and QA
Design first for 320px, then 390px and 1440px. Keep captions and limitations visible, use one state per row for maps, and avoid dual axes. Before any deployment run this editorial generator, verify `PASS_CODEX_EDITORIAL_MASTER_CLOSEOUT`, then run claim audit, forbidden scan and browser QA at all three viewports. HTML must not become an empirical source.

## Forbidden wording and actions
Do not call a divergence a buy/sell signal, volume trend confirmation, or a forecast. Do not turn an in-sample ordering into stability on new data. Do not run statistics, alter research artifacts or deploy before a separate implementation closeout. Any prose edit must be made in `canonical_content/` and rerun through the editorial audit.
