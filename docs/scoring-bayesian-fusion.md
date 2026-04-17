# Bayesian fusion — design slice (`verifiedsignal_bayes_v1`)

This document specifies a **first incremental slice** of Bayesian-style fusion for **`document_scores`**, aligned with the existing pipeline (**heuristic** always, **HTTP** optional) and the **`scoring-http.md`** contract.

## 1. Goal (slice scope)

Produce a **single interpretable posterior** for “how synthetic-like is this document?” by combining:

1. **Heuristic** row: **`verifiedsignal_heuristic`** (already canonical unless HTTP promotion replaced it).
2. **HTTP** row when present: **`verifiedsignal_http`** with **`job_status: completed`** and usable **`ai_generation_probability`** (and optionally **`confidence_score`**).

**Out of scope for v1:** extra signals (metadata tags, extract stats, second remote model), learned calibration layers, per-collection priors from rollups (see §8). Those attach later as additional likelihood terms or as empirical priors.

**Deliverable:** a new **`document_scores`** row with **`scorer_name = verifiedsignal_bayes_v1`**, **`scorer_version = 1.0.0`**, **`score_schema_version = 1`**, storing the **fused** scalars in the same columns the UI/API already use (**`ai_generation_probability`**, **`factuality_score`**, **`confidence_score`**) plus a **rich `score_payload`** for audit and replay.

---

## 2. Event definition (binary v1)

**Hypothesis \(H_1\):** “document is synthetic / AI-generated (for product purposes).”  
**Complement \(H_0\):** “not \(H_1\)” (human or benign mixed; we do not distinguish sub-classes in v1).

All probabilities below are **\(P(H_1 \mid \cdot)\)** unless noted.

---

## 3. Math: log-odds fusion (independent signals, v1)

### 3.1 Log-odds form

Let \(\pi_0 = P(H_1)\) be the **prior** (config; see §5).  
Log-odds prior: \(\ell_0 = \log\frac{\pi_0}{1-\pi_0}\).

For each **signal** \(i\) that outputs a **probability estimate** \(p_i \approx P(H_1 \mid \text{signal}_i)\) (see §4 for mapping), define the **evidential log-odds increment**:

\[
\Delta_i = \log\frac{p_i}{1-p_i} - \ell_0
\]

Interpretation: shift from **prior** log-odds to **posterior** log-odds **if** that signal were the only observation and were **perfectly calibrated**.

### 3.2 Naïve combination (v1 default)

Assume **conditional independence** of signals given \(H_0\) vs \(H_1\) (naïve Bayes on log-odds):

\[
\ell_{\text{fused}} = \ell_0 + \Delta_{\text{heuristic}} + \Delta_{\text{http}}
\]

If HTTP is **missing** or not completed, use **only** \(\Delta_{\text{heuristic}}\) (still emit a fusion row so operators get one consistent “fused” channel).

Convert back:

\[
p_{\text{fused}} = \sigma(\ell_{\text{fused}}) = \frac{1}{1 + e^{-\ell_{\text{fused}}}}
\]

**Clamp** \(p_{\text{fused}}\) to **[0.001, 0.999]** before persisting as **`ai_generation_probability`** to avoid infinite log-odds in storage while staying honest that extremes are uncertain.

### 3.3 Optional: down-weight a source

If **`confidence_score`** (or HTTP **`metadata.calibration`** later) should temper a term, v1 can apply a **damping factor** \(\lambda_i \in [0, 1]\):

\[
\ell_{\text{fused}} = \ell_0 + \lambda_h \Delta_{\text{heuristic}} + \lambda_r \Delta_{\text{http}}
\]

**v1 defaults:** \(\lambda_h = 1\), \(\lambda_r = 1\) if HTTP completed; if HTTP returns **`confidence_score`**, set \(\lambda_r = \texttt{clamp}(\texttt{confidence\_score}, 0.25, 1)\) so low-confidence remotes contribute less.

---

## 4. Mapping scores to \(p_i\) (calibration stance)

### 4.1 Heuristic (`verifiedsignal_heuristic`)

The heuristic **`ai_generation_probability`** is a **deliberately rough** proxy (lexical diversity). For fusion:

- **v1 rule:** use **`row.ai_generation_probability` as \(p_h\)** directly when present.
- **`score_payload`** already carries **`method: heuristic_v1`** and ratios — copy into fusion payload for traceability.

**Risk:** double-counting if heuristic is miscalibrated. **Mitigation in v1:** document in **`score_payload.warnings`**; later slice adds **Platt scaling** or **isotonic** fit on a labeled dev set.

### 4.2 HTTP (`verifiedsignal_http`)

When **`job_status === completed`** and **`ai_generation_probability`** is set:

- **v1 rule:** use **`ai_generation_probability` as \(p_r\)**.
- If only **`factuality_score`** is present, **do not** invent \(p_r\) in v1 — skip HTTP term and set **`score_payload.http_skipped_reason`**.

Operator expectation: remote scorers should move toward **reasonably calibrated** \(P(H_1)\) per **`external-scorer-implementation-guide.md`**.

---

## 5. Prior \(\pi_0\) (configuration)

| Source | Variable | Default | Notes |
|--------|----------|---------|--------|
| Global prior | **`BAYES_FUSION_PRIOR_AI_PROB`** | **0.15** | Base rate “synthetic” for corpus; conservative. |
| Future | collection rollup | — | Replace or blend with **`collection_id`**-specific prior (§8). |

Prior is **not** a secret; store **`score_payload.prior`** as **`{ "pi0": 0.15, "source": "global_env" }`**.

