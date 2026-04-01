import React from 'react';
import { Navbar } from '../components/Navbar';
import { useAuth } from '../lib/dagzflix';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { User, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, onLogout } = useAuth();

  const handleLogout = async () => {
    await onLogout();
    toast.success('Déconnexion réussie');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] lg:pl-20">
      <Navbar />
      
      <div className="px-4 sm:px-6 lg:px-10 pt-8 pb-24 lg:pb-12">
        <div className="mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold mb-2 text-[color:var(--fg)]">Profil</h1>
          <p className="text-base md:text-lg text-[color:var(--fg-muted)]">
            Gérez votre compte et vos préférences
          </p>
        </div>

        <div className="max-w-2xl space-y-6">
          <Card className="glass-strong border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-[color:var(--fg)]">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[color:var(--primary)] to-[color:var(--accent)] flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                {user?.name || 'Utilisateur'}
              </CardTitle>
              <CardDescription className="text-[color:var(--fg-muted)]">
                ID: {user?.id}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-[color:var(--fg-muted)]">Rôle:</span>
                <Badge variant="outline" className="border-white/20 text-[color:var(--fg-muted)]">
                  {user?.role || 'Utilisateur'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-strong border-white/10">
            <CardHeader>
              <CardTitle className="text-[color:var(--fg)]">Actions du compte</CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleLogout}
                variant="destructive"
                data-testid="profile-logout-button"
                className="w-full bg-[color:var(--danger)] hover:brightness-110 text-white"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Se déconnecter
              </Button>
            </CardContent>
          </Card>

          <Card className="glass-strong border-white/10">
            <CardHeader>
              <CardTitle className="text-[color:var(--fg)]">Information</CardTitle>
              <CardDescription className="text-[color:var(--fg-muted)]">
                DagzFlix version 1.0.0
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-[color:var(--fg-subtle)]">
              <p>Lecteur multimédia avec support HEVC/H.265</p>
              <p className="mt-2">Sélection automatique audio français (FR/VFQ/VOSTFR)</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
