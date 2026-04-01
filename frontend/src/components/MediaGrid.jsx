import React from 'react';
import { PosterCard } from './PosterCard';
import { Skeleton } from './ui/skeleton';

export const MediaGrid = ({ items, loading, onPlay, onViewDetail, onToggleFavorite }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 lg:gap-5">
        {[...Array(12)].map((_, i) => (
          <Skeleton key={i} className="aspect-[2/3] rounded-[var(--radius-md)]" />
        ))}
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-lg text-[color:var(--fg-muted)] mb-2">Aucun contenu trouvé</p>
        <p className="text-sm text-[color:var(--fg-subtle)]">Essayez de modifier vos filtres</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 lg:gap-5">
      {items.map((item) => (
        <PosterCard
          key={item.id}
          item={item}
          onPlay={onPlay}
          onViewDetail={onViewDetail}
          onToggleFavorite={onToggleFavorite}
        />
      ))}
    </div>
  );
};
