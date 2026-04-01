# plan.md (mis à jour)

## 1) Objectifs

### Objectifs produit (court terme — V1 avec Jellyfin)
- **Porter DagzFlix** de Next.js vers **React CRA + FastAPI + MongoDB** (stack FARM).
- **Zéro hardcoding** : aucune URL / clé API (Jellyfin, TMDB/IMDB, Radarr, Sonarr) dans le code. Tout passe par une **page Setup (premier démarrage)** et est stocké en MongoDB.
- Livrer un **lecteur Web “Netflix-grade”** :
  - **Choix intelligent Direct Play vs HLS** (transcodage)
  - Support **HEVC/H.265** :
    - Direct Play seulement si le navigateur le supporte réellement
    - Sinon fallback **HLS transcodé**
  - **Sélection automatique langue** :
    - Audio : **FR (FRA/FRE/FR)** puis **VFQ**
    - Si pas de FR : **VO + sous-titres FR (VOSTFR)**
  - **Sous-titres MKV** : extraction/serving via Jellyfin et rendu fiable côté navigateur (WebVTT)
  - **Progress / reprise** : remontée à Jellyfin + télémétrie locale

### Objectifs produit (moyen/long terme — “Sans Jellyfin”)
- Préparer une trajectoire pour **remplacer Jellyfin** par un “DagzFlix Media Server” autonome :
  - Gestion utilisateurs interne (auth, profils, rôles)
  - **Panel admin complet** (inspiré Jellyfin)
  - Gestion de bibliothèques **Films / Séries** (indexation, métadonnées, jaquettes)
  - Pipeline média futur (scan dossiers, transcodage, HLS, sous-titres)

### Clarifications clés (intégrations)
- **Recherche** : doit se faire via **TMDB/IMDB** (ou TMDB principalement), **pas** via Radarr/Sonarr.
- **Radarr/Sonarr** : servent **uniquement** à **demander** le téléchargement (request), pas à rechercher.

### Design
- Design cible : **Netflix + Apple TV**
  - Dark-only, **glassmorphism** (blur, transparence), arrondis
  - Micro-interactions et fluidité (framer-motion)
  - Respect des règles : pas de `transition: all`, gradients limités (<20% viewport), accessibilité (focus ring).

---

## 2) Étapes d’implémentation (par phases)

### Phase 0 — État actuel / travail déjà réalisé (DONE / IN PROGRESS)
**Backend**
- ✅ FastAPI initialisé, MongoDB branché (Motor)
- ✅ Routes majeures déjà présentes (Setup, Auth, Media, Stream, Search/Discover, Request, Proxy, etc.)
- ✅ Logique serveur de sélection FR/VFQ/VOSTFR déjà implémentée
- ✅ Génération URL Direct/HLS + WebVTT déjà implémentée

**Frontend**
- ✅ CRA initialisé (`index.js`, styles de base)
- ✅ `lib/dagzflix.js` : helper API + cache + `AuthProvider` + `PlayerProvider`
- ⚠️ `App.js` encore en mode placeholder (à remplacer par routing + pages)

**Guidelines UI**
- ✅ Design guidelines Netflix/Apple TV disponibles dans `/app/design_guidelines.md`

---

### Phase 1 — Frontend “Foundation” (routing + shell + Setup/Login) (P0)
**Objectif :** rendre l’app utilisable de bout en bout (Setup → Login → Home).

1) **App shell & routing React Router**
- Remplacer `App.js` par :
  - `BrowserRouter` + routes pages
  - Garde de routes basée sur `AuthProvider.status` (setup/login/ready)
- Pages V1 : `Setup`, `Login`, `Home`, `Movies`, `Series`, `Search`, `MediaDetail`, `Favorites`, `Player` (overlay/page)

2) **Design tokens & CSS global**
- Implémenter tokens (variables CSS) dans `index.css` selon `design_guidelines.md`
- Ajouter utilitaires glass (`glass`, `glass-strong`) cohérents
- Vérifier :
  - pas de centrage global `.App { text-align:center }`
  - pas de `transition: all`

3) **Setup Wizard (first-run)**
- Formulaire en sections (accordion/wizard) :
  - Jellyfin URL (+ méthode d’auth selon choix : API key ou login)
  - TMDB key (et/ou IMDB si prévu)
  - Radarr (URL+key)
  - Sonarr (URL+key)
- Bouton “Tester” : `/api/setup/test`
- Bouton “Sauvegarder” : `/api/setup/save`

4) **Login page**
- Auth Jellyfin : `/api/auth/login`
- Persistance session via cookie + check `/api/auth/session`

**Exit criteria (Phase 1)**
- Setup → Save → Login → Home (sans erreurs)
- Aucune URL/clé hardcodée dans le front

---

### Phase 2 — Parcours media complet (browse → detail → play) (P0)
**Objectif :** navigation type Netflix + pages fonctionnelles.

1) **Composants core UI (réutilisables)**
- `<PosterCard />` (actions rapides, hover lift, testids)
- `<MediaRow />` (ScrollArea horizontal + skeleton)
- `<MediaGrid />` (grille Movies/Series)
- `<Navbar />` (desktop rail + mobile bottom nav)

2) **Home**
- Continue Watching : `/api/media/resume`
- Recos : `/api/recommendations`
- Discover : `/api/discover`

