import React from 'react';
import { Lock, ShieldCheck, RefreshCw } from 'lucide-react';

export default function ApprovalGate({ 
  status, 
  generatedToken, 
  onApprove, 
  onReject 
}) {
  const [tokenInput, setTokenInput] = React.useState('');
  const [error, setError] = React.useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!tokenInput.trim()) {
      setError('Please input the approval token.');
      return;
    }
    
    // Call approval handler
    onApprove(tokenInput.trim(), (success) => {
      if (!success) {
        setError('Invalid Security Token. Remediation rejected.');
      } else {
        setError('');
      }
    });
  };

  if (status !== 'Awaiting Approval') return null;

  return (
    <div className="bg-panel border-2 border-amber-500/40 glow-diagnostician rounded-xl p-5 mb-6 animate-soft-pulse">
      <div className="flex items-center gap-3 border-b border-panel/60 pb-3 mb-4">
        <div className="p-1.5 bg-amber-500/10 border border-amber-500/30 rounded text-amber-400">
          <Lock className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-textPrimary font-mono">REMEDIATION APPROVAL REQUIRED</h3>
          <p className="text-xs text-textSecondary">
            A pipeline fix has passed sandbox validation. Enter security token to apply changes.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-[11px] font-mono uppercase text-textSecondary mb-1.5">
            Human Operator Security Token (Check logs for generated token):
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={tokenInput}
              onChange={(e) => {
                setTokenInput(e.target.value);
                setError('');
              }}
              placeholder="e.g. SO-A3F9C2D"
              className="flex-1 bg-background border border-panel text-textPrimary font-mono text-sm uppercase rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-amber-500 placeholder-textSecondary/30"
              autoFocus
            />
            <button
              type="submit"
              className="flex items-center gap-1.5 bg-remediator text-background hover:bg-remediator/90 px-5 py-2 rounded-lg text-xs font-mono font-bold transition-all duration-200 focus:ring-2 focus:ring-offset-2 focus:ring-remediator"
            >
              <ShieldCheck className="w-4 h-4" />
              Approve
            </button>
          </div>
        </div>

        {error && (
          <p className="text-xs text-alert font-mono">
            {error}
          </p>
        )}

        <div className="flex items-center justify-between border-t border-panel/60 pt-3 text-[11px] font-mono">
          <span className="text-textSecondary">
            Session Target Instance: <code className="bg-background px-1.5 py-0.5 rounded text-detector">i-091a1a2b3c...</code>
          </span>
          <button
            type="button"
            onClick={onReject}
            className="flex items-center gap-1 text-textSecondary hover:text-alert transition-all"
          >
            <RefreshCw className="w-3 h-3" />
            Reject & Reset
          </button>
        </div>
      </form>
    </div>
  );
}
