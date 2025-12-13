import React from 'react';
import { useResearchStore } from '../stores/useResearchStore';
import { ChatInterface } from './ChatInterface';
import { PDFViewer } from './PDFViewer';

export function ReadingWorkspace() {
    const { activePaper, papers } = useResearchStore();

    return (
        <div className="flex h-full w-full">
            {/* Paper List Sidebar (Collapsible?) */}
            <div className="w-64 border-r border-white/10 bg-research-panel/30 backdrop-blur flex flex-col">
                <div className="p-4 font-bold text-sm uppercase tracking-widest text-gray-500">Library</div>
                <div className="flex-1 overflow-y-auto">
                    {papers.map(p => (
                        <div
                            key={p.path}
                            onClick={() => useResearchStore.getState().setActivePaper(p)}
                            className={`p-3 m-2 rounded cursor-pointer text-sm transition-colors border border-transparent
                        ${activePaper?.path === p.path ? 'bg-research-blue/20 border-research-blue/50 text-white' : 'hover:bg-white/5 text-gray-400'}
                    `}
                        >
                            {p.title}
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content: Split View PDF + Chat */}
            <div className="flex-1 flex max-w-[calc(100vw-64px)]">
                {/* PDF Area - 50% width by default, could be resizable */}
                <div className="flex-1 border-r border-white/10 relative">
                    {activePaper ? (
                        <PDFViewer paper={activePaper} />
                    ) : (
                        <div className="h-full flex items-center justify-center text-gray-500">
                            Select a paper to read
                        </div>
                    )}
                </div>

                {/* Chat / Copilot Area - 400px fixed or flex */}
                <div className="w-[450px] bg-research-panel/50 backdrop-blur border-l border-white/5">
                    <ChatInterface />
                </div>
            </div>
        </div>
    );
}
