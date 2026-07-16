"""
analyze_cohort.py — Genuine-agent cohort analyzer (agent-eval §IX–XIII).

HONESTY RULES (enforced):
  - Only runs with execution_type=='genuine_agent' count. NO_MODEL_BOUND / dry / synthetic /
    deterministic_workflow are EXCLUDED from every agent KPI denominator.
  - 0/0 is NEVER 0% — it returns 'N/A' and the cohort status becomes INCONCLUSIVE_NO_GENUINE_RUNS.
  - 5 NO_MODEL_BOUND records are NOT 5 agent failures (critical_failure_rate stays N/A, not 1.0).
  - run-consistency computed from Cohort A (exact-repeat) ONLY; recovery from Cohort B ONLY.
  - HRS coverage gate: <70% observed dimensions → status PRELIMINARY, decision_eligible false.
  - Critical hard-gate violation → production_status FAIL regardless of mean HRS.
  - Small-sample: bootstrap + exact binomial CI; never render X/N as '100% success probability'.
"""
import json, math, statistics, itertools

GENUINE = "genuine_agent"

def _is_genuine(r):
    return r.get("execution_type")==GENUINE and not r.get("invalidated")

def _recall(r):
    v = r.get("recall_pct")
    if v is None:  # runner records it nested under validator_results
        v = r.get("validator_results",{}).get("recall_pct")
    return v if isinstance(v,(int,float)) else None

def _cohort(runs, name):
    return [r for r in runs if r.get("cohort")==name and _is_genuine(r)]

def _pass_rate(rs):
    if not rs: return "N/A"
    p = sum(1 for r in rs if r.get("final_verdict")=="PASS")
    return p/len(rs)

def _mean(rs, key):
    vals = [_recall(r) if key=="recall" else r.get(key) for r in rs]
    vals = [v for v in vals if isinstance(v,(int,float))]
    return statistics.fmean(vals) if vals else None

def _std(rs):
    vals = [_recall(r) for r in rs]
    vals = [v for v in vals if isinstance(v,(int,float))]
    return statistics.pstdev(vals) if len(vals)>1 else 0.0

def _binom_ci(passes, n, conf=0.95):
    """Exact Clopper-Pearson binomial interval for a pass rate (small-sample honest)."""
    if n==0: return (None,None)
    import math
    alpha = 1-conf
    def betaincinv(p, a, b):
        # incomplete beta inverse via brute bisection (no scipy) — sufficient precision for CI bounds
        # using a regularized incomplete-beta approximation
        try:
            from scipy.stats import beta as _b; return _b.ppf(p,a,b)
        except Exception:
            return None
    lo = betaincinv(alpha/2, passes, n-passes+1) if passes>0 else 0.0
    hi = betaincinv(1-alpha/2, passes+1, n-passes) if passes<n else 1.0
    return (round(lo,4) if lo is not None else None, round(hi,4) if hi is not None else None)

def _bootstrap_ci(rs, n_boot=2000, seed=42):
    vals=[_recall(r) for r in rs]; vals=[v for v in vals if isinstance(v,(int,float))]
    if len(vals)<2: return (None,None)
    import random; rng=random.Random(seed); stats=[]
    for _ in range(n_boot):
        s=[vals[rng.randrange(len(vals))] for _ in vals]; stats.append(statistics.fmean(s))
    stats.sort()
    return (round(stats[int(0.025*n_boot)],4), round(stats[min(n_boot-1,int(0.975*n_boot))],4))

def _hrs_coverage(cohort_runs):
    """How many of the 6 HRS dimensions have evidence from the observed runs."""
    dims = {"spec_adherence":False,"workflow_adherence":False,"validation_discipline":False,
            "output_conformity":False,"recovery_robustness":False,"run_consistency":False}
    for r in cohort_runs:
        if r.get("final_verdict") is not None: dims["validation_discipline"]=True
        if r.get("phases_completed",0)>=1: dims["workflow_adherence"]=True
        if _recall(r) is not None: dims["spec_adherence"]=True
        if r.get("artifacts"): dims["output_conformity"]=True
        if r.get("recovered_from_error"): dims["recovery_robustness"]=True
    if len(cohort_runs)>=2: dims["run_consistency"]=True
    return (sum(dims.values())/6*100, dims)

# HRS dimension weights (sum=1.0) — locked in protocol
HRS_WEIGHTS = {"spec_adherence":0.30,"workflow_adherence":0.20,"validation_discipline":0.20,
               "output_conformity":0.10,"recovery_robustness":0.10,"run_consistency":0.10}

