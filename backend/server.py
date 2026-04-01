from fastapi import FastAPI, APIRouter, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os, uuid, logging, httpx, asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any, Dict
from pydantic import BaseModel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ─────────────────────────────────────────────────────────────────────────────
# MongoDB
# ─────────────────────────────────────────────────────────────────────────────
mongo_url = os.environ['MONGO_URL']
db_name   = os.environ.get('DB_NAME', 'dagzflix')
_client   = AsyncIOMotorClient(mongo_url)
db        = _client[db_name]

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────
app        = FastAPI(title='DagzFlix API')
api_router = APIRouter(prefix='/api')

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
async def get_config():
    return await db['config'].find_one({'_id': 'main'})

async def get_session(request: Request):
    session_id = request.cookies.get('dagzflix_session')
    if not session_id:
        return None
    session = await db['sessions'].find_one({'_id': session_id})
    if not session:
        return None
    if session.get('expiresAt') and session['expiresAt'] < datetime.now(timezone.utc):
        await db['sessions'].delete_one({'_id': session_id})
        return None
    return session

def set_cookie(response: Response, name: str, value: str, max_age: int = 0):
    response.set_cookie(name, value, max_age=max_age, httponly=True,
                        samesite='lax', secure=False, path='/')

TMDB_GENRE_ID_TO_NAME = {
    12:'Adventure',14:'Fantasy',16:'Animation',18:'Drama',27:'Horror',
    28:'Action',35:'Comedy',36:'History',37:'Western',53:'Thriller',80:'Crime',
    99:'Documentary',878:'Science Fiction',9648:'Mystery',10402:'Music',
    10749:'Romance',10751:'Family',10752:'War',10759:'Action & Adventure',
    10762:'Kids',10763:'News',10764:'Reality',10765:'Sci-Fi & Fantasy',
    10766:'Soap',10767:'Talk',10768:'War & Politics',10770:'TV Movie',
}
TMDB_GENRE_NAME_TO_ID = {v.lower(): k for k, v in TMDB_GENRE_ID_TO_NAME.items()}

def extract_tmdb_id(provider_ids: dict):
    return provider_ids.get('Tmdb') or provider_ids.get('TMDb') or provider_ids.get('tmdb')

def map_jellyfin_item(item: dict) -> dict:
    tmdb_id = extract_tmdb_id(item.get('ProviderIds') or {})
    return {
        'id': item.get('Id'),
        'name': item.get('Name', ''),
        'type': item.get('Type', ''),
        'overview': item.get('Overview', ''),
        'genres': item.get('Genres', []),
        'communityRating': item.get('CommunityRating', 0),
        'officialRating': item.get('OfficialRating', ''),
        'premiereDate': item.get('PremiereDate', ''),
        'year': item.get('ProductionYear', ''),
        'runtime': round(item['RunTimeTicks'] / 600000000) if item.get('RunTimeTicks') else 0,
        'posterUrl': f'/api/proxy/image?itemId={item["Id"]}&type=Primary&maxWidth=400',
        'backdropUrl': f'/api/proxy/image?itemId={item["Id"]}&type=Backdrop&maxWidth=1920',
        'thumbUrl': f'/api/proxy/image?itemId={item["Id"]}&type=Thumb&maxWidth=600',
        'hasSubtitles': item.get('HasSubtitles', False),
        'isPlayed': (item.get('UserData') or {}).get('Played', False),
        'playbackPositionTicks': (item.get('UserData') or {}).get('PlaybackPositionTicks', 0),
        'mediaSources': bool(item.get('MediaSources')),
        'studios': [s['Name'] for s in (item.get('Studios') or [])],
        'mediaStatus': 5,
        'tmdbId': tmdb_id,
        'localId': item.get('Id'),
        'providerIds': item.get('ProviderIds', {}),
    }

def map_tmdb_item(item: dict, force_tv=None) -> dict:
    media_type = item.get('mediaType') or item.get('media_type', '')
    is_tv = force_tv if force_tv is not None else (media_type == 'tv')
    poster  = item.get('posterPath') or item.get('poster_path', '')
    backdrop= item.get('backdropPath') or item.get('backdrop_path', '')
    release = item.get('releaseDate') or item.get('release_date', '')
    air     = item.get('firstAirDate') or item.get('first_air_date', '')
    rating  = item.get('voteAverage') or item.get('vote_average', 0)
    real_tmdb_id = item.get('tmdbId') or item.get('id')
    genre_ids = item.get('genreIds') or item.get('genre_ids', [])
    return {
        'id': real_tmdb_id,
        'tmdbId': real_tmdb_id,
        'name': item.get('title') or item.get('name', ''),
        'type': 'Series' if is_tv else 'Movie',
        'mediaType': 'tv' if is_tv else 'movie',
        'overview': item.get('overview', ''),
        'posterUrl': f'/api/proxy/tmdb?path={poster}&width=w400' if poster else '',
        'backdropUrl': f'/api/proxy/tmdb?path={backdrop}&width=w1280' if backdrop else '',
        'year': (release or air)[:4],
        'voteAverage': rating,
        'communityRating': rating,
        'genreIds': genre_ids,
        'genres': [TMDB_GENRE_ID_TO_NAME.get(g_id, '') for g_id in genre_ids if g_id in TMDB_GENRE_ID_TO_NAME],
        'mediaStatus': min((item.get('mediaInfo') or {}).get('status', 0), 4),
    }

async def get_local_tmdb_ids(config: dict, session: dict) -> dict:
    """Returns dict {tmdb_id: jellyfin_id}"""
    try:
        url = f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items'
        params = {'Recursive': 'true', 'IncludeItemTypes': 'Movie,Series',
                  'Fields': 'ProviderIds', 'Limit': '10000'}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, params=params,
                                 headers={'X-Emby-Token': session['jellyfinToken']})
        if not r.is_success:
            return {}
        data = r.json()
        result = {}
        for item in data.get('Items', []):
            tmdb_id = extract_tmdb_id(item.get('ProviderIds') or {})
            if tmdb_id:
                result[str(tmdb_id)] = item['Id']
        return result
    except Exception as e:
        logger.error(f'get_local_tmdb_ids error: {e}')
        return {}

async def inject_favorite_status(items: list, user_id: str) -> list:
    if not items or not user_id:
        return items
    favs = await db['favorites'].find({'userId': user_id}, {'itemId': 1}).to_list(None)
    fav_set = {str(f['itemId']) for f in favs}
    for item in items:
        cid = str(item.get('tmdbId') or item.get('id') or '')
        item['isFavorite'] = cid in fav_set
    return items

def resolve_genres(item: dict) -> list:
    genres = item.get('genres') or item.get('Genres', [])
    if genres and isinstance(genres[0], str):
        return genres
    if genres and isinstance(genres[0], dict):
        return [g.get('name') or g.get('Name', '') for g in genres]
    ids = item.get('genreIds') or item.get('genre_ids', [])
    return [TMDB_GENRE_ID_TO_NAME[i] for i in ids if i in TMDB_GENRE_ID_TO_NAME]

# ─────────────────────────────────────────────────────────────────────────────
# DagzRank
# ─────────────────────────────────────────────────────────────────────────────
def calculate_dagz_rank(item: dict, prefs: dict, watch_history: list, tel_data: dict) -> int:
    score = 25
    item_genres = resolve_genres(item)
    fav_genres   = [g.lower() for g in (prefs or {}).get('favoriteGenres', [])]
    dis_genres   = [g.lower() for g in (prefs or {}).get('dislikedGenres', [])]
    if item_genres and fav_genres:
        match  = sum(1 for g in item_genres if g.lower() in fav_genres)
        dis    = sum(1 for g in item_genres if g.lower() in dis_genres)
        score += max(0, (match / max(len(item_genres), 1)) * 25 - (dis / max(len(item_genres), 1)) * 10)
    else:
        score += 8
    rating = item.get('communityRating') or item.get('voteAverage') or 0
    score += (rating / 10) * 15
    year = item.get('year') or item.get('ProductionYear') or 0
    if year:
        age = datetime.now().year - int(year)
        if age <= 1:   score += 10
        elif age <= 3: score += 7
        elif age <= 5: score += 4
        elif age <= 10:score += 2
    score += 5  # telemetry neutral
    score += 5  # collaborative neutral
    if item.get('isPlayed'):
        score = max(0, score - 30)
    return min(100, round(score))

CHILD_BLOCKED_GENRES = {'horror', 'horreur', 'erotic', 'érotique', 'thriller'}
CHILD_ALLOWED_RATINGS = {'', 'G', 'PG', 'PG-13', 'TV-Y', 'TV-Y7', 'TV-G', 'TV-PG',
                         'Tout public', 'U', 'NR', 'Not Rated'}

def apply_parental_filter(items: list, user_profile: dict) -> list:
    if not items:
        return items
    if not user_profile or user_profile.get('role') != 'child':
        return items
    result = []
    for item in items:
        if item.get('adult'):
            continue
        ig = [g.lower() for g in resolve_genres(item)]
        if any(g in CHILD_BLOCKED_GENRES for g in ig):
            continue
        rating = item.get('officialRating') or item.get('OfficialRating', '')
        if rating and rating not in CHILD_ALLOWED_RATINGS:
            continue
        result.append(item)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# French language selection helpers
