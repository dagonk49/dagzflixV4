# plan.md

## 1) Objectives
- **Port DagzFlix** from Next.js (App Router + API routes) to **React CRA + FastAPI + MongoDB**.
- **Zero hardcoding** of service URLs/API keys: everything comes from a **first-run Setup** stored in MongoDB.
- Deliver a **Netflix-quality Web VideoPlayer** with:
  - **Direct Play** when browser supports container+codecs (esp. HEVC/H.265)
  - **Transcode fallback** (HLS) when not supported
  - **French audio priority**: FRA/FRE > VFQ > otherwise **VO + French subtitles (VOSTFR)**
  - **Working subtitles** (embedded in MKV) served as **WebVTT** (and selectable)
  - Progress reporting to Jellyfin + local telemetry
- Add **Radarr/Sonarr** integrations for requesting content (in addition to Jellyseerr).

## 2) Implementation Steps (Phased)

### Phase 1 — Core Playback POC (isolation; must pass before full port)
**Goal:** Prove the hardest workflow: `PlaybackInfo → choose DirectPlay vs HLS → pick FR audio/subs → play in browser`.

1) **Web research (best-practice quick pass)**
- Verify Jellyfin endpoints for:
  - PlaybackInfo usage and fields for direct play/transcode decisions
  - Direct stream URL formats and required params
  - Subtitles WebVTT streaming endpoints
  - HLS + hls.js subtitle track handling

2) **Backend POC (FastAPI) — minimal endpoints**
- `GET /api/setup/check` (returns setupComplete)
- `POST /api/setup/save` (save Jellyfin/Jellyseerr/Radarr/Sonarr config in MongoDB)
- `POST /api/auth/login` (Jellyfin AuthenticateByName; create session cookie)
- `GET /api/media/stream?itemId=...` returns **playback plan**:
  - `mode`: `direct` or `hls`
  - `streamUrl`
  - `mediaSourceId`, `playSessionId`
  - `audioTracks[]`, `subtitleTracks[]`
  - `selectedAudioIndex`, `selectedSubtitleIndex`

3) **Codec capability probe (frontend POC)**
- Implement `getBrowserPlaybackSupport()` using:
  - `navigator.mediaCapabilities.decodingInfo` when available
  - fallback `video.canPlayType`
- Decide direct-play feasibility based on:
  - container support (mp4/webm; mkv usually no)
  - codec support (hevc/h265 only on Safari; h264 broadly)

4) **French track auto-selection (backend POC)**
- Implement scoring for audio/subtitle tracks:
  - Audio priority: `fra|fre|french` > `fr-ca|vfq|quebec` > default
  - If no French audio: choose “VO” (non-fr) + best French subtitle (VOSTFR)
  - Subtitle priority: `forced`(fr) > `fra/fre` > any fr-variant

5) **Subtitles POC**
- For `mode=direct`: return `subtitleVttUrl` for selected track + list for menu.
- For `mode=hls`: confirm subtitles appear via manifest or expose VTT endpoints as fallback.

6) **POC Frontend player page**
- Simple page: input `itemId` → Play.
- Support:
  - HLS via hls.js
  - Direct stream via `<video src>`
  - Subtitles via `<track kind="subtitles" src=...>` for direct mode

**Exit criteria (Phase 1):**
- At least 1 item plays successfully:
  - Direct play on Safari-capable HEVC OR direct play H264 on Chrome
  - Transcode HLS plays on Chrome for HEVC
  - Auto-select FR audio when present, else VO+FR subs
  - Subtitle renders in browser

---

### Phase 2 — V1 App Development (full port; MVP)
**Goal:** Port enough of DagzFlix to support the core user journey end-to-end.

1) **Backend: FastAPI “BFF” port (MVP subset first)**
- Collections: `config`, `sessions`, `users`, `favorites`, `preferences`, `telemetry`.
- Endpoints (minimum):
  - Setup: `check/test/save`
  - Auth: `login/logout/session`
  - Media: `library/detail/stream/progress/resume/seasons/episodes/next-episode`
  - Proxy: Jellyfin images + TMDB images
  - Search/Discover: minimal parity (search + discover)
  - Requests: Jellyseerr request + Radarr/Sonarr request (basic)

