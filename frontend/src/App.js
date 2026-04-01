import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/dagzflix';
import { PlayerProvider } from './lib/dagzflix';
import { Toaster } from './components/ui/sonner';
import './App.css';

// Pages
import SetupPage from './pages/SetupPage';
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import HomePage from './pages/HomePage';
import MoviesPage from './pages/MoviesPage';
import SeriesPage from './pages/SeriesPage';
import SearchPage from './pages/SearchPage';
import MediaDetailPage from './pages/MediaDetailPage';
import FavoritesPage from './pages/FavoritesPage';
import ProfilePage from './pages/ProfilePage';

// Route guard component
function ProtectedRoute({ children }) {
  const { status } = useAuth();

  if (status === 'loading') {
    return (
      <div data-testid="app-loading" className="flex items-center justify-center min-h-screen bg-[color:var(--bg)]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-[color:var(--accent)] border-t-transparent rounded-full animate-spin" />
          <p className="text-[color:var(--fg-muted)]">Chargement...</p>
        </div>
      </div>
    );
  }

  if (status === 'setup') {
    return <Navigate to="/setup" replace />;
  }

  if (status === 'login') {
    return <Navigate to="/login" replace />;
  }

  if (status === 'onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
}

function AppRoutes() {
  const { status } = useAuth();

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/setup" element={<SetupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/onboarding" element={<OnboardingPage />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/movies"
        element={
          <ProtectedRoute>
            <MoviesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/series"
        element={
          <ProtectedRoute>
            <SeriesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/search"
        element={
          <ProtectedRoute>
            <SearchPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/media/:id"
        element={
          <ProtectedRoute>
            <MediaDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/favorites"
        element={
          <ProtectedRoute>
            <FavoritesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <PlayerProvider>
        <BrowserRouter>
          <div className="App">
            <AppRoutes />
            <Toaster position="top-right" richColors />
          </div>
        </BrowserRouter>
      </PlayerProvider>
    </AuthProvider>
  );
}

export default App;
