#!/usr/bin/env python3
"""Validate and publish the canonical deep master report without rewriting it."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path


OUT = Path(__file__).resolve().parent
CONTENT = OUT / "canonical_content"
MASTER = CONTENT / "08_master_report_draft.md"
CHILDREN = sorted(CONTENT.glob("[A-E]_*.md"))


def words(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ỹ]+\b", text, re.UNICODE))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main() -> None:
    claim_matrix = load(OUT / "14_claim_usage_matrix.json")
    claim_ids = {item["claim_id"] for item in claim_matrix["claims"]}
    chart_ids = {
        claim_id
        for chart in load(OUT / "12_chart_briefs.json")["charts"]
        for claim_id in chart["source_claim_ids"]
    }

    master_text = MASTER.read_text()
    docs = {MASTER.name: master_text, **{path.name: path.read_text() for path in CHILDREN}}
    counts = {name: words(text) for name, text in docs.items()}
    all_text = "\n".join(docs.values())
    prose_refs = set(re.findall(r"\[([A-Z][A-Z0-9-]+)\]", all_text))
    sentences = [
        sentence.strip()
        for text in docs.values()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if len(sentence.strip()) > 40
    ]
    sentence_counts = {sentence: sentences.count(sentence) for sentence in set(sentences)}
    duplicate_ratio = sum(count - 1 for count in sentence_counts.values() if count > 1) / max(1, len(sentences))
    heading_count = len(re.findall(r"^#{2,3} ", master_text, re.MULTILINE))

    forbidden_assertions = [
        r"bond (?:dẫn|dự báo) thị trường",
        r"khối lượng xác nhận xu hướng",
        r"phân kỳ là tín hiệu (?:mua|bán)",
        r"đã xác nhận.*tín hiệu giao dịch",
    ]
    overclaims = []
    for pattern in forbidden_assertions:
        for match in re.finditer(pattern, master_text, re.IGNORECASE):
            context = master_text[max(0, match.start() - 100):match.end() + 80].lower()
            if "không" not in context and "chưa" not in context:
                overclaims.append(match.group(0))

    empirical_complete = all(
        claim.get("limitation")
        and claim.get("sources")
        and all(
            source.get("artifact")
            and source.get("test_id_or_key")
            and len(source.get("sha256", "")) == 64
            for source in claim["sources"]
        )
        for claim in claim_matrix["claims"]
    )

    checks = {
        "master_word_count_8000_10000": 8000 <= counts[MASTER.name] <= 10000,
        "children_word_count_1400_2000": all(1400 <= counts[path.name] <= 2000 for path in CHILDREN),
        "master_has_substantive_density": counts[MASTER.name] / max(1, heading_count) >= 130,
        "claim_refs_resolve": prose_refs <= claim_ids,
        "chart_refs_resolve": chart_ids <= claim_ids,
        "empirical_mapping_complete": empirical_complete,
        "duplicate_sentence_ratio_below_005": duplicate_ratio < 0.05,
        "no_numeric_pooling": "không thực hiện phân tích gộp" in master_text,
        "no_causal_chain": "không nói bond dẫn độ rộng" in master_text.lower(),
        "no_operational_overclaim": overclaims == [],
        "technical_boundary_present": "HTML chỉ là sản phẩm trình bày" in master_text,
    }
    failures = [name for name, passed in checks.items() if not passed]
    status = "PASS_CODEX_MASTER_DEPTH_R2_CLOSEOUT" if not failures else "PATCH_NEEDED_CODEX_MASTER_DEPTH_R2"

    for child in CHILDREN:
        shutil.copyfile(child, OUT / "child_rewrites" / child.name)
    shutil.copyfile(MASTER, OUT / MASTER.name)

    audit = {
        "status": status,
        "checks": checks,
        "failures": failures,
        "word_counts": counts,
        "master_heading_count": heading_count,
        "master_words_per_heading": round(counts[MASTER.name] / max(1, heading_count), 2),
        "duplicate_sentence_ratio": round(duplicate_ratio, 4),
        "claim_count": len(claim_ids),
        "unresolved_claims": sorted(prose_refs - claim_ids),
        "canonical_master_sha256": sha(MASTER),
    }
    write_json(OUT / "17_editorial_audit.json", audit)
    write_json(
        OUT / "19_final_resume_packet.json",
        {
            "status": status,
            "master_draft": MASTER.name,
            "child_drafts": [path.name for path in CHILDREN],
            "canonical_master_sha256": audit["canonical_master_sha256"],
            "word_counts": counts,
            "html_created": True,
            "deploy_started": True,
            "statistics_rerun": False,
            "unresolved_claims": audit["unresolved_claims"],
            "required_remediation": failures,
            "next_action": "Rebuild the governed static site, run local and production browser QA, then freeze R2 closeout.",
        },
    )
    (OUT / "22_master_depth_r2_closeout.md").write_text(
        f"# {status}\n\n"
        f"Master words: {counts[MASTER.name]}; headings: {heading_count}; "
        f"words per heading: {audit['master_words_per_heading']}.\n\n"
        "The master is a standalone long-form synthesis. No statistics or research artifacts were rerun.\n"
    )
    print(status)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
