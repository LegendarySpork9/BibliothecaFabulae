# Bibliotheca Fabulae - Infrastructure Document

## Overview

Bibliotheca Fabulae is a self-hosted personal fanfiction archive and reader. It downloads and preserves fics from 100+ supported sites, stores them locally with full metadata, and provides a private web interface for reading, searching, and organising.

- **Author:** Hunter Industries / Toby Hunter
- **Version:** 1.0.0
- **Repository:** https://github.com/LegendarySpork9/BibliothecaFabulae

## Technology Stack

### Backend

| Component | Technology | Version |
|---|---|---|
| Framework | FastAPI | 0.115.6 |
| Language | Python | 3.12 |
| ASGI Server | Uvicorn | 0.34.0 |
| ORM | SQLAlchemy (async) | 2.0.36 |
| Database | SQLite (WAL mode) | - |
| Migrations | Alembic | 1.14.0 |
| Async SQLite Driver | aiosqlite | 0.20.0 |
| Authentication | PyJWT | 2.10.1 |
| Password Hashing | bcrypt | 4.2.1 |
| TOTP | pyotp | 2.9.0 |
| QR Code Generation | qrcode (with PIL) | 8.0 |
| Encryption | cryptography (AES-256-GCM) | 44.0.0 |
| Validation | Pydantic | 2.10.3 |
| Configuration | pydantic-settings | 2.7.0 |
| Scheduling | APScheduler | 3.10.4 |
| Rate Limiting | SlowAPI | 0.1.9 |
| Testing | pytest | 8.3.4 |
| Test Coverage | pytest-cov | 6.0.0 |
| Async Testing | pytest-asyncio | 0.24.0 |
| HTTP Test Client | httpx | 0.28.1 |

### Frontend

| Component | Technology | Version |
|---|---|---|
| Framework | React | 19.0.0 |
| Language | TypeScript | 5.7.2 |
| Build Tool | Vite | 6.0.3 |
| Routing | React Router | 7.1.0 |
| Server State | TanStack React Query | 5.62.0 |
| HTTP Client | Axios | 1.7.9 |
| CSS Framework | Tailwind CSS | 3.4.17 |
| Icons | Lucide React | 0.468.0 |
| Testing | Vitest | 5.1.1 |
| Test Utilities | Testing Library (React) | 16.3.3 |

### Deployment

| Component | Technology |
|---|---|
| Containerisation | Docker (multi-stage) |
| Orchestration | Docker Compose |
| Reverse Proxy (Linux) | Nginx |
| Reverse Proxy (Windows) | IIS with URL Rewrite |

## Project Structure

```
BibliothecaFabulae/
+-- backend/                        # FastAPI application
|   +-- api/                        # Route handlers
|   |   +-- auth.py                 # Authentication endpoints
|   |   +-- dependencies.py         # Dependency injection (get_current_user)
|   |   +-- health.py               # Health check endpoint
|   |   +-- middleware.py            # Setup guard middleware
|   |   +-- notifications.py        # Notification CRUD endpoints
|   |   +-- settings.py             # Settings, account, and storage endpoints
|   |   +-- setup.py                # Setup wizard endpoints
|   +-- cli/                        # CLI utilities
|   +-- core/                       # Configuration and utilities
|   |   +-- auth.py                 # JWT, bcrypt, TOTP utilities
|   |   +-- config.py               # Pydantic settings with .env overrides
|   |   +-- database.py             # Async SQLAlchemy engine and session
|   |   +-- encryption.py           # AES-256-GCM encrypt/decrypt
|   |   +-- logging_config.py       # Rotating file log handler
|   |   +-- security.py             # Rate limiting configuration
|   |   +-- utils.py                # Shared utilities (utcnow)
|   +-- downloader/                 # FanFicFare integration (future)
|   +-- models/                     # SQLAlchemy ORM models
|   |   +-- base.py                 # Declarative base
|   |   +-- notification.py         # Notification and NotificationPreference
|   |   +-- session.py              # RefreshToken
|   |   +-- settings.py             # Settings (singleton)
|   |   +-- user.py                 # User
|   +-- scanner/                    # Archive Scanner integration (future)
|   +-- services/                   # Business logic
|   |   +-- auth_service.py         # Authentication and session management
|   |   +-- email_service.py        # SMTP email sending
|   |   +-- notification_service.py # Notification creation and delivery
|   |   +-- settings_service.py     # Settings CRUD and account management
|   |   +-- setup_service.py        # Setup wizard logic
|   |   +-- storage_service.py      # Disk and storage usage monitoring
|   +-- tts/                        # Text-to-speech engine (future)
+-- frontend/                       # React SPA
|   +-- public/                     # Static assets (favicon, logo)
|   +-- src/
|   |   +-- api/                    # API client and typed endpoints
|   |   +-- components/             # Reusable UI components
|   |   |   +-- guards/             # Auth and setup route guards
|   |   |   +-- layout/             # App shell (sidebar, topbar)
|   |   |   +-- notifications/      # Notification UI components
|   |   |   +-- storage/            # Storage visualisation components
|   |   |   +-- ui/                 # Shared UI primitives
|   |   +-- contexts/               # React contexts (Auth, Theme, Toast)
|   |   +-- hooks/                  # Custom hooks
|   |   +-- pages/                  # Page components
|   |   |   +-- settings/           # Settings sub-pages
|   |   |   +-- setup/              # Setup wizard and steps
|   |   +-- test/                   # Test setup
|   |   +-- types/                  # TypeScript type definitions
+-- alembic/                        # Database migration scripts
+-- Deployments/                    # Deployment configuration
+-- tests/                          # Backend test suite
+-- iis/                            # IIS configuration files
+-- nginx/                          # Nginx configuration
+-- .github/workflows/              # CI/CD pipeline definitions
```

