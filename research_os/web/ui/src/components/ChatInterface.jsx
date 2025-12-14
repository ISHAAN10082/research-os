import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useResearchStore } from '../stores/useResearchStore';
import { wsSync } from '../services/WebSocketSync';
import { Send, Zap, Cloud, Bot } from 'lucide-react';

export function ChatInterface() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]); // { role: 'user'|'ai', content: '' }
    const [isGenerating, setGenerating] = useState(false);
    const messagesEndRef = useRef(null);

    const { useCloud, toggleCloud } = useResearchStore();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim() || isGenerating) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg, { role: 'ai', content: '' }]); // Optimistic AI placeholder
        setGenerating(true);
        setInput('');

        // Retrieve context from store (e.g. active paper text)
        // Priority: raw_text (full PDF) > abstract (from ArXiv) > empty
        const activePaper = useResearchStore.getState().activePaper;
        const context = activePaper?.raw_text || activePaper?.["p.raw_text"] || activePaper?.abstract || "";

        wsSync.streamChat(
            userMsg.content,
            context,
            useCloud,
            (token) => {
                setMessages(prev => {
                    const newHistory = [...prev];
                    const lastIdx = newHistory.length - 1;
                    // CRITICAL: Copy the object to avoid mutation in Strict Mode (which causes double printing)
                    const lastMsg = { ...newHistory[lastIdx] };
                    lastMsg.content += token;
                    newHistory[lastIdx] = lastMsg;
                    return newHistory;
                });
            },
            () => {
                setGenerating(false);
            }
        );
    };

    return (
        <div className="flex flex-col h-full font-sans">
            {/* Header */}
            <div className="h-14 border-b border-white/10 flex items-center justify-between px-4 bg-white/5 sticky top-0 z-10 backdrop-blur">
                <div className="flex items-center gap-2 text-research-text font-medium">
                    <Bot className="w-5 h-5 text-research-blue" />
                    <span>Research Copilot</span>
                </div>

                {/* Model Toggle */}
                <button
                    onClick={toggleCloud}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all border
                ${useCloud
                            ? 'bg-purple-500/20 text-purple-300 border-purple-500/50'
                            : 'bg-green-500/20 text-green-300 border-green-500/50'
                        }
            `}
                    title={useCloud ? "Using Cloud Model (70B)" : "Using Local Model (Phi-3)"}
                >
                    {useCloud ? <Cloud className="w-3 h-3" /> : <Zap className="w-3 h-3" />}
                    {useCloud ? 'GROQ 70B' : 'LOCAL'}
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                {messages.length === 0 && (
                    <div className="text-center text-gray-500 mt-20 text-sm">
                        Ask questions about your selected paper.
                    </div>
                )}
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                            className={`max-w-[85%] rounded-2xl p-3 text-sm leading-relaxed overflow-hidden
                        ${msg.role === 'user'
                                    ? 'bg-research-blue text-white rounded-br-none'
                                    : 'bg-white/10 text-gray-200 rounded-bl-none border border-white/5 markdown-body'
                                }
                    `}
                        >
                            {msg.role === 'user' ? (
                                msg.content
                            ) : (
                                <ReactMarkdown
                                    remarkPlugins={[remarkMath, remarkGfm]}
                                    rehypePlugins={[rehypeKatex]}
                                    components={{
                                        code({ node, inline, className, children, ...props }) {
                                            return !inline ? (
                                                <div className="bg-black/30 rounded p-2 my-2 overflow-x-auto text-xs font-mono border border-white/10">
                                                    <code {...props}>{children}</code>
                                                </div>
                                            ) : (
                                                <code className="bg-black/30 rounded px-1 py-0.5 text-xs font-mono" {...props}>
                                                    {children}
                                                </code>
                                            )
                                        }
                                    }}
                                >
                                    {msg.content}
                                </ReactMarkdown>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-white/10 bg-research-panel/80">
                <form onSubmit={handleSubmit} className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask ResearchOS..."
                        className="w-full bg-black/50 border border-white/10 rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:border-research-blue/50 transition-colors text-white placeholder-gray-600"
                    />
                    <button
                        type="submit"
                        disabled={isGenerating || !input.trim()}
                        className="absolute right-2 top-2 p-1.5 bg-research-blue text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
}
