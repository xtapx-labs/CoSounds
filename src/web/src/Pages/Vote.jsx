import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, LogOut, Bluetooth, Check, X, RefreshCw } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { apiClient } from '../lib/apt';
import { supabase } from '../lib/supabase';

// Django Bluetooth Presence Detection Configuration
const DJANGO_API_URL = import.meta.env.VITE_DJANGO_API_URL || 'http://localhost:8000/api';
const LAPTOP_BLUETOOTH_MAC = import.meta.env.VITE_LAPTOP_BLUETOOTH_MAC || '';
const ENABLE_BLUETOOTH_PRESENCE = !!LAPTOP_BLUETOOTH_MAC;

/**
 * Handle Bluetooth presence detection when user checks in.
 * Registers device on first visit, checks in on subsequent visits.
 */
const handleBluetoothPresence = async () => {
  if (!ENABLE_BLUETOOTH_PRESENCE) return;

  try {
    const session = await supabase.auth.getSession();
    const token = session.data.session?.access_token;

    if (!token) {
      console.warn('⚠️  No auth token available for Bluetooth presence');
      return;
    }

    // Step 1: Check if device is already registered
    const statusResponse = await fetch(`${DJANGO_API_URL}/my-status`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!statusResponse.ok) {
      console.warn('⚠️  Failed to check Bluetooth device status');
      return;
    }

    const status = await statusResponse.json();

    if (!status.has_device) {
      // FIRST TIME - Register device
      console.log('🔵 Registering Bluetooth device for presence detection...');
      const registerResponse = await fetch(`${DJANGO_API_URL}/register-device`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          device_mac: LAPTOP_BLUETOOTH_MAC,
          device_name: 'Demo Laptop'
        })
      });

      if (registerResponse.ok) {
        const result = await registerResponse.json();
        console.log('✅ Bluetooth device registered:', result);
      } else {
        console.warn('⚠️  Device registration failed');
      }
    } else {
      // ALREADY REGISTERED - Check in
      console.log('🔵 Checking in with Bluetooth presence system...');
      const checkinResponse = await fetch(`${DJANGO_API_URL}/check-in`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (checkinResponse.ok) {
        const result = await checkinResponse.json();
        console.log('✅ Bluetooth presence check-in successful:', result);
      } else {
        console.warn('⚠️  Bluetooth check-in failed');
      }
    }
  } catch (error) {
    console.error('❌ Bluetooth presence error:', error);
  }
};

