# Fixed accounting comparison: manufacturing energy exposure

29 October 2026. This specific protocol precedes full-panel retrieval and all decomposition, ranking or outcome summaries. Earlier source discovery inspected only Germany-2023 dimension labels and availability counts. It did not rank or summarise numerical outcomes.

## Decision and measured scope

For an analyst screening manufacturing energy exposure, determine how much the interpretation of energy-use change and industry rankings depends on nominal versus price-controlled gross output. The original program outline proposed separating production changes from price-driven expenditure changes. These sources do not observe energy expenditure or energy prices; the executable question therefore concerns output-price sensitivity, not energy-bill inflation. This clarification is made before analysis.

Use current historical snapshots of Eurostat env_ac_pefa04 (NETDOM_EUSE, TJ) and nama_10_a64 (P1 gross output, CP_MEUR and PYP_MEUR). Obtain CLV_I15 as a separate official sector-volume cross-check when available. Net domestic energy use includes energy and non-energy uses; it is not interchangeable with final fuel consumption or an energy footprint. The residence/accounting boundary follows the source. Gross output includes intermediate production transactions and is not value added or GDP.

Fix six euro-area countries: BE, DE, ES, FR, IT and NL. Fix years 2015 through 2023. Fix these nineteen non-overlapping NACE Rev.2 groups: C10-C12, C13-C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C25, C26, C27, C28, C29, C30, C31_C32 and C33. Request the aggregate C only for reconciliation, never alongside its children in a sector sum. Country selection is convenient and does not represent all Europe or individual firms.

## Source and coverage gate

Retain exact sequential API responses, request parameters, timestamps, dataset update labels, dimension/code labels, status flags and SHA-256 hashes. Reuse the source only with attribution and a clear modification notice. Never fill missing cells with zero or silently replace suppressed data. No private records or third-party source papers enter Git history.

A country is eligible only if every fixed industry has positive, finite energy and both output measures for every year, and its nineteen-group sums reconcile to the corresponding C aggregate within 2 TJ for energy and 2 million euro for output. These source-accounting allowances reflect published rounding; they are distinct from computational tolerances. Keep every mismatch. Source flags containing break-in-series or definition-difference codes b/d exclude the affected country from the complete-period main comparison; retain the exclusion and flagged observations. Other published flags remain visible. At least four complete countries are required; otherwise retain a source hold without changing these criteria after inspection.

Primary analysis uses only eligible complete countries. Also report the number and energy share of excluded/missing industries/countries where computable. Do not renormalize partial country coverage into a full manufacturing claim. All-source flags and exclusions remain in machine-readable output. Reconciliation checks mapping and internal accounting; it is not independent proof of Eurostat measurement accuracy.

## Accounting estimands and baselines

For an annual transition t-1 to t, use prior-year current-price gross output q0 and current-year previous-year-price output q1, which share the same price basis. Let A=sum(q), s_i=q_i/A, and I_i=E_i/q_i. For positive inputs the exact identity E=sum(A*s_i*I_i) holds. Define logarithmic mean L(x,y)=(x-y)/(log(x)-log(y)), with L(x,x)=x. Additive LMDI contributions are sum_i L(E1_i,E0_i) times the log ratio of A, s_i or I_i. Their sum must equal the observed TJ change.

As a price-naive comparator, repeat the same identity with current-price q1. Both methods reconcile to the same physical energy change but may attribute it differently. Report every annual country effect and the sum of linked annual effects over 2019-2023 and 2015-2023. These sums are in TJ and reconcile to endpoint energy changes. They do not imply constant price-base levels or causal mechanisms.

For each industry, compare annual log intensity change log(E1/E0)-log(q1/q0) using the two output bases. Their difference equals log(CP_t/PYP_t); retain and independently verify that price wedge. Classify opposite signs only when both changes exceed 1e-10 in absolute log units, a numerical zero guard rather than a business-materiality threshold. Report all transitions and magnitudes, including same-sign and near-zero cases.

Build per-industry volume indices by chaining PYP_t/CP_(t-1), starting at 100 in 2015, and verify their growth against the official CLV_I15 series. Never sum chain-linked sector levels: those are generally non-additive. Annual sector shares and additive decompositions instead use matched current/previous-year-price values. Report within-country 2023 top-five industry ranks using energy/CP and energy/PYP, with deterministic code-order tie-breaking; retain all nineteen ranks. Cross-country price-level and product-mix differences limit comparisons even in a common currency.

Source-series comparison clarification, recorded after coverage checks but before any index or outcome calculation: retain every reconstructed-versus-official index difference. Treat a difference above 0.25 index points as an unresolved source-series consistency problem requiring investigation. This is a prespecified practical reconciliation bound, not an official precision guarantee or a fitted threshold. It does not replace the strict computational tolerance for independent reconstruction.

No sampling confidence interval is claimed: these are revised published accounting estimates and a small convenience panel, with no microdata sampling model. Preserve source flags, denominator sensitivity, annual variation and leave-one-industry-out accounting sensitivity. Such sensitivity ranges are not confidence intervals. No engineering efficiency, carbon, energy-cost, firm-level or realized-savings claim follows directly.

## Separation, implementation and independent checks

This is parameter-free descriptive accounting, not a trained prediction system. There are no hyperparameters, fitted coefficients, train/test losses or optimization optima to invent. Develop the implementation using synthetic boundary fixtures and the eligible countries other than Belgium; reserve Belgium's decompositions, intensity contrasts, volume indices and rankings until the code and source accounting are committed. Source-coverage totals and shares use all six countries, including Belgium, solely to describe exclusions. Apply the same frozen analysis code to Belgium if eligible, retaining its reconciliation separately. That is an implementation-transfer check, not a population-generalization test. The source gate admits three development countries; the other two prespecified countries remain excluded rather than being used to fill out development coverage.

Check meaningful equal-value, constant-intensity, activity-only, structure-only, unit-scaling, order-invariance and nonpositive-input cases. A separate standard-library/SQL path must decode every API cell and reconcile the analytic panel. A separate 50-digit Decimal logarithm path must reconstruct every decomposition, price wedge, index, aggregate and rank without importing the main analysis helpers. Require unchanged absolute 1e-7 / relative 1e-9 scientific-value tolerances; do not relax a failed check. Export every source/eligibility observation, annual effect, sector contrast and sensitivity calculation.

## Deliverables and acceptance

Produce the complete reproducible code/data/results package, three original scientific figures, a concise executive first layer and an independent research manuscript with source references and limits. Keep third-party papers and formal-publication projects private. Require source/rights, coverage, separation, independent arithmetic, fresh replay, rendered figures/manuscript, staged privacy and exact-head Linux checks before counting the release. Preserve failed receipts and meaningful Git history, verify merged/tested tree identity and the annotated remote tag, and update the program register. Review remains bounded by the program's three rounds, 45 active review minutes and 60 review tool calls; execution is separate.
