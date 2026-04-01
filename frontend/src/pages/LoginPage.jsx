import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, api } from '../lib/dagzflix';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const navigate = useNavigate();
  const { onLogin } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!credentials.username.trim()) {
      toast.error('Veuillez entrer un nom d\'utilisateur');
      return;
    }

    setLoading(true);
    try {
      const result = await api('auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials)
      });

      if (result.success) {
        toast.success('Connexion réussie !');
        onLogin(result.user, result.onboardingComplete);
        navigate('/');
      } else {
        toast.error(result.error || 'Erreur de connexion');
      }
    } catch (error) {
      toast.error(error.message || 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] flex items-center justify-center p-4 hero-gradient noise-overlay">
      <Card className="w-full max-w-md glass-strong border-white/10 shadow-[var(--shadow)]">
        <CardHeader className="space-y-1">
          <CardTitle className="text-3xl font-bold text-gradient text-center">DagzFlix</CardTitle>
          <CardDescription className="text-[color:var(--fg-muted)] text-center">
            Connectez-vous à votre compte Jellyfin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-[color:var(--fg-muted)]">
                Nom d'utilisateur
              </Label>
              <Input
                id="username"
                data-testid="login-username-input"
                type="text"
                placeholder="Votre nom d'utilisateur"
                value={credentials.username}
                onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                className="glass border-white/10 text-[color:var(--fg)] placeholder:text-[color:var(--fg-subtle)]"
                disabled={loading}
                autoComplete="username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-[color:var(--fg-muted)]">
                Mot de passe
              </Label>
              <Input
                id="password"
                data-testid="login-password-input"
                type="password"
                placeholder="Votre mot de passe"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                className="glass border-white/10 text-[color:var(--fg)] placeholder:text-[color:var(--fg-subtle)]"
                disabled={loading}
                autoComplete="current-password"
              />
            </div>

            <Button
              type="submit"
              disabled={loading || !credentials.username.trim()}
              data-testid="login-submit-button"
              className="w-full bg-[color:var(--primary)] hover:brightness-110 text-white font-semibold py-6 rounded-[var(--radius-md)] transition-[filter,background-color]"
            >
              {loading && <Loader2 className="w-5 h-5 mr-2 animate-spin" />}
              {loading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-[color:var(--fg-subtle)]">
            <p>Vos identifiants Jellyfin sont utilisés pour l'authentification</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
