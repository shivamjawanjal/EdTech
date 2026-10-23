# Budget-Conscious Infrastructure & Deployment Plan

## 1. Cost Principle: Ultra-Low Operating Expense

For an initial cohort of 90–150 students with a single teacher, infrastructure expenses must remain strictly predictable and minimal ($15–$25/month). We avoid costly enterprise managed clusters, dedicated WebRTC servers, and expensive SaaS subscriptions.

---

## 2. Infrastructure Topology

```
┌────────────────────────────────────────────────────────┐
│ Cloudflare (Free Tier / CDN + DNS + DDoS Protection)   │
└───────────────────────────┬────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│  Compute & API Node ($7-$10)│   │  Object Storage ($2-$5)     │
│  - Hetzner / DigitalOcean   │   │  - Cloudflare R2 / AWS S3   │
│    (2 vCPU, 2GB-4GB RAM)    │   │  - Zero Egress Fees (R2)    │
│  - Caddy Web Server (HTTPS) │   │  - Pre-Signed Ephemeral     │
│  - FastAPI Application      │   │    Streaming & Uploads      │
│  - Local PostgreSQL 15      │   │  - 50GB-100GB Video Storage │
└─────────────────────────────┘   └─────────────────────────────┘
```

---

## 3. Projected Monthly Cost Breakdown (150 Active Students)

| Component | Provider / Solution | Resource Sizing | Projected Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Compute & API Server** | Hetzner Cloud CPX11 / DigitalOcean Droplet | 2 vCPU, 2GB–4GB RAM, 40GB NVMe SSD | **$6.50 – $10.00** |
| **Database** | PostgreSQL 15 on same host (with automated backup) | Co-located on NVMe SSD | **$0.00** (Included in VPS) |
| **Reverse Proxy & SSL** | Caddy Server | Native auto Let's Encrypt SSL, HTTP/3 | **$0.00** (Open Source) |
| **Static Web App Hosting** | Cloudflare Pages / Vercel (Hobby) | React Vite PWA static bundle | **$0.00** |
| **Object Storage (Videos)** | Cloudflare R2 | 50GB storage, $0 egress transfer fee | **$0.75 – $2.00** |
| **Live Classes** | Google Meet (via external launcher) | Standard Google account | **$0.00** |
| **Backup Storage** | Backblaze B2 / AWS S3 Glacier | Daily DB dump offsite | **$0.50** |
| **Domain & DNS** | Cloudflare DNS | Standard `.com` / `.in` domain | **$1.00** (~$12/year) |
| **TOTAL MONTHLY EXPENSE**| | | **~$10.00 – $15.00 / month** |

---

## 4. Scaling Horizon: Up to 500 Students

When the student body grows from 150 to 500+:
1. **Vertical VPS Sizing**: Upgrade VPS to 4 vCPU, 8GB RAM (~$18/month).
2. **Database Separation (Optional)**: Move PostgreSQL to a lightweight managed DB (e.g., Supabase, Neon, or DigitalOcean Managed DB at $15/month).
3. **Storage Bandwidth**: Because Cloudflare R2 charges $0 for egress bandwidth, serving 10x more video hours introduces negligible extra cost.
