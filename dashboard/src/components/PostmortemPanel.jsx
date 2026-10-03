import React from 'react';
import { FileText, Award, Calendar, AlertCircle } from 'lucide-react';

export default function PostmortemPanel({ postmortem }) {
  if (!postmortem) return null;

  // Extremely basic markdown-to-html formatter for the simple postmortem templates we generate
  const renderMarkdown = (text) => {
    return text.split('\n').map((line, idx) => {
      if (line.startsWith('# ')) {
        return <h2 key={idx} className="text-base font-bold text-textPrimary border-b border-panel/60 pb-1 mt-4 mb-2 font-mono uppercase tracking-wider">{line.replace('# ', '')}</h2>;
      }
      if (line.startsWith('## ')) {
        return <h3 key={idx} className="text-xs font-bold text-detector uppercase tracking-wider mt-4 mb-2 font-mono">{line.replace('## ', '')}</h3>;
      }
      if (line.startsWith('**') && line.endsWith('**')) {
        return <p key={idx} className="text-xs text-textSecondary mt-1">{line}</p>;
      }
      if (line.startsWith('- ')) {
        return <li key={idx} className="text-xs text-textPrimary/90 ml-4 list-disc mb-1">{line.replace('- ', '')}</li>;
      }
      if (line.trim() === '') return <div key={idx} className="h-2" />;
      
      // Inline formatting replacements
      let formattedLine = line
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code class="bg-background px-1.5 py-0.5 rounded text-detector font-mono text-[11px]">$1</code>');

      return (
        <p 
          key={idx} 
          className="text-xs text-textPrimary/80 leading-relaxed mb-1" 
          dangerouslySetInnerHTML={{ __html: formattedLine }} 
        />
      );
    });
  };

  return (
    <div className="bg-panel border border-panel/60 rounded-xl overflow-hidden flex flex-col h-[230px]">
      {/* Title Bar */}
      <div className="bg-background/80 px-4 py-2 border-b border-panel/60 flex justify-between items-center">
        <div className="flex items-center gap-2 text-textSecondary">
          <FileText className="w-3.5 h-3.5 text-remediator" />
          <span className="text-xs font-mono tracking-wider font-bold uppercase">Generated SRE Incident Report</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-remediator bg-remediator/10 px-2 py-0.5 rounded border border-remediator/20">
          <Award className="w-3 h-3" />
          Audit Signed
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 bg-[#0a111f] font-sans">
        <div className="border-l-2 border-remediator pl-3 py-1 bg-remediator/5 rounded-r mb-3 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-remediator mt-0.5 flex-shrink-0" />
          <div>
            <span className="text-[10px] uppercase font-mono font-bold text-remediator">Postmortem Auto-Archive Status</span>
            <p className="text-[11px] text-textSecondary mt-0.5">Report written to disk & synchronized with replica S3 SRE bucket.</p>
          </div>
        </div>
        <div className="space-y-1">
          {renderMarkdown(postmortem)}
        </div>
      </div>
    </div>
  );
}
