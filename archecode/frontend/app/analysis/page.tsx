"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  FileCode2,
  Loader2,
  AlertTriangle,
  Bug,
  Shield,
  Layers,
  Activity,
  BarChart3,
  BookOpen,
  MessageSquare,
  ChevronRight,
  Folder,
  FolderOpen,
  File,
  ArrowLeft,
  RefreshCw,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { projectApi, analysisApi } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import {
  getSeverityColor,
  formatNumber,
  getLanguageColor,
} from "@/lib/utils";
import type {
  Project,
  AnalysisResult,
  FileNode,
  AnalysisFinding,
} from "@/types";
import { DependencyGraph } from "@/components/visualization/dependency-graph";
import { FileTree } from "@/components/analysis/file-tree";
import { FindingsList } from "@/components/analysis/findings-list";
import { HealthScore } from "@/components/analysis/health-score";
import { MarkdownPreview } from "@/components/analysis/markdown-preview";

export default function AnalysisPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectId = searchParams.get("id");

  const [project, setProject] = useState<Project | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [depGraph, setDepGraph] = useState<any>(null);

  // Load project data
  useEffect(() => {
    if (!projectId) {
      router.push("/");
      return;
    }

    const loadData = async () => {
      try {
        const proj = await projectApi.get(projectId);
        setProject(proj);

        if (proj.file_tree) {
          setFileTree(proj.file_tree);
        }

        // Check if analysis exists
        const analyses = await analysisApi.getByProject(projectId);
        if (analyses.length > 0) {
          setAnalysis(analyses[0]);
          // Load dependency graph
          try {
            const graph = await analysisApi.getDependencyGraph(analyses[0].id);
            setDepGraph(graph);
          } catch {}
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [projectId, router]);

  // Start analysis
  const startAnalysis = useCallback(async () => {
    if (!projectId) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await analysisApi.start(projectId);
      setAnalysis(result);

      // Reload project for updated metadata
      const proj = await projectApi.get(projectId);
      setProject(proj);
      if (proj.file_tree) setFileTree(proj.file_tree);

      // Load dependency graph
      try {
        const graph = await analysisApi.getDependencyGraph(result.id);
        setDepGraph(graph);
      } catch {}
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  }, [projectId]);

  // Load file content
  const loadFileContent = useCallback(
    async (path: string) => {
      if (!projectId) return;
      setSelectedFile(path);
      try {
        const result = await projectApi.getFile(projectId, path);
        setFileContent(result.content);
      } catch {
        setFileContent("Unable to load file content.");
      }
    },
    [projectId]
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-muted-foreground">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Project not found</h2>
          <Button onClick={() => router.push("/")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  const meta = project.metadata;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Navigation */}
      <nav className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1800px] mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/")}
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Home
            </Button>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <FileCode2 className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold">{project.name}</span>
              <Badge variant="secondary" className="text-xs">
                {meta?.project_type?.replace(/_/g, " ") || "unknown"}
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!analysis && (
              <Button
                onClick={startAnalysis}
                disabled={isAnalyzing}
                variant="glow"
                size="sm"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Activity className="w-4 h-4 mr-2" />
                    Run Analysis
                  </>
                )}
              </Button>
            )}
            {analysis && (
              <Button
                onClick={() => router.push(`/chat?id=${projectId}`)}
                variant="outline"
                size="sm"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                AI Chat
              </Button>
            )}
          </div>
        </div>
      </nav>

      {/* Error banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-2">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - File Tree */}
        <aside className="w-64 border-r border-border/50 flex flex-col shrink-0">
          <div className="p-3 border-b border-border/50">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Project Files
            </h3>
          </div>
          <ScrollArea className="flex-1">
            {fileTree ? (
              <FileTree
                node={fileTree}
                selectedFile={selectedFile}
                onSelectFile={loadFileContent}
              />
            ) : (
              <div className="p-4 text-center text-sm text-muted-foreground">
                No file tree available
              </div>
            )}
          </ScrollArea>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="flex-1 flex flex-col overflow-hidden"
          >
            <div className="border-b border-border/50 px-4">
              <TabsList className="bg-transparent h-12">
                <TabsTrigger value="overview" className="gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="findings" className="gap-2">
                  <Bug className="w-4 h-4" />
                  Findings
                  {analysis && (
                    <Badge variant="secondary" className="ml-1">
                      {analysis.total_findings}
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="architecture" className="gap-2">
                  <Layers className="w-4 h-4" />
                  Architecture
                </TabsTrigger>
                <TabsTrigger value="security" className="gap-2">
                  <Shield className="w-4 h-4" />
                  Security
                </TabsTrigger>
                <TabsTrigger value="docs" className="gap-2">
                  <BookOpen className="w-4 h-4" />
                  Documentation
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-auto">
              {/* File Content View (shown when a file is selected) */}
              {selectedFile && fileContent && activeTab === "overview" && (
                <div className="border-b border-border/50">
                  <div className="flex items-center justify-between px-4 py-2 bg-muted/30">
                    <span className="text-sm font-mono text-muted-foreground">
                      {selectedFile}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedFile(null);
                        setFileContent(null);
                      }}
                    >
                      Close
                    </Button>
                  </div>
                  <pre className="p-4 text-sm font-mono overflow-auto max-h-80 bg-muted/20">
                    {fileContent}
                  </pre>
                </div>
              )}

              {/* Overview Tab */}
              <TabsContent value="overview" className="m-0 p-4 space-y-4">
                {!analysis ? (
                  <div className="flex flex-col items-center justify-center py-20">
                    <Activity className="w-16 h-16 text-muted-foreground/30 mb-4" />
                    <h3 className="text-lg font-semibold mb-2">
                      No analysis yet
                    </h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      Run an analysis to get insights about this project.
                    </p>
                    <Button
                      onClick={startAnalysis}
                      disabled={isAnalyzing}
                      variant="glow"
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Activity className="w-4 h-4 mr-2" />
                          Start Analysis
                        </>
                      )}
                    </Button>
                  </div>
                ) : (
                  <>
                    {/* Metrics Row */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card>
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold">
                            {formatNumber(meta?.total_files || 0)}
                          </div>
                          <p className="text-xs text-muted-foreground">Files</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold">
                            {formatNumber(meta?.total_lines || 0)}
                          </div>
                          <p className="text-xs text-muted-foreground">Lines</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold">
                            {meta?.tech_stack?.length || 0}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Technologies
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4">
                          <HealthScore
                            score={analysis.overall_health_score}
                          />
                        </CardContent>
                      </Card>
                    </div>

                    {/* Summary + Languages */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      <Card className="lg:col-span-2">
                        <CardHeader>
                          <CardTitle className="text-base">
                            Project Summary
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          {analysis.summary ? (
                            <MarkdownPreview content={analysis.summary} />
                          ) : (
                            <p className="text-sm text-muted-foreground">
                              No summary available.
                            </p>
                          )}
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">
                            Languages
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          {meta?.languages &&
                            Object.entries(meta.languages)
                              .sort(([, a], [, b]) => b - a)
                              .slice(0, 8)
                              .map(([lang, count]) => {
                                const total = Object.values(
                                  meta.languages
                                ).reduce((s, v) => s + v, 0);
                                const pct = total > 0 ? (count / total) * 100 : 0;
                                return (
                                  <div key={lang}>
                                    <div className="flex justify-between text-sm mb-1">
                                      <span className="flex items-center gap-2">
                                        <div
                                          className="w-2.5 h-2.5 rounded-full"
                                          style={{
                                            backgroundColor:
                                              getLanguageColor(lang),
                                          }}
                                        />
                                        {lang}
                                      </span>
                                      <span className="text-muted-foreground">
                                        {pct.toFixed(1)}%
                                      </span>
                                    </div>
                                    <Progress
                                      value={pct}
                                      className="h-1.5"
                                      indicatorClassName=""
                                      style={
                                        {
                                          "--tw-bg-opacity": 1,
                                        } as React.CSSProperties
                                      }
                                    />
                                  </div>
                                );
                              })}
                        </CardContent>
                      </Card>
                    </div>

                    {/* Tech Stack */}
                    {meta?.tech_stack && meta.tech_stack.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">
                            Tech Stack
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="flex flex-wrap gap-2">
                            {meta.tech_stack.map((tech) => (
                              <Badge
                                key={tech.name}
                                variant="secondary"
                                className="px-3 py-1"
                              >
                                {tech.name}
                                <span className="ml-2 text-xs text-muted-foreground">
                                  {tech.category}
                                </span>
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Refactoring Suggestions */}
                    {analysis.refactoring_suggestions.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">
                            Refactoring Suggestions
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {analysis.refactoring_suggestions.map(
                              (suggestion, i) => (
                                <div
                                  key={i}
                                  className="p-3 bg-muted/50 rounded-lg text-sm"
                                >
                                  <MarkdownPreview content={suggestion} />
                                </div>
                              )
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </>
                )}
              </TabsContent>

              {/* Findings Tab */}
              <TabsContent value="findings" className="m-0 p-4">
                {analysis ? (
                  <FindingsList
                    findings={analysis.findings}
                    onFileClick={(path) => loadFileContent(path)}
                  />
                ) : (
                  <div className="text-center py-20 text-muted-foreground">
                    Run an analysis first to see findings.
                  </div>
                )}
              </TabsContent>

              {/* Architecture Tab */}
              <TabsContent value="architecture" className="m-0 p-4">
                {depGraph && depGraph.nodes.length > 0 ? (
                  <div className="h-[600px]">
                    <DependencyGraph data={depGraph} />
                  </div>
                ) : analysis ? (
                  <div className="space-y-4">
                    {analysis.architecture_description && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">
                            Architecture Description
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <MarkdownPreview
                            content={analysis.architecture_description}
                          />
                        </CardContent>
                      </Card>
                    )}
                    {!depGraph && (
                      <div className="text-center py-10 text-muted-foreground">
                        <Layers className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>
                          Dependency graph not available for this project.
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-20 text-muted-foreground">
                    Run an analysis first.
                  </div>
                )}
              </TabsContent>

              {/* Security Tab */}
              <TabsContent value="security" className="m-0 p-4">
                {analysis ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {(["critical", "high", "medium", "low"] as const).map(
                        (sev) => {
                          const count = analysis.security_issues.filter(
                            (s) => s.severity === sev
                          ).length;
                          return (
                            <Card key={sev}>
                              <CardContent className="p-4 text-center">
                                <div className="text-2xl font-bold">
                                  {count}
                                </div>
                                <Badge
                                  variant={
                                    sev === "critical"
                                      ? "critical"
                                      : sev === "high"
                                      ? "destructive"
                                      : sev === "medium"
                                      ? "warning"
                                      : "info"
                                  }
                                  className="mt-1"
                                >
                                  {sev}
                                </Badge>
                              </CardContent>
                            </Card>
                          );
                        }
                      )}
                    </div>

                    {analysis.security_issues.length > 0 ? (
                      <div className="space-y-3">
                        {analysis.security_issues.map((issue) => (
                          <Card
                            key={issue.id}
                            className="border-l-4"
                            style={{
                              borderLeftColor:
                                issue.severity === "critical"
                                  ? "#ef4444"
                                  : issue.severity === "high"
                                  ? "#f97316"
                                  : issue.severity === "medium"
                                  ? "#eab308"
                                  : "#3b82f6",
                            }}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-semibold text-sm">
                                  {issue.title}
                                </h4>
                                <Badge
                                  variant={
                                    issue.severity === "critical"
                                      ? "critical"
                                      : issue.severity === "high"
                                      ? "destructive"
                                      : "warning"
                                  }
                                >
                                  {issue.severity}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2">
                                {issue.description}
                              </p>
                              <p className="text-xs font-mono text-muted-foreground mb-2">
                                {issue.location.file_path}:
                                {issue.location.line_start}
                              </p>
                              {issue.location.code_snippet && (
                                <pre className="text-xs bg-muted p-2 rounded mb-2 overflow-x-auto">
                                  {issue.location.code_snippet}
                                </pre>
                              )}
                              <p className="text-xs text-blue-400">
                                {issue.recommendation}
                              </p>
                              {issue.cwe_id && (
                                <Badge variant="outline" className="mt-2">
                                  {issue.cwe_id}
                                </Badge>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-10">
                        <Shield className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                        <p className="text-emerald-400 font-semibold">
                          No security issues found
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-20 text-muted-foreground">
                    Run an analysis first.
                  </div>
                )}
              </TabsContent>

              {/* Documentation Tab */}
              <TabsContent value="docs" className="m-0 p-4">
                {analysis?.readme_content ? (
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle className="text-base">
                        Generated README
                      </CardTitle>
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <MarkdownPreview content={analysis.readme_content} />
                    </CardContent>
                  </Card>
                ) : (
                  <div className="text-center py-20 text-muted-foreground">
                    <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>
                      Run an analysis with AI enabled to generate documentation.
                    </p>
                  </div>
                )}
              </TabsContent>
            </div>
          </Tabs>
        </main>
      </div>
    </div>
  );
}
