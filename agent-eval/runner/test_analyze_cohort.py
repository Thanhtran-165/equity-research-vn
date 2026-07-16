# test_analyze_cohort.py — TDD for the cohort analyzer.
# Pins the honesty rules: non-genuine runs excluded; 0/0 → N/A not 0%; hard-gate override;
# per-cohort separation; HRS coverage gate; small-sample CI; intervention/recovery/premature classes.
import os, sys, json, pytest, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze_cohort as AC

# ---------- sealed fixtures ----------
def genuine(run_id, verdict="PASS", recall=92.9, phases=8, intervention="none", premature=False,
            recovered=False, hard_gate_violations=None, cohort="exact-repeat"):
    return {"run_id":run_id,"cohort":cohort,"scored":True,"execution_type":"genuine_agent",
            "final_verdict":verdict,"recall_pct":recall,"phases_completed":phases,
            "duration_seconds":120,"requirements_passed":["REQ-001"],"requirements_failed":[] if verdict=="PASS" else ["REQ-009"],
            "human_intervention":{"severity":intervention,"actions":[]},
            "completion_claimed": True if premature else (verdict=="PASS"),
            "hard_gate_violations":hard_gate_violations or [],
            "recovered_from_error": recovered,
            "validator_results":{"verdict":verdict,"pass":1 if verdict=="PASS" else 0,"fail":0 if verdict=="PASS" else 1}}

def no_model(run_id):
    return {"run_id":run_id,"execution_type":"NO_MODEL_BOUND","scored":False,"final_verdict":None,"recall_pct":None}

def dry(run_id):
    return {"run_id":run_id,"execution_type":"NO_MODEL_BOUND","scored":False,"final_verdict":None}

def synthetic(run_id):
    return {"run_id":run_id,"execution_type":"synthetic_replay","scored":False,"final_verdict":"PASS","recall_pct":90}

# ---------- filtering ----------
def test_no_model_bound_excluded_from_kpis():
    runs = [no_model(f"nm-{i}") for i in range(5)]
    out = AC.analyze(runs)
    assert out["genuine_runs"] == 0
    assert out["status"] == "INCONCLUSIVE_NO_GENUINE_RUNS"
    assert out["first_pass_yield"] == "N/A"  # NOT 0.0
    assert out["autonomous_successful_completion_rate"] == "N/A"

def test_5_no_model_not_counted_as_5_failures():
    runs = [no_model(f"nm-{i}") for i in range(5)]
    out = AC.analyze(runs)
    assert out["genuine_runs"] == 0
    assert out["critical_failure_rate"] == "N/A"  # not 1.0

def test_mixed_cohort_only_counts_genuine():
    runs = [genuine("g1"), no_model("nm1"), dry("d1"), synthetic("s1"), genuine("g2",verdict="FAIL")]
    out = AC.analyze(runs)
    assert out["genuine_runs"] == 2
    assert out["final_pass_rate"] == 0.5  # 1 PASS / 2 genuine

# ---------- hard-gate override ----------
def test_high_recall_but_critical_violation_fails():
    runs = [genuine("g1", verdict="PASS", recall=99, hard_gate_violations=["HG-FAB"])]
    out = AC.analyze(runs)
    assert out["hard_gate_status"] == "FAIL"
    assert out["production_status"] == "FAIL"
    assert "HG-FAB" in out["critical_violations"]

def test_no_critical_violation_passes_gate():
    runs = [genuine("g1", verdict="PASS", recall=85)]
    out = AC.analyze(runs)
    assert out["hard_gate_status"] == "PASS"

# ---------- per-cohort separation ----------
def test_run_consistency_only_from_exact_repeat():
    # Cohort B (controlled) must NOT feed run-consistency (Cohort A metric)
    runs = [genuine("a1",cohort="exact-repeat",recall=90),genuine("a2",cohort="exact-repeat",recall=92),
            genuine("b1",cohort="controlled-robustness",recall=99),
            genuine("b2",cohort="controlled-robustness",recall=40)]
    out = AC.analyze(runs)
    assert out["exact_repeat"]["mean_recall"] == 91.0
    assert out["controlled_robustness"]["mean_recall"] == 69.5

# ---------- HRS coverage gate ----------
def test_hrs_preliminary_when_low_coverage():
    # with only 2 genuine runs, run_consistency dim has evidence but recovery maybe not
    runs = [genuine("a1",cohort="exact-repeat"),genuine("a2",cohort="exact-repeat")]
    out = AC.analyze(runs)
    assert out["hrs"]["evidence_coverage_pct"] < 70 or out["hrs"]["status"]=="PRELIMINARY"

# ---------- incomplete / invalidated cohort ----------
def test_incomplete_cohort_flagged():
    # protocol wants 5 exact-repeat; only 3 present
    runs = [genuine(f"a{i}",cohort="exact-repeat") for i in range(3)]
    out = AC.analyze(runs, expected={"exact_repeat":5,"controlled_robustness":5})
    assert out["exact_repeat"]["completeness"] == "INCOMPLETE"
    assert out["exact_repeat"]["observed"] == 3
    assert out["exact_repeat"]["expected"] == 5

