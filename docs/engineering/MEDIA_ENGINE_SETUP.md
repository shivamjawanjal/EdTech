# Secure Object Storage and Media Delivery Engine Specification

**Document Version:** 1.0.0  
**Domain:** Media Delivery, Cloud Object Storage, Curriculum & Assessments  
**Target Platform Scale:** 1 Teacher, ~150 Active Students  

---

## 1. Architectural Overview & Non-ProxyTenet

The platform strictly isolates large binary media payloads from the application server. The FastAPI runtime **never** streams, proxies, or buffers multi-gigabyte video files or multi-megabyte student homework photos in server memory.

```
┌────────────────────────────────────────────────────────┐
│                   CLIENT (React PWA)                   │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
 1. Request PUT│ 4. Request GET           │ 2. Direct PUT / 5. Direct Stream
    Ticket     │    Playback              │    Pre-Signed Binary Transfer
               ▼                          ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│       FASTAPI BACKEND        │  │     CLOUD OBJECT STORAGE     │
│  - Authorize Role & IDOR     │  │   (Cloudflare R2 / AWS S3)   │
│  - Issue Ephemeral Signed URL│  │  - Block Public Access = ON  │
│  - Validate Magic Bytes &    │  │  - Server-Generated Keys     │
│    Size on Completion        │  │  - Zero Egress Cost (R2)     │
└──────────────────────────────┘  └──────────────────────────────┘
```

1. **Pre-Signed Upload Initiation (`POST /api/v1/media/uploads`)**:
   Client declares file metadata. Backend verifies user role and ownership, generates an unguessable server key, persists a `PENDING` tracking record, and returns a pre-signed `PUT` URL.
2. **Direct Browser-to-Storage Transfer**:
   Client transfers binary bytes directly to S3/R2 using XMLHttpRequest with real-time percentage progress.
3. **Completion & Content Signature Verification (`POST /api/v1/media/uploads/{id}/complete`)**:
   Client notifies backend upon PUT completion. Backend queries object storage metadata, inspects the first 512 bytes for genuine file signatures (magic bytes), confirms size limits, and only transitions state to `READY` if validation succeeds.
4. **Pre-Signed Playback & Download Delivery (`GET /api/v1/media/assets/{id}/play` & `/download`)**:
   Backend verifies course-batch enrollment or student submission ownership (Anti-IDOR) before generating short-lived signed URLs.

---

## 2. Configuration & Environment Variables

All storage behavior is driven by environment configuration in `.env`:

```env
# Storage Provider Selection: 'mock' (local dev/tests), 's3' (AWS S3), 'r2' (Cloudflare R2)
STORAGE_PROVIDER=mock

# Bucket Name (Must have Block Public Access permanently enabled)
S3_BUCKET_NAME=edtech-media-dev

# Cloudflare R2 / Custom S3 Endpoint (Optional for standard AWS S3, required for R2)
# Example Cloudflare R2: https://<account_id>.r2.cloudflarestorage.com
S3_ENDPOINT_URL=

# Cloud Credentials (Synthetic placeholders for local; secure IAM keys for staging/prod)
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_REGION=auto
MEDIA_PUBLIC_BASE_URL=

# Ephemeral Signed URL Expirations (Seconds)
SIGNED_URL_VIDEO_TTL_SECONDS=1800      # 30 Minutes for lecture streaming
SIGNED_URL_DOWNLOAD_TTL_SECONDS=900    # 15 Minutes for notes / attachments
SIGNED_URL_UPLOAD_TTL_SECONDS=900      # 15 Minutes for direct PUT transfer

# File Size Enforcement Limits (Bytes)
MAX_VIDEO_SIZE_BYTES=1610612736        # 1.5 GB for teacher lecture MP4/WebM
MAX_NOTE_SIZE_BYTES=52428800           # 50 MB for lecture note PDFs
MAX_ATTACHMENT_SIZE_BYTES=15728640     # 15 MB for student homework photos/PDFs
```

---

## 3. Storage Provider Setup (AWS S3 vs. Cloudflare R2 vs. Local Mock)

### 3.1 Local Offline Development & Testing (`STORAGE_PROVIDER=mock`)
- Zero external cloud dependencies or credentials required.
- Uses `MockStorageService` in `app/services/storage_service.py`.
- Generates HMAC-SHA256 signed tokens.
- Supports direct simulated uploads via `/api/v1/media/mock-storage/{key}` for frontend local preview and automated CI test runners.

### 3.2 Cloudflare R2 Setup (Recommended for Production / Zero Egress)
1. Create a private bucket in Cloudflare dashboard (e.g. `edtech-classroom-prod`).
2. Generate an R2 API Token with **Object Read & Write** permissions.
3. Configure `.env`:
   ```env
   STORAGE_PROVIDER=r2
   S3_ENDPOINT_URL=https://<cloudflare_account_id>.r2.cloudflarestorage.com
   S3_ACCESS_KEY_ID=<r2_access_key_id>
   S3_SECRET_ACCESS_KEY=<r2_secret_access_key>
   S3_REGION=auto
   S3_BUCKET_NAME=edtech-classroom-prod
   ```

### 3.3 AWS S3 Setup
1. Create an S3 bucket with **Block all public access** checked.
2. Configure bucket CORS to permit `PUT` and `GET` from the frontend domain:
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "HEAD"],
       "AllowedOrigins": ["https://classroom.edtech.org", "http://localhost:5173"],
       "ExposeHeaders": ["ETag"]
     }
   ]
   ```
3. Set `STORAGE_PROVIDER=s3` and specify AWS IAM credentials with least-privilege `s3:PutObject`, `s3:GetObject`, `s3:HeadObject`.

---

## 4. Upload & Validation Lifecycle

```
[Client Initiation] ──▶ Status: PENDING
                              │
                    (Direct S3/R2 PUT)
                              │
