import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Film, Tv, Search, Heart, User, LogOut } from 'lucide-react';
import { useAuth } from '../lib/dagzflix';
import { Button } from './ui/button';
import { toast } from 'sonner';

export const Navbar = () => {
  const location = useLocation();
  const { onLogout, user } = useAuth();

  const navItems = [
    { path: '/', icon: Home, label: 'Accueil', testId: 'nav-home' },
    { path: '/movies', icon: Film, label: 'Films', testId: 'nav-movies' },
    { path: '/series', icon: Tv, label: 'Séries', testId: 'nav-series' },
    { path: '/search', icon: Search, label: 'Recherche', testId: 'nav-search' },
    { path: '/favorites', icon: Heart, label: 'Favoris', testId: 'nav-favorites' },
  ];

  const handleLogout = async () => {
    await onLogout();
    toast.success('Déconnexion réussie');
  };

  return (
    <>
      {/* Desktop nav */}
      <nav data-testid="app-desktop-nav" className="hidden lg:flex fixed left-0 top-0 bottom-0 w-20 hover:w-60 flex-col py-6 glass-strong z-50 transition-all duration-300 group">
        <div className="flex flex-col h-full">
          <div className="px-4 mb-8">
            <h1 className="text-2xl font-bold text-gradient whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">DagzFlix</h1>
            <div className="lg:group-hover:hidden text-2xl font-bold text-gradient">D</div>
          </div>
          
          <div className="flex-1 flex flex-col gap-2 px-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={item.testId}
                  className={`flex items-center gap-4 px-4 py-3 rounded-[var(--radius-md)] transition-[background-color,border-color] ${
                    isActive
                      ? 'bg-[color:var(--primary)] text-white'
                      : 'text-[color:var(--fg-muted)] hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="mt-auto px-3 space-y-2">
            <Link
              to="/profile"
              data-testid="nav-profile"
              className="flex items-center gap-4 px-4 py-3 rounded-[var(--radius-md)] text-[color:var(--fg-muted)] hover:bg-white/10 transition-[background-color]"
            >
              <User className="w-5 h-5 flex-shrink-0" />
              <span className="whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">{user?.name || 'Profil'}</span>
            </Link>
            <Button
              onClick={handleLogout}
              data-testid="nav-logout"
              variant="ghost"
              className="w-full flex items-center gap-4 px-4 py-3 text-[color:var(--fg-muted)] hover:bg-white/10"
            >
              <LogOut className="w-5 h-5 flex-shrink-0" />
              <span className="whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">Déconnexion</span>
            </Button>
          </div>
        </div>
      </nav>

      {/* Mobile bottom nav */}
      <nav data-testid="app-mobile-bottom-nav" className="lg:hidden fixed bottom-0 left-0 right-0 glass-strong border-t border-white/10 z-50">
        <div className="flex justify-around items-center py-2 px-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                data-testid={`${item.testId}-mobile`}
                className={`flex flex-col items-center gap-1 px-3 py-2 rounded-[var(--radius-sm)] transition-[background-color,color] ${
                  isActive
                    ? 'text-[color:var(--primary)]'
                    : 'text-[color:var(--fg-subtle)] hover:text-[color:var(--fg)]'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[10px] font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
};
