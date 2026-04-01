import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, api } from '../lib/dagzflix';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../components/ui/accordion';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, Check, X } from 'lucide-react';
import { toast } from 'sonner';

export default function SetupPage() {
  const navigate = useNavigate();
  const { onSetupComplete } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState({});
  
  const [config, setConfig] = useState({
    jellyfinUrl: '',
    jellyfinApiKey: '',
    jellyseerrUrl: '',
    jellyseerrApiKey: '',
    radarrUrl: '',
    radarrApiKey: '',
    sonarrUrl: '',
    sonarrApiKey: ''
  });

  const handleChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setTestResults(prev => ({ ...prev, [field.replace('Url', '').replace('ApiKey', '')]: undefined }));
  };

  const testConnection = async (type, url, apiKey) => {
    if (!url.trim()) {
      toast.error('URL requise');
      return;
    }
    
    setTestResults(prev => ({ ...prev, [type]: 'testing' }));
    
    try {
      const result = await api('setup/test', {
        method: 'POST',
        body: JSON.stringify({ type, url: url.trim(), apiKey: apiKey?.trim() || '' })
      });
      
      if (result.success) {
        setTestResults(prev => ({ ...prev, [type]: 'success' }));
        toast.success(`${type} connecté avec succès`);
      } else {
        setTestResults(prev => ({ ...prev, [type]: 'error' }));
        toast.error(result.error || 'Erreur de connexion');
      }
    } catch (error) {
      setTestResults(prev => ({ ...prev, [type]: 'error' }));
      toast.error(error.message || 'Erreur de connexion');
    }
  };

  const handleSave = async () => {
    if (!config.jellyfinUrl.trim()) {
      toast.error('L\'URL Jellyfin est requise');
      return;
    }
    
    setLoading(true);
    try {
      await api('setup/save', {
        method: 'POST',
        body: JSON.stringify(config)
      });
      
      toast.success('Configuration sauvegardée avec succès !');
      onSetupComplete();
      navigate('/login');
    } catch (error) {
      toast.error(error.message || 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const TestButton = ({ type, url, apiKey }) => {
    const status = testResults[type];
    return (
      <Button
        type="button"
        variant="outline"
        size="sm"
        data-testid={`setup-test-${type}-button`}
        onClick={() => testConnection(type, url, apiKey)}
        disabled={!url.trim() || status === 'testing'}
        className="glass-control text-[color:var(--fg)]"
      >
        {status === 'testing' && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
        {status === 'success' && <Check className="w-4 h-4 mr-2 text-[color:var(--success)]" />}
        {status === 'error' && <X className="w-4 h-4 mr-2 text-[color:var(--danger)]" />}
        {status === 'testing' ? 'Test...' : 'Tester'}
      </Button>
    );
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] flex items-center justify-center p-4 hero-gradient">
      <Card className="w-full max-w-2xl glass-strong border-white/10 shadow-[var(--shadow)]">
        <CardHeader>
          <CardTitle className="text-3xl font-bold text-gradient">Configuration DagzFlix</CardTitle>
          <CardDescription className="text-[color:var(--fg-muted)]">
            Configurez vos services pour commencer à utiliser DagzFlix
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Accordion type="single" collapsible defaultValue="jellyfin" className="w-full">
            {/* Jellyfin */}
            <AccordionItem value="jellyfin" className="border-white/10">
              <AccordionTrigger className="hover:no-underline text-[color:var(--fg)]">
                <div className="flex items-center gap-2">
                  Jellyfin
                  {testResults.jellyfin === 'success' && <Check className="w-4 h-4 text-[color:var(--success)]" />}
                  {testResults.jellyfin === 'error' && <X className="w-4 h-4 text-[color:var(--danger)]" />}
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="jellyfinUrl" className="text-[color:var(--fg-muted)]">URL du serveur *</Label>
                  <Input
                    id="jellyfinUrl"
                    data-testid="setup-jellyfin-url-input"
                    placeholder="https://jellyfin.example.com"
                    value={config.jellyfinUrl}
                    onChange={(e) => handleChange('jellyfinUrl', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="jellyfinApiKey" className="text-[color:var(--fg-muted)]">Clé API (optionnelle pour le test)</Label>
                  <Input
                    id="jellyfinApiKey"
                    data-testid="setup-jellyfin-apikey-input"
                    type="password"
                    placeholder="Entrez votre clé API Jellyfin"
                    value={config.jellyfinApiKey}
                    onChange={(e) => handleChange('jellyfinApiKey', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                <TestButton type="jellyfin" url={config.jellyfinUrl} apiKey={config.jellyfinApiKey} />
              </AccordionContent>
            </AccordionItem>

            {/* Jellyseerr */}
            <AccordionItem value="jellyseerr" className="border-white/10">
              <AccordionTrigger className="hover:no-underline text-[color:var(--fg)]">
                <div className="flex items-center gap-2">
                  Jellyseerr (Optionnel)
                  {testResults.jellyseerr === 'success' && <Check className="w-4 h-4 text-[color:var(--success)]" />}
                  {testResults.jellyseerr === 'error' && <X className="w-4 h-4 text-[color:var(--danger)]" />}
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="jellyseerrUrl" className="text-[color:var(--fg-muted)]">URL</Label>
                  <Input
                    id="jellyseerrUrl"
                    data-testid="setup-jellyseerr-url-input"
                    placeholder="https://jellyseerr.example.com"
                    value={config.jellyseerrUrl}
                    onChange={(e) => handleChange('jellyseerrUrl', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="jellyseerrApiKey" className="text-[color:var(--fg-muted)]">Clé API</Label>
                  <Input
                    id="jellyseerrApiKey"
                    data-testid="setup-jellyseerr-apikey-input"
                    type="password"
                    placeholder="Clé API Jellyseerr"
                    value={config.jellyseerrApiKey}
                    onChange={(e) => handleChange('jellyseerrApiKey', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                {config.jellyseerrUrl && <TestButton type="jellyseerr" url={config.jellyseerrUrl} apiKey={config.jellyseerrApiKey} />}
              </AccordionContent>
            </AccordionItem>

            {/* Radarr */}
            <AccordionItem value="radarr" className="border-white/10">
              <AccordionTrigger className="hover:no-underline text-[color:var(--fg)]">
                <div className="flex items-center gap-2">
                  Radarr (Optionnel)
                  {testResults.radarr === 'success' && <Check className="w-4 h-4 text-[color:var(--success)]" />}
                  {testResults.radarr === 'error' && <X className="w-4 h-4 text-[color:var(--danger)]" />}
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="radarrUrl" className="text-[color:var(--fg-muted)]">URL</Label>
                  <Input
                    id="radarrUrl"
                    data-testid="setup-radarr-url-input"
                    placeholder="https://radarr.example.com"
                    value={config.radarrUrl}
                    onChange={(e) => handleChange('radarrUrl', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="radarrApiKey" className="text-[color:var(--fg-muted)]">Clé API</Label>
                  <Input
                    id="radarrApiKey"
                    data-testid="setup-radarr-apikey-input"
                    type="password"
                    placeholder="Clé API Radarr"
                    value={config.radarrApiKey}
                    onChange={(e) => handleChange('radarrApiKey', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                {config.radarrUrl && <TestButton type="radarr" url={config.radarrUrl} apiKey={config.radarrApiKey} />}
              </AccordionContent>
            </AccordionItem>

            {/* Sonarr */}
            <AccordionItem value="sonarr" className="border-white/10">
              <AccordionTrigger className="hover:no-underline text-[color:var(--fg)]">
                <div className="flex items-center gap-2">
                  Sonarr (Optionnel)
                  {testResults.sonarr === 'success' && <Check className="w-4 h-4 text-[color:var(--success)]" />}
                  {testResults.sonarr === 'error' && <X className="w-4 h-4 text-[color:var(--danger)]" />}
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label htmlFor="sonarrUrl" className="text-[color:var(--fg-muted)]">URL</Label>
                  <Input
                    id="sonarrUrl"
                    data-testid="setup-sonarr-url-input"
                    placeholder="https://sonarr.example.com"
                    value={config.sonarrUrl}
                    onChange={(e) => handleChange('sonarrUrl', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sonarrApiKey" className="text-[color:var(--fg-muted)]">Clé API</Label>
                  <Input
                    id="sonarrApiKey"
                    data-testid="setup-sonarr-apikey-input"
                    type="password"
                    placeholder="Clé API Sonarr"
                    value={config.sonarrApiKey}
                    onChange={(e) => handleChange('sonarrApiKey', e.target.value)}
                    className="glass border-white/10 text-[color:var(--fg)]"
                  />
                </div>
                {config.sonarrUrl && <TestButton type="sonarr" url={config.sonarrUrl} apiKey={config.sonarrApiKey} />}
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Alert className="glass border-white/10">
            <AlertDescription className="text-[color:var(--fg-muted)] text-sm">
              * Jellyfin est requis. Les autres services sont optionnels et peuvent être configurés plus tard.
            </AlertDescription>
          </Alert>

          <Button
            onClick={handleSave}
            disabled={loading || !config.jellyfinUrl.trim()}
            data-testid="setup-save-button"
            className="w-full bg-[color:var(--primary)] hover:brightness-110 text-white font-semibold py-6 rounded-[var(--radius-md)]"
          >
            {loading && <Loader2 className="w-5 h-5 mr-2 animate-spin" />}
            Sauvegarder et continuer
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
