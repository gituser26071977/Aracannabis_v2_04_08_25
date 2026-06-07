# Rate Limit Strategy Review

**Date:** 2026-06-02  
**Status:** REVIEWED  
**Risk:** MEDIUM (single-process only)  
**Recommendation:** UPGRADE before production deployment

---

## Current Configuration

```python
# app.py
limiter = Limiter(
    key_func=lambda: request.headers.get("X-Association-ID", "global"),
    storage_uri="memory://"
)
```

## Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Per-tenant limiting | ✅ OK | Uses `X-Association-ID` as key |
| Default limits | ✅ OK | 200/minute general, 10/minute auth |
| Storage | ⚠️ WARNING | `memory://` — single process only |
| Multi-worker deployment | ❌ FAIL | Each worker has independent counter |
| Restart persistence | ❌ FAIL | Counters reset on restart |
| Horizontal scaling | ❌ FAIL | Cannot share state across instances |

## Impact on MeshOS Replay

- Replay reads are lightweight (GET requests)
- Replay rate is controlled by MeshOS driver
- **Current limits:** 200 req/min general, 10 req/min auth
- **Replay impact:** LOW (replay will stay well below 200/min)

## Recommended Upgrades

### Short Term (Pre-Production)

**Option A: Redis-backed storage (Recommended)**

```python
limiter = Limiter(
    key_func=lambda: request.headers.get("X-Association-ID", "global"),
    storage_uri="redis://localhost:6379/0"
)
```

Requirements:
- Redis server (already used for Celery/background tasks)
- Minimal code change
- Shared state across workers

### Medium Term

**Option B: Per-endpoint fine-tuning**

```python
# Strict for writes, relaxed for reads
@limiter.limit("10/minute")  # POST /api/pacientes
@limiter.limit("50/minute")  # POST /api/exames
@limiter.limit("500/minute") # GET /api/pacientes (replay)
```

### Long Term

**Option C: Adaptive rate limiting**

- Monitor actual usage patterns
- Adjust limits based on tenant subscription tier
- Add burst allowance for legitimate traffic spikes

## Migration Path

1. **NOW:** Document current behavior (this document)
2. **Before prod:** Switch to Redis storage
3. **Post-prod:** Fine-tune per-endpoint limits
4. **Ongoing:** Monitor and adjust

## Success Criteria

- [ ] Rate limits shared across all workers
- [ ] Counters survive restart
- [ ] MeshOS replay not throttled under normal conditions
- [ ] Alerts on rate limit violations
