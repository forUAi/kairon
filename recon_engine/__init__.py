"""
Reconciliation Engine Package

This is the root module for the modular, production-grade reconciliation system used inside Kairon.

Modules Included:
- recon: Orchestration engine for reconciliation jobs
- ledger: Event-sourced ledger reader
- sources: External transaction readers (CSV, API, etc.)
- matchers: Exact and fuzzy matching logic
- api: FastAPI routes for job control and result viewing
- jobs: Async background scheduler for daily execution
- tests: Unit and integration tests for all components
"""

__version__ = "0.1.0"
__author__ = "Vishal (Kairon Core Infra)"
