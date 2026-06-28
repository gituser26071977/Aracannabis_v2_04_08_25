"""Cenário soak — teste de fadiga (100 usuários por 15 min).

Detecta memory leaks no gunicorn worker e fadiga do pool de conexões.

Use:
    locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 15m \\
        --host=https://api.visualsmartflow.com.br \\
        --html reports/load_soak.html \\
        --csv reports/load_soak
"""