2) **Frontend: React CRA port (routing + contexts)**
- React Router pages: `Setup`, `Login`, `Home`, `Movies`, `Series`, `MediaDetail`, `Search`, `Favorites`, `Admin (later)`.
- Port contexts:
  - `AuthProvider` (session check + redirects)
  - `PlayerProvider` (open/close player)
- Port shared components: `Navbar`, `MediaGrid`, `MediaCard`, `MediaModal`.

3) **Netflix-quality VideoPlayer v1**
- UX: auto-hide controls, keyboard shortcuts, scrubbing, volume, fullscreen.
- Quality menu:
  - HLS levels from hls.js
  - Direct-play “quality” shows `source` info only
- Audio/subtitle menu:
  - Use backend-selected defaults on load
  - Allow switching (recompute streamUrl or swap track)
- Progress reporting:
  - `POST /api/media/progress` every 10s while playing + stop event

4) **Radarr/Sonarr request v1**
- Setup stores Radarr/Sonarr config.
- Media detail shows “Request” when not local:
  - Movies → Radarr
  - Series → Sonarr (optionally season selection)
  - Keep Jellyseerr as optional fallback if configured

5) **End-to-end test pass (v1)**
- Setup → Login → Browse → Detail → Play (direct/hls) → subtitles/audio switching → request.

**User stories (Phase 2)**
1. As a user, I want a first-run Setup so I can configure Jellyfin/Jellyseerr/Radarr/Sonarr without editing code.
2. As a user, I want to log in with my Jellyfin account and stay logged in via secure cookies.
3. As a user, I want playback to automatically choose Direct Play when my browser supports the media.
4. As a user, I want French audio to be selected automatically, otherwise VO with French subtitles.
5. As a user, I want to request missing movies/series via Radarr/Sonarr directly from the media page.

---

### Phase 3 — Feature Expansion + Hardening
1) **Full parity port (remaining controllers)**
- Favorites, ratings, wizard/recommendations, admin telemetry/users.

2) **Player upgrades (Netflix-like polish)**
- Better buffering states, seek preview (optional), chapter markers (if available), “Skip intro” (future).
- Smarter ABR defaults and bandwidth estimation.

3) **Subtitles robustness**
- Handle embedded ASS/SRT via Jellyfin VTT conversion endpoints.
- Ensure correct charset + timing; add fallback if HLS subtitle manifest missing.

4) **Requests/status unification**
- Normalize availability/pending status across Jellyseerr/Radarr/Sonarr.

5) **Testing & regression**
- Automated smoke checks for core endpoints.

**User stories (Phase 3)**
1. As a user, I want favorites and continue-watching to persist and load fast.
2. As a user, I want subtitle styling/selection to be reliable across browsers.
3. As a user, I want a consistent “available/pending/downloading” badge across all request providers.
4. As an admin, I want telemetry dashboards to understand watch behavior.
5. As a user, I want search/discover to feel instant with caching.

---

### Phase 4 — Production-readiness
- Security: origin validation, rate limiting (basic), safer proxying.
- Observability: structured logs, error IDs.
- Config migrations + backup/export.
- Optional: pluggable “no Jellyfin” provider layer (future path).

**User stories (Phase 4)**
1. As a user, I want the app to recover gracefully when Jellyfin is temporarily down.
2. As a user, I want my config exportable so I can move servers easily.
3. As a developer, I want services to be modular so I can swap Jellyfin later.
4. As a user, I want fast startup and minimal loading flashes.
5. As a user, I want my sessions to remain secure and stable.

## 3) Next Actions (immediate)
1) Implement Phase 1 POC backend endpoints + Mongo config store.
2) Implement codec capability probe in frontend.
3) Implement `/api/media/stream` returning direct-vs-hls plan + FR track selection.
4) Validate playback (Chrome: HEVC → HLS; Safari: HEVC → direct if supported).

## 4) Success Criteria
- First-run Setup works; no service URL/API key exists in code.
- One-click playback works end-to-end with:
  - correct Direct Play/HLS selection per browser/media
  - FR audio preferred; otherwise VOSTFR when possible
  - subtitles render reliably
  - progress updates recorded
- Radarr/Sonarr requests succeed when configured.
