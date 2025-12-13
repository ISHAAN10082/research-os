import React, { useEffect } from 'react';
import { useResearchStore } from './stores/useResearchStore';
import { wsSync } from './services/WebSocketSync';
import { Layout, BookOpen, GitGraph, Brain } from 'lucide-react';
import { motion } from 'framer-motion';

import { ReadingWorkspace } from './components/ReadingWorkspace';
import { GraphWorkspace } from './components/GraphWorkspace';
import { SynthesisWorkspace } from './components/SynthesisWorkspace';

function App() {
  const { mode, setMode, isConnected } = useResearchStore();

  useEffect(() => {
    wsSync.connect();
    // Load initial data
    fetch('/api/papers').then(r => r.json()).then(papers => useResearchStore.getState().setPapers(papers));
  }, []);

  const navItems = [
    { id: 'synthesis', icon: Brain, label: 'Synthesis' },
    { id: 'reading', icon: BookOpen, label: 'Reading' },
    { id: 'graph', icon: GitGraph, label: 'Graph' },
  ];

  return (
    <div className="flex h-screen w-screen bg-research-dark text-research-text overflow-hidden font-sans">
      {/* Sidebar */}
      <nav className="w-20 border-r border-white/10 flex flex-col items-center py-6 gap-6 bg-research-panel/50 backdrop-blur-xl">
        <div className="mb-4">
          <Layout className="w-8 h-8 text-research-blue" />
        </div>

        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => {
              setMode(item.id);
              wsSync.sendTelemetry(item.id, 'nav_switch', { to: item.id });
            }}
            className={`p-3 rounded-xl transition-all duration-300 relative group
              ${mode === item.id ? 'bg-research-blue/20 text-research-blue' : 'text-gray-500 hover:bg-white/5 hover:text-white'}
            `}
          >
            <item.icon className="w-6 h-6" />
            <span className="absolute left-16 bg-black px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-white/10 z-50">
              {item.label}
            </span>
          </button>
        ))}

        <div className="mt-auto">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`} title={isConnected ? "Online" : "Disconnected"} />
        </div>
      </nav>

      {/* Main Content Area - Glassmorphism & Animations */}
      <main className="flex-1 relative flex flex-col">
        {/* Top Bar / Header could go here */}

        <motion.div
          key={mode}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex-1 overflow-hidden"
        >
          {mode === 'synthesis' && <SynthesisWorkspace />}
          {mode === 'reading' && <ReadingWorkspace />}
          {mode === 'graph' && <GraphWorkspace />}
        </motion.div>
      </main>
    </div>
  );
}

export default App;
