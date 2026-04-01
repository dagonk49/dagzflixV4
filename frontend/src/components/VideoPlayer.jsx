import React, { useState, useEffect, useRef } from 'react';
import Hls from 'hls.js';
import { X, Play, Pause, Volume2, VolumeX, Maximize, Settings, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { api } from '../lib/dagzflix';

export const VideoPlayer = ({ itemId, onClose }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const controlsTimeoutRef = useRef(null);
  const progressIntervalRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [buffering, setBuffering] = useState(false);

  const [streamData, setStreamData] = useState(null);
  const [selectedAudioIndex, setSelectedAudioIndex] = useState(-1);
  const [selectedSubtitleIndex, setSelectedSubtitleIndex] = useState(-1);

  useEffect(() => {
    loadStream();
    return () => {
      cleanup();
    };
  }, [itemId]);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.volume = volume;
      videoRef.current.muted = muted;
    }
  }, [volume, muted]);

  const cleanup = () => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
  };

  const detectHEVCSupport = async () => {
    if (!navigator.mediaCapabilities) {
      return false;
    }

    try {
      const config = {
        type: 'file',
        video: {
          contentType: 'video/mp4; codecs="hev1.1.6.L93.B0"',
          width: 1920,
          height: 1080,
          bitrate: 10000000,
          framerate: 24
        }
      };
      const result = await navigator.mediaCapabilities.decodingInfo(config);
      return result.supported && result.smooth;
    } catch {
      return false;
    }
  };

  const loadStream = async () => {
    setLoading(true);
    try {
      const hevcSupport = await detectHEVCSupport();
      
      const params = new URLSearchParams({
        itemId,
        hevcSupport: hevcSupport.toString()
      });

      const data = await api(`media/stream?${params.toString()}`);
      setStreamData(data);
      setSelectedAudioIndex(data.selectedAudioIndex);
      setSelectedSubtitleIndex(data.selectedSubtitleIndex);

      await initializePlayer(data);
    } catch (error) {
      console.error('Error loading stream:', error);
      toast.error('Erreur lors du chargement de la vidéo');
    } finally {
      setLoading(false);
    }
  };

  const initializePlayer = async (data) => {
    const video = videoRef.current;
    if (!video) return;

    cleanup();

    if (data.playMode === 'hls') {
      if (Hls.isSupported()) {
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: false,
          backBufferLength: 90,
          maxBufferLength: 30,
          maxMaxBufferLength: 600
        });

        hls.loadSource(data.streamUrl);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          video.play().catch(() => {});
        });

        hls.on(Hls.Events.ERROR, (event, errorData) => {
          if (errorData.fatal) {
            console.error('HLS fatal error:', errorData);
            toast.error('Erreur de lecture HLS');
          }
        });

        hlsRef.current = hls;
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = data.streamUrl;
        video.addEventListener('loadedmetadata', () => {
          video.play().catch(() => {});
        });
      }
    } else {
      // Direct play
      video.src = data.streamUrl;
      
      // Add subtitle track if available
      if (data.subtitleVttUrl) {
        const track = video.addTextTrack('subtitles', 'Français', 'fr');
        track.mode = 'showing';
      }

      video.addEventListener('loadedmetadata', () => {
        video.play().catch(() => {});
      });
    }

    // Progress reporting
    progressIntervalRef.current = setInterval(() => {
      if (video && !video.paused) {
        reportProgress(false);
      }
    }, 10000);
  };

  const reportProgress = async (isStopped = false) => {
    if (!streamData || !videoRef.current) return;

    try {
      await api('media/progress', {
        method: 'POST',
        body: JSON.stringify({
          itemId: streamData.itemId,
          positionTicks: Math.floor(videoRef.current.currentTime * 10000000),
          isPaused: videoRef.current.paused,
          isStopped,
          playSessionId: streamData.playSessionId,
          mediaSourceId: streamData.mediaSourceId
        })
      });
    } catch (error) {
      console.error('Progress report error:', error);
    }
  };

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      video.play();
      setPlaying(true);
    } else {
      video.pause();
      setPlaying(false);
    }
  };

  const handleSeek = (value) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = value[0];
    setCurrentTime(value[0]);
  };

  const handleVolumeChange = (value) => {
    setVolume(value[0]);
    if (value[0] > 0 && muted) {
      setMuted(false);
    }
  };

  const toggleMute = () => {
    setMuted(!muted);
  };

  const toggleFullscreen = () => {
    const player = videoRef.current?.parentElement;
    if (!document.fullscreenElement) {
      player?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      if (playing) {
        setShowControls(false);
      }
    }, 2500);
  };

  const handleClose = async () => {
    await reportProgress(true);
    cleanup();
    onClose();
  };

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-[color:var(--accent)] animate-spin" />
          <p className="text-white">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black"
      onMouseMove={handleMouseMove}
      data-testid="video-player"
    >
      <video
        ref={videoRef}
        className="w-full h-full"
        onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
        onDurationChange={(e) => setDuration(e.target.duration)}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onWaiting={() => setBuffering(true)}
        onPlaying={() => setBuffering(false)}
        onClick={togglePlay}
      />

      {/* Buffering indicator */}
      {buffering && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <Loader2 className="w-12 h-12 text-white animate-spin" />
        </div>
      )}

      {/* Controls overlay */}
      <div
        className={`absolute inset-0 transition-opacity duration-300 ${
          showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      >
        {/* Top bar */}
        <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/80 to-transparent flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              onClick={handleClose}
              variant="ghost"
              size="icon"
              data-testid="player-back-button"
              className="text-white hover:bg-white/20"
            >
              <X className="w-6 h-6" />
            </Button>
            {streamData && (
              <div className="flex items-center gap-2">
                <Badge className="bg-[color:var(--primary)] text-white border-0">
                  {streamData.playMode === 'direct' ? 'Direct Play' : 'HLS'}
                </Badge>
                <Badge variant="outline" className="border-white/40 text-white">
                  {streamData.languageMode}
                </Badge>
              </div>
            )}
          </div>

          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                data-testid="player-settings-button"
                className="text-white hover:bg-white/20"
              >
                <Settings className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent className="glass-strong border-white/10">
              <SheetHeader>
                <SheetTitle className="text-[color:var(--fg)]">Paramètres</SheetTitle>
              </SheetHeader>
              <div className="space-y-6 mt-6">
                {streamData?.audioTracks && streamData.audioTracks.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-sm text-[color:var(--fg-muted)]">Piste audio</label>
                    <Select
                      value={selectedAudioIndex.toString()}
                      onValueChange={(value) => setSelectedAudioIndex(parseInt(value))}
                      data-testid="player-audio-menu"
                    >
                      <SelectTrigger className="glass border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-strong">
                        {streamData.audioTracks.map((track) => (
                          <SelectItem key={track.index} value={track.index.toString()}>
                            {track.title || `${track.language || 'Inconnu'} (${track.codec})`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {streamData?.subtitleTracks && streamData.subtitleTracks.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-sm text-[color:var(--fg-muted)]">Sous-titres</label>
                    <Select
                      value={selectedSubtitleIndex.toString()}
                      onValueChange={(value) => setSelectedSubtitleIndex(parseInt(value))}
                      data-testid="player-subtitle-menu"
                    >
                      <SelectTrigger className="glass border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-strong">
                        <SelectItem value="-1">Désactivé</SelectItem>
                        {streamData.subtitleTracks.map((track) => (
                          <SelectItem key={track.index} value={track.index.toString()}>
                            {track.title || `${track.language || 'Inconnu'}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>

        {/* Bottom controls */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
          <div className="space-y-3">
            {/* Progress bar */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-white font-mono min-w-[60px]">
                {formatTime(currentTime)}
              </span>
              <Slider
                value={[currentTime]}
                max={duration || 100}
                step={1}
                onValueChange={handleSeek}
                data-testid="player-seek-slider"
                className="flex-1"
              />
              <span className="text-xs text-white font-mono min-w-[60px] text-right">
                {formatTime(duration)}
              </span>
            </div>

            {/* Controls row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  onClick={togglePlay}
                  variant="ghost"
                  size="icon"
                  data-testid="player-play-toggle"
                  className="text-white hover:bg-white/20"
                >
                  {playing ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" fill="currentColor" />}
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    onClick={toggleMute}
                    variant="ghost"
                    size="icon"
                    data-testid="player-volume-toggle"
                    className="text-white hover:bg-white/20"
                  >
                    {muted || volume === 0 ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                  </Button>
                  <Slider
                    value={[muted ? 0 : volume]}
                    max={1}
                    step={0.1}
                    onValueChange={handleVolumeChange}
                    data-testid="player-volume-slider"
                    className="w-24"
                  />
                </div>
              </div>

              <Button
                onClick={toggleFullscreen}
                variant="ghost"
                size="icon"
                data-testid="player-fullscreen-button"
                className="text-white hover:bg-white/20"
              >
                <Maximize className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