def test_invalidated_cohort_excluded():
    runs = [genuine("a1",cohort="exact-repeat"),
            {"run_id":"a2","cohort":"exact-repeat","invalidated":True,"execution_type":"genuine_agent"}]
    out = AC.analyze(runs, expected={"exact_repeat":5})
    assert out["exact_repeat"]["observed"] == 1  # invalidated run excluded

# ---------- small-sample CI ----------
def test_pass_rate_exact_binomial_interval():
    # 4/5 pass → binomial 95% CI is wide (small sample)
    runs = [genuine(f"a{i}",cohort="exact-repeat",verdict="PASS") for i in range(4)] + [genuine("a5",cohort="exact-repeat",verdict="FAIL")]
    out = AC.analyze(runs, expected={"exact_repeat":5})
    lo, hi = out["exact_repeat"]["pass_rate_ci_95"]
    assert 0.0 <= lo <= 0.8 <= hi <= 1.0  # CI contains the 0.8 point estimate, wide

# ---------- premature completion / recovery / intervention classes ----------
def test_premature_completion_claim_detected():
    runs = [genuine("a1",cohort="exact-repeat",verdict="FAIL",premature=True)]
    out = AC.analyze(runs, expected={"exact_repeat":5})
    assert out["premature_completion_claim_rate"] == 1.0

def test_autonomous_recovery_classified():
    runs = [genuine("a1",cohort="controlled-robustness",verdict="PASS",recovered=True)]
    out = AC.analyze(runs)
    assert out["controlled_robustness"]["autonomous_recovery_rate"] == 1.0

def test_intervention_classification():
    runs = [genuine("a1",cohort="exact-repeat",intervention="minor"),
            genuine("a2",cohort="exact-repeat",intervention="critical"),
            genuine("a3",cohort="exact-repeat",intervention="none")]
    out = AC.analyze(runs)
    assert out["human_intervention_rate"] == pytest.approx(2/3, abs=1e-3)
    assert out["critical_intervention_rate"] == pytest.approx(1/3, abs=1e-3)
    # autonomous_SUCCESSFUL only counts PASS-without-intervention
    assert out["autonomous_successful_completion_rate"] == pytest.approx(1/3, abs=1e-3)
    # pipeline_execution_completion: all 3 ran the pipeline (genuine_agent), regardless of verdict
    assert out["pipeline_execution_completion_rate"] == pytest.approx(1.0, abs=1e-3)

# ---------- corrected metric semantics (owner directive) ----------
def test_pipeline_complete_but_all_fail():
    """5 runs that execute the pipeline but FAIL: pipeline completion 1.0, autonomous SUCCESSFUL 0.0."""
    runs = [genuine(f"a{i}",cohort="exact-repeat",verdict="FAIL") for i in range(5)]
    out = AC.analyze(runs, expected={"exact_repeat":5})
    assert out["pipeline_execution_completion_rate"] == 1.0
    assert out["autonomous_successful_completion_rate"] == 0.0  # zero PASS-without-intervention
    assert out["final_pass_rate"] == 0.0

def test_consistent_failure_is_not_high_quality():
    """Consistent failure (σ=0, all FAIL) must NOT be interpreted as high consistency-quality."""
    runs = [genuine(f"a{i}",cohort="exact-repeat",verdict="FAIL",recall=39.3) for i in range(5)]
    out = AC.analyze(runs, expected={"exact_repeat":5})
    # run_consistency observed (from Cohort A) BUT quality is poor
    assert "run_consistency" in out["hrs"]["observed_dimensions"]
    assert out["exact_repeat"]["std"] == 0.0  # perfectly consistent...
    assert out["final_pass_rate"] == 0.0       # ...in failing
    assert out["autonomous_successful_completion_rate"] == 0.0

def test_run_consistency_observed_from_cohort_a():
    """Run-consistency evidence comes from Cohort A exact-repeat (≥2 runs), NOT only Cohort B."""
    runs = [genuine("a1",cohort="exact-repeat",recall=90),genuine("a2",cohort="exact-repeat",recall=92)]
    out = AC.analyze(runs)
    assert "run_consistency" in out["hrs"]["observed_dimensions"]

def test_autonomous_successful_requires_pass_and_no_intervention():
    """PASS + intervention = not autonomous_successful; FAIL + no intervention = also not."""
    runs = [genuine("a1",cohort="exact-repeat",verdict="PASS",intervention="minor"),  # PASS but intervened
            genuine("a2",cohort="exact-repeat",verdict="FAIL",intervention="none"),  # no intervention but FAIL
            genuine("a3",cohort="exact-repeat",verdict="PASS",intervention="none")]  # genuine success
    out = AC.analyze(runs)
    assert out["autonomous_successful_completion_rate"] == pytest.approx(1/3, abs=1e-3)
