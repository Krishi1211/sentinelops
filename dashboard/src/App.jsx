import React from 'react';
import Header from './components/Header';
import PipelineStrip from './components/PipelineStrip';
import TraceTerminal from './components/TraceTerminal';
import MetricsChart from './components/MetricsChart';
import ApprovalGate from './components/ApprovalGate';
import PostmortemPanel from './components/PostmortemPanel';
import EvalScorecard from './components/EvalScorecard';
import { mockScenarios } from './data/mockScenarios';

export default function App() {
  const [isMockMode, setIsMockMode] = React.useState(true);
  const [status, setStatus] = React.useState('Monitoring');
  const [activeFault, setActiveFault] = React.useState(null);
  const [approvalToken, setApprovalToken] = React.useState(null);
  const [logs, setLogs] = React.useState([]);
  const [metrics, setMetrics] = React.useState([]);
  const [pipeline, setPipeline] = React.useState({
    detector: { status: 'idle', duration: null },
    diagnostician: { status: 'idle', duration: null },
    remediator: { status: 'idle', duration: null }
  });
  const [postmortem, setPostmortem] = React.useState(null);

  // For offline mock play timeline
  const [mockPlaying, setMockPlaying] = React.useState(false);
  const [mockSteps, setMockSteps] = React.useState([]);
  const [mockIndex, setMockIndex] = React.useState(0);

  const wsRef = React.useRef(null);

  // Initialize healthy baseline metrics
  React.useEffect(() => {
    const initialMetrics = [];
    const now = new Date();
    for (let i = 0; i < 15; i++) {
      const t = new Date(now.getTime() - (15 - i) * 5000);
      initialMetrics.push({
        Timestamp: t.toLocaleTimeString(),
        p99_latency_ms: 150 + (i * 3) % 25
      });
    }
    setMetrics(initialMetrics);
  }, []);

  // WebSocket management
  React.useEffect(() => {
    if (isMockMode) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    // Connect to local python backend
    const socket = new WebSocket('ws://127.0.0.1:8000/ws/trace');
    wsRef.current = socket;

    socket.onopen = () => {
      setLogs([{
        timestamp: new Date().toLocaleTimeString(),
        agent: 'SYSTEM',
        type: 'INFO',
        content: 'CONNECTED to Live SentinelOps Agent Orchestrator.'
      }]);
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.event) {
        case 'state':
          const s = msg.data;
          setStatus(s.status);
          setPipeline(s.pipeline);
          setLogs(s.logs);
          if (s.metrics && s.metrics.length > 0) setMetrics(s.metrics);
          setPostmortem(s.postmortem);
          setActiveFault(s.active_fault);
          setApprovalToken(s.approval_token);
          break;
        case 'status':
          setStatus(msg.data);
          break;
        case 'pipeline':
          setPipeline(msg.data);
          break;
        case 'log':
          setLogs(prev => [...prev, msg.data]);
          break;
        case 'metrics':
          setMetrics(msg.data);
          break;
        case 'postmortem':
          setPostmortem(msg.data);
          break;
        case 'reset':
          handleResetState();
          break;
        default:
          break;
      }
    };

    socket.onerror = () => {
      setLogs(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        agent: 'SYSTEM',
        type: 'ALERT',
        content: 'Failed to connect to backend. Falling back to local Mock Simulation Mode.'
      }]);
      setIsMockMode(true);
    };

    socket.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      if (socket) socket.close();
    };
  }, [isMockMode]);

  const handleResetState = () => {
    setStatus('Monitoring');
    setActiveFault(null);
    setApprovalToken(null);
    setLogs([]);
    setPostmortem(null);
    setPipeline({
      detector: { status: 'idle', duration: null },
      diagnostician: { status: 'idle', duration: null },
      remediator: { status: 'idle', duration: null }
    });
    
    // Reset metrics to healthy baseline
    const initialMetrics = [];
    const now = new Date();
    for (let i = 0; i < 15; i++) {
      const t = new Date(now.getTime() - (15 - i) * 5000);
      initialMetrics.push({
        Timestamp: t.toLocaleTimeString(),
        p99_latency_ms: 150 + (i * 3) % 25
      });
    }
    setMetrics(initialMetrics);
    
    setMockPlaying(false);
    setMockSteps([]);
    setMockIndex(0);
  };

  // Mock Timeline Step Executor
  React.useEffect(() => {
    if (!isMockMode || !mockPlaying || mockIndex >= mockSteps.length) return;

    const step = mockSteps[mockIndex];
    
    // Process step
    const timer = setTimeout(() => {
      if (step.type === 'log') {
        // Add log
        const logEntry = {
          timestamp: new Date().toLocaleTimeString(),
          agent: step.agent,
          type: step.logType,
          content: step.content
        };
        setLogs(prev => [...prev, logEntry]);
        
        // Update metric
        setMetrics(prev => {
          const newPoints = [...prev, {
            Timestamp: new Date().toLocaleTimeString(),
            p99_latency_ms: step.latency
          }];
          if (newPoints.length > 25) newPoints.shift();
          return newPoints;
        });

        // Update pipeline state
        if (step.pipeline) {
          setPipeline(step.pipeline);
        }

        // Check if checkpoint (Approval Gate block)
        if (step.checkpoint) {
          setStatus('Awaiting Approval');
          const token = activeFault === 'config_regression' ? 'SO-A3F9C2D' : 'SO-SG8080X';
          setApprovalToken(token);
          setMockIndex(mockIndex + 1);
          return; // Halts timer execution loop
        }

        setMockIndex(mockIndex + 1);
      } else if (step.type === 'postmortem') {
        setPostmortem(step.postmortem);
        setStatus('Resolved');
        setMockPlaying(false);
      }
    }, mockIndex === 0 ? 0 : 700 + Math.random() * 500); // realistic timing spacing

    return () => clearTimeout(timer);
  }, [isMockMode, mockPlaying, mockIndex, mockSteps, activeFault]);

  // Inject Incident Trigger
  const handleInjectFault = async (type) => {
    handleResetState();

    if (isMockMode) {
      setActiveFault(type);
      setStatus('Incident Active');
      setMockSteps(mockScenarios[type].steps);
      setMockIndex(0);
      setMockPlaying(true);
    } else {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/scenario/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type })
        });
        if (!response.ok) {
          const data = await response.json();
          alert(data.detail || 'Failed to inject fault.');
        }
      } catch (err) {
        alert('Backend connection error: ' + err.message);
      }
    }
  };

  // Remediation approval gate
  const handleApprove = async (token, callback) => {
    if (isMockMode) {
      const expectedToken = activeFault === 'config_regression' ? 'SO-A3F9C2D' : 'SO-SG8080X';
      if (token.toUpperCase() === expectedToken) {
        callback(true);
        setStatus('Incident Active');
        // Continue simulation
        setMockPlaying(true);
      } else {
        callback(false);
      }
    } else {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/remediation/approve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token })
        });
        if (response.ok) {
          callback(true);
        } else {
          callback(false);
        }
      } catch (err) {
        alert('Backend connection error: ' + err.message);
        callback(false);
      }
    }
  };

  // Remediation rejection / simulation reset
  const handleReject = async () => {
    if (isMockMode) {
      handleResetState();
    } else {
      try {
        await fetch('http://127.0.0.1:8000/api/remediation/reject', { method: 'POST' });
      } catch (err) {
        alert('Backend connection error: ' + err.message);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background text-textPrimary flex flex-col antialiased">
      {/* Header */}
      <Header 
        status={status} 
        activeFault={activeFault} 
        onInject={handleInjectFault}
        isMockMode={isMockMode}
        setIsMockMode={setIsMockMode}
      />

      {/* Core Body Container */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {/* Horizontal Pipeline Status */}
        <PipelineStrip pipeline={pipeline} />

        {/* Dynamic Approval Gate */}
        <ApprovalGate 
          status={status}
          generatedToken={approvalToken}
          onApprove={handleApprove}
          onReject={handleReject}
        />

        {/* Dashboard Grid split: Trace logs on left, chart + postmortem on right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Trace console logs */}
          <div className="lg:col-span-7">
            <TraceTerminal logs={logs} />
          </div>

          {/* Right Column details */}
          <div className="lg:col-span-5 space-y-6">
            <MetricsChart metrics={metrics} />
            <PostmortemPanel postmortem={postmortem} />
          </div>
        </div>

        {/* Evaluation Benchmarks */}
        <EvalScorecard />
      </main>
    </div>
  );
}
