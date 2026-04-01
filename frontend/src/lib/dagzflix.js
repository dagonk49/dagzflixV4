import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND}/api`;

// ── Cache ──
const _cache = new Map();
const CACHE_TTLS = {
  'setup/check': 120000, 'auth/session': 60000, 'media/library': 300000,
  'media/genres': 600000, 'media/detail': 600000, 'media/seasons': 600000,
  'media/episodes': 600000, 'media/trailer': 3600000, 'media/collection': 3600000,
  'media/status': 60000, 'media/resume': 300000, 'recommendations': 300000,
  'discover': 300000, 'search': 120000,
};
function getTTL(path) {
  for (const [k, v] of Object.entries(CACHE_TTLS)) { if (path.startsWith(k)) return v; }
  return 60000;
}
export function invalidateCache(prefix) {
  for (const k of _cache.keys()) { if (k.startsWith(prefix)) _cache.delete(k); }
}
export function clearCache() { _cache.clear(); }

export async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}/${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith('auth/')) {
      window.dispatchEvent(new CustomEvent('dagzflix:session-expired'));
    }
    const err = new Error(payload?.error || payload?.message || `API error ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return payload;
}

export async function cachedApi(path, options = {}) {
  const isGet = !options.method || options.method === 'GET';
  if (isGet) {
    const hit = _cache.get(path);
    if (hit && Date.now() - hit.ts < getTTL(path)) return hit.data;
  }
  const data = await api(path, options);
  if (isGet && data && !data.error) _cache.set(path, { data, ts: Date.now() });
  return data;
}

// ── Auth Context ──
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    (async () => {
      try {
        const s = await cachedApi('setup/check');
        if (!s.setupComplete) { setStatus('setup'); return; }
        const sess = await cachedApi('auth/session');
        if (sess.authenticated) {
          setUser(sess.user);
          setStatus(sess.onboardingComplete ? 'ready' : 'onboarding');
        } else {
          setStatus('login');
        }
      } catch { setStatus('setup'); }
    })();
  }, []);

  useEffect(() => {
    const handler = () => { clearCache(); setUser(null); setStatus('login'); };
    window.addEventListener('dagzflix:session-expired', handler);
    return () => window.removeEventListener('dagzflix:session-expired', handler);
  }, []);

  const onLogin = useCallback((u, onboardingComplete) => {
    clearCache(); setUser(u); setStatus(onboardingComplete ? 'ready' : 'onboarding');
  }, []);
  const onLogout = useCallback(async () => {
    try { await api('auth/logout', { method: 'POST' }); } catch {}
    clearCache(); setUser(null); setStatus('login');
  }, []);
  const onSetupComplete    = useCallback(() => setStatus('login'), []);
  const onOnboardingComplete = useCallback(() => setStatus('ready'), []);

  return (
    <AuthContext.Provider value={{ user, status, onLogin, onLogout, onSetupComplete, onOnboardingComplete }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

// ── Player Context ──
const PlayerContext = createContext(null);
export function PlayerProvider({ children }) {
  const [playerItem, setPlayerItem] = useState(null);
  const [episodeId, setEpisodeId] = useState(null);
  const play = useCallback((item, epId = null) => { setPlayerItem(item); setEpisodeId(epId); }, []);
  const close = useCallback(() => { setPlayerItem(null); setEpisodeId(null); }, []);
  return (
    <PlayerContext.Provider value={{ playerItem, episodeId, play, close }}>
      {children}
    </PlayerContext.Provider>
  );
}
export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
