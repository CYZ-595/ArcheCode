// ArcheCode TypeScript Type Definitions

// ============================================================
// Project Types
// ============================================================

export type ProjectStatus =
  | "uploading"
  | "extracting"
  | "analyzing"
  | "completed"
  | "failed";

export type ProjectType =
  | "web_app"
  | "api_service"
  | "cli_tool"
  | "library"
  | "microservice"
  | "monolith"
  | "mobile_app"
  | "data_pipeline"
  | "unknown";

export type ArchitecturePattern =
  | "mvc"
  | "clean_architecture"
  | "microservices"
  | "monolith"
  | "plugin"
  | "event_driven"
  | "layered"
  | "hexagonal"
  | "unknown";

export interface TechStackItem {
  name: string;
  version?: string;
  category: string;
  confidence: number;
}

export interface FileNode {
  name: string;
  path: string;
  is_directory: boolean;
  children: FileNode[];
  size?: number;
  language?: string;
  line_count?: number;
}

export interface ProjectMetadata {
  name: string;
  description?: string;
  project_type: ProjectType;
  architecture_pattern: ArchitecturePattern;
  tech_stack: TechStackItem[];
  entry_points: string[];
  total_files: number;
  total_lines: number;
  languages: Record<string, number>;
  has_tests: boolean;
  has_docs: boolean;
  has_ci: boolean;
  has_docker: boolean;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  source_type: string;
  source_url?: string;
  upload_path?: string;
  metadata?: ProjectMetadata;
  file_tree?: FileNode;
  created_at: string;
  updated_at: string;
  error?: string;
}

export interface ProjectUploadResponse {
  project_id: string;
  status: ProjectStatus;
  message: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  project_type: ProjectType;
  total_files: number;
  created_at: string;
}

// ============================================================
// Analysis Types
// ============================================================

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type FindingCategory =
  | "bug"
  | "dead_code"
  | "tech_debt"
  | "security"
  | "performance"
  | "style"
  | "complexity"
  | "duplication"
  | "circular_dependency"
  | "magic_number"
  | "naming"
  | "deprecated";

export interface CodeLocation {
  file_path: string;
  line_start: number;
  line_end?: number;
  column_start?: number;
  column_end?: number;
  code_snippet?: string;
}

export interface AnalysisFinding {
  id: string;
  category: FindingCategory;
  severity: Severity;
  title: string;
  description: string;
  location?: CodeLocation;
  suggestion?: string;
  auto_fixable: boolean;
  confidence: number;
}

export interface SecurityIssue {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  location: CodeLocation;
  cwe_id?: string;
  recommendation: string;
}

export interface ModuleDependency {
  source: string;
  target: string;
  dependency_type: string;
  weight: number;
}

export interface FunctionInfo {
  name: string;
  file_path: string;
  line_start: number;
  line_end: number;
  parameters: string[];
  return_type?: string;
  docstring?: string;
  complexity?: number;
  is_exported: boolean;
  callers: string[];
  callees: string[];
}

export interface ClassInfo {
  name: string;
  file_path: string;
  line_start: number;
  line_end: number;
  methods: FunctionInfo[];
  base_classes: string[];
  attributes: string[];
  docstring?: string;
}

export interface AnalysisResult {
  project_id: string;
  id: string;
  created_at: string;
  summary: string;
  project_type: string;
  architecture_pattern: string;
  findings: AnalysisFinding[];
  security_issues: SecurityIssue[];
  dependencies: ModuleDependency[];
  functions: FunctionInfo[];
  classes: ClassInfo[];
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  overall_health_score: number;
  readme_content?: string;
  api_docs?: string;
  architecture_description?: string;
  refactoring_suggestions: string[];
}

// ============================================================
// Chat Types
// ============================================================

export type MessageRole = "user" | "assistant" | "system";

export interface CodeReference {
  file_path: string;
  line_start: number;
  line_end?: number;
  description?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  code_references: CodeReference[];
  timestamp: string;
}

export interface ChatRequest {
  project_id: string;
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  conversation_id: string;
  context_files: string[];
}

// ============================================================
// Visualization Types
// ============================================================

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  data: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
