const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 5000;

app.use(express.json());

// Keep track of active faults
let activeFault = null; // 'config_regression' or 'security_group' or null

// Help simulate delays
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', activeFault });
});

app.get('/api/data', async (req, res) => {
  const start = Date.now();
  
  if (activeFault === 'config_regression') {
    // Simulate database pool connection timeout exhaustion
    await delay(4200);
    return res.status(500).json({
      error: 'Internal Server Error',
      message: 'Connection pool exhausted. Timeout waiting for connection after 4000ms.'
    });
  } else if (activeFault === 'security_group') {
    // Simulate connection timeout to Auth service
    await delay(3000);
    return res.status(503).json({
      error: 'Service Unavailable',
      message: 'Gateway Timeout. Auth Service did not respond.'
    });
  }

  // Normal path: slight variable latency around 150-180ms
  const randomLatency = 150 + Math.floor(Math.random() * 30);
  await delay(randomLatency);
  res.json({
    status: 'success',
    latency_ms: Date.now() - start,
    data: [
      { id: 1, name: 'Prod-DB-Replica-1', role: 'Read' },
      { id: 2, name: 'Prod-DB-Replica-2', role: 'Read' }
    ]
  });
});

// Fault simulation triggers
app.post('/simulate/fault', (req, res) => {
  const { type } = req.body;
  if (type === 'config_regression' || type === 'security_group') {
    activeFault = type;
    console.log(`[FAULT INJECTED] ${type}`);
    return res.json({ status: 'injected', activeFault });
  }
  res.status(400).json({ error: 'Invalid fault type' });
});

app.post('/simulate/clear', (req, res) => {
  console.log(`[FAULT CLEARED] Previous: ${activeFault}`);
  activeFault = null;
  res.json({ status: 'cleared', activeFault });
});

app.listen(PORT, () => {
  console.log(`Target web application running on port ${PORT}`);
});
