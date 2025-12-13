import React, { useState } from 'react';
import { FileText, Table, Image } from 'lucide-react';

export function PDFViewer({ paper }) {
    const [mode, setMode] = useState('pdf'); // 'pdf' | 'structure'

    // Construct PDF path using API proxy
    // paper.path is absolute path, server needs relative or we use the serve endpoint
    const pdfUrl = `/api/papers/pdf?path=${encodeURIComponent(paper.path)}`;

    return (
        <div className="h-full flex flex-col relative group">
            {/* Toolbar Overlay */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur border border-white/10 rounded-full px-4 py-2 flex items-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity z-50 shadow-2xl">
                <button
                    onClick={() => setMode('pdf')}
                    className={`flex items-center gap-2 text-xs font-bold ${mode === 'pdf' ? 'text-white' : 'text-gray-500 hover:text-white'}`}
                >
                    <FileText className="w-4 h-4" /> Original
                </button>
                <div className="w-px h-4 bg-white/20" />
                <button
                    onClick={() => setMode('structure')}
                    className={`flex items-center gap-2 text-xs font-bold ${mode === 'structure' ? 'text-research-blue' : 'text-gray-500 hover:text-white'}`}
                >
                    <Table className="w-4 h-4" /> Deep Structure
                </button>
            </div>

            {mode === 'pdf' ? (
                <iframe
                    src={pdfUrl}
                    className="w-full h-full border-none bg-white"
                    title="PDF Viewer"
                />
            ) : (
                <StructureView paper={paper} />
            )}
        </div>
    );
}

function StructureView({ paper }) {
    // Placeholder for Grobid data visualization
    return (
        <div className="h-full overflow-y-auto p-8 bg-research-dark text-center">
            <h2 className="text-xl font-bold mb-4">Deep Structure Analysis</h2>
            <p className="text-gray-500 mb-8">Extracted via Grobid & Unstructured</p>

            <div className="grid grid-cols-2 gap-4 max-w-2xl mx-auto">
                <div className="p-6 rounded-xl bg-white/5 border border-white/10 hover:border-research-blue/50 transition-colors cursor-pointer">
                    <Table className="w-8 h-8 text-research-blue mb-2 mx-auto" />
                    <div className="font-bold">2 Tables Detected</div>
                </div>
                <div className="p-6 rounded-xl bg-white/5 border border-white/10 hover:border-research-blue/50 transition-colors cursor-pointer">
                    <Image className="w-8 h-8 text-purple-500 mb-2 mx-auto" />
                    <div className="font-bold">5 Figures</div>
                </div>
            </div>

            <div className="mt-8 p-4 bg-yellow-500/10 border border-yellow-500/20 text-yellow-200 rounded text-sm">
                Run <code>docker-compose up</code> to enable live Grobid extraction.
            </div>
        </div>
    )
}
