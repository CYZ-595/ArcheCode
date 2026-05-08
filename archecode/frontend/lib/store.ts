// ArcheCode Global State Store (Zustand)
import { create } from "zustand";
import type {
  Project,
  AnalysisResult,
  ChatMessage,
  FileNode,
} from "@/types";

interface AppState {
  // Current project
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;

  // Analysis
  currentAnalysis: AnalysisResult | null;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;
  isAnalyzing: boolean;
  setIsAnalyzing: (v: boolean) => void;

  // Chat
  chatMessages: ChatMessage[];
  addChatMessage: (msg: ChatMessage) => void;
  clearChat: () => void;
  conversationId: string | null;
  setConversationId: (id: string | null) => void;

  // File explorer
  selectedFile: string | null;
  setSelectedFile: (path: string | null) => void;
  fileContent: string | null;
  setFileContent: (content: string | null) => void;

  // UI state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Current project
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  // Analysis
  currentAnalysis: null,
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  isAnalyzing: false,
  setIsAnalyzing: (v) => set({ isAnalyzing: v }),

  // Chat
  chatMessages: [],
  addChatMessage: (msg) =>
    set((state) => ({ chatMessages: [...state.chatMessages, msg] })),
  clearChat: () => set({ chatMessages: [], conversationId: null }),
  conversationId: null,
  setConversationId: (id) => set({ conversationId: id }),

  // File explorer
  selectedFile: null,
  setSelectedFile: (path) => set({ selectedFile: path }),
  fileContent: null,
  setFileContent: (content) => set({ fileContent: content }),

  // UI state
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  activeTab: "overview",
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