## Application Architecture

### Backend (FastAPI)

The backend is an async FastAPI application served by Uvicorn. It uses SQLAlchemy with aiosqlite for non-blocking database access, and serves the built React frontend as static files with a catch-all SPA fallback route.

### Frontend (React SPA)

The frontend is a single-page application built with Vite. It uses React Router for client-side routing, TanStack React Query for server state management, and Tailwind CSS for styling with a class-based dark/light theme toggle.

### Database

SQLite in WAL (Write-Ahead Logging) mode, configured via SQLAlchemy async engine. WAL mode and foreign keys are enabled on every connection via event listeners. Database schema is managed by Alembic migrations, with `create_all` as a fallback on startup.

### Data Models

| Model | Table | Purpose |
|---|---|---|
| User | `users` | Single admin account (username, bcrypt password hash, encrypted TOTP secret) |
| Settings | `settings` | Singleton configuration row (storage path, theme, SMTP, backup, Cloudflare trust) |
| Notification | `notifications` | Individual notification records with type, severity, and read status |
| NotificationPreference | `notification_preferences` | Per-type delivery preferences (UI and email toggles) |
| RefreshToken | `refresh_tokens` | Active session tracking with token rotation |

### Services

| Service | Responsibility |
|---|---|
| `auth_service` | Username/password authentication, TOTP verification, JWT token issuance, refresh token rotation, session management |
| `setup_service` | Setup wizard: account creation, TOTP enrolment, storage configuration, SMTP setup, completion |
| `settings_service` | Settings CRUD, password changes, TOTP regeneration, theme/backup/SMTP updates |
| `storage_service` | Disk usage monitoring, per-subdirectory size breakdown, low storage warnings |
| `email_service` | SMTP email sending with TLS, connection testing with live and stored credentials |
| `notification_service` | Notification creation with preference checks, async email dispatch, CRUD operations |

### API Endpoints

| Prefix | Purpose | Auth Required |
|---|---|---|
| `/api/health` | Health check and setup status | No |
| `/api/auth/*` | Login, TOTP verification, token refresh, logout, sessions | Varies |
| `/api/setup/*` | Setup wizard (account, TOTP, storage, SMTP, complete) | No (guarded by setup state) |
| `/api/settings/*` | Application settings and SMTP configuration | Yes |
| `/api/account/*` | Account management (password, TOTP) | Yes |
| `/api/storage/*` | Storage usage and warnings | Yes |
| `/api/notifications/*` | Notification CRUD and preferences | Yes |

## Authentication and Security

### Single-User Authentication

- Username and password login with bcrypt hashing (12 rounds minimum)
- Two-step flow: credentials → temporary JWT → TOTP verification → access + refresh tokens

### JWT Tokens

| Token | Scope | Lifetime | Storage |
|---|---|---|---|
| Access Token | `access` | 15 minutes | In-memory (frontend) |
| Temp Token | `totp_verification` | 5 minutes | Passed between login steps |
| Refresh Token | - | 24 hours (default) or 7 days (remember device) | HTTP-only cookie |