# ─────────────────────────────────────────────────────────────────────────────
FRENCH_AUDIO_LANGS = {'fra', 'fre', 'french', 'fr', 'vff'}
VFQ_LANGS = {'vfq', 'frca', 'fr-ca', 'qc', 'québécois', 'quebecois', 'canada'}

def score_audio_track(stream: dict) -> int:
    lang = (stream.get('Language') or '').lower().strip()
    title = (stream.get('DisplayTitle') or stream.get('Title') or '').lower()
    if lang in FRENCH_AUDIO_LANGS or 'french' in title or 'français' in title:
        return 100
    if lang in VFQ_LANGS or 'vfq' in title or 'québec' in title or 'quebec' in title or 'canada' in title:
        return 80
    return 0

def score_subtitle_track(stream: dict) -> int:
    lang  = (stream.get('Language') or '').lower().strip()
    title = (stream.get('DisplayTitle') or stream.get('Title') or '').lower()
    if lang in FRENCH_AUDIO_LANGS or 'french' in title or 'français' in title:
        forced = 'forced' in title or stream.get('IsForced', False)
        return 120 if forced else 100
    if lang in VFQ_LANGS or 'vfq' in title:
        return 80
    return 0

def select_french_tracks(media_streams: list, jellyfin_url: str, item_id: str,
                          media_source_id: str, token: str):
    """
    Returns (audio_index, subtitle_index, mode_label, subtitle_vtt_url)
    Priority: FR audio > VFQ audio > VO + FR subtitles (VOSTFR)
    """
    audio_tracks = [s for s in media_streams if s.get('Type') == 'Audio']
    sub_tracks   = [s for s in media_streams if s.get('Type') == 'Subtitle']

    # Score audio tracks
    best_audio = None
    best_audio_score = 0
    for tr in audio_tracks:
        s = score_audio_track(tr)
        if s > best_audio_score:
            best_audio_score = s
            best_audio = tr

    # Score subtitle tracks
    best_sub = None
    best_sub_score = 0
    for tr in sub_tracks:
        s = score_subtitle_track(tr)
        if s > best_sub_score:
            best_sub_score = s
            best_sub = tr

    default_audio = next((t for t in audio_tracks if t.get('IsDefault')), audio_tracks[0] if audio_tracks else None)

    if best_audio_score >= 80:
        # French audio found → no subtitle forced
        audio_idx = best_audio['Index']
        sub_idx   = best_sub['Index'] if (best_sub and best_sub_score >= 80) else -1
        mode = 'VF' if best_audio_score == 100 else 'VFQ'
    elif best_sub_score >= 80:
        # No French audio but French subtitle → VOSTFR
        audio_idx = default_audio['Index'] if default_audio else -1
        sub_idx   = best_sub['Index']
        mode = 'VOSTFR'
    else:
        # Nothing French → VO, no subtitle
        audio_idx = default_audio['Index'] if default_audio else -1
        sub_idx   = -1
        mode = 'VO'

    # Build subtitle VTT URL for direct play
    sub_vtt_url = None
    if sub_idx >= 0:
        sub_vtt_url = (f'{jellyfin_url}/Videos/{item_id}/{media_source_id}'
                       f'/Subtitles/{sub_idx}/Stream.vtt?api_key={token}')

    return audio_idx, sub_idx, mode, sub_vtt_url

# ─────────────────────────────────────────────────────────────────────────────
# Direct Play detection helper
# ─────────────────────────────────────────────────────────────────────────────
BROWSER_DIRECT_PLAY_CONTAINERS = {'mp4', 'm4v', 'webm', 'ogg'}
BROWSER_DIRECT_PLAY_VIDEO_CODECS = {'h264', 'avc', 'vp8', 'vp9', 'av1', 'theora'}
# HEVC / H.265 only natively in Safari on Apple Silicon — we never direct-play HEVC server-side decision
HEVC_CODECS = {'hevc', 'h265', 'hvc1', 'hev1'}

def can_direct_play(source: dict) -> bool:
    """
    Server-side heuristic: can the browser likely direct-play this source?
    Returns True only for broadly-supported h264/vp9 in mp4/webm containers.
    HEVC → always transcode (browser will override via MediaCapabilities API).
    MKV  → never direct-play in browser (container not supported).
    """
    container = (source.get('Container') or '').lower()
    video_streams = [s for s in (source.get('MediaStreams') or []) if s.get('Type') == 'Video']
    if not video_streams:
        return False
    video_codec = (video_streams[0].get('Codec') or '').lower()

    # MKV never direct-plays in browsers
    if container in ('mkv', 'matroska', 'avi', 'wmv', 'flv'):
        return False

    # HEVC only on Safari — we default to transcode and let client override
    if video_codec in HEVC_CODECS:
        return False

    # H.264/VP9/AV1 in mp4/webm → likely direct-playable
    if container in BROWSER_DIRECT_PLAY_CONTAINERS and video_codec in BROWSER_DIRECT_PLAY_VIDEO_CODECS:
        return True

    return False

# ─────────────────────────────────────────────────────────────────────────────
# ── ROUTES ───────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

# ── Health ──
@api_router.get('/')
async def root():
    return {'message': 'DagzFlix API'}

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/setup/check')
async def setup_check():
    config = await get_config()
    return {
        'setupComplete': bool(config and config.get('setupComplete')),
        'jellyfinConfigured': bool(config and config.get('jellyfinUrl')),
        'jellyseerrConfigured': bool(config and config.get('jellyseerrUrl')),
        'radarrConfigured': bool(config and config.get('radarrUrl')),
        'sonarrConfigured': bool(config and config.get('sonarrUrl')),
    }

class SetupTestBody(BaseModel):
    type: str
    url: str
    apiKey: str = ''

@api_router.post('/setup/test')
async def setup_test(body: SetupTestBody):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if body.type == 'jellyfin':
                r = await client.get(f'{body.url.rstrip("/")}/System/Info/Public',
                                     headers={'X-Emby-Token': body.apiKey})
                r.raise_for_status()
                d = r.json()
                return {'success': True, 'serverName': d.get('ServerName'), 'version': d.get('Version')}
            elif body.type == 'jellyseerr':
                r = await client.get(f'{body.url.rstrip("/")}/api/v1/status',
                                     headers={'X-Api-Key': body.apiKey})
                r.raise_for_status()
                d = r.json()
                return {'success': True, 'version': d.get('version')}
            elif body.type == 'radarr':
                r = await client.get(f'{body.url.rstrip("/")}/api/v3/system/status',
                                     headers={'X-Api-Key': body.apiKey})
                r.raise_for_status()
                d = r.json()
                return {'success': True, 'version': d.get('version')}
            elif body.type == 'sonarr':
                r = await client.get(f'{body.url.rstrip("/")}/api/v3/system/status',
                                     headers={'X-Api-Key': body.apiKey})
                r.raise_for_status()
                d = r.json()
                return {'success': True, 'version': d.get('version')}
            return {'success': False, 'error': 'Type invalide'}
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=400)

class SetupSaveBody(BaseModel):
    jellyfinUrl: str
    jellyfinApiKey: str = ''
    jellyseerrUrl: str = ''
    jellyseerrApiKey: str = ''
    radarrUrl: str = ''
    radarrApiKey: str = ''
    sonarrUrl: str = ''
    sonarrApiKey: str = ''

@api_router.post('/setup/save')
async def setup_save(body: SetupSaveBody):
    await db['config'].update_one(
        {'_id': 'main'},
        {'$set': {
            'jellyfinUrl':      body.jellyfinUrl.rstrip('/'),
            'jellyfinApiKey':   body.jellyfinApiKey,
            'jellyseerrUrl':    body.jellyseerrUrl.rstrip('/') if body.jellyseerrUrl else '',
            'jellyseerrApiKey': body.jellyseerrApiKey,
            'radarrUrl':        body.radarrUrl.rstrip('/') if body.radarrUrl else '',
            'radarrApiKey':     body.radarrApiKey,
            'sonarrUrl':        body.sonarrUrl.rstrip('/') if body.sonarrUrl else '',
            'sonarrApiKey':     body.sonarrApiKey,
            'setupComplete':    True,
            'updatedAt':        datetime.now(timezone.utc),
        }},
        upsert=True
    )
    return {'success': True, 'message': 'Configuration sauvegardée'}

# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────
class LoginBody(BaseModel):
    username: str
    password: str

