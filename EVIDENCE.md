# Local acceptance evidence

Measured 2026-10-01 on this Windows machine, Python 3.12.10, CPU only.

The installed lra executable ran fixtures, run and report --format md in 0.735710 seconds total (wall clock, process startup included). The complete Markdown report was captured and checked for no traceback. This is local execution timing, not time saved against a baseline.

All 200 dossiers were computed. Exact hand-computed totals: 40 qualified, 160 unqualified, 1,600,000 stated budget pence, 400,000 qualified stated budget pence. Qualified IDs exactly p001 through p040: all planted eligible cases found, zero false positives. These counts measure fixture correctness only; budgets and prospects are synthetic and illustrative.

46 pytest cases passed. Coverage includes empty input, malformed JSON, schema drift, negative/extreme values, duplicate IDs across files, strict dates, Unicode and long text, Windows paths, changed fixture outputs, cached-total tampering, deterministic bytes and atomic write failures. No prohibited long dash characters were found in project source, docs or generated reports.

Evidence-based improvement during build: inspection exposed qualify totals that counted excluded dossiers. Totals and provenance now recompute for the displayed subset, verified by test_qualify_totals_reconcile. Real demand and accuracy remain unmeasured; the two-week verdict is pending.
