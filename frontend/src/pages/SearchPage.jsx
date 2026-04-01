import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { MediaGrid } from '../components/MediaGrid';
import { cachedApi } from '../lib/dagzflix';
import { Input } from '../components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Search } from 'lucide-react';

export default function SearchPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [mediaType, setMediaType] = useState('');

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q, mediaType);
    }
  }, [searchParams]);

  const performSearch = async (searchQuery, type) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({ q: searchQuery.trim() });
      if (type) params.append('mediaType', type);

      const result = await cachedApi(`search?${params.toString()}`);
      setResults(result.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      performSearch(query, mediaType);
    }
  };

  const handleTypeChange = (value) => {
    setMediaType(value);
    if (query.trim()) {
      performSearch(query, value);
    }
  };

  const handlePlay = (item) => {
    navigate(`/media/${item.id}?autoplay=true`);
  };

  const handleViewDetail = (item) => {
    navigate(`/media/${item.id}`);
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
      <Navbar />
      
      <div className="px-4 sm:px-6 lg:px-10 pt-8 pb-24 lg:pb-12">
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold mb-2 text-[color:var(--fg)]">Recherche</h1>
          <p className="text-base md:text-lg text-[color:var(--fg-muted)]">
            Recherchez parmi les films et séries disponibles
          </p>
        </div>

        <div className="max-w-4xl mx-auto mb-8 space-y-4">
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[color:var(--fg-subtle)]" />
            <Input
              placeholder="Rechercher un film, une série..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-12 pr-4 py-6 text-lg glass-strong border-white/10 text-[color:var(--fg)] rounded-[var(--radius-lg)]"
              data-testid="search-input"
              autoFocus
            />
          </form>

          <Tabs value={mediaType} onValueChange={handleTypeChange} className="w-full">
            <TabsList className="glass border border-white/10 w-full">
              <TabsTrigger value="" className="flex-1">Tout</TabsTrigger>
              <TabsTrigger value="movie" className="flex-1">Films</TabsTrigger>
              <TabsTrigger value="tv" className="flex-1">Séries</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {query.trim() && (
          <div>
            <p className="text-sm text-[color:var(--fg-muted)] mb-4">
              {loading ? 'Recherche en cours...' : `${results.length} résultat(s) pour "${query}"`}
            </p>
            <MediaGrid
              items={results}
              loading={loading}
              onPlay={handlePlay}
              onViewDetail={handleViewDetail}
            />
          </div>
        )}

        {!query.trim() && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Search className="w-16 h-16 text-[color:var(--fg-subtle)] mb-4" />
            <p className="text-lg text-[color:var(--fg-muted)] mb-2">Recherchez du contenu</p>
            <p className="text-sm text-[color:var(--fg-subtle)]">Entrez un titre de film ou de série</p>
          </div>
        )}
      </div>
    </div>
  );
}
