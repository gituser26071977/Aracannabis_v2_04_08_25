"""Cenário peak — horário de pico (200 usuários por 3 min).

Use:
    locust -f tests/load/locustfile.py --headless -u 200 -r 20 -t 3m \\
        --host=https://api.visualsmartflow.com.br \\
        --html reports/load_peak.html \\
        --csv reports/load_peak
"""
