# Layer 2 AI Application — top-level delegation Makefile
# Most actions delegate to apps/er-triage (the only currently-implemented app)

.PHONY: help eval-all eval-rachel eval-traffic-light eval-crystal-ball eval-mad-lib eval-smoke-detector eval-treasure-map eval-police-lineup smoke drift redteam-test test baseline-all install

help:
	@echo "Layer 2 — AI Application (apps + services + shared)"
	@echo ""
	@echo "  Apps:"
	@echo "    apps/er-triage/                 working — see Makefile in there"
	@echo "    apps/ops-capacity-assistant/    Phase 5 stub"
	@echo "    apps/executive-dashboard/       Phase 5 stub"
	@echo ""
	@echo "  Services (READMEs only — Phase 5 implementations):"
	@echo "    services/rag-api/         services/guardrails-api/"
	@echo "    services/feature-api/     services/analytics-api/"
	@echo ""
	@echo "  Common targets (delegate to apps/er-triage):"
	@echo "    make install              install Python deps"
	@echo "    make eval-all             run all 7 pattern evals"
	@echo "    make smoke                Phase 2 ESI smoke test"
	@echo "    make drift                Phase 3 drift monitor"
	@echo "    make redteam-test         red-team regression gate"
	@echo "    make baseline-all         re-run Ragas + redteam + router baselines"
	@echo "    make test                 all pytest tests"

# All targets below delegate to apps/er-triage
install eval-all eval-rachel eval-traffic-light eval-crystal-ball eval-mad-lib eval-smoke-detector eval-treasure-map eval-police-lineup smoke drift redteam-test test baseline-all:
	@cd apps/er-triage && $(MAKE) $@
