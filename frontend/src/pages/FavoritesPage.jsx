import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { MediaGrid } from '../components/MediaGrid';
import { cachedApi } from '../lib/dagzflix';
import { Heart } from 'lucide-react';

export default function FavoritesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    setLoading(true);
    try {
      // TODO: Implement actual favorites API endpoint
      // For now, showing empty state
      setFavorites([]);
    } catch (error) {
      console.error('Error loading favorites:', error);
      setFavorites([]);
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
    loadFavorites();
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
      <Navbar />
      
      <div className="px-4 sm:px-6 lg:px-10 pt-8 pb-24 lg:pb-12">
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold mb-2 text-[color:var(--fg)]">Favoris</h1>
          <p className="text-base md:text-lg text-[color:var(--fg-muted)]">
            Vos films et séries préférés
          </p>
        </div>

        {favorites.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Heart className="w-16 h-16 text-[color:var(--fg-subtle)] mb-4" />
            <p className="text-lg text-[color:var(--fg-muted)] mb-2">Aucun favori pour le moment</p>
            <p className="text-sm text-[color:var(--fg-subtle)]">Ajoutez des films et séries à vos favoris</p>
          </div>
        ) : (
          <MediaGrid
            items={favorites}
            loading={loading}
            onPlay={handlePlay}
            onViewDetail={handleViewDetail}
            onToggleFavorite={handleToggleFavorite}
          />
        )}
      </div>
    </div>
  );
}
