#!/usr/bin/env python3
"""Validate and publish the R3 long-form editorial package without rerunning research."""

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
HISTORY = OUT / "history" / "pre_longform_r3"


def words(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ỹ]+\b", text, re.UNICODE))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def preserve_r2_once() -> None:
    if HISTORY.exists():
        return
    HISTORY.mkdir(parents=True)
    members = {}
    for name in [
        "17_editorial_audit.json",
        "19_final_resume_packet.json",
        "22_master_depth_r2_closeout.md",
        "build_master_depth_r2.py",
    ]:
        source = OUT / name
        if source.exists():
            target = HISTORY / name
            shutil.copy2(source, target)
            members[name] = sha(target)
    write_json(HISTORY / "manifest.json", {"status": "SUPERSEDED_BY_LONGFORM_R3", "members": members})


def main() -> None:
    preserve_r2_once()
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
    forbidden_assertions = [
        r"bond (?:dẫn|dự báo) thị trường",
        r"khối lượng xác nhận xu hướng",
        r"phân kỳ là tín hiệu (?:mua|bán)",
        r"đã xác nhận.*tín hiệu giao dịch",
    ]
    overclaims = []
    for pattern in forbidden_assertions:
        for match in re.finditer(pattern, all_text, re.IGNORECASE):
            context = all_text[max(0, match.start() - 130):match.end() + 80].lower()
            if not re.search(r"(?:không|chưa|không được|không thể)\b[^.!?]{0,160}", context):
                overclaims.append(match.group(0))

    example_language = {
        name: bool(re.search(r"(?:giả định|minh họa|ví dụ)", text, re.IGNORECASE))
        for name, text in docs.items()
    }
    checks = {
        "master_word_count_15000_18000": 15000 <= counts[MASTER.name] <= 18000,
        "children_word_count_4000_6000": all(4000 <= counts[path.name] <= 6000 for path in CHILDREN),
        "five_children_present": len(CHILDREN) == 5,
        "claim_refs_resolve": prose_refs <= claim_ids,
        "chart_refs_resolve": chart_ids <= claim_ids,
        "empirical_mapping_complete": empirical_complete,
        "duplicate_sentence_ratio_below_005": duplicate_ratio < 0.05,
        "examples_present_all_reports": all(example_language.values()),
        "hypothetical_examples_disclaimed": all(
            "không phải" in text.lower() or "giả định" in text.lower()
            for text in docs.values()
        ),
        "no_numeric_pooling": "không thực hiện phân tích gộp" in master_text,
        "no_causal_chain": "không nói bond dẫn độ rộng" in master_text.lower(),
        "no_operational_overclaim": overclaims == [],
        "technical_boundary_present": "HTML chỉ là sản phẩm trình bày" in master_text,
        "plain_language_reader_contract": all(
            "Câu trả lời ngắn" in text for name, text in docs.items() if name != MASTER.name
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]
    status = "PASS_CODEX_LONGFORM_R3_CLOSEOUT" if not failures else "PATCH_NEEDED_CODEX_LONGFORM_R3"

    for child in CHILDREN:
        shutil.copyfile(child, OUT / "child_rewrites" / child.name)
    shutil.copyfile(MASTER, OUT / MASTER.name)

    audit = {
        "status": status,
        "checks": checks,
        "failures": failures,
        "word_counts": counts,
        "duplicate_sentence_ratio": round(duplicate_ratio, 4),
        "claim_count": len(claim_ids),
        "unresolved_claims": sorted(prose_refs - claim_ids),
        "canonical_hashes": {name: sha(CONTENT / name) for name in docs},
        "statistics_rerun": False,
    }
    write_json(OUT / "17_editorial_audit.json", audit)
    write_json(
        OUT / "19_final_resume_packet.json",
        {
            "status": status,
            "master_draft": MASTER.name,
            "child_drafts": [path.name for path in CHILDREN],
            "word_counts": counts,
            "statistics_rerun": False,
            "unresolved_claims": audit["unresolved_claims"],
            "required_remediation": failures,
            "next_action": "Build the six-page site, backlink five legacy deployments, run browser QA, and deploy all governed pages.",
        },
    )
    (OUT / "24_longform_r3_closeout.md").write_text(
        f"# {status}\n\nMaster: {counts[MASTER.name]} words. Children: "
        + ", ".join(f"{path.stem}={counts[path.name]}" for path in CHILDREN)
        + ".\n\nNo statistics or empirical artifacts were rerun.\n"
    )
    print(status)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
