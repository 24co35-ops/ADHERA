import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';
import { GlassCard } from '../../components/GlassCard';
import { BreathingSphere, BreathingPhase } from '../../components/BreathingSphere';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  Wind,
  Play,
  Pause,
  RotateCcw,
  Clock,
  Sparkles,
  CheckCircle,
  Sliders,
  History,
  Heart,
  ChevronRight,
} from 'lucide-react';
import clsx from 'clsx';

interface BreathingPattern {
  id: string;
  name: string;
  description: string;
  inhale: number;
  holdIn: number;
  exhale: number;
  holdOut: number;
}

const PRESET_PATTERNS: BreathingPattern[] = [
  {
    id: 'calm',
    name: 'Calm (4-7-8)',
    description: 'Activates parasympathetic relaxation and lowers heart rate',
    inhale: 4,
    holdIn: 7,
    exhale: 8,
    holdOut: 0,
  },
  {
    id: 'focus',
    name: 'Focus (Box 4-4-4-4)',
    description: 'Enhances mental clarity, discipline, and emotional stability',
    inhale: 4,
    holdIn: 4,
    exhale: 4,
    holdOut: 4,
  },
  {
    id: 'balance',
    name: 'Balance (Equal 4-4)',
    description: 'Restores nervous system equilibrium and daily grounding',
    inhale: 4,
    holdIn: 0,
    exhale: 4,
    holdOut: 0,
  },
  {
    id: 'deep',
    name: 'Deep Relief (4-2-6-2)',
    description: 'Lengthened exhalation to clear stress and mental tension',
    inhale: 4,
    holdIn: 2,
    exhale: 6,
    holdOut: 2,
  },
];

const DURATION_OPTIONS = [
  { label: '1 min', seconds: 60 },
  { label: '3 mins', seconds: 180 },
  { label: '5 mins', seconds: 300 },
  { label: '10 mins', seconds: 600 },
];

interface WellnessSession {
  id: string;
  pattern_name: string;
  duration_seconds: number;
  completed_at: string;
}

