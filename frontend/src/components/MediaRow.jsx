import React from 'react';
import { ScrollArea, ScrollBar } from './ui/scroll-area';
import { PosterCard } from './PosterCard';
import { Skeleton } from './ui/skeleton';
import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const MediaRow = ({ title, items, loading, onPlay, onViewDetail, onToggleFavorite, viewAllLink }) => {
  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-32" />
        <div className="flex gap-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="aspect-[2/3] w-40 rounded-[var(--radius-md)]" />
          ))}
        </div>
      </div>
    );
  }

  if (!items || items.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between px-4 sm:px-6 lg:px-10">
        <h2 className="text-lg md:text-xl font-semibold text-[color:var(--fg)]">{title}</h2>
        {viewAllLink && (
          <Link
            to={viewAllLink}
            className="text-sm text-[color:var(--accent)] hover:underline flex items-center gap-1"
          >
            Tout voir <ChevronRight className="w-4 h-4" />
          </Link>
        )}
      </div>
      <ScrollArea className="w-full whitespace-nowrap">
        <div className="flex gap-3 px-4 sm:px-6 lg:px-10 pb-3">
          {items.map((item) => (
            <div key={item.id} className="w-40 flex-shrink-0">
              <PosterCard
                item={item}
                onPlay={onPlay}
                onViewDetail={onViewDetail}
                onToggleFavorite={onToggleFavorite}
              />
            </div>
          ))}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
};
