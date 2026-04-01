import React, { useState } from 'react';
import { Star } from 'lucide-react';
import { motion } from 'framer-motion';

export const RatingStars = ({ value = 0, onChange, readonly = false, size = 'md' }) => {
  const [hoverValue, setHoverValue] = useState(0);
  
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const handleClick = (rating) => {
    if (!readonly && onChange) {
      onChange(rating);
    }
  };

  return (
    <div className="flex items-center gap-1" data-testid="rating-stars">
      {[1, 2, 3, 4, 5].map((star) => {
        const isActive = (hoverValue || value) >= star;
        return (
          <motion.button
            key={star}
            type="button"
            disabled={readonly}
            onClick={() => handleClick(star)}
            onMouseEnter={() => !readonly && setHoverValue(star)}
            onMouseLeave={() => !readonly && setHoverValue(0)}
            data-testid={`star-${star}`}
            className={`transition-transform ${
              readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'
            }`}
            whileHover={readonly ? {} : { scale: 1.1 }}
            whileTap={readonly ? {} : { scale: 0.95 }}
          >
            <Star
              className={`${sizes[size]} transition-colors ${
                isActive
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'text-[color:var(--fg-subtle)]'
              }`}
            />
          </motion.button>
        );
      })}
      {value > 0 && (
        <span className="ml-2 text-sm text-[color:var(--fg-muted)] font-medium">
          {value}/5
        </span>
      )}
    </div>
  );
};