3) **Movies / Series**
- Listing via `/api/media/library?type=Movie|Series`
- Filtres (genres, searchTerm, etc.)

4) **Search (TMDB/IMDB)**
- Mettre en conformité avec la nouvelle règle :
  - Recherche prioritaire via **TMDB** (idéalement via une route backend `/api/tmdb/search` ou réutiliser `/api/search` en s’assurant qu’il n’appelle pas Radarr/Sonarr)
  - Afficher disponibilité locale (mapping TMDB → Jellyfin)

5) **Media Detail**
- `/api/media/detail`
- Pour séries : `/api/media/seasons`, `/api/media/episodes`, `/api/media/next-episode`
- CTA Play + CTA Request (si non dispo)

**Exit criteria (Phase 2)**
- L’utilisateur peut explorer Home/Movies/Series/Search
- Ouvrir MediaDetail et lancer la lecture

---

### Phase 3 — Lecteur vidéo “Netflix-grade” (P0)
**Objectif :** lecteur premium avec détection HEVC et choix Direct/HLS + audio/subs auto.

1) **Détection compatibilité côté client**
- Implémenter `getBrowserPlaybackSupport()` :
  - `navigator.mediaCapabilities.decodingInfo` si dispo
  - fallback `video.canPlayType`
- Envoyer le signal au backend (`hevcSupport=true|false`) pour optimiser PlaybackInfo.

2) **Intégration player**
- Côté React :
  - Direct: `<video src>`
  - HLS: hls.js + gestion niveaux ABR
- Controls overlay :
  - Play/Pause, seek, volume, fullscreen
  - Menus audio/subtitles/quality (shadcn Dropdown/Sheet)
  - Auto-hide (2.5s idle)
  - Raccourcis clavier (Space, flèches, M, F, S)

3) **Audio/Subtitles**
- Defaults via backend (`selectedAudioIndex`, `selectedSubtitleIndex`, `languageMode`)
- Switching : rappeler `/api/media/stream?audioIndex=...&subtitleIndex=...` et recharger source proprement

4) **Sous-titres MKV**
- Utiliser `Stream.vtt` via Jellyfin
- Vérifier rendu : `<track>` pour direct play; pour HLS : manifestSubtitles vtt + fallback VTT externe si nécessaire

5) **Progress reporting**
- Timer (ex: toutes les 10s) → `POST /api/media/progress`
- Stop/pause events

**Exit criteria (Phase 3)**
- HEVC sur Chrome → HLS fonctionne
- Contenu compatible → Direct Play fonctionne
- FR/VFQ/VOSTFR auto fonctionne et menus de switch aussi
- Sous-titres intégrés MKV visibles

---

### Phase 4 — Requests (Radarr/Sonarr) + statut (P1)
**Objectif :** demander du contenu manquant sans utiliser Radarr/Sonarr pour la recherche.

1) **UI Request**
- Bouton “Demander” visible si `mediaStatus != available`
- Pour film → Radarr
- Pour série → Sonarr (option saisons si possible)

2) **Backend**
- Conserver `/api/media/request` mais :
  - s’assurer que le workflow “search” UI n’appelle pas Radarr/Sonarr
  - Radarr/Sonarr uniquement sur action explicite (request)

3) **Badges de statut**
- Harmoniser `available / pending / partial / not_available`

---

### Phase 5 — Hardening + QA + perf (P1)
- Tests E2E manuels guidés : Setup → Login → Browse → Play (direct/hls) → switch audio/subs → request
- Tests backend (smoke) : auth/session, media/stream, setup/test
- Performance : lazy-load images, skeletons, cache API (déjà présent), éviter re-render player

---

### Phase 6 — “Sans Jellyfin” (R&D, architecture provider) (P2 / long terme)
**Objectif :** préparer un remplacement progressif de Jellyfin.

1) **Abstraction provider**
- Introduire une couche `MediaProvider` (JellyfinProvider aujourd’hui)
- Spécifier les interfaces : auth, library, item detail, playback, subtitles, progress

2) **Auth interne + Admin**
- Schéma users/roles complet
- Panel admin (gestion users, bibliothèques, transcodage, stockage)

3) **Gestion bibliothèques**
- Scanner dossiers (films/séries), mapping TMDB
- Génération HLS interne + extraction subs

---

## 3) Next Actions (immédiat)
1) Remplacer `App.js` par le routing + guards (Setup/Login/Home)
2) Implémenter Setup Wizard (UI) connecté à `/api/setup/*`
3) Implémenter Login (UI) connecté à `/api/auth/login`
4) Implémenter le shell de navigation (Netflix/Apple TV)
5) Démarrer Player V1 (overlay + hls.js + menus)

---

## 4) Critères de succès
- **Aucun hardcoding** de services (URL/keys)
- Setup first-run fonctionnel + sessions stables
- Parcours : Browse → Detail → Play fonctionne
- Lecture robuste : Direct Play si possible sinon HLS, y compris HEVC
- Audio FR/VFQ prioritaire sinon VO + subs FR (VOSTFR)
- Sous-titres MKV rendus correctement
- Recherche via TMDB/IMDB (pas Radarr/Sonarr)
- Requests Radarr/Sonarr uniquement à la demande utilisateur
