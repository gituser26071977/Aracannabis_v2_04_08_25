# HARDENING-2 — Evolution Audit Timestamps

**Date:** 2026-06-02  
**Status:** COMPLETE  
**Risk Before:** HIGH (missing replay timestamps)  
**Risk After:** LOW

---

## Problem

`Evolucao` model had only `data_evolucao` (business date). No `created_at` or `updated_at` system timestamps.

## Impact on Replay

- Could not determine when an evolution was first persisted
- Could not detect modifications after creation
- Replay ordering relied solely on business date, which may differ from system time

## Changes Made

### File: `models.py`

```python
class Evolucao(db.Model):
    # ... existing fields ...
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### Updated `to_dict()`

```python
def to_dict(self):
    return {
        # ... existing fields ...
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
```

### Migration: `migrations/versions/REDACTED.py`

```python
with op.batch_alter_table('evolucoes', schema=None) as batch_op:
    batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
    batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
```

## Backward Compatibility

- `created_at` and `updated_at` are nullable
- Existing records will have `NULL` until backfilled or modified
- `to_dict()` safely handles `None` with conditional `isoformat()`

## Database Migration Status

**Applied on:** PostgreSQL `localhost:5434/aracannabis` via Alembic  
**Command:** `flask db upgrade`  
**Result:** ✅ SUCCESS — `created_at`/`updated_at` columns confirmed in `evolucoes` table

## Test Coverage

| Test | Status |
|------|--------|
| `test_evolucao_tem_created_at` | ✅ PASS |
| `REDACTED` | ✅ PASS |

**Test Execution:** `25 passed, 370 warnings in 13.84s`

## Success Criteria

- [x] `created_at` added to `Evolucao`
- [x] `updated_at` added to `Evolucao`
- [x] `to_dict()` includes timestamps
- [x] Migration created
- [x] Backward compatibility preserved
- [x] Tests pass
