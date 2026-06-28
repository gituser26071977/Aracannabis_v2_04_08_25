"""Cenário baseline — dia típico (50 usuários simultâneos por 5 min).

Use:
    locust -f tests/load/locustfile.py --headless -u 50 -r 5 -t 5m \\
        --host=https://api.visualsmartflow.com.br \\
        --html reports/load_baseline.html \\
        --csv reports/load_baseline
"""
