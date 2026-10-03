import React from 'react';
import { Eye, Search, ShieldAlert, CheckCircle, Loader2 } from 'lucide-react';

export default function PipelineStrip({ pipeline }) {
  const stages = [
    {
      id: 'detector',
      label: '1. Detector',
      description: 'Monitoring & Anomalies',
      color: 'text-detector',
      glowClass: 'glow-detector',
      bgGlow: 'bg-detector/10',
      icon: Eye
    },
    {
      id: 'diagnostician',
      label: '2. Diagnostician',
      description: 'Hypothesis Verification',
      color: 'text-diagnostician',
      glowClass: 'glow-diagnostician',
      bgGlow: 'bg-diagnostician/10',
      icon: Search
    },
    {
      id: 'remediator',
      label: '3. Remediator',
      description: 'Sandbox Testing & Fix',
      color: 'text-remediator',
      glowClass: 'glow-remediator',
      bgGlow: 'bg-remediator/10',
      icon: ShieldAlert
    }
  ];

  return (
    <div className="bg-panel/40 border border-panel/60 rounded-xl p-6 mb-6">
      <div className="flex flex-col md:flex-row justify-between items-center gap-6 relative">
        {stages.map((stage, idx) => {
          const state = pipeline[stage.id] || { status: 'idle', duration: null };
          const Icon = stage.icon;

          const isActive = state.status === 'active';
          const isDone = state.status === 'done';

          return (
            <React.Fragment key={stage.id}>
              {/* Stage Node */}
              <div 
                className={`flex-1 flex items-center gap-4 p-4 rounded-xl border transition-all duration-300 w-full md:w-auto ${
                  isActive 
                    ? `border-textPrimary bg-background ${stage.glowClass}`
                    : isDone
                      ? 'border-panel/80 bg-panel/30 text-textSecondary'
                      : 'border-panel/40 bg-panel/10 text-textSecondary/50'
                }`}
              >
                <div className={`p-2.5 rounded-lg border ${
                  isActive
                    ? `${stage.color} border-current ${stage.bgGlow}`
                    : isDone
                      ? 'text-remediator border-remediator/20 bg-remediator/5'
                      : 'text-textSecondary/30 border-panel bg-panel/20'
                }`}>
                  {isActive ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : isDone ? (
                    <CheckCircle className="w-5 h-5 text-remediator" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-xs font-mono font-bold tracking-wider ${isActive ? 'text-textPrimary' : 'text-textSecondary'}`}>
                      {stage.label}
                    </span>
                    {isDone && state.duration && (
                      <span className="text-[10px] font-mono bg-panel px-1.5 py-0.5 rounded text-remediator">
                        {state.duration}s
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-textSecondary truncate block mt-0.5">
                    {isActive ? 'Investigating...' : isDone ? 'Completed' : stage.description}
                  </span>
                </div>
              </div>

              {/* Connecting Line (Only between nodes) */}
              {idx < stages.length - 1 && (
                <div className="hidden md:block w-8 h-[2px] bg-panel/30 relative">
                  <div className={`absolute top-0 left-0 h-full bg-gradient-to-r from-detector to-diagnostician transition-all duration-500 ${
                    pipeline[stages[idx].id]?.status === 'done' ? 'w-full' : 'w-0'
                  }`} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