@api_router.post('/auth/login')
async def auth_login(body: LoginBody, response: Response):
    config = await get_config()
    if not config or not config.get('jellyfinUrl'):
        return JSONResponse({'success': False, 'error': 'Serveur non configuré'}, 400)
    try:
        auth_header = 'MediaBrowser Client="DagzFlix", Device="Web", DeviceId="dagzflix-web", Version="1.0"'
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f'{config["jellyfinUrl"]}/Users/AuthenticateByName',
                json={'Username': body.username, 'Pw': body.password},
                headers={'Content-Type': 'application/json', 'X-Emby-Authorization': auth_header}
            )
        if r.status_code == 401 or r.status_code == 403:
            return JSONResponse({'success': False, 'error': 'Identifiants incorrects'}, 401)
        if not r.is_success:
            return JSONResponse({'success': False, 'error': f'Erreur serveur {r.status_code}'}, 502)

        auth_data    = r.json()
        user_id      = auth_data['User']['Id']
        access_token = auth_data['AccessToken']
        display_name = auth_data['User'].get('Name', body.username)

        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db['sessions'].insert_one({
            '_id': session_id, 'userId': user_id, 'jellyfinToken': access_token,
            'jellyfinUserId': user_id, 'username': display_name,
            'createdAt': datetime.now(timezone.utc), 'expiresAt': expires_at,
        })
        await db['users'].update_one(
            {'userId': user_id},
            {'$setOnInsert': {'userId': user_id, 'username': display_name, 'role': 'adult',
                              'maxRating': '', 'createdAt': datetime.now(timezone.utc)},
             '$set': {'lastLogin': datetime.now(timezone.utc)}},
            upsert=True
        )
        user_profile = await db['users'].find_one({'userId': user_id})
        prefs        = await db['preferences'].find_one({'userId': user_id})

        data = JSONResponse({
            'success': True,
            'user': {'id': user_id, 'name': display_name, 'role': (user_profile or {}).get('role', 'adult')},
            'onboardingComplete': bool(prefs and prefs.get('onboardingComplete')),
        })
        data.set_cookie('dagzflix_session', session_id, max_age=7*24*3600,
                        httponly=True, samesite='lax', path='/')
        return data
    except Exception as e:
        logger.error(f'Login error: {e}')
        return JSONResponse({'success': False, 'error': str(e)}, 500)

@api_router.post('/auth/logout')
async def auth_logout(request: Request):
    session_id = request.cookies.get('dagzflix_session')
    if session_id:
        await db['sessions'].delete_one({'_id': session_id})
    resp = JSONResponse({'success': True})
    resp.delete_cookie('dagzflix_session')
    return resp