def _hrs_value(cohort_runs, dims_observed):
    """Compute the HRS VALUE (0-100) from observed-dimension scores, separate from coverage.
    FIX #1: 'publishable' only means coverage suffices; the value can still be low."""
    n = len(cohort_runs) or 1
    recalls = [_recall(r) for r in cohort_runs]; recalls = [v for v in recalls if isinstance(v,(int,float))]
    dim_scores = {}
    # spec_adherence: mean recall (capped 0-100)
    dim_scores["spec_adherence"] = statistics.fmean(recalls) if recalls else None
    # workflow_adherence: fraction of phases_completed/9
    dim_scores["workflow_adherence"] = (statistics.fmean([r.get("phases_completed",0) for r in cohort_runs])/9*100) if cohort_runs else None
    # validation_discipline: 100 if verifier ran and no premature claims, else scaled
    premature = sum(1 for r in cohort_runs if r.get("completion_claimed") and r.get("final_verdict")!="PASS")
    dim_scores["validation_discipline"] = (100 * (1 - premature/n)) if cohort_runs else None
    # output_conformity: fraction with an artifact
    dim_scores["output_conformity"] = (100*sum(1 for r in cohort_runs if r.get("artifacts"))/n) if cohort_runs else None
    # recovery_robustness: only if any run had a recoverable error
    recovable = [r for r in cohort_runs if r.get("recovered_from_error") is not None]
    dim_scores["recovery_robustness"] = (100*sum(1 for r in recovable if r.get("recovered_from_error"))/len(recovable)) if recovable else None
    # run_consistency: 100 - normalized std (lower variance → higher consistency-quality)
    if len(recalls)>=2:
        std = statistics.pstdev(recalls)
        dim_scores["run_consistency"] = max(0.0, 100 - std*2)  # σ=0→100, σ=50→0
    else:
        dim_scores["run_consistency"] = None
    # weighted value over OBSERVED dims only
    observed = {k: dim_scores[k] for k in dims_observed if dims_observed[k] and dim_scores.get(k) is not None}
    w_mass = sum(HRS_WEIGHTS[k] for k in observed)
    value = sum(HRS_WEIGHTS[k]*observed[k] for k in observed)/w_mass if w_mass>0 else None
    return round(value,2) if value is not None else None, dim_scores

def _intervention(runs):
    if not runs: return {k:"N/A" for k in ["human_intervention_rate","minor_intervention_rate","major_intervention_rate","critical_intervention_rate","autonomous_successful_completion_rate","pipeline_execution_completion_rate"]}
    n=len(runs) or 1
    def rate(sev): return sum(1 for r in runs if r.get("human_intervention",{}).get("severity")==sev)/n
    none=rate("none"); minor=rate("minor"); major=rate("major"); critical=rate("critical")
    # autonomous SUCCESSFUL = PASS AND no intervention (the corrected semantic; old name conflated with pipeline completion)
    autonomous_successful = sum(1 for r in runs if r.get("final_verdict")=="PASS" and r.get("human_intervention",{}).get("severity")=="none")/n
    # pipeline EXECUTION completion = ran the genuine pipeline regardless of verdict (all `runs` here are genuine)
    pipeline_complete = sum(1 for r in runs if r.get("phases_completed",0)>=1)/n
    return {"human_intervention_rate":round(minor+major+critical,4),
            "minor_intervention_rate":round(minor,4),"major_intervention_rate":round(major,4),
            "critical_intervention_rate":round(critical,4),
            "autonomous_successful_completion_rate":round(autonomous_successful,4),
            "pipeline_execution_completion_rate":round(pipeline_complete,4)}