---

## 6. Row semantics (`document_scores`)

### 6.1 New row

| Column | Value |
|--------|--------|
| **`scorer_name`** | **`verifiedsignal_bayes_v1`** |
| **`scorer_version`** | **`1.0.0`** (bump when formula or mapping changes) |
| **`is_canonical`** | **`false` by default**; set **`true`** only when **`BAYES_FUSION_PROMOTE_CANONICAL=true`** (mirrors HTTP promotion pattern). |
| **`ai_generation_probability`** | **`p_fused`** |
| **`factuality_score`** | **v1:** `1 - p_fused` **or** leave **`null`** if product prefers not to overload factuality; **recommendation:** set **`1 - p_fused`** only when no dedicated factuality fusion exists — **better:** **`null`** in v1 to avoid lying; UI continues to show heuristic factuality elsewhere until a real fusion rule exists. **Decision for slice:** **`factuality_score = null`**, **`fallacy_score = null`**, focus fused signal on **`ai_generation_probability`**. |
| **`confidence_score`** | **`min(heuristic.confidence, http.confidence)`** when both exist; else the one present; default **0.5** if heuristic fixed **0.35** only. |

### 6.2 `score_payload` (required keys)

```json
{
  "kind": "bayes_fusion_v1",
  "prior": { "pi0": 0.15, "source": "global_env" },
  "log_odds": {
    "prior": -1.7346,
    "delta_heuristic": 0.42,
    "delta_http": 0.91,
    "fused": -0.40
  },
  "p_inputs": {
    "heuristic_ai_prob": 0.62,
    "http_ai_prob": 0.78
  },
  "lambdas": { "heuristic": 1, "http": 1 },
  "document_score_ids": {
    "heuristic": "uuid-or-null",
    "http": "uuid-or-null"
  },
  "content_fingerprint": "same as HTTP idempotency when http used; else heuristic fingerprint",
  "warnings": []
}
```

---

## 7. When fusion runs (orchestration)

**Trigger (recommended):** at the **end** of **`run_score_document_sync`** after:

- HTTP path **finishes** (success or terminal failure), **or**
- HTTP **skipped** (stub / no URL) — still compute **heuristic-only** fusion so behavior is uniform.

**Alternative (second PR):** separate ARQ job **`fuse_document_scores`** to avoid lengthening HTTP worker transactions; v1 can stay **inline** for simplicity.

**Idempotency:** before insert, check for existing **`verifiedsignal_bayes_v1`** row with same **`content_fingerprint`** and same **input score row ids** (or same **`score_payload.input_hash`**). If present, **skip** (ARQ retry-safe).

---

## 8. Canonical policy & UX

- **Default:** fusion row **`is_canonical = false`**; **heuristic** (or HTTP-promoted row) remains the canonical row for **collection analytics** until operators trust fusion.
- **`BAYES_FUSION_PROMOTE_CANONICAL=true`:** demote all other rows for that **`document_id`**, set fusion **`is_canonical = true`** (same pattern as **`SCORE_API_PROMOTE_CANONICAL`**).

**API / web:** document detail already surfaces **canonical** score; add a **non-breaking** optional block “Fused (Bayes v1)” when a non-canonical fusion row exists, or promote and keep one canonical only.

---

## 9. Future extensions (not in slice)

| Extension | Idea |
|-----------|------|
| **Collection prior** | Use **`collection_analytics_service`** fraction of high-**`ai_generation_probability`** docs as empirical \(\pi_0\) with smoothing. |
| **More likelihoods** | Metadata tags, entropy, language-model detectors — each adds \(\Delta_i\) with learned \(\lambda_i\). |
| **Calibration layer** | Fit **`p_i → calibrated`** on held-out labels; store calibration version in **`scorer_version`**. |
| **Correlated signals** | Replace naïve sum with **low-rank covariance** or **simple discount** (e.g. multiply total \(\Delta\) by 0.85). |

---

## 10. Testing

| Test | Intent |
|------|--------|
| **Unit** | \(\ell\) arithmetic, clamp, missing HTTP branch, \(\lambda\) from confidence. |
| **Integration** | Pipeline + HTTP mock → three rows (heuristic, http, bayes); assert **`p_fused`** orderings on fixed inputs. |
| **Idempotency** | Second worker run does not duplicate fusion row. |

---

## 11. Implementation status (v1)

| Piece | Location |
|-------|----------|
| Math + DB insert | **`app/services/bayes_fusion_score.py`** — `compute_fused_ai_probability`, `apply_bayes_fusion` |
| Config | **`BAYES_FUSION_ENABLED`**, **`BAYES_FUSION_PRIOR_AI_PROB`**, **`BAYES_FUSION_PROMOTE_CANONICAL`** in **`app/core/config.py`** |
| Orchestration | **`app/services/score_document_worker.py`** — after stub/HTTP, **`session.flush()`** then **`apply_bayes_fusion`** |
| Tests | **`tests/unit/test_bayes_fusion_score.py`**, **`tests/integration/test_score_http_worker.py`** (fusion cases) |

**Optional later:** UI surfacing of **`score_payload.log_odds`**, OpenAPI “explain score” route.

---

## 12. Summary

**Slice = one new scorer row** that combines **heuristic** and **optional HTTP** **`ai_generation_probability`** via **log-odds naïve Bayes** with a **configurable prior**, full **audit JSON**, **idempotency**, and **conservative canonical policy**. No DB migration required if existing **`document_scores`** columns and **`score_payload`** JSONB suffice.
