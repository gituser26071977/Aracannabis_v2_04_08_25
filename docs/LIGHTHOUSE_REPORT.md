# LIGHTHOUSE_REPORT — MISSÃO 23

**Data:** 2026-06-25
**Modo:** EXECUTE
**Origem:** M23 FASE 4 — Lighthouse desktop + mobile

---

## Status: ❌ NÃO EXECUTADO

**Motivo:** Lighthouse CLI **NÃO está instalado** no ambiente local.

## Tentativa

```bash
$ which lighthouse
(0 lines — não encontrado)
$ which lhci
(0 linhas)
```

## Artefatos QUE EXISTEM no repositório

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `.lighthouserc.json` | 923B | Thresholds: Perf ≥0.80, A11y ≥0.90, BP recomendado, SEO recomendado |
| `.github/workflows/lighthouse.yml` | 1284B | Pipeline CI para Lighthouse desktop + mobile |

**Configuração encontrada:**
```json
{
  "ci": {
    "collect": {
      "url": [
        "https://staging.visualsmartflow.com.br/",
        "https://staging.visualsmartflow.com.br/login",
        "https://staging.visualsmartflow.com.br/dashboard",
        "https://api.staging.visualsmartflow.com.br/api/status"
      ],
      "numberOfRuns": 3,
      "settings": {
        "preset": "desktop"
      }
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance":     ["error", { "minScore": 0.80 }],
        "categories:accessibility":   ["error", { "minScore": 0.90 }]
      }
    }
  }
}
```

## Por que NÃO executei

1. **Lighthouse CLI ausente** — `npm install -g lighthouse` ou `npx @lhci/cli` não executado.
2. **URLs alvo exigem staging público** — `https://staging.visualsmartflow.com.br/` não está acessível sem DNS/SSL/Traefik em VPS.
3. **Não há alternativa local** — frontend container expõe `http://localhost:3000` mas Lighthouse precisa de HTTPS para métricas confiáveis (exceto `preset: debug`).
4. **Missão 22.2 já corrigiu docs** — POST_DEPLOY_SMOKE §16 removeu teste contra Prometheus/Grafana e não tem teste de Lighthouse.

## O QUE FOI COMPROVADO nesta missão

- Workflow `lighthouse.yml` está estruturado para rodar contra staging público
- Threshold Perf ≥ 0.80 e A11y ≥ 0.90 estão documentados
- 4 URLs são avaliadas por run
- 3 runs são feitas (numberOfRuns=3)

## Recomendação para MISSÃO 24+

Provisionar staging público (VPS + Traefik + Let's Encrypt + DNS) antes de rodar Lighthouse. Lighthouse requer URL pública HTTPS.

**Status final: NÃO COMPROVADO nesta missão.**