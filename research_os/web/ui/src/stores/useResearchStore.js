import { create } from 'zustand';

/**
 * Global ResearchOS State.
 * Manages the "Spatial" context of the user.
 */
export const useResearchStore = create((set, get) => ({
    // Workspace State
    mode: 'synthesis', // 'synthesis' | 'reading' | 'graph'
    setMode: (mode) => set({ mode }),

    // Data
    papers: [],
    setPapers: (papers) => set({ papers }),

    // Reading Mode State
    activePaper: null,
    setActivePaper: (paper) => set({ activePaper: paper }),

    // Model Choice
    useCloud: false,
    toggleCloud: () => set((state) => ({ useCloud: !state.useCloud })),

    // Intelligence / Dashboard
    stats: {
        crystallizationRate: 0,
        readingVelocity: 0,
    },
    setStats: (stats) => set({ stats }),

    // WebSocket Status
    isConnected: false,
    setConnected: (status) => set({ isConnected: status }),
}));
