import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, cachedApi, api, invalidateCache } from '../lib/dagzflix';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Sparkles, Heart, XCircle, Film, Tv, Star, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { onOnboardingComplete } = useAuth();
  
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [genres, setGenres] = useState([]);
  const [preferences, setPreferences] = useState({
    favoriteGenres: [],
    dislikedGenres: [],
    preferredType: '' // movie, tv, both
  });

  const totalSteps = 3;

  useEffect(() => {
    loadGenres();
  }, []);

  const loadGenres = async () => {
    try {
      const result = await cachedApi('media/genres');
      setGenres(result.genres || []);
    } catch (error) {
      console.error('Error loading genres:', error);
    }
  };

  const toggleFavoriteGenre = (genreName) => {
    setPreferences(prev => {
      const newFavorites = prev.favoriteGenres.includes(genreName)
        ? prev.favoriteGenres.filter(g => g !== genreName)
        : [...prev.favoriteGenres, genreName];
      
      // Remove from disliked if added to favorites
      const newDisliked = newFavorites.includes(genreName)
        ? prev.dislikedGenres.filter(g => g !== genreName)
        : prev.dislikedGenres;
      
      return { ...prev, favoriteGenres: newFavorites, dislikedGenres: newDisliked };
    });
  };

  const toggleDislikedGenre = (genreName) => {
    setPreferences(prev => {
      const newDisliked = prev.dislikedGenres.includes(genreName)
        ? prev.dislikedGenres.filter(g => g !== genreName)
        : [...prev.dislikedGenres, genreName];
      
      // Remove from favorites if added to disliked
      const newFavorites = newDisliked.includes(genreName)
        ? prev.favoriteGenres.filter(g => g !== genreName)
        : prev.favoriteGenres;
      
      return { ...prev, favoriteGenres: newFavorites, dislikedGenres: newDisliked };
    });
  };

  const handleNext = () => {
    if (step === 1 && preferences.favoriteGenres.length === 0) {
      toast.error('Sélectionnez au moins un genre favori');
      return;
    }
    if (step === 3 && !preferences.preferredType) {
      toast.error('Sélectionnez une préférence');
      return;
    }
    
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleFinish();
    }
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      await api('preferences/save', {
        method: 'POST',
        body: JSON.stringify({
          ...preferences,
          onboardingComplete: true
        })
      });
      
      invalidateCache('recommendations');
      toast.success('🎉 Profil configuré ! Bienvenue sur DagzFlix');
      onOnboardingComplete();
      navigate('/');
    } catch (error) {
      toast.error(error.message || 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] flex items-center justify-center p-4 hero-gradient noise-overlay">
      <Card className="w-full max-w-4xl glass-strong border-white/10 shadow-[var(--shadow)]">
        <CardHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[color:var(--primary)] to-[color:var(--accent)] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-3xl font-bold text-gradient">DagzRank</CardTitle>
              <CardDescription className="text-[color:var(--fg-muted)]">
                L'algorithme qui vous connaît mieux que Netflix
              </CardDescription>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-[color:var(--fg-muted)]">
              <span>Étape {step} sur {totalSteps}</span>
              <span>{Math.round((step / totalSteps) * 100)}%</span>
            </div>
            <Progress value={(step / totalSteps) * 100} className="h-2" />
          </div>
        </CardHeader>

        <CardContent className="min-h-[400px]">
          <AnimatePresence mode="wait">
            {/* Step 1: Favorite Genres */}
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <Heart className="w-16 h-16 mx-auto mb-4 text-[color:var(--primary)]" />
                  <h2 className="text-2xl font-bold text-[color:var(--fg)] mb-2">
                    Quels genres adorez-vous ?
                  </h2>
                  <p className="text-[color:var(--fg-muted)]">
                    Sélectionnez vos genres préférés (minimum 1)
                  </p>
                </div>

                <div className="flex flex-wrap gap-3 justify-center">
                  {genres.map((genre) => {
                    const isSelected = preferences.favoriteGenres.includes(genre.name);
                    return (
                      <motion.button
                        key={genre.id}
                        onClick={() => toggleFavoriteGenre(genre.name)}
                        data-testid={`favorite-genre-${genre.name}`}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className={`px-6 py-3 rounded-[var(--radius-md)] font-medium transition-all ${
                          isSelected
                            ? 'bg-[color:var(--primary)] text-white shadow-lg scale-105'
                            : 'glass border border-white/10 text-[color:var(--fg)] hover:bg-white/10'
                        }`}
                      >
                        {genre.name}
                      </motion.button>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* Step 2: Disliked Genres */}
            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <XCircle className="w-16 h-16 mx-auto mb-4 text-[color:var(--danger)]" />
                  <h2 className="text-2xl font-bold text-[color:var(--fg)] mb-2">
                    Et ceux que vous évitez ?
                  </h2>
                  <p className="text-[color:var(--fg-muted)]">
                    Sélectionnez les genres que vous n'aimez pas (optionnel)
                  </p>
                </div>

                <div className="flex flex-wrap gap-3 justify-center">
                  {genres.map((genre) => {
                    const isSelected = preferences.dislikedGenres.includes(genre.name);
                    const isFavorite = preferences.favoriteGenres.includes(genre.name);
                    
                    return (
                      <motion.button
                        key={genre.id}
                        onClick={() => toggleDislikedGenre(genre.name)}
                        disabled={isFavorite}
                        data-testid={`disliked-genre-${genre.name}`}
                        whileHover={{ scale: isFavorite ? 1 : 1.05 }}
                        whileTap={{ scale: isFavorite ? 1 : 0.95 }}
                        className={`px-6 py-3 rounded-[var(--radius-md)] font-medium transition-all ${
                          isFavorite
                            ? 'glass border border-white/5 text-[color:var(--fg-subtle)] opacity-50 cursor-not-allowed'
                            : isSelected
                            ? 'bg-[color:var(--danger)] text-white shadow-lg scale-105'
                            : 'glass border border-white/10 text-[color:var(--fg)] hover:bg-white/10'
                        }`}
                      >
                        {genre.name}
                      </motion.button>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* Step 3: Preferred Type */}
            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <Star className="w-16 h-16 mx-auto mb-4 text-[color:var(--accent)]" />
                  <h2 className="text-2xl font-bold text-[color:var(--fg)] mb-2">
                    Plutôt films ou séries ?
                  </h2>
                  <p className="text-[color:var(--fg-muted)]">
                    Indiquez votre préférence générale
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
                  {[
                    { value: 'movie', label: 'Films', icon: Film, color: 'var(--primary)' },
                    { value: 'both', label: 'Les deux', icon: Sparkles, color: 'var(--accent)' },
                    { value: 'tv', label: 'Séries', icon: Tv, color: 'var(--info)' }
                  ].map((option) => {
                    const Icon = option.icon;
                    const isSelected = preferences.preferredType === option.value;
                    return (
                      <motion.button
                        key={option.value}
                        onClick={() => setPreferences(prev => ({ ...prev, preferredType: option.value }))}
                        data-testid={`preferred-type-${option.value}`}
                        whileHover={{ scale: 1.05, y: -4 }}
                        whileTap={{ scale: 0.95 }}
                        className={`p-8 rounded-[var(--radius-lg)] transition-all ${
                          isSelected
                            ? 'glass-strong border-2 shadow-[var(--shadow)] scale-105'
                            : 'glass border border-white/10 hover:border-white/20'
                        }`}
                        style={{
                          borderColor: isSelected ? option.color : undefined
                        }}
                      >
                        <Icon
                          className="w-12 h-12 mx-auto mb-4"
                          style={{ color: isSelected ? option.color : 'var(--fg-muted)' }}
                        />
                        <p className={`text-lg font-semibold ${
                          isSelected ? 'text-[color:var(--fg)]' : 'text-[color:var(--fg-muted)]'
                        }`}>
                          {option.label}
                        </p>
                      </motion.button>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/10">
            {step > 1 ? (
              <Button
                variant="outline"
                onClick={() => setStep(step - 1)}
                className="glass-control text-[color:var(--fg)]">
                Retour
              </Button>
            ) : (
              <div />
            )}

            <Button
              onClick={handleNext}
              disabled={loading}
              data-testid="onboarding-next-button"
              className="bg-[color:var(--primary)] hover:brightness-110 text-white font-semibold px-8 py-6 rounded-[var(--radius-md)]"
            >
              {loading ? 'Sauvegarde...' : step === totalSteps ? 'Terminer' : 'Suivant'}
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
