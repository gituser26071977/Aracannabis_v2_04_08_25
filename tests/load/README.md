# Testes de Carga — AraOS

Suite Locust para validar a capacidade do backend em produção (VPS).

## Instalação

```bash
pip install -r tests/load/requirements.txt
```

## Cenários Pré-configurados

| Cenário | Usuários | Ramp-up | Duração | Quando usar |
|---------|----------|---------|---------|-------------|
| **baseline** | 50 | 5/s | 5 min | Dia típico — validar capacidade normal |
| **peak** | 200 | 20/s | 3 min | Horário de pico — validar degradação |
| **soak** | 100 | 10/s | 15 min | Detectar memory leaks e fadiga |

## Como rodar

```bash
# criar diretório de relatórios
mkdir -p reports

# 1) baseline
locust -f tests/load/locustfile.py --headless \
  --host=https://api.visualsmartflow.com.br \
  -u 50 -r 5 -t 5m \
  --html reports/load_baseline.html \
  --csv reports/load_baseline

# 2) peak
locust -f tests/load/locustfile.py --headless \
  --host=https://api.visualsmartflow.com.br \
  -u 200 -r 20 -t 3m \
  --html reports/load_peak.html \
  --csv reports/load_peak

# 3) soak
locust -f tests/load/locustfile.py --headless \
  --host=https://api.visualsmartflow.com.br \
  -u 100 -r 10 -t 15m \
  --html reports/load_soak.html \
  --csv reports/load_soak
```

Para rodar com UI (debug):
```bash
locust -f tests/load/locustfile.py --host=https://api.visualsmartflow.com.br
# abrir http://localhost:8089
```

## Usuário usado

Por padrão, `locustfile.py` usa o usuário de teste:
- Email: `tester.modulos@araos.dev`
- Senha: `Tester@2025`

Para usar outro usuário, sobrescreva via env:
```bash
LOAD_TEST_EMAIL=outro@dominio.com LOAD_TEST_PASSWORD=outrasenha locust ...
```

## Endpoints exercitados

| Endpoint | Peso | Por quê |
|----------|------|---------|
| `GET /api/dashboard/stats` | 20 | Mais comum (tela inicial) |
| `GET /api/pacientes` | 15 | Lista de pacientes |
| `GET /api/pacientes/<id>` | 10 | Detalhe de paciente |
| `GET /api/consultas` | 8 | Agenda do dia |
| `GET /api/modulos` | 7 | Tela de módulos |
| `GET /api/planos` | 6 | Tela de planos |
| `GET /api/status` | 5 | Health check público |
| `GET /api/catalogo/produtos` | 4 | Catálogo |
| `GET /api/prescricoes` | 3 | Lista de prescrições |
| `GET /api/evolucoes` | 3 | Lista de evoluções |
| `GET /api/billing/resumo` | 2 | Resumo de cobrança |
| `GET /api/meus-modulos/<slug>` | 1 | Detalhe de módulo |

## Interpretação dos resultados

Métricas-chave em `reports/*.csv`:

- **RPS Total** (linha `Aggregated`): Sustentado vs. pico
- **p95/p99** por endpoint: latência no percentil 95/99
- **Failure Count**: requests com status 4xx/5xx ou timeout
- **Median Response Time**: latência mediana

### Critérios de aprovação sugeridos

| Cenário | p95 aceitável | Failure rate aceitável |
|---------|---------------|------------------------|
| baseline | < 500ms | < 1% |
| peak | < 2000ms | < 5% |
| soak | < 800ms | < 2% |

Se o teste de **peak** mostrar `> 50%` de erro 502/503/504, indica que o
backend atingiu o limite do pool de conexões PostgreSQL (ver
`config.py:pool_size`).

## Arquivos gerados

```
reports/
├── load_baseline.html       # relatório visual interativo
├── load_baseline_stats.csv  # stats por endpoint
├── load_baseline_failures.csv # falhas detalhadas
├── load_baseline_*.csv      # histórico
└── ...
```
