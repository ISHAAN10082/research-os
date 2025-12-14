import React, { useState } from 'react';
import { useResearchStore } from '../stores/useResearchStore';
import { ChatInterface } from './ChatInterface';
import { PDFViewer } from './PDFViewer';
import { Plus, Search, Loader2 } from 'lucide-react';

export function ReadingWorkspace() {
    const { activePaper, papers } = useResearchStore();
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState([]);
    const [searching, setSearching] = useState(false);
    const [ingesting, setIngesting] = useState(null); // ID of paper being ingested

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setSearching(true);
        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: searchQuery })
            });
            const data = await res.json();
            setSearchResults(data);
        } catch (e) {
            console.error("Search failed", e);
        } finally {
            setSearching(false);
        }
    };

    const handleIngest = async (paper) => {
        setIngesting(paper.id);
        try {
            // Send to backend (Async)
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: paper.title,
                    pdf_url: paper.url,
                    abstract: paper.abstract,
                    authors: paper.authors
                })
            });
            const ingestData = await res.json();

            if (res.ok) {
                // Refresh immediately (optimistic)
                const papers = await fetch('/api/papers').then(r => r.json());
                useResearchStore.getState().setPapers(papers);

                // Auto-select the new paper to prevent "Blank Screen" confusion
                const newPaper = papers.find(p => p.paper_id === ingestData.id);
                // Note: server returns 'id', schema uses 'paper_id'. 
                // Frontend 'papers' usually map to whatever schema returns.
                // Schema get_all_papers returns 'paper_id'.
                // Frontend might expect 'id' if using a specific store adapter?
                // Let's check search results 'id'.
                // Safest is to find by paper_id.

                if (newPaper) {
                    useResearchStore.getState().setActivePaper(newPaper);
                }

                // Close search after brief delay
                setTimeout(() => {
                    setIngesting(null);
                    setShowSearch(false);
                }, 500);
            }
        } catch (e) {
            alert("Failed to start ingestion");
            setIngesting(null);
        }
    };

    return (
        <div className="flex h-full w-full">
            {/* Paper List Sidebar */}
            <div className="w-64 border-r border-white/10 bg-research-panel/30 backdrop-blur flex flex-col">
                <div className="p-4 flex items-center justify-between">
                    <span className="font-bold text-sm uppercase tracking-widest text-gray-500">Library</span>
                    <button onClick={() => setShowSearch(true)} className="p-1 hover:bg-white/10 rounded text-research-blue" title="Add Paper">
                        <Plus className="w-4 h-4" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {papers.map(p => (
                        <div
                            key={p.paper_id || p.id}
                            onClick={async () => {
                                // Set active paper immediately for UI
                                useResearchStore.getState().setActivePaper(p);

                                // If paper has no text, trigger extraction
                                if (!p.raw_text && p.paper_id) {
                                    console.log("Extracting text for:", p.paper_id);
                                    try {
                                        await fetch(`/api/papers/extract/${p.paper_id}`, { method: 'POST' });
                                        // Refresh papers to get updated text
                                        const papers = await fetch('/api/papers').then(r => r.json());
                                        useResearchStore.getState().setPapers(papers);
                                        // Update active paper with new data
                                        const updated = papers.find(x => x.paper_id === p.paper_id);
                                        if (updated) {
                                            useResearchStore.getState().setActivePaper(updated);
                                        }
                                    } catch (e) {
                                        console.error("Extract failed:", e);
                                    }
                                }
                            }}
                            className={`p-3 m-2 rounded cursor-pointer text-sm transition-colors border border-transparent
                        ${activePaper?.paper_id === p.paper_id ? 'bg-research-blue/20 border-research-blue/50 text-white' : 'hover:bg-white/5 text-gray-400'}
                    `}
                        >
                            <div className="font-medium truncate">{p.title}</div>
                            <div className="text-xs text-gray-500 mt-1 truncate">{p.authors}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Search Modal */}
            {showSearch && (
                <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-10">
                    <div className="bg-research-panel border border-white/10 rounded-2xl w-full max-w-2xl h-[600px] flex flex-col shadow-2xl">
                        <div className="p-4 border-b border-white/10 flex items-center justify-between">
                            <h2 className="text-lg font-bold flex items-center gap-2">
                                <Search className="w-5 h-5 text-research-blue" />
                                Search ArXiv
                            </h2>
                            <button onClick={() => setShowSearch(false)} className="text-gray-500 hover:text-white">✕</button>
                        </div>
                        <div className="p-4">
                            <form onSubmit={(e) => { e.preventDefault(); handleSearch(); }} className="flex gap-2">
                                <input
                                    className="flex-1 bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-research-blue/50 outline-none"
                                    placeholder="Keywords, title, or author..."
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                />
                                <button type="submit" disabled={searching} className="bg-research-blue text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-500 disabled:opacity-50">
                                    {searching ? <Loader2 className="w-5 h-5 animate-spin" /> : "Search"}
                                </button>
                            </form>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-2">
                            {searchResults.map(r => (
                                <div key={r.id} className="p-4 border border-white/5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors flex justify-between items-start">
                                    <div className="flex-1 pr-4">
                                        <h3 className="font-bold text-research-blue">{r.title}</h3>
                                        <p className="text-xs text-gray-400 mt-1">{r.authors.slice(0, 3).join(", ")} ({r.year})</p>
                                        <p className="text-xs text-gray-500 mt-2 line-clamp-2">{r.abstract}</p>
                                    </div>
                                    <button
                                        onClick={() => handleIngest(r)}
                                        disabled={ingesting !== null}
                                        className={`text-xs px-3 py-1.5 rounded-lg transition-colors border border-white/10 flex items-center gap-2
                                            ${ingesting === r.id
                                                ? 'bg-research-blue text-white cursor-wait'
                                                : 'bg-white/10 hover:bg-green-500/20 hover:text-green-400'
                                            }
                                        `}
                                    >
                                        {ingesting === r.id ? (
                                            <>
                                                <Loader2 className="w-3 h-3 animate-spin" />
                                                <span>Adding...</span>
                                            </>
                                        ) : (
                                            "Add"
                                        )}
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

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