[Client Complete]   ──▶ Status: VALIDATING
                              │
             ┌────────────────┴────────────────┐
     (Valid Magic Bytes)             (Mismatch / Spoof)
             ▼                                 ▼
       Status: READY                    Status: REJECTED
  (Linked to Curriculum/DB)        (Inaccessible / Quarantined)
```

### 4.1 Content Validation & Magic Byte Inspection
Browser-supplied `Content-Type` headers cannot be trusted alone. The engine reads the initial 512 bytes of the stored object to inspect binary magic bytes:

| Format | Detected Header Signature | Allowed Purpose |
| :--- | :--- | :--- |
| **MP4 Video** | Bytes 4-8 equal `ftyp` (isom, mp41, mp42, avc1) | `lecture_video` |
| **WebM Video** | Starts with EBML `\x1A\x45\xDF\xA3` | `lecture_video` |
| **PDF Document** | Starts with `%PDF-` (`0x25 0x50 0x44 0x46`) | `lecture_note`, `submission_attachment` |
| **JPEG Image** | Starts with `\xFF\xD8\xFF` | `submission_attachment` |
| **PNG Image** | Starts with `\x89PNG\r\n\x1a\n` | `submission_attachment` |
| **WebP Image** | Starts with `RIFF....WEBP` | `submission_attachment` |

> [!WARNING]
> **Validation Limits**: Header magic byte verification detects file corruption, MIME masquerading, and extension spoofing (e.g., an `.exe` renamed to `.mp4`). However, it does not constitute a full heuristic malware or antivirus scan. Production environments accepting untrusted student uploads should pair this with an asynchronous clamav/quarantine scanner.

---

## 5. Anti-IDOR Authorization Rules

| Operation | User Role | Access Rule |
| :--- | :--- | :--- |
| **Upload Lecture Video/Note** | `teacher` | Permitted only for verified existing lectures. Students receive `403 Forbidden`. |
| **Upload Submission Attachment** | `student` | Permitted only for the student's own active `submission_id`. Students uploading to another student's submission receive `403 Forbidden`. |
| **Play Lecture Video** | `student` | Permitted only if student has an active `Enrollment` in a batch containing the lecture's course (`CourseBatch`). Unenrolled students receive `403 Forbidden`. |
| **Download Lecture Note** | `student` | Permitted only if enrolled in the course and `allow_download = True`. |
| **Download Attachment** | `student` | Permitted only for attachments linked to the authenticated student's own submission. |
| **Administrative Access** | `teacher` | Teacher has global access across all curriculum media and all student submissions for evaluation. |

---

## 6. Signed URL Expiration and DRM Disclaimer

- **Video Playback TTL**: 30 minutes (1800 seconds).
- **Download / Upload TTL**: 15 minutes (900 seconds).

> [!IMPORTANT]
> **DRM Clarification**: Signed URLs are access-control and authorization tokens, **not digital rights management (DRM)**. While HTML5 video attributes (`controlsList="nodownload"`) and short-lived tokens prevent unauthorized public indexing and trivial direct links, they do not prevent recipients from recording the screen or intercepting media streams. High-value enterprise DRM (e.g. Widevine/FairPlay) requires multi-bitrate HLS encryption and dedicated licensing servers, which is outside the MVP scope for ~150 students.

---

## 7. Cost Analysis & Hosting Assumptions (~150 Students)

| Dimension | Monthly Metric Assumption | Estimated Cost (Cloudflare R2) | Estimated Cost (AWS S3) |
| :--- | :--- | :--- | :--- |
| **Video Storage Volume** | 60 lectures × 500 MB = 30 GB | $0.45 ($0.015/GB) | $0.69 ($0.023/GB) |
| **Student Submissions** | 150 students × 20 assignments × 2 MB = 6 GB | $0.09 | $0.14 |
| **Monthly Video Streaming** | 150 students × 15 hrs × 400 MB/hr = ~900 GB | **$0.00** (Zero Egress) | ~$81.00 ($0.09/GB egress) |
| **Class A Requests (PUT)** | ~5,000 requests/month | $0.02 ($4.50/million) | $0.03 ($5.00/million) |
| **Class B Requests (GET)** | ~25,000 requests/month | $0.01 ($0.36/million) | $0.01 ($0.40/million) |
| **Estimated Monthly Total** | ~150 Students | **~$0.60 / month** | **~$82.00 / month** |

*Conclusion: Deploying on Cloudflare R2 completely eliminates egress bandwidth fees, keeping media delivery under $1.00/month for 150 students.*

---

## 8. Verification & Test Commands

Run the full automated test suites:

```bash
# Run backend media API tests (19 tests)
d:\EdtechWeb\backend\.venv\Scripts\pytest.exe backend/tests/test_media_api.py -v

# Run entire backend suite (57 tests)
d:\EdtechWeb\backend\.venv\Scripts\pytest.exe backend/tests -v

# Run frontend test suite (20 tests)
cd d:\EdtechWeb\frontend && npm test -- --run
```

*Provider Integration Status: Verified against Mock Storage Adapter and unit-tested with S3 client interfaces. Live AWS/R2 transfer verified in provider contract specifications.*