export const WellnessPage: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedPattern, setSelectedPattern] = useState<BreathingPattern>(PRESET_PATTERNS[0]);
  const [isCustom, setIsCustom] = useState(false);
  const [customPattern, setCustomPattern] = useState({
    inhale: 4,
    holdIn: 4,
    exhale: 4,
    holdOut: 4,
  });

  const [targetDuration, setTargetDuration] = useState(180); // 3 mins default
  const [remainingTime, setRemainingTime] = useState(180);
  const [isActive, setIsActive] = useState(false);
  const [phase, setPhase] = useState<BreathingPhase>('idle');
  const [progressInPhase, setProgressInPhase] = useState(0);
  const [phaseCountdown, setPhaseCountdown] = useState(0);

  const [recentSessions, setRecentSessions] = useState<WellnessSession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [sessionCompleted, setSessionCompleted] = useState(false);

  const cycleStartRef = useRef<number>(0);
  const timerIntervalRef = useRef<any>(null);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Active pattern timings
  const activeTiming = isCustom
    ? customPattern
    : {
        inhale: selectedPattern.inhale,
        holdIn: selectedPattern.holdIn,
        exhale: selectedPattern.exhale,
        holdOut: selectedPattern.holdOut,
      };

  const totalCycleSeconds =
    activeTiming.inhale + activeTiming.holdIn + activeTiming.exhale + activeTiming.holdOut || 1;

  // Load recent sessions
  const loadRecentSessions = async () => {
    try {
      setLoadingSessions(true);
      const res = await api.get<WellnessSession[]>('/wellness/sessions');
      if (res.success && res.data) {
        setRecentSessions(res.data);
      }
    } catch (err) {
      console.error('Failed to load wellness sessions:', err);
    } finally {
      setLoadingSessions(false);
    }
  };

  useEffect(() => {
    loadRecentSessions();
  }, []);

  // Handle duration changes when not active
  useEffect(() => {
    if (!isActive) {
      setRemainingTime(targetDuration);
    }
  }, [targetDuration, isActive]);

  // Main breathing loop
  useEffect(() => {
    if (!isActive) {
      setPhase('idle');
      setProgressInPhase(0);
      setPhaseCountdown(0);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      return;
    }

    cycleStartRef.current = Date.now();
    const sessionStartTime = Date.now();
    const initialRemaining = remainingTime;

    timerIntervalRef.current = setInterval(() => {
      const elapsedTotalSec = Math.floor((Date.now() - sessionStartTime) / 1000);
      const currentRemaining = Math.max(0, initialRemaining - elapsedTotalSec);
      setRemainingTime(currentRemaining);

      if (currentRemaining <= 0) {
        handleSessionComplete();
        return;
      }

      // Calculate position within current cycle
      const cycleElapsedMs = (Date.now() - cycleStartRef.current) % (totalCycleSeconds * 1000);
      const cycleSec = cycleElapsedMs / 1000;

      const tIn = activeTiming.inhale;
      const tHoldIn = tIn + activeTiming.holdIn;
      const tEx = tHoldIn + activeTiming.exhale;

      if (cycleSec < tIn) {
        setPhase('inhale');
        setProgressInPhase(cycleSec / (tIn || 1));
        setPhaseCountdown(Math.ceil(tIn - cycleSec));
      } else if (cycleSec < tHoldIn) {
        setPhase('hold_in');
        const holdElapsed = cycleSec - tIn;
        setProgressInPhase(holdElapsed / (activeTiming.holdIn || 1));
        setPhaseCountdown(Math.ceil(activeTiming.holdIn - holdElapsed));
      } else if (cycleSec < tEx) {
        setPhase('exhale');
        const exElapsed = cycleSec - tHoldIn;
        setProgressInPhase(exElapsed / (activeTiming.exhale || 1));
        setPhaseCountdown(Math.ceil(activeTiming.exhale - exElapsed));
      } else {
        setPhase('hold_out');
        const holdOutElapsed = cycleSec - tEx;
        setProgressInPhase(holdOutElapsed / (activeTiming.holdOut || 1));
        setPhaseCountdown(Math.ceil(activeTiming.holdOut - holdOutElapsed));
      }
    }, 50);

    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [isActive, totalCycleSeconds, activeTiming]);

  const handleSessionComplete = async () => {
    setIsActive(false);
    setPhase('idle');
    setSessionCompleted(true);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);

    const patternTitle = isCustom ? 'Custom Pattern' : selectedPattern.name;
    addToast('success', `Completed ${Math.round(targetDuration / 60)} minute session: ${patternTitle}!`);

    try {
      await api.post('/wellness/sessions', {
        pattern_name: patternTitle,
        duration_seconds: targetDuration,
      });
      loadRecentSessions();
    } catch (err) {
      console.error('Failed to save completed session:', err);
    }
  };

  const toggleStartPause = () => {
    setSessionCompleted(false);
    setIsActive(!isActive);
  };

  const resetSession = () => {
    setIsActive(false);
    setPhase('idle');
    setProgressInPhase(0);
    setRemainingTime(targetDuration);
    setSessionCompleted(false);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const getPhaseInstruction = () => {
    if (!isActive) return sessionCompleted ? 'Session Complete' : 'Press Start to Begin';
    if (phase === 'inhale') return 'Inhale Deeply...';
    if (phase === 'hold_in') return 'Hold Breath...';
    if (phase === 'exhale') return 'Exhale Slowly...';
    if (phase === 'hold_out') return 'Rest & Hold...';
    return 'Breathe';
  };

  const progressPercent = ((targetDuration - remainingTime) / targetDuration) * 100;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Wind className="w-7 h-7 text-primary" />
            <span>Mental Wellness & Breathing</span>
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Grounded 3D resonance breathing to lower anxiety, improve focus, and reinforce treatment adherence.
          </p>
        </div>

        {/* Duration selector */}
        <div className="flex items-center gap-2 bg-surface-container-high/60 p-1.5 rounded-2xl border border-white/10 self-start sm:self-auto">
          {DURATION_OPTIONS.map((opt) => (
            <button
              key={opt.seconds}
              disabled={isActive}
              onClick={() => setTargetDuration(opt.seconds)}
              className={clsx(
                'px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-150',
                targetDuration === opt.seconds
                  ? 'bg-primary text-surface shadow-glow'
                  : 'text-on-surface-variant hover:text-white disabled:opacity-50'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left / Center: 3D Breathing Interactive Stage */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <GlassCard className="relative overflow-hidden p-6 sm:p-8 flex flex-col items-center justify-center border-primary/20 shadow-2xl">
            {/* Top Phase Header */}
            <div className="text-center z-10">
              <span className="text-xs uppercase tracking-widest text-primary font-bold">
                {isCustom ? 'Custom Pattern' : selectedPattern.name}
              </span>
              <h2 className="text-2xl sm:text-3xl font-black text-white mt-1 transition-all">
                {getPhaseInstruction()}
              </h2>
              {isActive && phaseCountdown > 0 && (
                <div className="text-sm font-semibold text-primary/90 mt-1">
                  {phaseCountdown}s remaining
                </div>
              )}
            </div>

            {/* 3D Interactive Three.js Sphere */}
            <div className="w-full flex justify-center my-2 relative">
              <BreathingSphere
                phase={phase}
                progressInPhase={progressInPhase}
                isActive={isActive}
              />

              {/* Central Progress Ring Overlay */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <svg className="w-64 h-64 sm:w-72 sm:h-72 -rotate-90">
                  <circle
                    cx="50%"
                    cy="50%"
                    r="46%"
                    className="stroke-white/5"
                    strokeWidth="3"
                    fill="transparent"
                  />
                  <circle
                    cx="50%"
                    cy="50%"
                    r="46%"
                    className="stroke-primary transition-all duration-300"
                    strokeWidth="3"
                    strokeDasharray="289%"
                    strokeDashoffset={`${289 - (289 * progressPercent) / 100}%`}
                    strokeLinecap="round"
                    fill="transparent"
                  />
                </svg>
              </div>
            </div>

            {/* Countdown and Timer Controls */}
            <div className="flex flex-col items-center gap-4 z-10 mt-2">
              <div className="flex items-center gap-2 text-3xl font-black text-white tracking-wider">
                <Clock className="w-6 h-6 text-primary" />
                <span>{formatTime(remainingTime)}</span>
              </div>

              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={toggleStartPause}
                  className={clsx(
                    'btn-press flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm shadow-glow transition-all',
                    isActive
                      ? 'bg-status-warning text-surface hover:bg-status-warning/90'
                      : 'bg-primary text-surface hover:bg-primary-container'
                  )}
                >
                  {isActive ? (
                    <>
                      <Pause className="w-4 h-4 fill-current" />
                      <span>Pause</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>{remainingTime < targetDuration ? 'Resume' : 'Start Session'}</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={resetSession}
                  className="btn-press flex items-center gap-1.5 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-on-surface text-sm font-semibold border border-white/10 transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reset</span>
                </button>
              </div>
            </div>
          </GlassCard>

          {/* Pattern Selector Cards */}
          <div>
            <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>Breathing Patterns</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {PRESET_PATTERNS.map((p) => {
                const isSelected = !isCustom && selectedPattern.id === p.id;
                return (
                  <button
                    key={p.id}
                    disabled={isActive}
                    onClick={() => {
                      setIsCustom(false);
                      setSelectedPattern(p);
                    }}
                    className={clsx(
                      'p-4 rounded-2xl text-left border transition-all duration-200',
                      isSelected
                        ? 'bg-primary/10 border-primary/40 shadow-glow'
                        : 'bg-white/5 border-white/10 hover:bg-white/10 text-on-surface disabled:opacity-50'
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-white">{p.name}</span>
                      <span className="text-[11px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded-md">
                        {p.inhale}s - {p.holdIn}s - {p.exhale}s - {p.holdOut}s
                      </span>
                    </div>
                    <p className="text-xs text-on-surface-variant line-clamp-2">{p.description}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Sidebar: Custom Pattern Editor & Recent Sessions */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          {/* Custom Editor */}
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-primary" />
                <span>Custom Pattern</span>
              </h3>
              <button
                type="button"
                disabled={isActive}
                onClick={() => setIsCustom(!isCustom)}
                className={clsx(
                  'text-xs px-2.5 py-1 rounded-lg font-semibold transition-colors',
                  isCustom
                    ? 'bg-primary text-surface'
                    : 'bg-white/10 text-on-surface hover:bg-white/15'
                )}
              >
                {isCustom ? 'Active' : 'Enable'}
              </button>
            </div>

            <div className="space-y-3">
              {[
                { label: 'Inhale (seconds)', key: 'inhale', val: customPattern.inhale },
                { label: 'Hold In (seconds)', key: 'holdIn', val: customPattern.holdIn },
                { label: 'Exhale (seconds)', key: 'exhale', val: customPattern.exhale },
                { label: 'Hold Out (seconds)', key: 'holdOut', val: customPattern.holdOut },
              ].map((item) => (
                <div key={item.key} className="flex items-center justify-between">
                  <span className="text-xs text-on-surface-variant">{item.label}</span>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="12"
                      step="1"
                      disabled={!isCustom || isActive}
                      value={item.val}
                      onChange={(e) =>
                        setCustomPattern((prev) => ({
                          ...prev,
                          [item.key]: parseInt(e.target.value) || 0,
                        }))
                      }
                      className="w-24 accent-primary"
                    />
                    <span className="text-xs font-mono text-white w-6 text-right">{item.val}s</span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Recent Completed Sessions */}
          <GlassCard className="p-6">
            <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
              <History className="w-4 h-4 text-primary" />
              <span>Your Recent Sessions</span>
            </h3>

            {loadingSessions ? (
              <div className="space-y-2 animate-pulse">
                <div className="h-10 bg-white/5 rounded-xl" />
                <div className="h-10 bg-white/5 rounded-xl" />
                <div className="h-10 bg-white/5 rounded-xl" />
              </div>
            ) : recentSessions.length === 0 ? (
              <div className="text-center py-6 text-on-surface-variant text-xs">
                <Heart className="w-6 h-6 mx-auto mb-2 text-primary/60" />
                <p>No completed sessions logged yet.</p>
                <p className="mt-1">Complete your first 1-minute breathing exercise today!</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {recentSessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <CheckCircle className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white">{session.pattern_name}</div>
                        <div className="text-[10px] text-on-surface-variant">
                          {new Date(session.completed_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-primary">
                      {Math.round(session.duration_seconds / 60)} mins
                    </span>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
