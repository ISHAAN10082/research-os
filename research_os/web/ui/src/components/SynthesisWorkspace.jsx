import React, { useState } from 'react';
import { ChatInterface } from './ChatInterface';
import { Plus, MessageSquare } from 'lucide-react';

export function SynthesisWorkspace() {
    const [threads, setThreads] = useState([
        { id: 1, title: "Research Plan: Spatial Intelligence", date: 'Just now' },
        { id: 2, title: "Notes on Transformer Architecture", date: '2 hours ago' },
    ]);
    const [activeThreadId, setActiveThreadId] = useState(1);

    return (
        <div className="flex h-full w-full">
            {/* Thread List */}
            <div className="w-64 border-r border-white/10 bg-research-panel/30 backdrop-blur flex flex-col">
                <div className="p-4 flex items-center justify-between">
                    <span className="font-bold text-sm uppercase tracking-widest text-gray-500">Threads</span>
                    <button className="p-1 hover:bg-white/10 rounded text-research-blue">
                        <Plus className="w-4 h-4" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {threads.map(thread => (
                        <div
                            key={thread.id}
                            onClick={() => setActiveThreadId(thread.id)}
                            className={`p-3 m-2 rounded cursor-pointer text-sm transition-colors border border-transparent group
                                ${activeThreadId === thread.id ? 'bg-research-blue/20 border-research-blue/50 text-white' : 'hover:bg-white/5 text-gray-400'}
                            `}
                        >
                            <div className="font-medium flex items-center gap-2">
                                <MessageSquare className="w-3 h-3 opacity-50" />
                                {thread.title}
                            </div>
                            <div className="text-xs text-gray-600 mt-1 pl-5">{thread.date}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Thread View */}
            <div className="flex-1 flex flex-col bg-research-dark">
                {/* Reusing ChatInterface for the thread content */}
                {/* In a real app, we'd load the specific thread history here */}
                <ChatInterface key={activeThreadId} />
            </div>
        </div>
    );
}