@api_router.get('/auth/session')
async def auth_session(request: Request):
    session = await get_session(request)
    if not session:
        return {'authenticated': False}
    prefs       = await db['preferences'].find_one({'userId': session['userId']})
    user_profile= await db['users'].find_one({'userId': session['userId']})
    return {
        'authenticated': True,
        'user': {
            'id': session['userId'], 'name': session['username'],
            'jellyfinUserId': session['jellyfinUserId'],
            'role': (user_profile or {}).get('role', 'adult'),
        },
        'onboardingComplete': bool(prefs and prefs.get('onboardingComplete')),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Media Library
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/media/library')
async def media_library(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config = await get_config()
    url = request.url
    params = {
        'IncludeItemTypes': request.query_params.get('type', 'Movie'),
        'Limit': request.query_params.get('limit', '1000'),
        'StartIndex': request.query_params.get('startIndex', '0'),
        'SortBy': request.query_params.get('sortBy', 'DateCreated'),
        'SortOrder': request.query_params.get('sortOrder', 'Descending'),
        'Recursive': 'true',
        'Fields': 'Overview,Genres,CommunityRating,OfficialRating,PremiereDate,RunTimeTicks,People,ProviderIds,MediaSources,Studios',
        'ImageTypeLimit': '1',
        'EnableImageTypes': 'Primary,Backdrop,Thumb',
    }
    if g := request.query_params.get('genres'):    params['Genres'] = g
    if g := request.query_params.get('genreIds'):  params['GenreIds'] = g
    if s := request.query_params.get('studios'):   params['Studios'] = s
    if q := request.query_params.get('searchTerm'):params['SearchTerm'] = q
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items',
                params=params, headers={'X-Emby-Token': session['jellyfinToken']}
            )
        if not r.is_success:
            return {'items': [], 'totalCount': 0}
        data  = r.json()
        items = [map_jellyfin_item(i) for i in data.get('Items', [])]
        items = await inject_favorite_status(items, session['userId'])
        return {'items': items, 'totalCount': data.get('TotalRecordCount', 0)}
    except Exception as e:
        logger.error(f'media_library: {e}')
        return {'items': [], 'totalCount': 0}

@api_router.get('/media/genres')
async def media_genres(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config = await get_config()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Genres',
                params={'UserId': session['jellyfinUserId'], 'SortBy': 'SortName', 'SortOrder': 'Ascending'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        data = r.json()
        return {'genres': [{'id': g['Id'], 'name': g['Name']} for g in data.get('Items', [])]}
    except Exception:
        return {'genres': []}

# ─────────────────────────────────────────────────────────────────────────────
# Media Detail
# ─────────────────────────────────────────────────────────────────────────────
def parse_id(raw_id: str):
    s = str(raw_id or '')
    if s.startswith('tmdb-'):
        parts = s.split('-')
        if len(parts) >= 3 and parts[1] in ('tv', 'movie'):
            return '-'.join(parts[2:]), parts[1]
        return s.replace('tmdb-', ''), None
    return s, None

@api_router.get('/media/detail')
async def media_detail(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config      = await get_config()
    raw_id      = request.query_params.get('id', '')
    item_id, forced_type = parse_id(raw_id)

    # Try Jellyfin first
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/{item_id}',
                params={'Fields': 'Overview,Genres,CommunityRating,OfficialRating,PremiereDate,RunTimeTicks,People,ProviderIds,MediaSources,Studios,Taglines,HasSubtitles,ChildCount'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        if r.is_success:
            jf = r.json()
            tmdb_id = extract_tmdb_id(jf.get('ProviderIds') or {})
            people = []
            for p in (jf.get('People') or []):
                people.append({'Id': p.get('Id'), 'name': p.get('Name', ''), 'role': p.get('Role', ''), 'type': p.get('Type', ''), 'photoUrl': f'/api/proxy/image?itemId={p["Id"]}&type=Primary&maxWidth=200' if p.get('Id') else None})

            # Enrich cast from Jellyseerr
            if tmdb_id and config.get('jellyseerrUrl'):
                try:
                    ep_type = 'tv' if jf.get('Type') == 'Series' else 'movie'
                    async with httpx.AsyncClient(timeout=15) as c2:
                        cr = await c2.get(f'{config["jellyseerrUrl"]}/api/v1/{ep_type}/{tmdb_id}',
                                         params={'language': 'fr'}, headers={'X-Api-Key': config.get('jellyseerrApiKey', '')})
                    if cr.is_success:
                        cdata   = cr.json()
                        raw_c   = cdata.get('credits') or cdata.get('mediaInfo', {}).get('credits') or {}
                        cast    = (raw_c.get('cast') or [])[:15]
                        crew    = [c for c in (raw_c.get('crew') or []) if c.get('job') == 'Director' or c.get('department') == 'Writing'][:6]
                        if cast or crew:
                            people = [{'Id': None, 'tmdbId': p.get('id'), 'name': p.get('name', ''), 'role': p.get('character', ''), 'type': 'Actor', 'photoUrl': f'/api/proxy/tmdb?path={p["profilePath"]}&width=w200' if p.get('profilePath') else None} for p in cast]
                            people += [{'Id': None, 'tmdbId': p.get('id'), 'name': p.get('name', ''), 'role': p.get('job', ''), 'type': 'Director' if p.get('job') == 'Director' else 'Writer', 'photoUrl': f'/api/proxy/tmdb?path={p["profilePath"]}&width=w200' if p.get('profilePath') else None} for p in crew]
                except Exception:
                    pass

            fav = await db['favorites'].find_one({'userId': session['userId'], 'itemId': str(jf['Id'])})
            return {'item': {
                'id': jf['Id'], 'name': jf.get('Name', ''), 'originalTitle': jf.get('OriginalTitle', ''),
                'type': jf.get('Type', ''), 'overview': jf.get('Overview', ''),
                'genres': jf.get('Genres', []), 'communityRating': jf.get('CommunityRating', 0),
                'officialRating': jf.get('OfficialRating', ''), 'premiereDate': jf.get('PremiereDate', ''),
                'year': jf.get('ProductionYear', ''),
                'runtime': round(jf['RunTimeTicks'] / 600000000) if jf.get('RunTimeTicks') else 0,
                'posterUrl': f'/api/proxy/image?itemId={jf["Id"]}&type=Primary&maxWidth=500',
                'backdropUrl': f'/api/proxy/image?itemId={jf["Id"]}&type=Backdrop&maxWidth=1920',
                'people': people, 'providerIds': jf.get('ProviderIds', {}), 'tmdbId': tmdb_id,
                'studios': [s['Name'] for s in (jf.get('Studios') or [])],
                'taglines': jf.get('Taglines', []),
                'isPlayed': (jf.get('UserData') or {}).get('Played', False),
                'playbackPositionTicks': (jf.get('UserData') or {}).get('PlaybackPositionTicks', 0),
                'hasSubtitles': jf.get('HasSubtitles', False),
                'mediaStatus': 5, 'isFavorite': bool(fav),
                'numberOfSeasons': jf.get('ChildCount', 0) if jf.get('Type') == 'Series' else None,
            }}
    except Exception as e:
        logger.error(f'media_detail jellyfin: {e}')

    # Fallback Jellyseerr/TMDB
    if not config.get('jellyseerrUrl'):
        return JSONResponse({'error': 'Media introuvable'}, 404)
    endpoints = [forced_type] if forced_type else ['movie', 'tv']
    tmdb_data = None
    is_tv     = False
    for ep in endpoints:
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/{ep}/{item_id}',
                               params={'language': 'fr'}, headers={'X-Api-Key': config.get('jellyseerrApiKey', '')})
            if r.is_success:
                tmdb_data = r.json()
                is_tv     = (ep == 'tv')
                break
        except Exception:
            continue
    if not tmdb_data:
        return JSONResponse({'error': 'Media introuvable'}, 404)

    local_ids  = await get_local_tmdb_ids(config, session)
    tmdb_str   = str(tmdb_data.get('id', ''))
    is_local   = tmdb_str in local_ids
    local_jf_id= local_ids.get(tmdb_str)
    raw_c      = tmdb_data.get('credits') or {}
    cast_raw   = (raw_c.get('cast') or [])[:15]
    crew_raw   = [c for c in (raw_c.get('crew') or []) if c.get('job') == 'Director' or c.get('department') == 'Writing'][:6]
    people     = [{'Id': None, 'tmdbId': p.get('id'), 'name': p.get('name', ''), 'role': p.get('character', ''), 'type': 'Actor', 'photoUrl': f'/api/proxy/tmdb?path={p["profilePath"]}&width=w200' if p.get('profilePath') else None} for p in cast_raw]
    people    += [{'Id': None, 'tmdbId': p.get('id'), 'name': p.get('name', ''), 'role': p.get('job', ''), 'type': 'Director' if p.get('job') == 'Director' else 'Writer', 'photoUrl': f'/api/proxy/tmdb?path={p["profilePath"]}&width=w200' if p.get('profilePath') else None} for p in crew_raw]
    genre_ids  = tmdb_data.get('genreIds') or tmdb_data.get('genre_ids') or []
    fav        = await db['favorites'].find_one({'userId': session['userId'], 'itemId': tmdb_str})
    return {'item': {
        'id': local_jf_id or tmdb_data['id'], 'tmdbId': tmdb_data['id'],
        'name': tmdb_data.get('title') or tmdb_data.get('name', ''),
        'type': 'Series' if is_tv else 'Movie', 'mediaType': 'tv' if is_tv else 'movie',
        'overview': tmdb_data.get('overview', ''),
        'genres': [TMDB_GENRE_ID_TO_NAME.get(g, '') for g in genre_ids if g in TMDB_GENRE_ID_TO_NAME],
        'communityRating': tmdb_data.get('voteAverage') or tmdb_data.get('vote_average', 0),
        'premiereDate': tmdb_data.get('releaseDate') or tmdb_data.get('firstAirDate', ''),
        'year': ((tmdb_data.get('releaseDate') or tmdb_data.get('firstAirDate') or ''))[:4],
        'runtime': tmdb_data.get('runtime') or (tmdb_data.get('episodeRunTime') or [None])[0] or 0,
        'posterUrl': f'/api/proxy/tmdb?path={tmdb_data["posterPath"]}&width=w500' if tmdb_data.get('posterPath') else '',
        'backdropUrl': f'/api/proxy/tmdb?path={tmdb_data["backdropPath"]}&width=w1280' if tmdb_data.get('backdropPath') else '',
        'people': people, 'providerIds': {'Tmdb': tmdb_str},
        'studios': [c.get('name', '') for c in (tmdb_data.get('productionCompanies') or [])],
        'taglines': [tmdb_data['tagline']] if tmdb_data.get('tagline') else [],
        'isPlayed': False, 'playbackPositionTicks': 0, 'hasSubtitles': False,
        'mediaStatus': 5 if is_local else min((tmdb_data.get('mediaInfo') or {}).get('status', 0), 4),
        'localId': local_jf_id, 'isFavorite': bool(fav),
        'numberOfSeasons': tmdb_data.get('numberOfSeasons') or tmdb_data.get('number_of_seasons', 0) if is_tv else None,
    }}

# ─────────────────────────────────────────────────────────────────────────────
# Stream — Direct Play + HLS with French language selection
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/media/stream')
async def media_stream(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    raw_id  = request.query_params.get('itemId', '')
    audio_index_req   = request.query_params.get('audioIndex')
    subtitle_index_req= request.query_params.get('subtitleIndex')
    force_transcode   = request.query_params.get('forceTranscode', 'false').lower() == 'true'
    # Client reports HEVC support
    client_hevc_support = request.query_params.get('hevcSupport', 'false').lower() == 'true'

    item_id, _ = parse_id(raw_id)
    if not item_id:
        return JSONResponse({'error': 'itemId requis'}, 400)

    # Resolve TMDB ID to Jellyfin ID if needed
    if raw_id.startswith('tmdb-') or (item_id.isdigit()):
        local_ids = await get_local_tmdb_ids(config, session)
        jellyfin_id = local_ids.get(item_id)
        if not jellyfin_id:
            return JSONResponse({'error': 'Ce contenu n\'est pas disponible localement.'}, 404)
        item_id = jellyfin_id

    # Protect against Series/Season → find episode
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            info_r = await client.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/{item_id}',
                params={'Fields': 'Type'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        if info_r.is_success:
            info = info_r.json()
            if info.get('Type') in ('Series', 'Season'):
                async with httpx.AsyncClient(timeout=15) as client:
                    ep_r = await client.get(
                        f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items',
                        params={'ParentId': item_id, 'Recursive': 'true',
                                'IncludeItemTypes': 'Episode', 'Limit': '1'},
                        headers={'X-Emby-Token': session['jellyfinToken']}
                    )
                ep_data = ep_r.json()
                if ep_data.get('Items'):
                    item_id = ep_data['Items'][0]['Id']
    except Exception:
        pass

    # PlaybackInfo
    try:
        pb_url = f'{config["jellyfinUrl"]}/Items/{item_id}/PlaybackInfo'
        direct_play_video_codecs = 'h264,vp8,vp9,av1'
        if client_hevc_support:
            direct_play_video_codecs = 'h264,hevc,vp8,vp9,av1'

        async with httpx.AsyncClient(timeout=20) as client:
            pb_r = await client.post(
                pb_url,
                params={'UserId': session['jellyfinUserId'], 'IsPlayback': 'true',
                        'AutoStream': 'true', 'StartTimeTicks': '0'},
                json={
                    'DeviceProfile': {
                        'Name': 'DagzFlix Web',
                        'MaxStreamingBitrate': 140000000,
                        'DirectPlayProfiles': [
                            {'Container': 'mp4,m4v,webm', 'Type': 'Video',
                             'VideoCodec': direct_play_video_codecs,
                             'AudioCodec': 'aac,mp3,opus,vorbis,flac'},
                        ],
                        'TranscodingProfiles': [
                            {'Container': 'ts', 'Type': 'Video', 'AudioCodec': 'aac,mp3',
                             'VideoCodec': 'h264', 'Context': 'Streaming', 'Protocol': 'Http'},
                        ],
                        'SubtitleProfiles': [
                            {'Format': 'vtt', 'Method': 'Hls'},
                            {'Format': 'vtt', 'Method': 'External'},
                        ],
                    },
                    'EnableDirectPlay': not force_transcode,
                    'EnableDirectStream': not force_transcode,
                    'EnableTranscoding': True,
                    'PreferredAudioLanguage': 'fra',
                },
                headers={'Content-Type': 'application/json', 'X-Emby-Token': session['jellyfinToken']}
            )

        if not pb_r.is_success:
            return JSONResponse({'error': f'Jellyfin PlaybackInfo error {pb_r.status_code}'}, 500)

        pb_data = pb_r.json()
        source  = pb_data.get('MediaSources', [{}])[0]
        if not source:
            return JSONResponse({'error': 'Aucune source média trouvée'}, 404)

        play_session_id  = pb_data.get('PlaySessionId', '')
        media_source_id  = source.get('Id', item_id)
        media_streams    = source.get('MediaStreams', [])

        # ── French track auto-selection ──
        if audio_index_req is not None:
            selected_audio   = int(audio_index_req)
            selected_sub     = int(subtitle_index_req) if subtitle_index_req else -1
            language_mode    = 'Manuel'
            sub_vtt_url      = None
            if selected_sub >= 0:
                sub_vtt_url = (f'{config["jellyfinUrl"]}/Videos/{item_id}/{media_source_id}'
                               f'/Subtitles/{selected_sub}/Stream.vtt?api_key={session["jellyfinToken"]}')
        else:
            selected_audio, selected_sub, language_mode, sub_vtt_url = select_french_tracks(
                media_streams, config['jellyfinUrl'], item_id, media_source_id, session['jellyfinToken'])

        # ── Determine play mode ──
        play_method = source.get('SupportsDirectPlay', False) and not force_transcode
        is_direct   = play_method and can_direct_play(source)

        if is_direct and not force_transcode:
            # Direct Play URL
            container = source.get('Container', 'mp4')
            stream_url = (
                f'{config["jellyfinUrl"]}/Videos/{item_id}/stream.{container}'
                f'?Static=true&MediaSourceId={media_source_id}'
                f'&AudioStreamIndex={selected_audio}'
                f'&api_key={session["jellyfinToken"]}'
            )
            play_mode = 'direct'
        else:
            # HLS Transcode URL
            stream_params = {
                'MediaSourceId':              media_source_id,
                'PlaySessionId':              play_session_id,
                'VideoCodec':                 'h264',
                'AudioCodec':                 'aac,mp3',
                'AudioStreamIndex':           str(selected_audio) if selected_audio >= 0 else '-1',
                'SubtitleStreamIndex':        str(selected_sub),
                'VideoBitrate':               '140000000',
                'AudioBitrate':               '320000',
                'MaxFramerate':               '60',
                'MaxWidth':                   '3840',
                'MaxHeight':                  '2160',
                'TranscodingMaxAudioChannels':'6',
                'SegmentContainer':           'ts',
                'MinSegments':                '1',
                'BreakOnNonKeyFrames':        'true',
                'ManifestSubtitles':          'vtt',
                'X-Emby-Token':               session['jellyfinToken'],
            }
            from urllib.parse import urlencode
            stream_url = f'{config["jellyfinUrl"]}/Videos/{item_id}/master.m3u8?{urlencode(stream_params)}'
            play_mode  = 'hls'

        audio_tracks    = [{'index': s['Index'], 'language': s.get('Language', ''), 'title': s.get('DisplayTitle', ''), 'codec': s.get('Codec', ''), 'channels': s.get('Channels', 0), 'isDefault': s.get('Index') == source.get('DefaultAudioStreamIndex')} for s in media_streams if s.get('Type') == 'Audio']
        subtitle_tracks = [{'index': s['Index'], 'language': s.get('Language', ''), 'title': s.get('DisplayTitle', ''), 'codec': s.get('Codec', ''), 'isExternal': s.get('IsExternal', False), 'vttUrl': f'{config["jellyfinUrl"]}/Videos/{item_id}/{media_source_id}/Subtitles/{s["Index"]}/Stream.vtt?api_key={session["jellyfinToken"]}'} for s in media_streams if s.get('Type') == 'Subtitle']

        return {
            'streamUrl': stream_url,
            'playMode': play_mode,
            'playSessionId': play_session_id,
            'mediaSourceId': media_source_id,
            'itemId': item_id,
            'languageMode': language_mode,
            'selectedAudioIndex': selected_audio,
            'selectedSubtitleIndex': selected_sub,
            'subtitleVttUrl': sub_vtt_url,
            'audioTracks': audio_tracks,
            'subtitleTracks': subtitle_tracks,
            'source': {
                'id': source.get('Id'),
                'container': source.get('Container'),
                'name': source.get('Name'),
                'audioStreams': audio_tracks,
                'subtitleStreams': subtitle_tracks,
            }
        }
    except Exception as e:
        logger.error(f'media_stream error: {e}', exc_info=True)
        return JSONResponse({'error': str(e)}, 500)

# ─────────────────────────────────────────────────────────────────────────────
# Progress
# ─────────────────────────────────────────────────────────────────────────────
class ProgressBody(BaseModel):
    itemId: str
    positionTicks: int = 0
    isPaused: bool = False
    isStopped: bool = False
    playSessionId: str = ''
    mediaSourceId: str = ''

@api_router.post('/media/progress')
async def media_progress(body: ProgressBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    item_id, _ = parse_id(body.itemId)

    endpoint = f'{config["jellyfinUrl"]}/Sessions/Playing/Progress'
    if body.isStopped:
        endpoint = f'{config["jellyfinUrl"]}/Sessions/Playing/Stopped'
    elif body.positionTicks == 0:
        endpoint = f'{config["jellyfinUrl"]}/Sessions/Playing'

    payload = {
        'ItemId': item_id, 'PositionTicks': body.positionTicks,
        'IsPaused': body.isPaused, 'PlaySessionId': body.playSessionId,
        'MediaSourceId': body.mediaSourceId or item_id, 'CanSeek': True,
        'PlayMethod': 'Transcode',
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(endpoint, json=payload,
                              headers={'Content-Type': 'application/json',
                                       'X-Emby-Token': session['jellyfinToken']})
        if body.positionTicks > 0:
            watch_sec = round(body.positionTicks / 10_000_000)
            await db['telemetry'].update_one(
                {'userId': session['userId'], 'itemId': item_id, 'action': 'watch'},
                {'$set': {'timestamp': datetime.now(timezone.utc)}, '$inc': {'value': watch_sec}},
                upsert=True
            )
    except Exception as e:
        logger.warning(f'progress report failed: {e}')
    return {'success': True}

# ─────────────────────────────────────────────────────────────────────────────
# Resume / Seasons / Episodes / Next Episode
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/media/resume')
async def media_resume(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/Resume',
                params={'Limit': '20', 'Recursive': 'true',
                        'Fields': 'Overview,Genres,CommunityRating,PremiereDate,RunTimeTicks,MediaSources',
                        'MediaTypes': 'Video', 'ImageTypeLimit': '1', 'EnableImageTypes': 'Primary,Backdrop,Thumb'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        data  = r.json()
        items = [{**map_jellyfin_item(i), 'seriesName': i.get('SeriesName', ''),
                  'playbackPercentage': (i.get('UserData') or {}).get('PlayedPercentage', 0)}
                 for i in data.get('Items', [])]
        return {'items': items}
    except Exception:
        return {'items': []}

@api_router.get('/media/seasons')
async def media_seasons(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config    = await get_config()
    series_id = request.query_params.get('seriesId', '')
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Shows/{series_id}/Seasons',
                params={'UserId': session['jellyfinUserId'],
                        'Fields': 'Overview,PremiereDate,ProviderIds,ChildCount'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        data = r.json()
        seasons = [{'id': s['Id'], 'name': s.get('Name', ''), 'seasonNumber': s.get('IndexNumber', 0),
                    'episodeCount': s.get('ChildCount', 0),
                    'posterUrl': f'/api/proxy/image?itemId={s["Id"]}&type=Primary&maxWidth=500'}
                   for s in data.get('Items', [])]
        return {'seasons': seasons}
    except Exception:
        return {'seasons': []}

@api_router.get('/media/episodes')
async def media_episodes(request: Request):
    session   = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config    = await get_config()
    series_id = request.query_params.get('seriesId', '')
    season_id = request.query_params.get('seasonId', '')
    params    = {
        'UserId': session['jellyfinUserId'],
        'Fields': 'Overview,RunTimeTicks,UserData,MediaSources,ParentIndexNumber,IndexNumber,PremiereDate',
        'Limit': '200',
    }
    if season_id:
        params['SeasonId'] = season_id
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f'{config["jellyfinUrl"]}/Shows/{series_id}/Episodes',
                                 params=params, headers={'X-Emby-Token': session['jellyfinToken']})
        data = r.json()
        episodes = [{'id': e['Id'], 'name': e.get('Name', ''), 'overview': e.get('Overview', ''),
                     'episodeNumber': e.get('IndexNumber', 0), 'seasonNumber': e.get('ParentIndexNumber', 0),
                     'runtime': round(e['RunTimeTicks'] / 600000000) if e.get('RunTimeTicks') else 0,
                     'thumbUrl': f'/api/proxy/image?itemId={e["Id"]}&type=Primary&maxWidth=800',
                     'backdropUrl': f'/api/proxy/image?itemId={e["Id"]}&type=Backdrop&maxWidth=1280',
                     'isPlayed': (e.get('UserData') or {}).get('Played', False)}
                    for e in data.get('Items', [])]
        return {'episodes': episodes}
    except Exception:
        return {'episodes': []}

@api_router.get('/media/next-episode')
async def media_next_episode(request: Request):
    session   = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config    = await get_config()
    series_id = request.query_params.get('seriesId', '')
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/Resume',
                params={'ParentId': series_id, 'Limit': '1', 'Recursive': 'true',
                        'Fields': 'Overview', 'MediaTypes': 'Video'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        d = r.json()
        if d.get('Items'):
            ep = d['Items'][0]
            return {'episodeId': ep['Id'], 'seasonNumber': ep.get('ParentIndexNumber', 1),
                    'episodeNumber': ep.get('IndexNumber', 1), 'name': ep.get('Name', ''), 'found': 'resume'}
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items',
                params={'ParentId': series_id, 'IncludeItemTypes': 'Episode', 'IsPlayed': 'false',
                        'Recursive': 'true', 'SortBy': 'ParentIndexNumber,IndexNumber',
                        'SortOrder': 'Ascending', 'Limit': '1', 'Fields': 'Overview'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        d = r.json()
        if d.get('Items'):
            ep = d['Items'][0]
            return {'episodeId': ep['Id'], 'seasonNumber': ep.get('ParentIndexNumber', 1),
                    'episodeNumber': ep.get('IndexNumber', 1), 'name': ep.get('Name', ''), 'found': 'next-unplayed'}
    except Exception:
        pass
    return JSONResponse({'error': 'Aucun épisode trouvé', 'found': False}, 404)

# ─────────────────────────────────────────────────────────────────────────────
# Requests — Jellyseerr / Radarr / Sonarr
# ─────────────────────────────────────────────────────────────────────────────
class MediaRequestBody(BaseModel):
    mediaType: str
    tmdbId: Optional[str] = None
    itemId: Optional[str] = None
    seasons: Optional[List[int]] = None
    provider: Optional[str] = 'auto'  # 'jellyseerr', 'radarr', 'sonarr', 'auto'
    qualityProfileId: Optional[int] = None
    rootFolderPath: Optional[str] = None

@api_router.post('/media/request')
async def media_request(body: MediaRequestBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()

    tmdb_id, _ = parse_id(body.tmdbId or body.itemId or '')
    if not tmdb_id:
        return JSONResponse({'error': 'TMDB ID requis'}, 400)
    is_tv = body.mediaType == 'tv'

    # Try Radarr/Sonarr directly if configured and provider is not forced to jellyseerr
    if body.provider != 'jellyseerr':
        if not is_tv and config.get('radarrUrl') and config.get('radarrApiKey'):
            try:
                # Look up movie in Radarr
                async with httpx.AsyncClient(timeout=20) as c:
                    lookup = await c.get(f'{config["radarrUrl"]}/api/v3/movie/lookup',
                                        params={'term': f'tmdb:{tmdb_id}'},
                                        headers={'X-Api-Key': config['radarrApiKey']})
                if lookup.is_success and lookup.json():
                    movie = lookup.json()[0]
                    # Add movie to Radarr
                    add_payload = {
                        'tmdbId': int(tmdb_id),
                        'title': movie.get('title', ''),
                        'qualityProfileId': body.qualityProfileId or 1,
                        'rootFolderPath': body.rootFolderPath or movie.get('rootFolderPath', '/movies'),
                        'monitored': True,
                        'addOptions': {'searchForMovie': True},
                    }
                    async with httpx.AsyncClient(timeout=20) as c:
                        r = await c.post(f'{config["radarrUrl"]}/api/v3/movie', json=add_payload,
                                        headers={'X-Api-Key': config['radarrApiKey']})
                    if r.is_success or r.status_code == 400:  # 400 = already exists
                        return {'success': True, 'provider': 'radarr', 'message': 'Film ajouté à Radarr'}
            except Exception as e:
                logger.warning(f'Radarr request failed: {e}')

        if is_tv and config.get('sonarrUrl') and config.get('sonarrApiKey'):
            try:
                async with httpx.AsyncClient(timeout=20) as c:
                    lookup = await c.get(f'{config["sonarrUrl"]}/api/v3/series/lookup',
                                        params={'term': f'tmdb:{tmdb_id}'},
                                        headers={'X-Api-Key': config['sonarrApiKey']})
                if lookup.is_success and lookup.json():
                    series = lookup.json()[0]
                    add_payload = {
                        'tvdbId': series.get('tvdbId'),
                        'title': series.get('title', ''),
                        'qualityProfileId': body.qualityProfileId or 1,
                        'rootFolderPath': body.rootFolderPath or series.get('rootFolderPath', '/tv'),
                        'monitored': True,
                        'addOptions': {'searchForMissingEpisodes': True},
                        'seasons': series.get('seasons', []),
                    }
                    async with httpx.AsyncClient(timeout=20) as c:
                        r = await c.post(f'{config["sonarrUrl"]}/api/v3/series', json=add_payload,
                                        headers={'X-Api-Key': config['sonarrApiKey']})
                    if r.is_success or r.status_code == 400:
                        return {'success': True, 'provider': 'sonarr', 'message': 'Série ajoutée à Sonarr'}
            except Exception as e:
                logger.warning(f'Sonarr request failed: {e}')

    # Fallback: Jellyseerr
    if not config.get('jellyseerrUrl'):
        return JSONResponse({'error': 'Aucun service de requête configuré'}, 400)
    req_body: dict = {'mediaType': body.mediaType, 'mediaId': int(tmdb_id)}
    if is_tv and body.seasons:
        req_body['seasons'] = body.seasons
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f'{config["jellyseerrUrl"]}/api/v1/request', json=req_body,
                            headers={'X-Api-Key': config['jellyseerrApiKey']})
        if r.status_code == 409:
            return {'success': True, 'alreadyRequested': True, 'provider': 'jellyseerr'}
        if not r.is_success:
            return JSONResponse({'error': f'Jellyseerr error {r.status_code}'}, 500)
        return {'success': True, 'provider': 'jellyseerr', 'request': r.json()}
    except Exception as e:
        return JSONResponse({'error': str(e)}, 500)

@api_router.get('/media/status')
async def media_status(request: Request):
    session   = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config    = await get_config()
    raw_id    = request.query_params.get('id', '')
    raw_tmdb  = request.query_params.get('tmdbId', '')
    media_type= request.query_params.get('mediaType', 'movie')
    item_id, _ = parse_id(raw_id)
    tmdb_id, _ = parse_id(raw_tmdb)

    jf_available   = False
    local_id       = None
    seerr_status   = None

    if item_id:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(
                    f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/{item_id}',
                    params={'Fields': 'ChildCount,RecursiveItemCount,MediaSources'},
                    headers={'X-Emby-Token': session['jellyfinToken']}
                )
            if r.is_success:
                item = r.json()
                if media_type == 'tv' or item.get('Type') == 'Series':
                    jf_available = (item.get('ChildCount', 0) > 0 or item.get('RecursiveItemCount', 0) > 0)
                else:
                    jf_available = bool(item.get('MediaSources'))
                if jf_available:
                    local_id = item_id
        except Exception:
            pass

    if not jf_available and tmdb_id:
        local_ids = await get_local_tmdb_ids(config, session)
        if str(tmdb_id) in local_ids:
            jf_available = True
            local_id     = local_ids[str(tmdb_id)]

    if tmdb_id and config.get('jellyseerrUrl'):
        try:
            ep = 'tv' if media_type == 'tv' else 'movie'
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/{ep}/{tmdb_id}',
                               headers={'X-Api-Key': config.get('jellyseerrApiKey', '')})
            if r.is_success:
                seerr_status = (r.json().get('mediaInfo') or {}).get('status')
        except Exception:
            pass

    if jf_available:
        status = 'available'
    elif seerr_status in (2, 3, 5):
        status = 'pending'
    elif seerr_status == 4:
        status = 'partial'
    else:
        status = 'not_available'

    return {'status': status, 'jellyfinAvailable': jf_available, 'jellyseerrStatus': seerr_status, 'localId': local_id}

# ─────────────────────────────────────────────────────────────────────────────
# Discovery
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/search')
async def search(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    query   = request.query_params.get('q', '')
    page    = request.query_params.get('page', '1')
    mtype   = request.query_params.get('mediaType', '')
    if not query.strip():
        return {'results': []}

    local_ids = await get_local_tmdb_ids(config, session)

    if config.get('jellyseerrUrl'):
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/search',
                               params={'query': query, 'page': page},
                               headers={'X-Api-Key': config['jellyseerrApiKey']})
            if r.is_success:
                data    = r.json()
                results = [map_tmdb_item(i) for i in data.get('results', []) if i.get('mediaType') in ('movie', 'tv')]
                if mtype == 'movie':   results = [i for i in results if i['type'] == 'Movie']
                elif mtype == 'tv':    results = [i for i in results if i['type'] == 'Series']
                for item in results:
                    tid = str(item.get('tmdbId') or '')
                    if tid and tid in local_ids:
                        item['mediaStatus'] = 5
                        item['localId'] = local_ids[tid]
                results = await inject_favorite_status(results, session['userId'])
                return {'results': results, 'totalPages': data.get('totalPages', 1)}
        except Exception:
            pass

    # Fallback: Jellyfin search
    params = {'SearchTerm': query, 'Recursive': 'true', 'Limit': '20',
              'Fields': 'Overview,Genres,CommunityRating,ProviderIds'}
    if mtype == 'movie':   params['IncludeItemTypes'] = 'Movie'
    elif mtype == 'tv':    params['IncludeItemTypes'] = 'Series'
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items',
                           params=params, headers={'X-Emby-Token': session['jellyfinToken']})
        data    = r.json()
        results = [{**map_jellyfin_item(i), 'mediaStatus': 5} for i in data.get('Items', [])]
        results = await inject_favorite_status(results, session['userId'])
        return {'results': results, 'totalResults': data.get('TotalRecordCount', 0)}
    except Exception:
        return {'results': []}

@api_router.get('/discover')
async def discover(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    dtype   = request.query_params.get('type', 'movies')
    page    = request.query_params.get('page', '1')
    genre   = request.query_params.get('genre', '')
    if not config.get('jellyseerrUrl'):
        return {'results': [], 'totalPages': 0}
    endpoint = 'tv' if dtype == 'tv' else 'movies'
    params   = {'page': page, 'sortBy': 'popularity.desc'}
    if genre:
        g_id = TMDB_GENRE_NAME_TO_ID.get(genre.lower())
        if g_id:
            params['with_genres'] = str(g_id)
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/discover/{endpoint}',
                           params=params, headers={'X-Api-Key': config['jellyseerrApiKey']})
        if not r.is_success:
            return {'results': [], 'totalPages': 0}
        data     = r.json()
        items    = [map_tmdb_item(i, dtype == 'tv') for i in data.get('results', [])]
        local_ids= await get_local_tmdb_ids(config, session)
        for item in items:
            tid = str(item.get('tmdbId') or '')
            if tid and tid in local_ids:
                item['mediaStatus'] = 5
                item['localId'] = local_ids[tid]
        items = await inject_favorite_status(items, session['userId'])
        return {'results': items, 'totalPages': data.get('totalPages', 1)}
    except Exception as e:
        return {'results': [], 'totalPages': 0}

@api_router.get('/recommendations')
async def recommendations(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    prefs   = await db['preferences'].find_one({'userId': session['userId']})

    jf_items, seerr_items = [], []
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items',
                params={'Recursive': 'true', 'Limit': '100', 'IncludeItemTypes': 'Movie,Series',
                        'Fields': 'Overview,Genres,CommunityRating,PremiereDate',
                        'SortBy': 'Random'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        jf_items = [{**map_jellyfin_item(i)} for i in r.json().get('Items', [])]
    except Exception:
        pass

    if config.get('jellyseerrUrl'):
        for ep in ('movies', 'tv'):
            try:
                async with httpx.AsyncClient(timeout=20) as c:
                    r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/discover/{ep}',
                                   params={'page': '1'}, headers={'X-Api-Key': config['jellyseerrApiKey']})
                seerr_items += [map_tmdb_item(i, ep == 'tv') for i in r.json().get('results', [])]
            except Exception:
                pass

    seen = set()
    merged = []
    for item in jf_items + seerr_items:
        key = (item.get('name') or '').lower().strip()
        if key and key not in seen:
            seen.add(key)
            merged.append(item)

    scored = [{**i, 'dagzRank': calculate_dagz_rank(i, prefs, [], {})} for i in merged]
    scored.sort(key=lambda x: x['dagzRank'], reverse=True)
    top = scored[:25]
    top = await inject_favorite_status(top, session['userId'])
    return {'recommendations': top}

# ─────────────────────────────────────────────────────────────────────────────
# Favorites / Preferences / Telemetry / Ratings
# ─────────────────────────────────────────────────────────────────────────────
class FavoriteBody(BaseModel):
    itemId: str
    itemData: Optional[Dict[str, Any]] = None

@api_router.post('/media/favorite')
async def media_favorite(body: FavoriteBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    filt = {'userId': session['userId'], 'itemId': str(body.itemId)}
    existing = await db['favorites'].find_one(filt)
    if existing:
        await db['favorites'].delete_one(filt)
        return {'success': True, 'isFavorite': False}
    else:
        await db['favorites'].insert_one({**filt, 'itemData': body.itemData, 'createdAt': datetime.now(timezone.utc)})
        return {'success': True, 'isFavorite': True}

@api_router.get('/media/favorites')
async def media_favorites(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    favs  = await db['favorites'].find({'userId': session['userId']}).sort('createdAt', -1).to_list(None)
    items = []
    for f in favs:
        if f.get('itemData') and isinstance(f['itemData'], dict):
            items.append(f['itemData'])
        elif f.get('itemId'):
            items.append({'id': f['itemId'], 'name': f'Media #{f["itemId"]}', 'type': 'unknown', 'isFavorite': True})
    return {'items': items}

class PreferencesSaveBody(BaseModel):
    favoriteGenres: Optional[List[str]] = []
    dislikedGenres: Optional[List[str]] = []

@api_router.get('/preferences')
async def preferences_get(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    prefs = await db['preferences'].find_one({'userId': session['userId']})
    return {'preferences': {k: v for k, v in (prefs or {}).items() if k != '_id'} if prefs else {}}

@api_router.post('/preferences')
async def preferences_save(body: PreferencesSaveBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    await db['preferences'].update_one(
        {'userId': session['userId']},
        {'$set': {'userId': session['userId'], 'favoriteGenres': body.favoriteGenres,
                  'dislikedGenres': body.dislikedGenres, 'onboardingComplete': True,
                  'updatedAt': datetime.now(timezone.utc)}},
        upsert=True
    )
    return {'success': True}

class TelemetryClickBody(BaseModel):
    itemId: str
    title: str = ''
    posterUrl: str = ''
    type: str = ''
    genres: List[str] = []

@api_router.post('/telemetry/click')
async def telemetry_click(body: TelemetryClickBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    await db['telemetry'].insert_one({
        'userId': session['userId'], 'itemId': str(body.itemId), 'action': 'click',
        'value': 1, 'title': body.title, 'posterUrl': body.posterUrl,
        'mediaType': body.type, 'genres': body.genres, 'timestamp': datetime.now(timezone.utc),
    })
    return {'success': True}

class RateBody(BaseModel):
    itemId: str
    value: Any
    genres: Optional[List[str]] = []

@api_router.post('/media/rate')
async def media_rate(body: RateBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    rating = max(1, min(5, int(body.value)))
    await db['telemetry'].update_one(
        {'userId': session['userId'], 'itemId': str(body.itemId), 'action': 'rate'},
        {'$set': {'value': rating, 'genres': body.genres, 'timestamp': datetime.now(timezone.utc)}},
        upsert=True
    )
    return {'success': True, 'value': rating}

@api_router.get('/media/rating')
async def media_rating(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    item_id = request.query_params.get('id', '')
    user_r  = await db['telemetry'].find_one({'userId': session['userId'], 'itemId': item_id, 'action': 'rate'})
    global_agg = await db['telemetry'].aggregate([
        {'$match': {'itemId': item_id, 'action': 'rate'}},
        {'$group': {'_id': None, 'avg': {'$avg': '$value'}, 'count': {'$sum': 1}}},
    ]).to_list(1)
    return {
        'rating': user_r['value'] if user_r else None,
        'globalAverage': round(global_agg[0]['avg'], 1) if global_agg else None,
        'totalRatings': global_agg[0]['count'] if global_agg else 0,
    }

# ─────────────────────────────────────────────────────────────────────────────
# Trailer / Collection
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/media/trailer')
async def media_trailer(request: Request):
    session    = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config     = await get_config()
    item_id, _ = parse_id(request.query_params.get('id', ''))
    tmdb_id, _ = parse_id(request.query_params.get('tmdbId', ''))
    media_type = request.query_params.get('mediaType', 'movie')
    title      = request.query_params.get('title', '')
    trailers   = []

    if not tmdb_id and item_id:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(
                    f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/{item_id}',
                    params={'Fields': 'ProviderIds,RemoteTrailers'},
                    headers={'X-Emby-Token': session['jellyfinToken']}
                )
            if r.is_success:
                jf = r.json()
                tmdb_id = tmdb_id or extract_tmdb_id(jf.get('ProviderIds') or {})
                for tr in (jf.get('RemoteTrailers') or []):
                    if tr.get('Url'):
                        trailers.append({'name': tr.get('Name', 'Trailer'), 'url': tr['Url'], 'type': 'Trailer'})
        except Exception:
            pass

    if not trailers and tmdb_id and config.get('jellyseerrUrl'):
        try:
            ep = 'tv' if media_type == 'tv' else 'movie'
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/{ep}/{tmdb_id}',
                               headers={'X-Api-Key': config.get('jellyseerrApiKey', '')})
            if r.is_success:
                d = r.json()
                vids = d.get('videos', {}).get('results', []) or d.get('mediaInfo', {}).get('videos', {}).get('results', [])
                for v in vids:
                    key  = v.get('key')
                    site = v.get('site', 'YouTube').lower()
                    link = v.get('url', '')
                    if not link and key and 'youtube' in site:
                        link = f'https://www.youtube.com/watch?v={key}'
                    if link:
                        trailers.append({'name': v.get('name', 'Bande-annonce'), 'type': v.get('type', 'Trailer'), 'key': key, 'site': site, 'url': link})
        except Exception:
            pass

    if not trailers and title:
        trailers.append({'name': f'Recherche bande-annonce: {title}', 'type': 'Search', 'url': f'https://www.youtube.com/results?search_query={title}+trailer'})

    return {'trailers': trailers[:10]}

@api_router.get('/media/collection')
async def media_collection(request: Request):
    session    = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config     = await get_config()
    item_id, _ = parse_id(request.query_params.get('id', ''))
    tmdb_id, _ = parse_id(request.query_params.get('tmdbId', ''))
    if not tmdb_id or not config.get('jellyseerrUrl'):
        return {'collection': None, 'items': []}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/movie/{tmdb_id}',
                           headers={'X-Api-Key': config.get('jellyseerrApiKey', '')})
        if not r.is_success:
            return {'collection': None, 'items': []}
        d    = r.json()
        coll = d.get('belongsToCollection') or d.get('collection')
        if not coll or not coll.get('id'):
            return {'collection': None, 'items': []}
        parts = coll.get('parts', [])
        items = [map_tmdb_item(p, False) for p in parts]
        return {'collection': {'id': coll['id'], 'name': coll.get('name', ''), 'overview': coll.get('overview', '')}, 'items': items}
    except Exception:
        return {'collection': None, 'items': []}

# ─────────────────────────────────────────────────────────────────────────────
# Person Detail
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/person/detail')
async def person_detail(request: Request):
    session  = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config   = await get_config()
    raw_id   = request.query_params.get('id', '')
    person_id, _ = parse_id(raw_id)
    # Numeric → TMDB person via Jellyseerr
    if person_id.isdigit() and config.get('jellyseerrUrl'):
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/person/{person_id}',
                               params={'language': 'fr'}, headers={'X-Api-Key': config['jellyseerrApiKey']})
                cr = await c.get(f'{config["jellyseerrUrl"]}/api/v1/person/{person_id}/combined_credits',
                                params={'language': 'fr'}, headers={'X-Api-Key': config['jellyseerrApiKey']})
            person_info = r.json() if r.is_success else {}
            cred_data   = cr.json() if cr.is_success else {}
            cast        = (cred_data.get('cast') or [])
            items       = []
            seen = set()
            for c in cast:
                key = str(c.get('id', ''))
                if key not in seen:
                    seen.add(key)
                    items.append({**map_tmdb_item(c), 'role': c.get('character', '')})
            items.sort(key=lambda x: int(x.get('year') or 0), reverse=True)
            return {'person': {
                'id': person_id, 'name': person_info.get('name', ''),
                'overview': person_info.get('biography', ''),
                'birthDate': person_info.get('birthday', ''),
                'photoUrl': f'/api/proxy/tmdb?path={person_info["profilePath"]}&width=w400' if person_info.get('profilePath') else '',
            }, 'items': items[:30]}
        except Exception as e:
            return JSONResponse({'error': str(e)}, 500)
    # Jellyfin person
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items/{person_id}',
                params={'Fields': 'ProviderIds,Overview,PremiereDate'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        person = r.json() if r.is_success else None
        if not person:
            return JSONResponse({'error': 'Personne introuvable'}, 404)
        async with httpx.AsyncClient(timeout=15) as c:
            ir = await c.get(
                f'{config["jellyfinUrl"]}/Users/{session["jellyfinUserId"]}/Items',
                params={'PersonIds': person_id, 'Recursive': 'true', 'IncludeItemTypes': 'Movie,Series',
                        'Fields': 'Overview,ProviderIds,CommunityRating,PremiereDate,RunTimeTicks'},
                headers={'X-Emby-Token': session['jellyfinToken']}
            )
        items = [map_jellyfin_item(i) for i in (ir.json() if ir.is_success else {}).get('Items', [])]
        return {'person': {
            'id': person['Id'], 'name': person.get('Name', ''),
            'overview': person.get('Overview', ''), 'birthDate': person.get('PremiereDate', ''),
            'photoUrl': f'/api/proxy/image?itemId={person["Id"]}&type=Primary&maxWidth=400',
        }, 'items': items}
    except Exception as e:
        return JSONResponse({'error': str(e)}, 500)

# ─────────────────────────────────────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/admin/users')
async def admin_users(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    profile = await db['users'].find_one({'userId': session['userId']})
    if not profile or profile.get('role') != 'admin':
        return JSONResponse({'error': 'Accès réservé aux administrateurs'}, 403)
    users = await db['users'].find({}, {'_id': 0}).to_list(None)
    return {'users': users}

class UpdateUserBody(BaseModel):
    userId: str
    role: Optional[str] = None
    maxRating: Optional[str] = None

@api_router.post('/admin/users/update')
async def admin_update_user(body: UpdateUserBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    profile = await db['users'].find_one({'userId': session['userId']})
    if not profile or profile.get('role') != 'admin':
        return JSONResponse({'error': 'Accès réservé aux administrateurs'}, 403)
    upd: dict = {}
    if body.role:      upd['role'] = body.role
    if body.maxRating is not None: upd['maxRating'] = body.maxRating
    if upd:
        await db['users'].update_one({'userId': body.userId}, {'$set': upd})
    return {'success': True}

@api_router.get('/admin/telemetry')
async def admin_telemetry(request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    profile = await db['users'].find_one({'userId': session['userId']})
    if not profile or profile.get('role') != 'admin':
        return JSONResponse({'error': 'Accès réservé aux administrateurs'}, 403)
    clicks = await db['telemetry'].aggregate([
        {'$match': {'action': 'click'}},
        {'$group': {'_id': '$itemId', 'title': {'$first': '$title'}, 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 20},
    ]).to_list(20)
    return {'topClicks': clicks, 'totalEvents': await db['telemetry'].count_documents({})}

# ─────────────────────────────────────────────────────────────────────────────
# Proxy
# ─────────────────────────────────────────────────────────────────────────────
@api_router.get('/proxy/image')
async def proxy_image(request: Request):
    config  = await get_config()
    if not config:
        return Response('Not configured', status_code=503)
    raw_id, _ = parse_id(request.query_params.get('itemId', ''))
    img_type  = request.query_params.get('type', 'Primary')
    max_width = request.query_params.get('maxWidth', '400')
    headers   = {}
    if config.get('jellyfinApiKey'):
        headers['X-Emby-Token'] = config['jellyfinApiKey']
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f'{config["jellyfinUrl"]}/Items/{raw_id}/Images/{img_type}',
                           params={'maxWidth': max_width}, headers=headers)
        if not r.is_success:
            return Response('Not found', status_code=404)
        ct = r.headers.get('content-type', 'image/jpeg')
        return Response(r.content, media_type=ct, headers={'Cache-Control': 'public, max-age=86400'})
    except Exception:
        return Response('Error', status_code=500)

@api_router.get('/proxy/tmdb')
async def proxy_tmdb(request: Request):
    path  = request.query_params.get('path', '')
    width = request.query_params.get('width', 'w400')
    if not path:
        return Response('Missing path', status_code=400)
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f'https://image.tmdb.org/t/p/{width}{path}')
        if not r.is_success:
            return Response('Not found', status_code=404)
        return Response(r.content, media_type=r.headers.get('content-type', 'image/jpeg'),
                       headers={'Cache-Control': 'public, max-age=86400'})
    except Exception:
        return Response('Error', status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# Onboarding wizard
# ─────────────────────────────────────────────────────────────────────────────
class WizardDiscoverBody(BaseModel):
    mood: Optional[str] = None
    era: Optional[str] = None
    duration: Optional[str] = None
    mediaType: Optional[str] = 'movie'
    excludeIds: Optional[List[str]] = []

@api_router.post('/wizard/discover')
async def wizard_discover(body: WizardDiscoverBody, request: Request):
    session = await get_session(request)
    if not session:
        return JSONResponse({'error': 'Non authentifié'}, 401)
    config  = await get_config()
    if not config.get('jellyseerrUrl'):
        return {'perfectMatch': None, 'alternatives': []}
    is_tv    = body.mediaType == 'tv'
    endpoint = 'tv' if is_tv else 'movies'
    mood_genre_map = {
        'fun': ['comedy', 'family', 'animation'], 'love': ['romance', 'drama'],
        'adrenaline': ['action', 'thriller', 'adventure'], 'dark': ['thriller', 'horror', 'mystery'],
        'cinema': ['adventure', 'science fiction', 'drama'],
    }
    mood_genres  = mood_genre_map.get(body.mood or '', [])
    tmdb_genre_ids = [TMDB_GENRE_NAME_TO_ID.get(g) for g in mood_genres if TMDB_GENRE_NAME_TO_ID.get(g)]
    prefs        = await db['preferences'].find_one({'userId': session['userId']})
    all_items    = []
    try:
        params = {'page': '1', 'sortBy': 'vote_count.desc'}
        if tmdb_genre_ids:
            params['with_genres'] = ','.join(str(g) for g in tmdb_genre_ids)
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/discover/{endpoint}',
                           params=params, headers={'X-Api-Key': config['jellyseerrApiKey']})
        all_items = [map_tmdb_item(i, is_tv) for i in r.json().get('results', [])]
    except Exception:
        pass
    if not all_items:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f'{config["jellyseerrUrl"]}/api/v1/discover/{endpoint}',
                               params={'page': '1', 'sortBy': 'popularity.desc'},
                               headers={'X-Api-Key': config['jellyseerrApiKey']})
            all_items = [map_tmdb_item(i, is_tv) for i in r.json().get('results', [])]
        except Exception:
            pass
    exclude = set(body.excludeIds or [])
    all_items = [i for i in all_items if str(i.get('tmdbId', '')) not in exclude]
    scored = sorted([{**i, 'dagzRank': calculate_dagz_rank(i, prefs, [], {})} for i in all_items],
                   key=lambda x: x['dagzRank'], reverse=True)
    top     = scored[:8]
    import random
    picked  = random.choice(top) if top else None
    others  = [i for i in scored if not picked or (i.get('id') != picked.get('id'))][:12]
    return {'perfectMatch': picked, 'alternatives': others}

# ─────────────────────────────────────────────────────────────────────────────
# Include router
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(api_router)

@app.on_event('shutdown')
async def shutdown():
    _client.close()
