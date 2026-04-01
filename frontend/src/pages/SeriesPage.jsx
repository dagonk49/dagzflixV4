import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { MediaGrid } from '../components/MediaGrid';
import { cachedApi, invalidateCache } from '../lib/dagzflix';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Search } from 'lucide-react';

export default function SeriesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [series, setSeries] = useState([]);
  const [genres, setGenres] = useState([]);
  const [filters, setFilters] = useState({
    searchTerm: '',
    genre: '',
    sortBy: 'DateCreated',
    sortOrder: 'Descending'
  });

  useEffect(() => {
    loadGenres();
  }, []);

  useEffect(() => {
    loadSeries();
  }, [filters]);

  const loadGenres = async () => {
    try {
      const result = await cachedApi('media/genres');
      setGenres(result.genres || []);
    } catch (error) {
      console.error('Error loading genres:', error);
    }
  };

  const loadSeries = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        type: 'Series',
        limit: '100',
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder
      });

      if (filters.searchTerm.trim()) {
        params.append('searchTerm', filters.searchTerm.trim());
      }

      if (filters.genre) {
        params.append('genres', filters.genre);
      }

      const result = await cachedApi(`media/library?${params.toString()}`);
      setSeries(result.items || []);
    } catch (error) {
      console.error('Error loading series:', error);
      setSeries([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    invalidateCache('media/library');
    setFilters(prev => ({ ...prev, [key]: value }));
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
      
      <div className="px-4 sm:px-6 lg:px-10 pt-8 pb-24 lg:pb-12">
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold mb-2 text-[color:var(--fg)]">Séries</h1>
          <p className="text-base md:text-lg text-[color:var(--fg-muted)]">
            Explorez votre bibliothèque de séries
          </p>
        </div>

        {/* Filters */}
        <div className="sticky top-0 z-30 glass-strong rounded-[var(--radius-lg)] p-4 mb-8 border border-white/10">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[color:var(--fg-subtle)]" />
              <Input
                placeholder="Rechercher une série..."
                value={filters.searchTerm}
                onChange={(e) => handleFilterChange('searchTerm', e.target.value)}
                className="pl-10 glass border-white/10 text-[color:var(--fg)]"
                data-testid="series-search-input"
              />
            </div>

            <Select value={filters.genre} onValueChange={(value) => handleFilterChange('genre', value)}>
              <SelectTrigger className="glass border-white/10 text-[color:var(--fg)]" data-testid="series-genre-filter">
                <SelectValue placeholder="Tous les genres" />
              </SelectTrigger>
              <SelectContent className="glass-strong border-white/10">
                <SelectItem value="">Tous les genres</SelectItem>
                {genres.map((genre) => (
                  <SelectItem key={genre.id} value={genre.name}>{genre.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.sortBy} onValueChange={(value) => handleFilterChange('sortBy', value)}>
              <SelectTrigger className="glass border-white/10 text-[color:var(--fg)]" data-testid="series-sort-filter">
                <SelectValue placeholder="Trier par" />
              </SelectTrigger>
              <SelectContent className="glass-strong border-white/10">
                <SelectItem value="DateCreated">Date d'ajout</SelectItem>
                <SelectItem value="SortName">Titre</SelectItem>
                <SelectItem value="PremiereDate">Date de sortie</SelectItem>
                <SelectItem value="CommunityRating">Note</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Grid */}
        <MediaGrid
          items={series}
          loading={loading}
          onPlay={handlePlay}
          onViewDetail={handleViewDetail}
          onToggleFavorite={handleToggleFavorite}
        />
      </div>
    </div>
  );
}
