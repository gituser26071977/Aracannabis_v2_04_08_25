# HARDENING-4 — Patient Pagination

**Date:** 2026-06-02  
**Status:** NOT IMPLEMENTED  
**Risk:** MEDIUM (performance at scale)  
**Recommendation:** IMPLEMENT before production deployment

---

## Problem

`GET /api/pacientes` returns **all patients** as `.all()` without pagination.

### Current Code (routes/pacientes.py)

```python
@jwt_required()
def listar_pacientes():
    pacientes = Paciente.query.all()
    return jsonify([p.to_dict() for p in pacientes])
```

## Impact

| Scenario | Impact |
|----------|--------|
| 100 patients | ~50KB response, ~100ms |
| 1,000 patients | ~500KB response, ~500ms |
| 10,000 patients | ~5MB response, ~5s, potential OOM |
| 100,000 patients | ~50MB response, timeout/OOM |

## Proposed Solution

### Option A: Offset/Limit Pagination (Recommended — simplest)

```python
@jwt_required()
def listar_pacientes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)  # Max 100
    
    pagination = Paciente.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
        'per_page': pagination.per_page
    })
```

### Option B: Cursor Pagination (for very large datasets)

```python
@jwt_required()
def listar_pacientes():
    cursor = request.args.get('cursor')
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    query = Paciente.query.order_by(Paciente.id)
    if cursor:
        query = query.filter(Paciente.id > int(cursor))
    
    items = query.limit(per_page + 1).all()
    next_cursor = items[-1].id if len(items) > per_page else None
    
    return jsonify({
        'items': [p.to_dict() for p in items[:per_page]],
        'next_cursor': next_cursor
    })
```

## Recommendation

**Implement Option A** now. It:
- Uses SQLAlchemy built-in pagination
- Compatible with existing frontend
- Simple `page`/`per_page` query params
- Enforces max `per_page` guardrail

## MeshOS Replay Impact

- Replay will use `page` parameter to iterate patients
- Default `per_page=50` is sufficient for typical deployments
- No change to `to_dict()` serialization

## Success Criteria

- [ ] `GET /api/pacientes` accepts `page` and `per_page` query params
- [ ] Default `per_page=50`, max `per_page=100`
- [ ] Response includes `items`, `total`, `pages`, `page`, `per_page`
- [ ] Backward compatible: `page=1` without params returns first 50
- [ ] Tests verify pagination behavior
