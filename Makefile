# Makefile for MediMitra API and frontend orchestration

.PHONY: test-api run-backend run-frontend

run-backend:
	cd medimitra-backend && python run_backend.py

run-frontend:
	cd medimitra-frontend && python run_frontend.py

test-api:
	cd medimitra-backend && keploy test -c "python run_backend.py"
