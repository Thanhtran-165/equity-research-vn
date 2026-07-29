"""VTA Phase 3 independent verifier package.

Entry point: :func:`vta_verifier.run_verification`.

Six verification-domain modules, one per category group defined in
vta-phase-3-implementation-scope.yaml Section 7 and vta-VC-to-verifier-mapping.yaml
verifier_module_coverage:

  * formula_conformance   (15 VCs)
  * schema_conformance    (23 VCs)
  * provenance_integrity  (6 VCs)
  * language_policy       (5 VCs)
  * boundary_enforcement  (3 VCs)
  * setup_semantics       (12 VCs)
                          ----------------
                          64 canonical VCs

Independence is asserted in :mod:`common` and re-checked at import time of the
entrypoint.
"""

from .vta_verifier import run_verification, VerificationContext, VERIFIER_VERSION

__all__ = ["run_verification", "VerificationContext", "VERIFIER_VERSION"]