def analyze(runs, expected=None):
    expected = expected or {}
    exp_a = expected.get("exact_repeat",5); exp_b = expected.get("controlled_robustness",5)
    gen = [r for r in runs if _is_genuine(r)]
    a = _cohort(runs,"exact-repeat"); b = _cohort(runs,"controlled-robustness")
    overall_status = "OK" if gen else "INCONCLUSIVE_NO_GENUINE_RUNS"

    # hard gates: any critical violation across genuine runs → FAIL
    critical_violations = sorted({v for r in gen for v in (r.get("hard_gate_violations") or [])})
    hg_status = "FAIL" if critical_violations else ("PASS" if gen else "NOT_EVALUATED")

    # premature completion: claimed complete while final_verdict FAIL
    premature = sum(1 for r in gen if r.get("completion_claimed") and r.get("final_verdict")!="PASS")
    premature_rate = premature/len(gen) if gen else "N/A"

    # recovery (Cohort B only): recovered / runs that had a recoverable error
    recov = [r for r in b if r.get("recovered_from_error") is not None or r.get("final_verdict")]
    recovered = sum(1 for r in b if r.get("recovered_from_error"))
    recoverable = sum(1 for r in b if r.get("recovered_from_error") is True or (r.get("final_verdict")=="PASS"))
    auto_recovery = recovered/recoverable if recoverable else ("N/A" if b else "N/A")

    # HRS: coverage (evidence sufficiency) AND value (actual score) — SEPARATE (FIX #1).
    # Publishable ≠ good; publishable only means coverage ≥ threshold.
    cov_pct, cov_dims = _hrs_coverage(a if a else gen)
    hrs_value, hrs_dim_scores = _hrs_value(a if a else gen, cov_dims)
    hrs_status = "PRELIMINARY" if cov_pct<70 else "PUBLISHABLE"
    hrs_confidence = "HIGH" if cov_pct==100 else ("MEDIUM" if cov_pct>=70 else "LOW")

    interv = _intervention(gen)

    a_passes = sum(1 for r in a if r.get("final_verdict")=="PASS")
    b_passes = sum(1 for r in b if r.get("final_verdict")=="PASS")

    return {
      "status": overall_status,
      "genuine_runs": len(gen),
      "excluded_runs": len(runs)-len(gen),
      "first_pass_yield": (a_passes/len(a) if a else "N/A"),
      "pipeline_execution_completion_rate": interv["pipeline_execution_completion_rate"],
      "autonomous_successful_completion_rate": interv["autonomous_successful_completion_rate"],
      "_migration_note": "autonomous_completion_rate (old) was split into pipeline_execution_completion_rate (ran pipeline) + autonomous_successful_completion_rate (PASS without intervention). Old name conflated 'ran' with 'succeeded'.",
      "human_intervention_rate": interv["human_intervention_rate"],
      "major_intervention_rate": interv["major_intervention_rate"],
      "critical_intervention_rate": interv["critical_intervention_rate"],
      "premature_completion_claim_rate": premature_rate,
      "critical_failure_rate": (len([r for r in gen if r.get("hard_gate_violations")])/len(gen) if gen else "N/A"),
      "hard_gate_status": hg_status,
      "critical_violations": critical_violations,
      "final_pass_rate": _pass_rate(gen),
      "production_status": "FAIL" if hg_status=="FAIL" else ("PASS" if gen and _pass_rate(gen)==1.0 else "CONDITIONAL" if gen else "N/A"),
      "mean_recall": _mean(gen,"recall"),
      "minimum_recall": min([_recall(r) for r in gen if _recall(r) is not None],default=None),
      "maximum_recall": max([_recall(r) for r in gen if _recall(r) is not None],default=None),
      "std_recall": _std(gen),
      "exact_repeat": {
        "observed":len(a),"expected":exp_a,
        "completeness":"COMPLETE" if len(a)>=exp_a else "INCOMPLETE",
        "final_pass_rate":_pass_rate(a),"mean_recall":_mean(a,"recall"),"std":_std(a),
        "pass_rate_ci_95":_binom_ci(a_passes,len(a)) if a else (None,None),
        "recall_ci_95":_bootstrap_ci(a),
        "minimum_recall":min([_recall(r) for r in a if _recall(r) is not None],default=None),
        "maximum_recall":max([_recall(r) for r in a if _recall(r) is not None],default=None),
      },
      "controlled_robustness": {
        "observed":len(b),"expected":exp_b,
        "completeness":"COMPLETE" if len(b)>=exp_b else "INCOMPLETE",
        "final_pass_rate":_pass_rate(b),"mean_recall":_mean(b,"recall"),
        "autonomous_recovery_rate": auto_recovery,
      },
      "hrs": {"value": hrs_value,
              "evidence_coverage_pct":round(cov_pct,1),
              "confidence": hrs_confidence,
              "status":hrs_status,
              "dimension_scores": hrs_dim_scores,
              "observed_dimensions":[k for k,v in cov_dims.items() if v],
              "unobserved_dimensions":[k for k,v in cov_dims.items() if not v],
              "decision_eligible": hrs_status=="PUBLISHABLE" and hg_status!="FAIL"},
      "small_sample_note": "N≤10; pass-rate CI is wide; X/N is NOT a success-probability statement",
    }

def main():
    import sys, os, glob
    if len(sys.argv)<2:
        print("usage: analyze_cohort.py <runs_dir_or_glob> [expected_a] [expected_b]"); sys.exit(2)
    pat = sys.argv[1]; expected = {"exact_repeat":int(sys.argv[2]) if len(sys.argv)>2 else 5,
                                   "controlled_robustness":int(sys.argv[3]) if len(sys.argv)>3 else 5}
    files = sorted(glob.glob(pat))
    runs = [json.load(open(f)) for f in files]
    out = analyze(runs, expected)
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
