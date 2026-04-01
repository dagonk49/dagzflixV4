import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { VideoPlayer } from '../components/VideoPlayer';
import { RatingStars } from '../components/RatingStars';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Play, Info, Heart, Download, Star, Calendar, Clock } from 'lucide-react';
import { cachedApi, api } from '../lib/dagzflix';
import { toast } from 'sonner';

export default function MediaDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState(null);
  const [seasons, setSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(null);
  const [episodes, setEpisodes] = useState([]);
  const [showPlayer, setShowPlayer] = useState(false);
  const [playingItemId, setPlayingItemId] = useState(null);
  const [userRating, setUserRating] = useState(0);

  useEffect(() => {
    loadDetails();
  }, [id]);

  useEffect(() => {
    if (item) {
      loadUserRating();
      if (searchParams.get('autoplay') === 'true') {
        handlePlay();
      }
    }
  }, [item]);

  useEffect(() => {
    if (selectedSeason) {
      loadEpisodes(selectedSeason.id);
    }
  }, [selectedSeason]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const result = await cachedApi(`media/detail?id=${id}`);
      setItem(result.item);

      if (result.item.type === 'Series') {
        await loadSeasons(result.item.id);
      }
    } catch (error) {
      console.error('Error loading details:', error);
      toast.error('Erreur lors du chargement des détails');
    } finally {
      setLoading(false);
    }
  };

  const loadSeasons = async (seriesId) => {
    try {
      const result = await cachedApi(`media/seasons?seriesId=${seriesId}`);
      setSeasons(result.seasons || []);
      if (result.seasons && result.seasons.length > 0) {
        setSelectedSeason(result.seasons[0]);
      }
    } catch (error) {
      console.error('Error loading seasons:', error);
    }
  };

  const loadEpisodes = async (seasonId) => {
    try {
      const result = await cachedApi(`media/episodes?seriesId=${item.id}&seasonId=${seasonId}`);
      setEpisodes(result.episodes || []);
    } catch (error) {
      console.error('Error loading episodes:', error);
    }
  };

  const loadUserRating = async () => {
    try {
      const result = await cachedApi(`media/rating?itemId=${id}`);
      setUserRating(result.rating || 0);
    } catch (error) {
      console.error('Error loading rating:', error);
    }
  };

  const handleRatingChange = async (rating) => {
    try {
      await api('media/rate', {
        method: 'POST',
        body: JSON.stringify({
          itemId: id,
          value: rating,
          genres: item.genres || []
        })
      });
      setUserRating(rating);
      toast.success(`✨ Noté ${rating}/5 - DagzRank mis à jour !`);
    } catch (error) {
      toast.error('Erreur lors de la notation');
    }
  };

  const handlePlay = (episodeId = null) => {
    const idToPlay = episodeId || item.id;
    setPlayingItemId(idToPlay);
    setShowPlayer(true);
  };

  const handleRequest = async () => {
    if (!item) return;

    try {
      const mediaType = item.type === 'Series' ? 'tv' : 'movie';
      const tmdbId = item.tmdbId || item.id;

      const result = await api('media/request', {
        method: 'POST',
        body: JSON.stringify({
          mediaType,
          tmdbId: tmdbId.toString(),
          provider: 'auto'
        })
      });

      if (result.success) {
        toast.success(`Demande envoyée avec succès via ${result.provider}`);
      } else {
        toast.error(result.error || 'Erreur lors de la demande');
      }
    } catch (error) {
      toast.error(error.message || 'Erreur lors de la demande');
    }
  };

  const handleToggleFavorite = async () => {
    // TODO: Implement favorite toggle
    toast.info('Fonctionnalité à venir');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
        <Navbar />
        <div className="px-4 sm:px-6 lg:px-10 pt-8 pb-24">
          <Skeleton className="w-full h-[60vh] rounded-[var(--radius-lg)] mb-8" />
          <Skeleton className="h-12 w-2/3 mb-4" />
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-4/5" />
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <p className="text-[color:var(--fg-muted)]">Contenu introuvable</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
      <Navbar />

      {/* Hero section */}
      <div className="relative h-[70vh] mb-8">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(${item.backdropUrl || item.posterUrl})`,
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-t from-[color:var(--bg)] via-[color:var(--bg)]/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--bg)] via-transparent to-transparent" />
        </div>

        <div className="relative h-full flex items-end px-4 sm:px-6 lg:px-10 pb-16">
          <div className="max-w-4xl space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              {item.mediaStatus !== undefined && (
                <Badge
                  className={
                    item.mediaStatus === 5
                      ? 'bg-[color:var(--success)]'
                      : 'bg-[color:var(--warning)]'
                  }
                  data-testid="media-detail-status-badge"
                >
                  {item.mediaStatus === 5 ? 'Disponible' : 'Non disponible'}
                </Badge>
              )}
              {item.type && (
                <Badge variant="outline" className="border-white/20 text-white">
                  {item.type === 'Movie' ? 'Film' : 'Série'}
                </Badge>
              )}
              {item.year && (
                <Badge variant="outline" className="border-white/20 text-white flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {item.year}
                </Badge>
              )}
              {item.runtime > 0 && (
                <Badge variant="outline" className="border-white/20 text-white flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.runtime} min
                </Badge>
              )}
              {item.communityRating > 0 && (
                <Badge variant="outline" className="border-white/20 text-white flex items-center gap-1">
                  <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                  {item.communityRating.toFixed(1)}
                </Badge>
              )}
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white">
              {item.name}
            </h1>

            {item.genres && item.genres.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {item.genres.slice(0, 5).map((genre) => (
                  <span
                    key={genre}
                    className="text-sm px-3 py-1 rounded-full bg-white/10 border border-white/20 text-white"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}

            {item.overview && (
              <p className="text-base md:text-lg text-white/90 line-clamp-4 max-w-2xl">
                {item.overview}
              </p>
            )}

            <div className="flex items-center gap-3 flex-wrap">
              {item.mediaStatus === 5 && (
                <Button
                  onClick={() => handlePlay()}
                  data-testid="media-detail-play-button"
                  className="bg-[color:var(--primary)] hover:brightness-110 text-white font-semibold px-8 py-6 rounded-[var(--radius-md)]"
                >
                  <Play className="w-5 h-5 mr-2" fill="currentColor" />
                  Lecture
                </Button>
              )}
              {item.mediaStatus !== 5 && (
                <Button
                  onClick={handleRequest}
                  data-testid="media-detail-request-button"
                  className="bg-[color:var(--primary)] hover:brightness-110 text-white font-semibold px-8 py-6 rounded-[var(--radius-md)]"
                >
                  <Download className="w-5 h-5 mr-2" />
                  Demander
                </Button>
              )}
              <Button
                onClick={handleToggleFavorite}
                variant="outline"
                data-testid="media-detail-favorite-button"
                className="glass-control text-white font-semibold px-8 py-6 rounded-[var(--radius-md)]"
              >
                <Heart className={`w-5 h-5 mr-2 ${item.isFavorite ? 'fill-[color:var(--primary)]' : ''}`} />
                {item.isFavorite ? 'Retirer' : 'Favoris'}
              </Button>
            </div>

            {/* DagzRank Rating */}
            <div className="flex items-center gap-4 glass-control p-4 rounded-[var(--radius-md)] max-w-fit">
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 text-[color:var(--accent)]" fill="currentColor" />
                <span className="text-sm font-semibold text-[color:var(--fg)]">DagzRank</span>
              </div>
              <RatingStars value={userRating} onChange={handleRatingChange} size="lg" />
            </div>
          </div>
        </div>
      </div>

      {/* Content section */}
      <div className="px-4 sm:px-6 lg:px-10 pb-24 lg:pb-12">
        <Tabs defaultValue="info" className="w-full">
          <TabsList className="glass border border-white/10 mb-6">
            <TabsTrigger value="info">Informations</TabsTrigger>
            {item.type === 'Series' && seasons.length > 0 && (
              <TabsTrigger value="episodes">Épisodes</TabsTrigger>
            )}
            {item.people && item.people.length > 0 && (
              <TabsTrigger value="cast">Distribution</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="info" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-[color:var(--fg-muted)] mb-2">Synopsis</h3>
                <p className="text-[color:var(--fg)]">{item.overview || 'Aucun synopsis disponible'}</p>
              </div>
              {item.studios && item.studios.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-[color:var(--fg-muted)] mb-2">Studios</h3>
                  <p className="text-[color:var(--fg)]">{item.studios.join(', ')}</p>
                </div>
              )}
              {item.taglines && item.taglines.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-[color:var(--fg-muted)] mb-2">Slogan</h3>
                  <p className="text-[color:var(--fg)] italic">"{item.taglines[0]}"</p>
                </div>
              )}
            </div>
          </TabsContent>

          {item.type === 'Series' && seasons.length > 0 && (
            <TabsContent value="episodes" className="space-y-4">
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {seasons.map((season) => (
                  <Button
                    key={season.id}
                    variant={selectedSeason?.id === season.id ? 'default' : 'outline'}
                    onClick={() => setSelectedSeason(season)}
                    className={selectedSeason?.id === season.id ? 'bg-[color:var(--primary)]' : 'glass-control'}
                  >
                    {season.name}
                  </Button>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-4">
                {episodes.map((episode) => (
                  <Card
                    key={episode.id}
                    className="glass-strong border-white/10 p-4 hover:bg-white/10 transition-[background-color] cursor-pointer"
                    onClick={() => handlePlay(episode.id)}
                    data-testid={`episode-${episode.episodeNumber}`}
                  >
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-32 h-20 rounded-[var(--radius-sm)] bg-gradient-to-br from-[color:var(--bg-elev-2)] to-[color:var(--bg-elev-1)] flex items-center justify-center overflow-hidden">
                        {episode.thumbUrl ? (
                          <img src={episode.thumbUrl} alt={episode.name} className="w-full h-full object-cover" />
                        ) : (
                          <Play className="w-8 h-8 text-[color:var(--fg-subtle)]" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-[color:var(--fg-muted)]">
                            Épisode {episode.episodeNumber}
                          </span>
                          {episode.runtime > 0 && (
                            <Badge variant="outline" className="border-white/20 text-[color:var(--fg-subtle)] text-xs">
                              {episode.runtime} min
                            </Badge>
                          )}
                        </div>
                        <h4 className="font-semibold text-[color:var(--fg)] mb-2 truncate">{episode.name}</h4>
                        {episode.overview && (
                          <p className="text-sm text-[color:var(--fg-subtle)] line-clamp-2">{episode.overview}</p>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>
          )}

          {item.people && item.people.length > 0 && (
            <TabsContent value="cast">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {item.people.map((person, index) => (
                  <div key={person.Id || `${person.name}-${index}`} className="text-center">
                    <div className="aspect-square rounded-[var(--radius-md)] bg-gradient-to-br from-[color:var(--bg-elev-2)] to-[color:var(--bg-elev-1)] mb-2 overflow-hidden">
                      {person.photoUrl ? (
                        <img src={person.photoUrl} alt={person.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Info className="w-8 h-8 text-[color:var(--fg-subtle)]" />
                        </div>
                      )}
                    </div>
                    <p className="font-medium text-sm text-[color:var(--fg)] truncate">{person.name}</p>
                    <p className="text-xs text-[color:var(--fg-subtle)] truncate">{person.role || person.type}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
          )}
        </Tabs>
      </div>

      {/* Video player */}
      {showPlayer && playingItemId && (
        <VideoPlayer itemId={playingItemId} onClose={() => setShowPlayer(false)} />
      )}
    </div>
  );
}
