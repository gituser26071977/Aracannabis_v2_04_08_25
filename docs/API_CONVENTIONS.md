# API Conventions — AraOS Platform

> **Version:** 1.0.0  
> **Status:** Adopted from Week 11D  
> **Applies to:** All new endpoints. Legacy endpoints migrate gradually.

---

## 1. Response Envelope

Every API response MUST use this envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "timestamp": "2026-06-08T14:00:00Z",
    "request_id": "uuid-v4",
    "tenant_id": 1
  }
}
```

### Rules

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | ✅ | `true` for 2xx, `false` for 4xx/5xx |
| `data` | any | ✅ | Payload (object, array, or null) |
| `error` | object \| null | ✅ | `{code, message, details}` or `null` |
| `meta` | object | ✅ | Metadata about the request |

### Error Object

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Paciente não encontrado",
    "details": {"patient_id": 123}
  },
  "meta": {
    "timestamp": "2026-06-08T14:00:00Z",
    "request_id": "REDACTED"
  }
}
```

---

## 2. HTTP Status Codes

| Code | When to use |
|------|-------------|
| `200 OK` | Successful GET, PUT, PATCH |
| `201 Created` | Successful POST (resource created) |
| `204 No Content` | Successful DELETE |
| `400 Bad Request` | Validation error, malformed JSON |
| `401 Unauthorized` | Missing or invalid JWT |
| `403 Forbidden` | Valid auth, but insufficient permissions |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Business logic conflict (e.g., duplicate) |
| `422 Unprocessable Entity` | Semantic validation failed |
| `500 Internal Server Error` | Unexpected server error |

---

## 3. Naming Conventions

### URLs
- **Lowercase with hyphens:** `/api/cannabis-profiles`
- **No trailing slashes:** `/api/patients` not `/api/patients/`
- **Nouns, not verbs:** `/api/patients` not `/api/get-patients`
- **Plural resources:** `/api/patients`, `/api/doses`
- **Nested resources:** `/api/patients/{id}/doses`

### Query Parameters
| Parameter | Purpose | Example |
|-----------|---------|---------|
| `page` | Pagination page | `?page=2` |
| `per_page` | Items per page | `?per_page=20` |
| `sort` | Sort field | `?sort=-created_at` |
| `filter[field]` | Filter by field | `?filter[status]=active` |
| `include` | Eager load relations | `?include=doses,symptoms` |

---

## 4. Pagination

List endpoints MUST paginate:

```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "..."},
    {"id": 2, "name": "..."}
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## 5. Tenant Context

All tenant-scoped endpoints MUST accept:

**Header:** `X-Association-ID: {tenant_id}`

If missing, fallback to user's default association.

Superadmins can bypass with: `X-Superadmin-Override: true`

---

## 6. Audit Trail

All write operations (POST, PUT, PATCH, DELETE) MUST emit an Event Bus event:

```python
event_bus.publish(EventEnvelopeV2(
    event_type="RESOURCE_ACTION",
    tenant_id=tenant_id,
    payload={...},
    event_category=EventCategory.CLINICAL,
))
```

---

## 7. Legacy Migration

Existing endpoints that do NOT follow this convention are flagged as `LEGACY`.

Migration priority:
1. Cannabis Module APIs (new in Week 11D)
2. Digital Twin APIs (new in Week 11D)
3. Follow-up APIs (new in Week 11D)
4. Patient API (`/api/pacientes`) — migrate envelope format
5. Symptom/Dosage/Evolution APIs — migrate envelope format
6. All remaining legacy endpoints

---

## 8. Helper Utilities

Use the response builder:

```python
from araos.platform.api.response import success_response, error_response

# Success
return success_response(data=patient.to_dict(), meta={"request_id": req_id})

# Error
return error_response(
    code="PATIENT_NOT_FOUND",
    message="Paciente não encontrado",
    status=404,
    details={"patient_id": patient_id}
)
```
