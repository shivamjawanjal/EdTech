# Video Telemetry & Heartbeat Specification

## 1. Client Video Player Telemetry Protocol

To capture genuine student viewing habits without burdening the backend with high-frequency network requests, the video player implements a debounced heartbeat mechanism:

- **Sampling Interval**: Client checks playback state every 1 second.
- **Emission Frequency**: Client emits a heartbeat ping to `/api/v1/telemetry/video-heartbeat` every **10 seconds** of active continuous playback.
- **Immediate Event Flush**: Heartbeat is also immediately transmitted on:
  - Video Pause
  - Video Seek
  - Tab Inactive / Page Unload (`navigator.sendBeacon`)

---

## 2. Telemetry Payload Contract

```json
{
  "lecture_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "current_time_seconds": 412,
  "total_duration_seconds": 1420,
  "delta_watched_seconds": 10,
  "playback_rate": 1.25
}
```

---

## 3. Server-Side Upsert & Watch Milestone Logic

When a heartbeat payload arrives at FastAPI:
1. Validate authentication token and student batch enrollment.
2. Increment `seconds_watched` in `video_progress`:
   $$\text{completion\_percentage} = \min\left(100, \left\lfloor \frac{\text{seconds\_watched}}{\text{total\_duration\_seconds}} \times 100 \right\rfloor \right)$$
3. If $\text{completion\_percentage} \ge 85\%$, set `is_completed = TRUE`.
4. Update `last_heartbeat_at = NOW()`.
5. Return lightweight response:
   ```json
   {
     "success": true,
     "completion_percentage": 42,
     "is_completed": false
   }
   ```
