"""
scope.py
========
Single source of truth for the POC scope.

Imported by:
  - audit_processed.py    (reporting)
  - run_deterministic.py  (feature labeling)
  - build_analysis_set.py (capping and filtering)

If the scope changes, this is the only file to edit.
"""

MVP_BANKS = {"ING", "KBC", "Belfius", "Revolut", "N26"}
BACKUP_TRAD = {"BNP Paribas Fortis"}
BACKUP_NEO = {"bunq"}
ALL_BACKUPS = BACKUP_TRAD | BACKUP_NEO

# Capping policy for the analysis set
TARGET_YOUTH_PER_BANK = 10
MIN_YOUTH_PER_BANK = 5