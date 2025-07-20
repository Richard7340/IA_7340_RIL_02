import React, { useState, useEffect } from 'react';
import ControlPanel from './components/ControlPanel';
import IAWorkAssistant from './components/IAWorkAssistant';
import CommandExecutor from './components/CommandExecutor';
import SystemStatus from './components/SystemStatus';
import NeuralNetworkVisualizer from './components/NeuralNetworkVisualizer';
import './App.css';

export default function App() {
  const [controlTotal, setControlTotal] = useState(false);

  // Fetch initial control total state from backend
  useEffect(() => {
    fetch('http://localhost:5000/activar-control-total', { method: 'POST' })
      .then(res => res.json())
      .then(data => setControlTotal(data.control_total))
      .catch(err => console.error('Error fetching control total:', err));
  }, []);

  // Function to toggle control total
  const toggleControl = () => {
    fetch('http://localhost:5000/activar-control-total', { method: 'POST' })
      .then(res => res.json())
      .then(data => setControlTotal(data.control_total))
      .catch(err => console.error('Error activating control total:', err));
  };

  return (
    <div className="app-container">
      <ControlPanel />
      <div className="main-area">
        <SystemStatus />
        <NeuralNetworkVisualizer controlTotal={controlTotal} toggleControl={toggleControl} />
        <IAWorkAssistant />
        <CommandExecutor controlTotal={controlTotal} />
      </div>
    </div>
  );
}