const formatSongTitle = (title = '') =>
  title
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const Vote = () => {
  const { signOut } = useAuth();
  const [currentSong, setCurrentSong] = useState('');
  const [selectedVote, setSelectedVote] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [songName, setSongName] = useState('');
  const [liveSongTitle, setLiveSongTitle] = useState('');
  const [liveSongUpdatedAt, setLiveSongUpdatedAt] = useState(null);
  const [canonicalSong, setCanonicalSong] = useState('');
  const [isLoadingSong, setIsLoadingSong] = useState(true);
  const navigate = useNavigate();
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef(null);
  const [hasActiveSession, setHasActiveSession] = useState(false);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [timerSeconds, setTimerSeconds] = useState(null);
  const [sessionDurationSeconds, setSessionDurationSeconds] = useState(null);

  // Bluetooth state
  const [isBluetoothMenuOpen, setIsBluetoothMenuOpen] = useState(false);
  const [isBluetoothSupported, setIsBluetoothSupported] = useState(false);
  const [isBluetoothConnected, setIsBluetoothConnected] = useState(false);
  const [isBluetoothPairing, setIsBluetoothPairing] = useState(false);
  const [bluetoothDeviceName, setBluetoothDeviceName] = useState(null);
  const [bluetoothDeviceId, setBluetoothDeviceId] = useState(null);
  const [bluetoothError, setBluetoothError] = useState(null);
  const [requiresBluetoothTap, setRequiresBluetoothTap] = useState(false);
  const [isBluetoothAutoReconnecting, setIsBluetoothAutoReconnecting] = useState(false);
  const [bluetoothEnabled, setBluetoothEnabled] = useState(false);
  const bluetoothMenuRef = useRef(null);

  const fetchCurrentSong = useCallback(async (showSpinner = false) => {
    if (showSpinner) setIsLoadingSong(true);
    try {
      // Primary: Get current song from vote history
      const result = await apiClient('/api/current-song');
      const songValue = result?.data?.song || '';

      if (songValue) {
        setCurrentSong(songValue);
        setSongName(songValue);
        setCanonicalSong(songValue);
        console.log('Current song loaded:', songValue);
      } else {
        setCurrentSong('');
        setSongName('No song playing');
        setCanonicalSong('');
        console.log('No current song available');
      }

      // Background: Ping model endpoint to sync recommendation system
      apiClient('/api/model/currentSong')
        .then(modelResult => {
          if (modelResult?.current_song) {
            setLiveSongTitle(modelResult.current_song);
            setLiveSongUpdatedAt(modelResult.played_at || null);
            setCanonicalSong(modelResult.current_song);
          }
        })
        .catch(err => {
          console.log('Model endpoint not available:', err.status);
        });

    } catch (err) {
      console.error('Error loading current song:', err);
      setCurrentSong('');
      setSongName('Error loading song');
      setCanonicalSong('');
    } finally {
      if (showSpinner) setIsLoadingSong(false);
    }
  }, []);

  const syncTimerFromSession = useCallback((data) => {
    if (!data) {
      setTimerSeconds(null);
      setSessionDurationSeconds(null);
      return;
    }

    const expiresAt = data.expires_at ? new Date(data.expires_at).getTime() : null;
    const checkedAt = data.checked_in_at ? new Date(data.checked_in_at).getTime() : null;
    const expiresInMinutes =
      typeof data.minutes_remaining === 'number'
        ? data.minutes_remaining
        : typeof data.expires_in_minutes === 'number'
        ? data.expires_in_minutes
        : null;

    if (expiresAt) {
      const now = Date.now();
      const remainingSeconds = Math.max(0, Math.floor((expiresAt - now) / 1000));
      setTimerSeconds(remainingSeconds);
      if (checkedAt) {
        setSessionDurationSeconds(Math.max(1, Math.floor((expiresAt - checkedAt) / 1000)));
      } else if (expiresInMinutes !== null) {
        setSessionDurationSeconds(Math.max(1, Math.floor(expiresInMinutes * 60)));
      }
    } else if (expiresInMinutes !== null) {
      const seconds = Math.max(0, Math.floor(expiresInMinutes * 60));
      setTimerSeconds(seconds);
      setSessionDurationSeconds(Math.max(1, seconds));
    } else {
      setTimerSeconds(null);
      setSessionDurationSeconds(null);
    }
  }, []);

  useEffect(() => {
    fetchCurrentSong(true);
    const interval = setInterval(() => fetchCurrentSong(false), 20000);
    return () => clearInterval(interval);
  }, [fetchCurrentSong]);

  useEffect(() => {
    const initSession = async () => {
      try {
        const result = await apiClient('/api/session');
        if (result.active) {
          setHasActiveSession(true);
          setSessionInfo(result.data || null);
          syncTimerFromSession(result.data);
        } else {
          const checkinResult = await apiClient('/api/checkin', { method: 'POST' });
          if (checkinResult.success) {
            setHasActiveSession(true);
            setSessionInfo(checkinResult.data || null);
            syncTimerFromSession(checkinResult.data);
            // Register/check-in with Bluetooth presence system
            handleBluetoothPresence();
          } else {
            setSessionInfo(null);
            syncTimerFromSession(null);
          }
        }
      } catch (err) {
        console.error('Error initializing session:', err);
        setHasActiveSession(false);
        setSessionInfo(null);
        syncTimerFromSession(null);
      }
    };
    initSession();
  }, [syncTimerFromSession]);

  useEffect(() => {
    if (!hasActiveSession) return undefined;
    const interval = setInterval(async () => {
      try {
        const result = await apiClient('/api/session');
        if (result.active) {
          setSessionInfo(result.data || null);
          syncTimerFromSession(result.data);
        } else {
          setHasActiveSession(false);
          setSessionInfo(null);
          syncTimerFromSession(null);
        }
      } catch (error) {
        console.error('Error refreshing session:', error);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [hasActiveSession, syncTimerFromSession]);

  useEffect(() => {
    if (!hasActiveSession) return undefined;
    const interval = setInterval(() => {
      setTimerSeconds((prev) => {
        if (prev === null) return prev;
        if (prev <= 1) {
          setHasActiveSession(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [hasActiveSession]);

  const ensureSessionActive = useCallback(async () => {
    try {
      const current = await apiClient('/api/session');
      if (current.active) {
        setHasActiveSession(true);
        setSessionInfo(current.data || null);
        syncTimerFromSession(current.data);
        return true;
      }

      const checkinResult = await apiClient('/api/checkin', { method: 'POST' });
      if (checkinResult.success) {
        setHasActiveSession(true);
        setSessionInfo(checkinResult.data || null);
        syncTimerFromSession(checkinResult.data);
        // Register/check-in with Bluetooth presence system
        handleBluetoothPresence();
        return true;
      }
    } catch (error) {
      console.error('Unable to refresh session:', error);
    }
    setHasActiveSession(false);
    return false;
  }, [syncTimerFromSession]);

  const saveVote = async (rawVoteValue, nfctagid) => {
    if (isSubmitting) return;
    if (!hasActiveSession) {
      const restored = await ensureSessionActive();
      if (!restored) {
        console.error('No active session');
        return;
      }
    }

    // === BLUETOOTH PRESENCE DETECTION ===
    // Register device or check-in when user taps NFC
    if (ENABLE_BLUETOOTH_PRESENCE) {
      try {
        const session = await supabase.auth.getSession();
        const token = session.data.session?.access_token;

        if (token) {
          // Step 1: Check if device is already registered
          const statusResponse = await fetch(`${DJANGO_API_URL}/my-status`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (statusResponse.ok) {
            const status = await statusResponse.json();

            if (!status.has_device) {
              // FIRST TIME - Register device
              console.log('🔵 Registering Bluetooth device...');
              const registerResponse = await fetch(`${DJANGO_API_URL}/register-device`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                  device_mac: LAPTOP_BLUETOOTH_MAC,
                  device_name: 'Demo Laptop'
                })
              });

              if (registerResponse.ok) {
                const result = await registerResponse.json();
                console.log('✅ Bluetooth device registered:', result);
              } else {
                console.warn('⚠️  Device registration failed');
              }
            } else {
              // ALREADY REGISTERED - Check in
              console.log('🔵 Checking in with Bluetooth presence...');
              const checkinResponse = await fetch(`${DJANGO_API_URL}/check-in`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                }
              });

              if (checkinResponse.ok) {
                const result = await checkinResponse.json();
                console.log('✅ Checked in:', result);
              } else {
                console.warn('⚠️  Check-in failed');
              }
            }
          }
        }
      } catch (error) {
        // Don't block voting if Bluetooth presence fails
        console.error('Bluetooth presence detection error:', error);
      }
    }
    // === END BLUETOOTH PRESENCE DETECTION ===

    const normalizedVote = Number(rawVoteValue);
    if (Number.isNaN(normalizedVote)) {
      console.warn('Vote ignored: invalid vote value', rawVoteValue);
      return;
    }
    const isNegativeVote = normalizedVote <= 0;
    const uiVoteValue = isNegativeVote ? 0 : 1;
    const apiVoteValue = isNegativeVote ? -1 : 1;

    let activeSong = (songName || currentSong || '').trim();
    if (!activeSong) {
      activeSong = 'Unknown track';
    }
    const backendSong = canonicalSong || activeSong || 'Unknown track';
    const presentationTitle = formatSongTitle(backendSong) || 'Unknown track';

    setSelectedVote(uiVoteValue);
    setIsSubmitting(true);

    try {
      await apiClient('/api/votes', {
        method: 'POST',
        body: JSON.stringify({
          song: backendSong,
          vote_value: apiVoteValue,
          nfctagid: nfctagid || null,
        }),
      });
      sessionStorage.setItem('voteSubmitted', 'true');
      sessionStorage.setItem('voteValue', uiVoteValue.toString());
      sessionStorage.setItem('voteSong', presentationTitle);
      sessionStorage.setItem('voteCanonicalSong', backendSong);
      navigate(`/vote/${uiVoteValue}`, {
        state: { song: presentationTitle, canonicalSong: backendSong, voteValue: uiVoteValue, nfctagid },
      });
    } catch (error) {
      console.error('Vote failed:', error);
      setSelectedVote(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (!isAccountMenuOpen) return undefined;

    const handleClickOutside = (event) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target)) {
        setIsAccountMenuOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsAccountMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isAccountMenuOpen]);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    } finally {
      setIsAccountMenuOpen(false);
      navigate('/login');
    }
  };

  const trackLabel = (liveSongTitle || songName || currentSong || '').trim() || 'Loading track';
  const displaySongTitle = useMemo(() => formatSongTitle(trackLabel) || 'Loading track', [trackLabel]);
  const liveSongTimestamp = useMemo(() => {
    if (!liveSongUpdatedAt) return null;
    try {
      return new Date(liveSongUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return null;
    }
  }, [liveSongUpdatedAt]);
  const formattedTimer = useMemo(() => {
    if (timerSeconds === null) return '--:--';
    const minutes = Math.floor(timerSeconds / 60);
    const seconds = timerSeconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }, [timerSeconds]);

  const minutesLabel = useMemo(() => {
    if (timerSeconds === null) return '--';
    return Math.max(0, Math.floor(timerSeconds / 60));
  }, [timerSeconds]);

  const timerProgress = useMemo(() => {
    if (!sessionDurationSeconds || timerSeconds === null) {
      return hasActiveSession ? 5 : 0;
    }
    const consumed = Math.max(0, sessionDurationSeconds - timerSeconds);
    return Math.min(100, Math.max(0, (consumed / sessionDurationSeconds) * 100));
  }, [sessionDurationSeconds, timerSeconds, hasActiveSession]);

  // Bluetooth beacon detection constants
  const BEACON_NAME = 'SoundGuys Beacon';
  const BEACON_UUID = '19b10000-e8f2-537e-4f6c-d104768a1214';
  const DJANGO_API_URL = import.meta.env.VITE_DJANGO_API_URL || 'http://localhost:8000/api';
  const SCAN_INTERVAL = 5000; // 5 seconds

  // Check Web Bluetooth API support
  useEffect(() => {
    if (navigator.bluetooth) {
      setIsBluetoothSupported(true);
    } else {
      setBluetoothError('Web Bluetooth API not supported in this browser');
      console.warn('Web Bluetooth API not supported');
    }
  }, []);

  // Scan for beacon and report to Django
  const scanForBeacon = useCallback(async () => {
    if (!bluetoothEnabled || !isBluetoothSupported) return;

    try {
      // Request device (scans for nearby devices)
      const device = await navigator.bluetooth.requestDevice({
        filters: [{ name: BEACON_NAME }],
        optionalServices: [BEACON_UUID]
      });

      if (device && device.name === BEACON_NAME) {
        // Beacon detected! Report to Django
        setIsBluetoothConnected(true);
        setBluetoothDeviceName(device.name);
        setBluetoothDeviceId(device.id);
        setBluetoothError(null);

        const session = await supabase.auth.getSession();
        const token = session.data.session?.access_token;

        if (token) {
          const response = await fetch(`${DJANGO_API_URL}/beacon-detected`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ beacon_name: BEACON_NAME })
          });

          const result = await response.json();
          if (result.success) {
            console.log('✅ Beacon detected and reported to Django:', result.status);
          } else {
            console.error('Failed to report beacon detection:', result.error);
          }
        }
      }
    } catch (error) {
      // User canceled or beacon not found
      if (error.name === 'NotFoundError') {
        console.log('Beacon not in range');
        setIsBluetoothConnected(false);
      } else if (error.name === 'NotAllowedError') {
        console.log('Bluetooth permission denied');
        setBluetoothError('Bluetooth permission denied');
        setBluetoothEnabled(false);
      } else {
        console.error('Bluetooth error:', error);
        setBluetoothError(error.message);
      }
    }
  }, [bluetoothEnabled, isBluetoothSupported, BEACON_NAME, BEACON_UUID, DJANGO_API_URL]);

  // Poll for beacon every 5 seconds when enabled
  useEffect(() => {
    if (!bluetoothEnabled || !isBluetoothSupported) return undefined;

    // Initial scan
    scanForBeacon();

    // Set up interval for subsequent scans
    const interval = setInterval(() => {
      scanForBeacon();
    }, SCAN_INTERVAL);

    return () => clearInterval(interval);
  }, [bluetoothEnabled, isBluetoothSupported, scanForBeacon, SCAN_INTERVAL]);

  // Handle Bluetooth toggle
  const handleBluetoothToggle = useCallback(() => {
    if (!isBluetoothSupported) {
      setBluetoothError('Web Bluetooth API not supported in this browser');
      return;
    }
    setBluetoothEnabled(!bluetoothEnabled);
    if (!bluetoothEnabled) {
      setBluetoothError(null);
    }
  }, [isBluetoothSupported, bluetoothEnabled]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 px-4 pb-10 pt-6 text-slate-100">
      <div className="mx-auto flex w-full max-w-md flex-col gap-4">
        <header className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur">
            <div>
              <p className="text-xl font-medium uppercase tracking-[0.2em] text-white">Cosounds</p>
              <p className="text-xl font-semibold text-white/60">Connect through Sounds.</p>
              <p className="mt-2 text-[0.8rem] text-white/70">
                Tap the green or red stickers to shape what plays next. 
The more you vote, the better your music gets.
              </p>
            </div>
            <div className="mt-4 flex items-center justify-between gap-3">
              <span
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                hasActiveSession ? 'bg-emerald-500/20 text-emerald-200' : 'bg-slate-600/40 text-slate-200'
              }`}
            >
              Vibe pass {hasActiveSession ? 'on' : 'off'}
            </span>
            <div className="flex items-center gap-2">
              {/* Bluetooth button */}
              <button
                type="button"
                onClick={handleBluetoothToggle}
                className={`flex h-10 w-10 items-center justify-center rounded-full border ${
                  isBluetoothConnected
                    ? 'border-green-500 bg-green-500/20 text-green-400'
                    : bluetoothEnabled
                    ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                    : 'border-white/15 bg-white/10 text-white'
                }`}
                aria-label={bluetoothEnabled ? 'Disable Bluetooth' : 'Enable Bluetooth'}
                title={isBluetoothConnected ? 'Connected to beacon' : bluetoothEnabled ? 'Scanning for beacon...' : 'Enable Bluetooth'}
              >
                <Bluetooth size={18} />
              </button>

              <div className="relative" ref={accountMenuRef}>
                <button
                  type="button"
                  onClick={() => setIsAccountMenuOpen((prev) => !prev)}
                  className="flex h-10 w-10 items-center justify-center rounded-full border border-white/15 bg-white/10 text-white"
                  aria-expanded={isAccountMenuOpen}
                  aria-label="User menu"
                >
                  <User size={18} />
                </button>
                {isAccountMenuOpen && (
                  <div className="absolute right-0 top-12 w-40 rounded-2xl border border-white/10 bg-slate-900/90 p-1 text-sm shadow-lg">
                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-white/80 hover:bg-white/5"
                    >
                      <LogOut size={16} />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <section className="rounded-3xl border border-white/10 bg-white/5 p-5 text-center">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-white/60">Vibe timer</p>
          <div className="mt-2 text-4xl font-semibold">{formattedTimer}</div>
          <p className="mt-1 text-sm text-white/70">{minutesLabel} minutes of hang time left</p>
          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
            <span
              className="block h-full rounded-full bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 transition-all"
              style={{ width: `${timerProgress}%` }}
            />
          </div>
          <p className="mt-3 text-xs text-white/70">
            {hasActiveSession
              ? 'Need more time? Tap a sticker again and the algorithm keeps listening to you.'
              : "Timer paused. Tap any sticker so the model knows you're here."}
          </p>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <p className="text-sm font-medium uppercase tracking-[0.3em] text-white/60">Now playing</p>
              <h1 className="mt-1 text-2xl font-semibold text-white">{displaySongTitle}</h1>
              <p className="mt-2 text-sm text-white/70">
                {liveSongTimestamp ? `Updated ${liveSongTimestamp}` : 'Waiting for the DJ to push a new track.'}
              </p>
            </div>
            <div className="h-20 w-20 rounded-full bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 p-3 shadow-inner shadow-black/50">
              <div
                className="record-spin relative flex h-full w-full items-center justify-center overflow-hidden rounded-full bg-slate-950"
                style={{
                  background: 'radial-gradient(circle, #0f172a 25%, #020617 70%)',
                }}
              >
                <div
                  className="absolute inset-1 rounded-full opacity-30"
                  style={{
                    background:
                      'repeating-radial-gradient(circle, rgba(255,255,255,0.08) 0, rgba(255,255,255,0.08) 2px, transparent 3px, transparent 6px)',
                  }}
                />
                <span className="absolute top-2 left-1/2 h-3 w-0.5 -translate-x-1/2 rounded-full bg-white/50" />
                <div className="relative z-10 h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 shadow-lg shadow-blue-900/50" />
              </div>
            </div>
          </div>
        
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.3em] text-white/60">Tap a sticker</p>
            <h2 className="mt-1 text-xl font-semibold text-white">Two taps, personalized experience</h2>
          </div>
          <div className="mt-4 flex flex-col gap-3">
            <div className="rounded-2xl bg-emerald-500/15 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.3em] text-emerald-100">Green sticker</p>
              <p className="text-lg font-semibold text-white">Keep this vibe going</p>
              <p className="text-sm text-emerald-50">Positive reward = algorithm plays more like this.</p>
            </div>
            <div className="rounded-2xl bg-rose-500/15 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.3em] text-rose-100">Red sticker</p>
              <p className="text-lg font-semibold text-white">Not feeling it</p>
              <p className="text-sm text-rose-50">Negative reward = the model explores fresh textures.</p>
            </div>
          </div>

        </section>

      </div>
    </div>
  );
};

export default Vote;
