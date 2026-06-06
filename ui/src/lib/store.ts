import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AgentKey = "research" | "solution" | "experiment";

export interface ReportSections {
  literature_review?: string | null;
  datasets?: string | null;
  models?: string | null;
  evaluation_plan?: string | null;
  prototype_guidance?: string | null;
}

export interface TaskEvent {
  step: string;
  status: string;
  detail: string;
  timestamp: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  sections?: ReportSections;
  agentsUsed?: string[];
  reasoning?: string;
  pending?: boolean;
  taskProgress?: TaskEvent[];
  raw?: unknown;
}

interface AppState {
  messages: Message[];
  addMessage: (m: Message) => void;
  updateMessage: (id: string, partial: Partial<Message>) => void;
  replaceAllMessages: (msgs: Message[]) => void;
  clearMessages: () => void;
  darkMode: boolean | null; // null = system
  setDarkMode: (v: boolean | null) => void;
  drawerOpen: boolean;
  setDrawerOpen: (v: boolean) => void;
  provider: "gemini" | "openai" | "anthropic";
  setProvider: (p: AppState["provider"]) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      messages: [],
      addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
      updateMessage: (id, partial) =>
        set((s) => ({
          messages: s.messages.map((msg) =>
            msg.id === id ? { ...msg, ...partial } : msg,
          ),
        })),
      replaceAllMessages: (msgs) => set({ messages: msgs }),
      clearMessages: () => set({ messages: [] }),
      darkMode: null,
      setDarkMode: (v) => set({ darkMode: v }),
      drawerOpen: false,
      setDrawerOpen: (v) => set({ drawerOpen: v }),
      provider: "gemini",
      setProvider: (p) => set({ provider: p }),
    }),
    {
      name: "agent-black-store",
      partialize: (s) => ({
        messages: s.messages,
        darkMode: s.darkMode,
        provider: s.provider,
      }),
    },
  ),
);
