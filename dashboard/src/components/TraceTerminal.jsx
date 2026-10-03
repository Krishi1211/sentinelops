import React from 'react';
import { Terminal, Download } from 'lucide-react';

export default function TraceTerminal({ logs }) {
  const terminalEndRef = React.useRef(null);

  // Auto-scroll on new log entries
  React.useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getAgentColor = (agent) => {
    switch (agent.toUpperCase()) {
      case 'DETECTOR':
        return 'text-detector border-detector/20 bg-detector/5';
      case 'DIAGNOSTICIAN':
        return 'text-diagnostician border-diagnostician/20 bg-diagnostician/5';
      case 'REMEDIATOR':
        return 'text-remediator border-remediator/20 bg-remediator/5';
      case 'SYSTEM':
        return 'text-textPrimary border-panel bg-panel/30';
      default:
        return 'text-textSecondary border-panel/30 bg-panel/10';
    }
  };

  const getLogTypeColor = (type) => {
    switch (type) {
      case 'ALERT':
        return 'text-alert font-bold';
      case 'TOOL_CALL':
        return 'text-textSecondary/80 italic';
      case 'TOOL_RESPONSE':
        return 'text-textSecondary/60 italic';
      default:
        return 'text-textPrimary';
    }
  };

  const formatContent = (content) => {
    if (typeof content === 'object') {
      return JSON.stringify(content, null, 2);
    }
    return content;
  };

  const downloadLogs = () => {
    const logText = logs.map(l => `[${l.timestamp}] [${l.agent}] [${l.type}] ${typeof l.content === 'object' ? JSON.stringify(l.content) : l.content}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sentinelops_audit_trace_${Date.now()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-panel border border-panel/60 rounded-xl overflow-hidden flex flex-col h-[480px]">
      {/* Terminal Title Bar */}
      <div className="bg-background/80 px-4 py-2 border-b border-panel/60 flex justify-between items-center">
        <div className="flex items-center gap-2 text-textSecondary">
          <Terminal className="w-3.5 h-3.5 text-detector" />
          <span className="text-xs font-mono tracking-wider font-bold uppercase">Live Audit Trace Console</span>
        </div>
        
        <button
          onClick={downloadLogs}
          disabled={logs.length === 0}
          className="p-1 hover:bg-panel rounded text-textSecondary hover:text-textPrimary disabled:opacity-20 transition-all duration-200"
          title="Download full trace file"
        >
          <Download className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Terminal Body */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-[13px] leading-relaxed space-y-2 bg-[#080d17]">
        {logs.length === 0 ? (
          <div className="text-textSecondary/40 h-full flex flex-col items-center justify-center">
            <span>[SYS] Systems idle. Monitoring cloud health metrics.</span>
            <span className="text-[11px] mt-1 italic">Click "Inject Fault" to trigger a scripted sequence.</span>
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex items-start gap-2 border-b border-panel/10 pb-1.5 hover:bg-panel/5 transition-all">
              <span className="text-textSecondary/40 select-none text-xs pt-0.5">{log.timestamp}</span>
              <span className={`px-1.5 py-0.5 text-[10px] rounded border font-bold uppercase select-none ${getAgentColor(log.agent)}`}>
                {log.agent}
              </span>
              <span className={`flex-1 whitespace-pre-wrap ${getLogTypeColor(log.type)}`}>
                {formatContent(log.content)}
              </span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}
