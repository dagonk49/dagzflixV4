import React from 'react';
import { Play, Info, Heart, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card';

export const PosterCard = ({ item, onPlay, onViewDetail, onToggleFavorite }) => {
  const statusLabels = {
    5: 'Disponible',
    4: 'Partiel',
    3: 'En cours',
    2: 'En attente',
    1: 'Non disponible',
    0: 'Non disponible'
  };

  const statusColors = {
    5: 'bg-[color:var(--success)]',
    4: 'bg-[color:var(--info)]',
    3: 'bg-[color:var(--warning)]',
    2: 'bg-[color:var(--warning)]',
    1: 'bg-[color:var(--danger)]',
    0: 'bg-[color:var(--danger)]'
  };

  return (
    <HoverCard openDelay={300}>
      <HoverCardTrigger asChild>
        <motion.div
          data-testid={`poster-card-${item.id}`}
          className="group relative overflow-hidden rounded-[var(--radius-md)] border border-white/10 bg-white/5 poster-card cursor-pointer"
          whileHover={{ scale: 1.02, y: -4 }}
          transition={{ duration: 0.24 }}
          onClick={() => onViewDetail && onViewDetail(item)}
        >
          <div className="aspect-[2/3] relative">
            {item.posterUrl ? (
              <img
                src={item.posterUrl}
                alt={item.name}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-[color:var(--bg-elev-2)] to-[color:var(--bg-elev-1)] flex items-center justify-center">
                <span className="text-4xl font-bold text-[color:var(--fg-subtle)]">{item.name?.[0] || '?'}</span>
              </div>
            )}
            
            {/* Overlay gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            {/* Quick actions */}
            <div className="absolute inset-x-0 bottom-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center gap-2">
              {item.mediaStatus === 5 && onPlay && (
                <Button
                  size="sm"
                  data-testid={`poster-card-${item.id}-play`}
                  onClick={(e) => { e.stopPropagation(); onPlay(item); }}
                  className="bg-[color:var(--primary)] hover:brightness-110 text-white rounded-full w-8 h-8 p-0 flex items-center justify-center"
                >
                  <Play className="w-4 h-4" fill="currentColor" />
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                data-testid={`poster-card-${item.id}-info`}
                onClick={(e) => { e.stopPropagation(); onViewDetail && onViewDetail(item); }}
                className="bg-white/10 hover:bg-white/20 text-white rounded-full w-8 h-8 p-0 flex items-center justify-center"
              >
                <Info className="w-4 h-4" />
              </Button>
              {onToggleFavorite && (
                <Button
                  size="sm"
                  variant="ghost"
                  data-testid={`poster-card-${item.id}-favorite`}
                  onClick={(e) => { e.stopPropagation(); onToggleFavorite(item); }}
                  className="bg-white/10 hover:bg-white/20 text-white rounded-full w-8 h-8 p-0 flex items-center justify-center ml-auto"
                >
                  <Heart className={`w-4 h-4 ${item.isFavorite ? 'fill-[color:var(--primary)]' : ''}`} />
                </Button>
              )}
            </div>
          </div>

          {/* Status badge */}
          {item.mediaStatus !== undefined && (
            <div className="absolute top-2 right-2">
              <Badge
                data-testid={`poster-card-${item.id}-status`}
                className={`${statusColors[item.mediaStatus] || statusColors[0]} text-white text-[10px] px-2 py-0.5 rounded-full border-0`}
              >
                {statusLabels[item.mediaStatus] || 'Inconnu'}
              </Badge>
            </div>
          )}
        </motion.div>
      </HoverCardTrigger>
      <HoverCardContent side="right" className="w-80 glass-strong border-white/10">
        <div className="space-y-2">
          <h4 className="font-semibold text-sm">{item.name}</h4>
          {item.year && <p className="text-xs text-[color:var(--fg-muted)]">{item.year}</p>}
          {item.overview && (
            <p className="text-xs text-[color:var(--fg-subtle)] line-clamp-3">{item.overview}</p>
          )}
          {item.genres && item.genres.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {item.genres.slice(0, 3).map((genre) => (
                <span
                  key={genre}
                  className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[color:var(--fg-subtle)]"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}
        </div>
      </HoverCardContent>
    </HoverCard>
  );
};
