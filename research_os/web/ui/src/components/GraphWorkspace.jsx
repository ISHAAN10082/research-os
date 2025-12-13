import React from 'react';
import { CitationGraph } from './CitationGraph';
import { useResearchStore } from '../stores/useResearchStore';

export function GraphWorkspace() {
    const { setMode, setActivePaper } = useResearchStore();

    const handleNodeClick = (node) => {
        // e.g. node.path
        if (node.path) {
            setActivePaper(node);
            setMode('reading');
        }
    };

    return (
        <div className="w-full h-full relative">
            {/* HUD / Overlay */}
            <div className="absolute top-4 left-4 z-10 bg-black/50 backdrop-blur border border-white/10 p-4 rounded-xl text-xs text-gray-400">
                <h3 className="text-white font-bold mb-1">Knowledge Graph</h3>
                <p>Interactive Citation Network</p>
                <div className="mt-2 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-research-blue"></div>
                    <span>Paper</span>
                </div>
            </div>

            <CitationGraph onNodeClick={handleNodeClick} />
        </div>
    )
}
