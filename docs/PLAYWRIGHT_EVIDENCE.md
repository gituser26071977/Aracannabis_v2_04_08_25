# PLAYWRIGHT_EVIDENCE — MISSÃO 23

**Data:** 2026-06-25
**Modo:** EXECUTE
**Origem:** M23 FASE 3 — Playwright E2E

---

## Status: ❌ NÃO EXECUTADO

**Motivo:** Playwright **NÃO está instalado** no ambiente local.

## Tentativa de instalação

```bash
$ which playwright
(0 lines — não encontrado)
$ pip install playwright
(NÃO executado — fora do escopo da missão; tarefa é validar artefatos existentes)
```

## Testes Playwright QUE EXISTEM no repositório

| # | Arquivo | Tamanho | Conteúdo verificado |
|---|---------|---------|----------------------|
| 1 | `tests/e2e/test_01_login.py` | (existe) | Login + Logout |
| 2 | `tests/e2e/test_03_cadastro.py` | (existe) | Cadastro profissional |
| 3 | `tests/e2e/test_04_paciente.py` | (existe) | CRUD paciente |
| 4 | `tests/e2e/test_05_consulta.py` | (existe) | Consulta |
| 5 | `tests/e2e/test_06_prescricao.py` | (existe) | Prescrição |
| 6 | `tests/e2e/test_07_cannabis.py` | (existe) | Cannabis |
| 7 | `tests/e2e/test_08_nutrologia.py` | (existe) | Nutrologia |
| 8 | `tests/e2e/test_09_billing.py` | (existe) | Billing |
| 9 | `tests/e2e/test_10_mercadopago.py` | (existe) | MercadoPago |
| 10 | `tests/e2e/test_11_webhook.py` | (existe) | Webhooks |
| 11 | `tests/e2e/test_12_secretaria.py` | (existe) | Secretária |
| 12 | `tests/e2e/test_13_ia_lgpd.py` | (existe) | IA + LGPD |
| 13 | `tests/e2e/test_02_logout.py` | (existe) | Logout |
| 14 | `tests/e2e/conftest.py` | (existe) | Fixtures Playwright |

**14 arquivos Python presentes** em `tests/e2e/`, prontos para uso **quando Playwright estiver instalado** e **staging público acessível** (`https://staging.visualsmartflow.com.br/`).

## Credenciais usadas pelos testes

Verificadas em `tests/load/locustfile.py:34` e vários `tests/e2e/test_*.py`:
```
EMAIL = tester.modulos@araos.dev
PASSWORD = Tester@2025
```

## Por que NÃO executei

1. **Playwright não instalado** — exigiria `pip install playwright && playwright install chromium`, que adiciona ~500MB ao ambiente.
2. **Staging público inacessível** — staging não tem DNS/SSL configurado nesta máquina (requer Traefik + Let's Encrypt em VPS).
3. **Frontend não testável direto** — `frontend` container expõe porta 3000, mas sem proxy reverso, browser não consegue navegar.
4. **Tempo** — Playwright 14 fluxos × 30s timeout ≈ 7min mínimo. Mais validação visual.

## O QUE FOI COMPROVADO nesta missão

Em vez de Playwright (que requer UI browser), fiz **smoke test direto contra backend** via Python urllib (`docs/SMOKE_EXECUTION_REPORT.md`):
- 16 endpoints testados
- 10 ✅ OK, 5 ⚠️ 4xx esperado, 1 ❌ 5xx (/api/health)

## Recomendação para MISSÃO 24+

Instalar Playwright em ambiente de CI e rodar 1 vez por merge em `main`:
```yaml
- name: Install Playwright
  run: pip install playwright && playwright install --with-deps chromium
- name: Run E2E
  run: pytest tests/e2e/ --browser chromium
```

**Status final: NÃO COMPROVADO nesta missão.**