"""Conftest do tests/smoke/.

Os scripts em tests/smoke/ sao runners standalone (chamam sys.exit() no
nivel de modulo). Nao sao testes pytest. Excluimos da coleta pytables
para evitar o INTERNALERROR durante a descoberta.
"""
import pytest


collect_ignore_glob = ["test_webhook_security.py"]
