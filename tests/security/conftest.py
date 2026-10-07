"""Conftest do tests/security/.

`test_rate_limit_phase5a.py` é um runner standalone (chama sys.exit() no
nível de módulo) e quebra a coleta do pytest. Segue o mesmo padrão de
`tests/smoke/conftest.py`.
"""

collect_ignore_glob = ["test_rate_limit_phase5a.py"]
