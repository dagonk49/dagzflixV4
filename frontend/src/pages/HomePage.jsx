import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { MediaRow } from '../components/MediaRow';
import { cachedApi } from '../lib/dagzflix';
import { Play } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';

export default function HomePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [continueWatching, setContinueWatching] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [discoverMovies, setDiscoverMovies] = useState([]);
  const [discoverSeries, setDiscoverSeries] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [resume, recs, movies, series] = await Promise.all([
        cachedApi('media/resume').catch(() => ({ items: [] })),
        cachedApi('recommendations').catch(() => ({ results: [] })),
        cachedApi('discover?type=movies&page=1').catch(() => ({ results: [] })),
        cachedApi('discover?type=tv&page=1').catch(() => ({ results: [] }))
      ]);

      setContinueWatching(resume.items || []);
      setRecommendations(recs.results || []);
      setDiscoverMovies(movies.results || []);
      setDiscoverSeries(series.results || []);
    } catch (error) {
      console.error('Error loading home data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = (item) => {
    navigate(`/media/${item.id}?autoplay=true`);
  };

  const handleViewDetail = (item) => {
    navigate(`/media/${item.id}`);
  };

  const handleToggleFavorite = async (item) => {
    // TODO: Implement favorite toggle
    console.log('Toggle favorite:', item);
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
      <Navbar />
      
      <div className="pb-20 lg:pb-8">
        {/* Hero section */}
        {continueWatching.length > 0 && (
          <div className="relative h-[70vh] mb-8">
            <div
              className="absolute inset-0 bg-cover bg-center"
              style={{
                backgroundImage: `url(${continueWatching[0].backdropUrl || continueWatching[0].posterUrl})`,
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-t from-[color:var(--bg)] via-[color:var(--bg)]/60 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--bg)] via-transparent to-transparent" />
            </div>

            <div className="relative h-full flex items-end px-4 sm:px-6 lg:px-10 pb-16">
              <div className="max-w-2xl space-y-4">
                <div className="flex items-center gap-2">
                  <Badge className="bg-[color:var(--primary)] text-white border-0">En cours</Badge>
                  {continueWatching[0].type && (
                    <Badge variant="outline" className="border-white/20 text-[color:var(--fg-muted)]">
                      {continueWatching[0].type === 'Movie' ? 'Film' : 'Série'}
                    </Badge>
                  )}
                </div>
                
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[color:var(--fg)]">
                  {continueWatching[0].name}
                </h1>
                
                {continueWatching[0].overview && (
                  <p className="text-base md:text-lg text-[color:var(--fg-muted)] line-clamp-3 max-w-xl">
                    {continueWatching[0].overview}
                  </p>
                )}

                <div className="flex items-center gap-3">
                  <Button
                    onClick={() => handlePlay(continueWatching[0])}
                    data-testid="hero-play-button"
                    className="bg-[color:var(--primary)] hover:brightness-110 text-white font-semibold px-8 py-6 rounded-[var(--radius-md)]"
                  >
                    <Play className="w-5 h-5 mr-2" fill="currentColor" />
                    Reprendre
                  </Button>
                  <Button
                    onClick={() => handleViewDetail(continueWatching[0])}
                    variant="outline"
                    data-testid="hero-info-button"
                    className="glass-control text-[color:var(--fg)] font-semibold px-8 py-6 rounded-[var(--radius-md)]"
                  >
                    Plus d'infos
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content rows */}
        <div className="space-y-8">
          {continueWatching.length > 0 && (
            <MediaRow
              title="Continuer à regarder"
              items={continueWatching}
              loading={loading}
              onPlay={handlePlay}
              onViewDetail={handleViewDetail}
              onToggleFavorite={handleToggleFavorite}
            />
          )}

          <MediaRow
            title="Films populaires"
            items={discoverMovies.slice(0, 12)}
            loading={loading}
            onPlay={handlePlay}
            onViewDetail={handleViewDetail}
            onToggleFavorite={handleToggleFavorite}
            viewAllLink="/movies"
          />

          <MediaRow
            title="Séries populaires"
            items={discoverSeries.slice(0, 12)}
            loading={loading}
            onPlay={handlePlay}
            onViewDetail={handleViewDetail}
            onToggleFavorite={handleToggleFavorite}
            viewAllLink="/series"
          />

          {recommendations.length > 0 && (
            <MediaRow
              title="Recommandé pour vous"
              items={recommendations.slice(0, 12)}
              loading={loading}
              onPlay={handlePlay}
              onViewDetail={handleViewDetail}
              onToggleFavorite={handleToggleFavorite}
            />
          )}
        </div>
      </div>
    </div>
  );
}