### TOTP Two-Factor Authentication

- 32-character Base32-encoded secrets
- QR code generated for authenticator app enrolment
- Verification window: ±1 time step
- Secrets encrypted at rest using AES-256-GCM

### Refresh Token Rotation

Every refresh invalidates the old token and issues a new one. If a stolen token is replayed after the legitimate user already refreshed, it fails. Device name (parsed from User-Agent) is tracked and validated on refresh.

### Cloudflare Zero Trust Mode

Optional setting that skips username/password login when the site is behind Cloudflare Zero Trust. Only TOTP verification is required. The `/api/auth/totp-only` endpoint validates the `CF-Connecting-IP` header before proceeding.

### Encryption at Rest

- AES-256-GCM via the `cryptography` library
- TOTP secrets and SMTP passwords encrypted before database storage
- Key derived from `ENCRYPTION_KEY` via PBKDF2 (480,000 iterations) or used directly if 64-char hex
- Supports key rotation via `ENCRYPTION_KEY_PREVIOUS`

### Rate Limiting

- SlowAPI with in-memory backend
- Login endpoints: 5 requests/minute per IP
- Setup endpoints: 3-5 requests/minute per IP
- Account-level lockout after repeated failures

### Web Security

- CORS locked to configured origins with explicit method and header allow lists
- CSRF origin checking on all mutating `/api` requests
- Security headers on all responses: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- HSTS in production (`max-age=63072000; includeSubDomains`)
- HTTP-only, secure, SameSite cookies for refresh tokens (relaxed in development)
- Path traversal protection on SPA static file serving

### Setup Guard Middleware

When `setup_complete` is false, all API endpoints except `/api/health` and `/api/setup/*` return 403. This prevents any authenticated endpoints from being called before initial setup.

## Pages

| Page | Route | Purpose |
|---|---|---|
| Dashboard | `/dashboard` | Welcome card, storage overview, recent notifications |
| Login | `/login` | Username/password + TOTP, or TOTP-only (Cloudflare trust) |
| Setup Wizard | `/setup` | 5-step first-run: Account, 2FA, Storage, Email, Summary |
| Notifications | `/notifications` | Full notification list with filters and pagination |
| Settings — Storage | `/settings/storage` | Storage path and usage breakdown |
| Settings — Theme | `/settings/theme` | Dark/light theme toggle |
| Settings — Account | `/settings/account` | Password change, TOTP regeneration, Cloudflare trust, active sessions |
| Settings — Backup | `/settings/backup` | Backup path and schedule configuration |
| Settings — SMTP | `/settings/smtp` | SMTP email configuration with connection test |
| Settings — Notifications | `/settings/notifications` | Per-type notification delivery preferences |

## Data Persistence

### SQLite Database

| Table | Purpose |
|---|---|
| `users` | Single admin user account |
| `settings` | Application configuration (singleton row) |
| `notifications` | Notification records |
| `notification_preferences` | Per-type delivery toggles |
| `refresh_tokens` | Active session tracking |
| `alembic_version` | Migration version tracking |

### File System

| Data | Location |
|---|---|
| SQLite Database | `./data/bibliothecafabulae.db` |
| Application Logs | `./logs/app.log` (rotating, 10 MB, 5 backups) |
| Fic Storage | Configurable path (set during setup) |

### Datetime Handling

All datetimes are stored as naive UTC in SQLite. The `utcnow()` utility in `backend/core/utils.py` returns `datetime.now(UTC).replace(tzinfo=None)` for consistency.

## Notification System

### Notification Types

| Type | Description |
|---|---|
| `fic_updated` | A fic in the archive has new chapters |
| `sync_complete` | Bookmark sync finished successfully |
| `sync_failed` | Bookmark sync encountered errors |
| `auth_required` | A source site needs re-authentication |
| `storage_low` | Storage usage approaching the limit |
| `fic_unavailable` | A fic has been deleted or made private |
| `scanner_new_works` | Archive Scanner discovered new fics |
| `audio_ready` | TTS audio generation complete |

### Delivery Channels

Each notification type has configurable UI and email toggles. Email delivery requires SMTP to be configured. Email toggles are disabled in the UI when SMTP is not set up.

## Configuration

### Environment Variables (.env)

