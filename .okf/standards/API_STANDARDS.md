# REST API Design & Contract Standards

## 1. URL Path Conventions

- All API endpoints must be prefixed with `/api/v1/`.
- Resource names must be lowercase, plural nouns (e.g., `/api/v1/courses`, `/api/v1/lectures`, `/api/v1/assignments`).
- Hierarchical nesting should be limited to 2 levels maximum:
  - Good: `/api/v1/chapters/{chapter_id}/lectures`
  - Anti-pattern: `/api/v1/courses/{c_id}/subjects/{s_id}/chapters/{ch_id}/lectures/{l_id}/notes` (too deep; query `/api/v1/lectures/{id}` directly).

---

## 2. Standard HTTP Methods & Status Codes

| Method | Target | Successful Status | Error Statuses |
| :--- | :--- | :--- | :--- |
| `GET` | Retrieve resource(s) | `200 OK` | `401 Unauthorized`, `403 Forbidden`, `404 Not Found` |
| `POST` | Create a new resource / trigger action | `201 Created` or `200 OK` | `400 Bad Request`, `422 Unprocessable Entity` |
| `PUT` | Full replacement of resource | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `PATCH` | Partial update of resource | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE`| Remove resource / soft-delete | `204 No Content` | `403 Forbidden`, `404 Not Found` |

---

## 3. Standard Response Payload Structures

### Success Envelope
```json
{
  "success": true,
  "data": { ... },
  "message": "Resource retrieved successfully"
}
```

### Paginated List Envelope
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_count": 142,
    "total_pages": 8
  }
}
```

### Standard Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Lecture with ID 42 does not exist",
    "details": []
  }
}
```

---

## 4. Telemetry Heartbeat Contract

- **Endpoint**: `POST /api/v1/telemetry/video-heartbeat`
- **Payload**:
  ```json
  {
    "lecture_id": "uuid",
    "current_position_seconds": 345,
    "duration_seconds": 1200,
    "session_watch_seconds": 10
  }
  ```
- **Frequency**: Emitted by client video player every 10 seconds of active playback.
