// ArcheCode API Client
// Handles all communication with the backend FastAPI server.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    let message = `API Error: ${response.status}`;
    try {
      const parsed = JSON.parse(errorBody);
      message = parsed.detail || message;
    } catch {}
    throw new ApiError(message, response.status);
  }

  return response.json();
}

// ============================================================
// Project API
// ============================================================

import type {
  Project,
  ProjectSummary,
  ProjectUploadResponse,
  FileNode,
} from "@/types";

export const projectApi = {
  upload: async (file: File): Promise<ProjectUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/projects/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      let message = "Upload failed";
      try {
        const parsed = JSON.parse(errorBody);
        message = parsed.detail || message;
      } catch {}
      throw new ApiError(message, response.status);
    }

    return response.json();
  },

  importGithub: async (url: string): Promise<ProjectUploadResponse> => {
    return request("/projects/import-github", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  },

  list: async (): Promise<ProjectSummary[]> => {
    return request("/projects/");
  },

  get: async (id: string): Promise<Project> => {
    return request(`/projects/${id}`);
  },

  delete: async (id: string): Promise<void> => {
    return request(`/projects/${id}`, { method: "DELETE" });
  },

  getFiles: async (id: string): Promise<{ files: string[] }> => {
    return request(`/projects/${id}/files`);
  },

  getFile: async (
    id: string,
    filePath: string
  ): Promise<{ file_path: string; content: string }> => {
    return request(`/projects/${id}/files/${encodeURIComponent(filePath)}`);
  },

  getTree: async (id: string): Promise<FileNode> => {
    return request(`/projects/${id}/tree`);
  },
};

// ============================================================
// Analysis API
// ============================================================

import type { AnalysisResult, GraphData } from "@/types";

export const analysisApi = {
  start: async (
    projectId: string,
    analysisTypes?: string[],
    useAi: boolean = true
  ): Promise<AnalysisResult> => {
    return request("/analysis/start", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        analysis_types: analysisTypes || [
          "architecture",
          "bugs",
          "dead_code",
          "security",
          "tech_debt",
          "dependencies",
          "documentation",
        ],
        use_ai: useAi,
      }),
    });
  },

  get: async (id: string): Promise<AnalysisResult> => {
    return request(`/analysis/${id}`);
  },

  getByProject: async (projectId: string): Promise<AnalysisResult[]> => {
    return request(`/analysis/project/${projectId}`);
  },

  getDependencyGraph: async (id: string): Promise<GraphData> => {
    return request(`/analysis/${id}/graph/dependencies`);
  },

  getFunctionGraph: async (id: string): Promise<GraphData> => {
    return request(`/analysis/${id}/graph/functions`);
  },
};

// ============================================================
// Chat API
// ============================================================

import type { ChatResponse as ChatRespType } from "@/types";

export const chatApi = {
  send: async (
    projectId: string,
    message: string,
    conversationId?: string
  ): Promise<ChatRespType> => {
    return request("/chat/send", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        message,
        conversation_id: conversationId,
      }),
    });
  },

  getConversation: async (id: string) => {
    return request(`/chat/conversations/${id}`);
  },

  getSuggestions: async (
    projectId: string
  ): Promise<{ suggestions: string[] }> => {
    return request(`/chat/suggestions/${projectId}`);
  },
};