```
SECRET_KEY=<64-char hex string>
ENCRYPTION_KEY=<64-char hex string>
ENCRYPTION_KEY_PREVIOUS=<optional, for key rotation>
DATABASE_URL=sqlite+aiosqlite:///./data/bibliothecafabulae.db
CORS_ORIGINS=["http://localhost:8000"]
ENVIRONMENT=production|development
LOG_DIR=./logs
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Runtime Settings (Database)

Managed via the Settings page after setup:

| Setting | Default | Purpose |
|---|---|---|
| `storage_path` | (set during setup) | Fic file storage directory |
| `theme` | `dark` | UI theme (dark/light) |
| `smtp_host/port/username/password` | (optional) | Email notification delivery |
| `backup_location` | (optional) | Backup destination path |
| `backup_schedule` | (optional) | Backup frequency |
| `cloudflare_trust_enabled` | `false` | Skip username/password on login |
| `remember_device_days` | `30` | Days a remembered device stays logged in |

## Logging

- **Framework:** Python `logging` with `RotatingFileHandler`
- **Output:** Rolling file
- **File:** `{LOG_DIR}/app.log`
- **Max File Size:** 10 MB (configurable)
- **Backup Count:** 5 rolling files (configurable)
- **Format:** `{ISO8601 Timestamp} | {LEVEL} | {Logger Name} | {Message}`
- **Console Output:** Enabled in development mode only

## CI/CD

### GitHub Actions Workflows

| Workflow | Trigger | Steps |
|---|---|---|
| **CI on Commit** (`Commit.yml`) | Push to any branch | Checkout, Setup Python 3.12, Install backend deps, Setup Node.js 22, Install frontend deps, Build frontend |
| **CI on Pull Request** (`Pull Request.yml`) | PR to any branch | All Commit steps + Run frontend tests (`npm test`), Run backend tests with coverage (`pytest --cov=backend`), Post coverage status, Upload coverage artifact |
| **Check for Linked Issue** (`PR Linked Issue.yml`) | PR opened/edited/reopened/synchronised | Verifies PR has linked GitHub issues |

### Test Suite

| Suite | Runner | Tests | Coverage Target |
|---|---|---|---|
| Backend | pytest | 65 tests (auth, setup, settings, notifications, models, encryption, database) | `backend/` package |
| Frontend | Vitest | 10 tests (AuthGuard, Topbar, DashboardPage, ThemeContext) | - |

## Deployment

### Docker (Linux)

Multi-stage Dockerfile:
1. **Stage 1** (`node:22-alpine`): Builds React frontend
2. **Stage 2** (`python:3.12-slim`): Installs Python dependencies, copies backend + built frontend, runs as non-root user

**Production (`docker-compose.yml`):**
- `app` service: FastAPI + built frontend, volumes for data/logs/storage
- `nginx` service: Reverse proxy with SSL termination, security headers, rate limiting
- SSL certificates mounted from `nginx/ssl/`

**Development (`docker-compose.dev.yml`):**
- `app` service only, exposed on port 8000, hardcoded dev secrets

### IIS (Windows)

- URL Rewrite reverse proxy: `/api/*` → `http://localhost:8000`
- SPA fallback rule for client-side routing
- Security headers and request filtering for sensitive paths
- Backend runs as a Windows service via NSSM + Uvicorn

### Deployment Scripts

| Script | Platform | Purpose |
|---|---|---|
| `deploy.sh` | Linux | Generates .env secrets, self-signed SSL cert, runs `docker compose up` |
| `deploy.bat` | Windows | Creates venv, installs deps, builds frontend, runs Alembic, prints service instructions |

## Hosting Requirements

### Runtime Prerequisites

- Python 3.12+
- Node.js 22+ (build only)
- Docker and Docker Compose (Linux deployment)
- IIS with URL Rewrite and ARR (Windows deployment)

### Network Requirements

- HTTPS (port 443) for client access (or port 80 for HTTP redirect)
- Outbound HTTPS for future integrations (FanFicFare downloads, Archive Scanner)
- Outbound SMTP for email notifications

### File System Requirements

- Read/write access to the database directory (`./data/`)
- Read/write access to the log directory (`./logs/`)
- Read/write access to the configured storage path
- Read access to the frontend build directory

### Development Ports

| Service | URL |
|---|---|
| FastAPI (direct) | `http://localhost:8000` |
| Vite Dev Server | `http://localhost:5173` |
