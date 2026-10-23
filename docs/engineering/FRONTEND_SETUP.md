# Frontend Architecture & PWA Setup Guide

This document describes the React 19, TypeScript, Vite 8, and Tailwind CSS PWA frontend architecture, authentication integration, responsive layout shell, and testing procedures implemented in **TASK-006**.

---

## 1. Technology Stack & Directory Structure

```text
frontend/
├── public/
│   ├── favicon.svg             # Application SVG icon
│   ├── manifest.json           # Web app manifest for PWA installability
│   ├── offline.html            # Offline fallback screen
│   └── sw.js                   # Service worker caching shell & enforcing network-only API security
├── src/
│   ├── api/
│   │   ├── client.ts           # Native fetch wrapper with credentials: 'include' & CSRF auto-injection
│   │   └── auth.ts             # Typed authentication API (/login, /refresh, /logout, /me)
│   ├── components/
│   │   ├── common/
│   │   │   ├── Badge.tsx       # Pedagogical HealthBadges (On Track, Needs Attention, At Risk)
│   │   │   ├── Button.tsx      # Reusable button with variants, sizes, and loading state
│   │   │   ├── Card.tsx        # Card, CardHeader, CardTitle, CardContent, CardFooter
│   │   │   ├── EmptyState.tsx  # Empty state illustration & message
│   │   │   ├── Input.tsx       # Accessible text/password inputs with error messages & prefix icons
│   │   │   └── LoadingSpinner.tsx # Micro-spinners & full-page loader
│   │   └── layout/
│   │       ├── AppShell.tsx    # Responsive application container
│   │       ├── Header.tsx      # Top bar with role status, user badge, and logout
│   │       ├── MobileNav.tsx   # Fixed bottom navigation with 48px touch targets (<640px)
│   │       ├── ProtectedRoute.tsx # Route guard with role validation & redirect logic
│   │       └── Sidebar.tsx     # Desktop left navigation sidebar (260px)
│   ├── context/
│   │   ├── authContextDef.ts   # Context definition for fast-refresh compliance
│   │   ├── AuthContext.tsx     # Session restoration & auth provider
│   │   └── useAuth.ts          # useAuth custom hook
│   ├── pages/
│   │   ├── LoginPage.tsx       # Responsive login screen with demo quick-fill helpers
│   │   ├── StudentHome.tsx     # Mobile-first daily study center
│   │   ├── TeacherDashboard.tsx# Desktop-optimized teacher command console
│   │   └── UnauthorizedPage.tsx# 403 Access denied screen with safe return redirect
│   ├── test/
│   │   ├── setup.ts            # Vitest + Jest DOM matchers setup
│   │   ├── apiClient.test.ts   # Unit tests for CSRF token extraction & fetch options
│   │   ├── DesignTokensAndBadges.test.tsx # Component tests for health badges
│   │   ├── LoginPage.test.tsx  # Form validation & submission tests
│   │   └── ProtectedRoute.test.tsx # Route guard & redirect tests
│   ├── types/
│   │   └── auth.ts             # User, StudentProfile, TokenResponse, ApiErrorResponse interfaces
│   ├── App.tsx                 # Route declarations & role boundaries
│   ├── index.css               # Tailwind CSS v4 design tokens & typography
│   └── main.tsx                # App entrypoint & service worker registration
├── package.json
├── tsconfig.json
├── tsconfig.app.json
└── vite.config.ts              # Vite config with @tailwindcss/vite and /api proxy
```

---

## 2. Authentication & Cookie Security

### 2.1 HttpOnly Transport & Double-Submit CSRF
- **No Token Storage in JS**: Authentication tokens (`access_token` and `refresh_token`) are transported strictly inside `HttpOnly`, `SameSite` cookies managed by the browser. JavaScript cannot access them, eliminating XSS token theft.
- **CSRF Defense**: On every state-changing request (`POST`, `PUT`, `PATCH`, `DELETE`), `apiClient` automatically reads the non-HttpOnly `csrf_token` cookie and attaches it as the `X-CSRF-Token` request header.
- **Session Restoration**: When the app boots, `AuthProvider` makes a `GET /api/v1/auth/me` call. If unauthenticated (401), the app gracefully defaults to the guest state without triggering redirect loops.

### 2.2 Role-Based Routing
- `/login`: Public login form. Automatically redirects already-logged-in users to their role-specific dashboard.
- `/teacher/dashboard`: Guarded by `<ProtectedRoute requiredRole="teacher">`. Students attempting access are redirected to `/unauthorized`.
- `/student/home`: Guarded by `<ProtectedRoute requiredRole="student">`. Teachers attempting access are redirected to `/unauthorized`.
- `/unauthorized`: Friendly 403 access-denied screen with a return button.

---

## 3. PWA & Service Worker Security Constraints

### 3.1 Caching Strategy
- **App Shell Static Assets**: Cached on install (`/`, `/index.html`, `/offline.html`, `/favicon.svg`, `.js`, `.css`).
- **Offline Fallback**: When network is disconnected during page navigation, the service worker displays `/offline.html`.

### 3.2 Security Rules (Strictly Enforced)
- **Zero API Caching**: The service worker explicitly intercepts `/api/*` and passes all API requests through `fetch(event.request)`.
- **Zero Token/Credential Caching**: No credentials, tokens, submissions, grades, or student profiles are ever written to CacheStorage or IndexedDB.

---

## 4. Developer Verification Commands

```powershell
# 1. Navigate to frontend directory
cd d:\EdtechWeb\frontend

# 2. Run TypeScript type checking and production build
npm run build

# 3. Run ESLint
npm run lint

# 4. Run Vitest automated unit/component test suite
npm test

# 5. Start Vite local development server
npm run dev -- --port 5173
```

---

## 5. Test Credentials (from Seed Fixtures)

- **Teacher Console**:
  - Email / Username: `teacher@edtechweb.local` (or `+919999900000`)
  - Password: `TeacherPassword123!`
  - Lands on: `/teacher/dashboard`
- **Student Portal**:
  - Email / Username: `student001@edtechweb.local` (or `+919800000001`)
  - Password: `StudentPassword123!`
  - Lands on: `/student/home`
