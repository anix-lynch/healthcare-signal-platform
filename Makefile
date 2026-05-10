.PHONY: help install eval-all eval-rachel eval-traffic-light eval-crystal-ball eval-mad-lib eval-smoke-detector eval-treasure-map eval-police-lineup smoke drift redteam-test test layer1 layer2 layer3 baseline-all clean

help:
	@echo "healthcare-genai-fullstack — 3-layer enterprise GenAI"
	@echo ""
	@echo "  Per-layer entry points:"
	@echo "    make layer1               cd into layer1-data-backbone (dbt + Power BI + Fabric)"
	@echo "    make layer2               cd into layer2-ai-application (7 patterns + multi-cloud)"
	@echo "    make layer3               cd into layer3-governance (eval + red-team)"
	@echo ""
	@echo "  Layer 2 (AI application) — most-used:"
	@echo "    make install              install Python deps (Layer 2)"
	@echo "    make eval-all             run all 7 pattern evals"
	@echo "    make eval-rachel          ...retrieval"
	@echo "    make eval-traffic-light   ...classify"
	@echo "    make eval-crystal-ball    ...regress"
	@echo "    make eval-mad-lib         ...generate"
	@echo "    make eval-smoke-detector  ...anomaly"
	@echo "    make eval-treasure-map    ...cluster"
	@echo "    make eval-police-lineup   ...rank"
	@echo "    make smoke                Phase 2 ESI auto-tag smoke test"
	@echo "    make drift                Phase 3 drift monitor"
	@echo "    make redteam-test         red-team regression gate (must hold 100%)"
	@echo "    make test                 all pytest tests"
	@echo ""
	@echo "  Layer 3 (governance) — eval baselines:"
	@echo "    make baseline-all         re-run Ragas + redteam + router baselines"

# ── Layer 2 delegation (the primary runtime) ──
layer2:
	@cd layer2-ai-application && pwd && ls

install:
	cd layer2-ai-application && pip install -r requirements.txt

eval-all:
	cd layer2-ai-application && $(MAKE) eval-all

eval-rachel:
	cd layer2-ai-application && $(MAKE) eval-rachel

eval-traffic-light:
	cd layer2-ai-application && $(MAKE) eval-traffic-light

eval-crystal-ball:
	cd layer2-ai-application && $(MAKE) eval-crystal-ball

eval-mad-lib:
	cd layer2-ai-application && $(MAKE) eval-mad-lib

eval-smoke-detector:
	cd layer2-ai-application && $(MAKE) eval-smoke-detector

eval-treasure-map:
	cd layer2-ai-application && $(MAKE) eval-treasure-map

eval-police-lineup:
	cd layer2-ai-application && $(MAKE) eval-police-lineup

smoke:
	cd layer2-ai-application && $(MAKE) smoke

drift:
	cd layer2-ai-application && $(MAKE) drift

redteam-test:
	cd layer2-ai-application && $(MAKE) redteam-test

test:
	cd layer2-ai-application && $(MAKE) test

# ── Layer 3 delegation (governance baselines) ──
layer3:
	@cd layer3-governance && pwd && ls

baseline-all:
	cd layer3-governance && \
		python scripts/02_run_ragas_healthcare.py && \
		python scripts/06_redteam_suite.py && \
		python scripts/03_classifier_router.py

# ── Layer 1 entry (dbt + Power BI workflows are tool-specific) ──
layer1:
	@cd layer1-data-backbone && pwd && ls

# ── Hygiene ──
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
