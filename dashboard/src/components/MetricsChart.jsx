import React from 'react';
import { Activity } from 'lucide-react';

export default function MetricsChart({ metrics }) {
  const width = 500;
  const height = 180;
  const padding = 20;

  // Find max value in metrics or default to 5000
  const maxVal = Math.max(...metrics.map(m => m.p99_latency_ms), 5000);
  const minVal = 0;

  // Convert points to SVG coordinates
  const getCoordinates = () => {
    if (metrics.length < 2) return '';
    
    return metrics.map((point, index) => {
      const x = padding + (index / (metrics.length - 1)) * (width - padding * 2);
      const y = height - padding - ((point.p99_latency_ms - minVal) / (maxVal - minVal)) * (height - padding * 2);
      return `${x},${y}`;
    }).join(' ');
  };

  const points = getCoordinates();
  const pathData = points ? `M ${points}` : '';
  
  // Create area path data by closing the shape at the bottom
  const areaData = points 
    ? `${pathData} L ${width - padding},${height - padding} L ${padding},${height - padding} Z` 
    : '';

  const getLatestLatency = () => {
    if (metrics.length === 0) return '150 ms';
    return `${Math.round(metrics[metrics.length - 1].p99_latency_ms)} ms`;
  };

  const isAlarm = metrics.some(m => m.p99_latency_ms > 1000);

  return (
    <div className="bg-panel border border-panel/60 rounded-xl p-4 flex flex-col h-[230px]">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2 text-textSecondary">
          <Activity className="w-3.5 h-3.5 text-alert" />
          <span className="text-xs font-mono tracking-wider font-bold uppercase">Realtime Telemetry (p99 latency)</span>
        </div>
        <div className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
          isAlarm 
            ? 'text-alert border-alert/20 bg-alert/5 animate-pulse' 
            : 'text-detector border-detector/20 bg-detector/5'
        }`}>
          Latest: {getLatestLatency()}
        </div>
      </div>

      <div className="flex-1 relative w-full h-full min-h-[120px]">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" preserveAspectRatio="none">
          <defs>
            {/* Area gradient */}
            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={isAlarm ? "#E0574F" : "#4FC3E0"} stopOpacity={0.25} />
              <stop offset="100%" stopColor={isAlarm ? "#E0574F" : "#4FC3E0"} stopOpacity={0.0} />
            </linearGradient>
          </defs>

          {/* Gridlines */}
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#1F2D44" strokeWidth="1" strokeDasharray="3 3" />
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#1F2D44" strokeWidth="1" strokeDasharray="3 3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#1F2D44" strokeWidth="1" />

          {/* Threshold alert line (1000ms mark) */}
          {(() => {
            const thresholdY = height - padding - ((1000 - minVal) / (maxVal - minVal)) * (height - padding * 2);
            return (
              <>
                <line 
                  x1={padding} 
                  y1={thresholdY} 
                  x2={width - padding} 
                  y2={thresholdY} 
                  stroke="#E0574F" 
                  strokeWidth="1.2" 
                  strokeDasharray="4 2" 
                  opacity="0.6"
                />
                <text 
                  x={padding + 5} 
                  y={thresholdY - 4} 
                  fill="#E0574F" 
                  fontSize="8" 
                  fontFamily="monospace" 
                  opacity="0.8"
                >
                  ALARM THRESHOLD (1000ms)
                </text>
              </>
            );
          })()}

          {/* Filled Area */}
          {areaData && (
            <path d={areaData} fill="url(#chartGradient)" />
          )}

          {/* Line Path */}
          {pathData && (
            <path 
              d={pathData} 
              fill="none" 
              stroke={isAlarm ? "#E0574F" : "#4FC3E0"} 
              strokeWidth="2" 
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Data nodes */}
          {metrics.map((point, index) => {
            if (index % Math.max(1, Math.floor(metrics.length / 10)) !== 0 && index !== metrics.length - 1) return null;
            const x = padding + (index / (metrics.length - 1)) * (width - padding * 2);
            const y = height - padding - ((point.p99_latency_ms - minVal) / (maxVal - minVal)) * (height - padding * 2);
            return (
              <circle 
                key={index} 
                cx={x} 
                cy={y} 
                r="3.5" 
                fill={point.p99_latency_ms > 1000 ? "#E0574F" : "#4FC3E0"} 
                stroke="#0B1220" 
                strokeWidth="1" 
              />
            );
          })}
        </svg>

        {/* Chart Y Axis Labels */}
        <div className="absolute top-4 left-6 text-[9px] font-mono text-textSecondary opacity-60">
          {Math.round(maxVal)}ms
        </div>
        <div className="absolute bottom-6 left-6 text-[9px] font-mono text-textSecondary opacity-60">
          0ms
        </div>
      </div>
    </div>
  );
}
