import React from 'react';
import { Activity, Play, Zap, Wifi, WifiOff } from 'lucide-react';

export default function Header({ 
  status, 
  activeFault, 
  onInject, 
  isMockMode, 
  setIsMockMode 
}) {
  const [selectedScenario, setSelectedScenario] = React.useState('config_regression');

  const getStatusColor = () => {
    switch (status) {
      case 'Monitoring':
        return 'bg-green-500/10 text-green-400 border-green-500/30';
      case 'Incident Active':
        return 'bg-red-500/10 text-red-400 border-red-500/30 animate-pulse';
      case 'Awaiting Approval':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse';
      case 'Resolved':
        return 'bg-green-500/10 text-green-400 border-green-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <header className="border-b border-panel/60 bg-panel px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
      {/* Title */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gradient-to-br from-detector/20 to-remediator/20 border border-detector/20 rounded-lg">
          <Zap className="w-6 h-6 text-detector" />
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-[0.25em] text-textSecondary font-mono block">
            Autonomous Incident Response
          </span>
          <h1 className="text-xl font-bold text-textPrimary tracking-tight">
            Sentinel<span className="text-remediator">Ops</span>
          </h1>
        </div>
      </div>

      {/* Control Actions */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Status Pill */}
        <div className={`px-3 py-1 text-xs font-mono font-bold rounded-full border flex items-center gap-2 ${getStatusColor()}`}>
          <Activity className="w-3 h-3" />
          {status}
        </div>

        {/* Mock/Real toggle */}
        <button
          onClick={() => setIsMockMode(!isMockMode)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono transition-all duration-300 ${
            isMockMode 
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20' 
              : 'bg-green-500/10 text-green-400 border-green-500/30 hover:bg-green-500/20'
          }`}
          title="Toggle between real Ollama backend connection or local mock simulation"
        >
          {isMockMode ? <WifiOff className="w-3.5 h-3.5" /> : <Wifi className="w-3.5 h-3.5" />}
          {isMockMode ? 'Mock Simulation' : 'Live Backend'}
        </button>

        {/* Fault Selector & Trigger */}
        <div className="flex items-center gap-2">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            disabled={status !== 'Monitoring' && status !== 'Resolved'}
            className="bg-background border border-panel text-textPrimary text-xs rounded-lg px-3 py-1.5 font-mono focus:outline-none focus:ring-1 focus:ring-detector disabled:opacity-50"
          >
            <option value="config_regression">Config Regression</option>
            <option value="security_group">Security Group Lockdown</option>
          </select>
          
          <button
            onClick={() => onInject(selectedScenario)}
            disabled={status !== 'Monitoring' && status !== 'Resolved'}
            className="flex items-center gap-1.5 bg-alert/15 text-alert border border-alert/30 hover:bg-alert/25 disabled:opacity-30 disabled:hover:bg-alert/15 px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all duration-200"
          >
            <Play className="w-3 h-3 fill-alert" />
            Inject Fault
          </button>
        </div>
      </div>
    </header>
  );
}
