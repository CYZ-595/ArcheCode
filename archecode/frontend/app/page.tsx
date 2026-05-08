"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  Github,
  Search,
  Shield,
  FileCode2,
  GitBranch,
  Zap,
  ArrowRight,
  Loader2,
  BookOpen,
  Bug,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { projectApi } from "@/lib/api";

const FEATURES = [
  {
    icon: Search,
    title: "Code Archaeology",
    description:
      "Deep analysis of project architecture, module dependencies, and code relationships.",
  },
  {
    icon: Bug,
    title: "Bug Detection",
    description:
      "Automatically identify bugs, dead code, magic numbers, and suspicious patterns.",
  },
  {
    icon: Shield,
    title: "Security Audit",
    description:
      "Scan for SQL injection, XSS, hardcoded secrets, and other security vulnerabilities.",
  },
  {
    icon: Layers,
    title: "Architecture Analysis",
    description:
      "Detect MVC, Clean Architecture, microservices patterns and generate architecture diagrams.",
  },
  {
    icon: BookOpen,
    title: "Auto Documentation",
    description:
      "Generate comprehensive README, API docs, and architecture descriptions powered by AI.",
  },
  {
    icon: Zap,
    title: "AI Chat",
    description:
      "Ask questions about the codebase in natural language. Get answers with code references.",
  },
];

const SUPPORTED_LANGUAGES = [
  "Python",
  "JavaScript",
  "TypeScript",
  "Java",
  "Go",
  "Rust",
  "Ruby",
  "PHP",
];

export default function HomePage() {
  const router = useRouter();
  const [githubUrl, setGithubUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      const file = acceptedFiles[0];

      if (!file.name.endsWith(".zip")) {
        setError("Please upload a .zip file");
        return;
      }

      setIsUploading(true);
      setError(null);

      try {
        const result = await projectApi.upload(file);
        router.push(`/analysis?id=${result.project_id}`);
      } catch (err: any) {
        setError(err.message || "Upload failed. Please try again.");
      } finally {
        setIsUploading(false);
      }
    },
    [router]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/zip": [".zip"] },
    maxFiles: 1,
    disabled: isUploading,
  });

  const handleGithubImport = async () => {
    if (!githubUrl.trim()) {
      setError("Please enter a GitHub repository URL");
      return;
    }

    setIsImporting(true);
    setError(null);

    try {
      const result = await projectApi.importGithub(githubUrl.trim());
      router.push(`/analysis?id=${result.project_id}`);
    } catch (err: any) {
      setError(err.message || "Import failed. Please check the URL.");
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <FileCode2 className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight">
                Arche<span className="text-primary">Code</span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="hidden sm:flex">
                v1.0.0
              </Badge>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-purple-500/5 to-transparent pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 relative">
          <div className="text-center max-w-3xl mx-auto">
            <Badge variant="outline" className="mb-6">
              AI-Powered Code Analysis
            </Badge>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              Understand any codebase{" "}
              <span className="gradient-text">in 10 minutes</span>
            </h1>
            <p className="text-lg sm:text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
              Upload a project or paste a GitHub URL. ArcheCode automatically
              analyzes architecture, finds bugs, detects security issues, and
              generates documentation.
            </p>

            {/* Upload Area */}
            <div className="max-w-2xl mx-auto space-y-6">
              {/* Zip Upload */}
              <div
                {...getRootProps()}
                className={`
                  relative border-2 border-dashed rounded-2xl p-10 cursor-pointer
                  transition-all duration-300 ease-out group
                  ${
                    isDragActive
                      ? "border-primary bg-primary/5 scale-[1.02]"
                      : "border-border hover:border-primary/50 hover:bg-muted/50"
                  }
                  ${isUploading ? "pointer-events-none opacity-60" : ""}
                `}
              >
                <input {...getInputProps()} />
                {isUploading ? (
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-10 h-10 text-primary animate-spin" />
                    <p className="text-sm text-muted-foreground">
                      Uploading and extracting project...
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Upload className="w-7 h-7 text-primary" />
                    </div>
                    <div>
                      <p className="text-base font-medium">
                        {isDragActive
                          ? "Drop your project here"
                          : "Drop a zip file here, or click to upload"}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Supports .zip archives up to 50MB
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Divider */}
              <div className="flex items-center gap-4">
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-muted-foreground uppercase tracking-wider">
                  or import from
                </span>
                <div className="flex-1 h-px bg-border" />
              </div>

              {/* GitHub Import */}
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="https://github.com/owner/repo"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleGithubImport()}
                    className="pl-10 h-12 bg-muted/50"
                    disabled={isImporting}
                  />
                </div>
                <Button
                  onClick={handleGithubImport}
                  disabled={isImporting || !githubUrl.trim()}
                  variant="glow"
                  className="h-12 px-6"
                >
                  {isImporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <GitBranch className="w-4 h-4 mr-2" />
                      Import
                    </>
                  )}
                </Button>
              </div>

              {error && (
                <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
                  {error}
                </p>
              )}

              {/* Supported languages */}
              <div className="flex items-center justify-center gap-2 flex-wrap">
                <span className="text-xs text-muted-foreground">
                  Supports:
                </span>
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <Badge key={lang} variant="secondary" className="text-xs">
                    {lang}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
            Everything you need to understand a codebase
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            From architecture analysis to AI-powered documentation, ArcheCode
            gives you a complete picture in minutes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card
                key={feature.title}
                className="group hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
              >
                <CardHeader>
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <CardTitle className="text-base">{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-border/50 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
              How it works
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Three simple steps to understand any codebase.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Upload",
                description:
                  "Upload a zip file or import from GitHub. ArcheCode extracts and indexes the project.",
              },
              {
                step: "02",
                title: "Analyze",
                description:
                  "AI analyzes architecture, detects bugs, finds security issues, and maps dependencies.",
              },
              {
                step: "03",
                title: "Understand",
                description:
                  "Explore interactive diagrams, read AI-generated docs, and chat with the codebase.",
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <span className="text-sm font-bold text-primary">
                    {item.step}
                  </span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <FileCode2 className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-medium">ArcheCode</span>
            </div>
            <p className="text-xs text-muted-foreground">
              AI-powered code archaeology platform
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
