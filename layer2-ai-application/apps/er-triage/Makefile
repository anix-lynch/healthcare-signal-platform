.PHONY: help install smoke drift test classify eval-all eval-rachel eval-traffic-light eval-crystal-ball eval-mad-lib eval-smoke-detector eval-treasure-map eval-police-lineup cloud-test

help:
	@echo "ER3 — seven-lens healthcare triage + multi-cloud adapter"
	@echo ""
	@echo "  Build / setup"
	@echo "    make install               install requirements"
	@echo ""
	@echo "  Per-pattern eval (the 7-lens harness)"
	@echo "    make eval-rachel           Pattern 1 — retrieval (P@K, NDCG, Recall@K)"
	@echo "    make eval-traffic-light    Pattern 2 — classify (acc, F1, calibration)"
	@echo "    make eval-crystal-ball     Pattern 3 — regress (MAE, R², schema validity)"
	@echo "    make eval-mad-lib          Pattern 4 — generate (faithfulness, LLM-judge)"
	@echo "    make eval-smoke-detector   Pattern 5 — anomaly (precision/recall on outliers)"
	@echo "    make eval-treasure-map     Pattern 6 — cluster (silhouette, BERTopic)"
	@echo "    make eval-police-lineup    Pattern 7 — rank (NDCG, MRR, win-rate)"
	@echo "    make eval-all              run every per-pattern eval, write JSON report"
	@echo ""
	@echo "  Smoke / drift / cloud"
	@echo "    make smoke                 ESI auto-tag smoke test (must always pass)"
	@echo "    make drift                 compute drift metrics vs baseline"
	@echo "    make cloud-test            test all 3 CloudProvider implementations"
	@echo "    make test                  run all pytest tests"
	@echo ""
	@echo "  CLI"
	@echo "    make classify              classify a case from stdin"

install:
	pip install -r requirements.txt

# ── Per-pattern eval (7-lens harness) ──
eval-rachel:
	cd ../.. && python -m shared.evaluation.retrieval_eval

eval-traffic-light:
	cd ../.. && python -m shared.evaluation.classify_eval

eval-crystal-ball:
	cd ../.. && python -m shared.evaluation.regress_eval

eval-mad-lib:
	cd ../.. && python -m shared.evaluation.generate_eval

eval-smoke-detector:
	cd ../.. && python -m shared.evaluation.anomaly_eval

eval-treasure-map:
	cd ../.. && python -m shared.evaluation.cluster_eval

eval-police-lineup:
	cd ../.. && python -m shared.evaluation.rank_eval

eval-all: eval-rachel eval-traffic-light eval-crystal-ball eval-mad-lib eval-smoke-detector eval-treasure-map eval-police-lineup
	@echo "→ All 7 pattern evals complete. JSON report at outputs/eval_report.json"

# ── Folded pipelines (from healthcare-rag-guardrails 2026-05-09) ──
gen-qa:
	python scripts/gen_healthcare_qa.py --n 200 --output inputs/healthcare_qa_200.json

run-ragas:
	python scripts/run_ragas_eval.py --qa inputs/healthcare_qa_200.json \
		--output outputs/baseline/ragas_baseline.json

run-redteam:
	python scripts/run_redteam_suite.py --output outputs/baseline/redteam_baseline.json

run-pii-mask:
	python scripts/run_pii_masker.py --input inputs/healthcare_qa_200.json \
		--output outputs/pii_masked_sample.json

run-router:
	cd ../.. && python -m shared.classify.router --queries apps/er-triage/inputs/healthcare_qa_200.json \
		--output apps/er-triage/outputs/baseline/router_baseline.json

baseline-all: run-ragas run-redteam run-router
	@echo "→ All baseline evals re-run. Check outputs/baseline/."

# ── Existing targets ──
smoke:
	pytest tests/test_smoke_esi.py -v

drift:
	cd ../.. && python -m shared.anomaly.drift

cloud-test:
	pytest tests/test_*_provider.py -v

redteam-test:
	pytest tests/red_team/ -v

test:
	pytest tests/ -v

classify:
	python -m classify.esi_classifier
