"use client";

import { useState } from "react";
import {
  Bug,
  AlertTriangle,
  Shield,
  Zap,
  Layers,
  Copy,
  Hash,
  Tag,
  Info,
  Skull,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn, getSeverityColor } from "@/lib/utils";
import type { AnalysisFinding, Severity, FindingCategory } from "@/types";

interface FindingsListProps {
  findings: AnalysisFinding[];
  onFileClick: (path: string) => void;
}

const CATEGORY_ICONS: Record<FindingCategory, typeof Bug> = {
  bug: Bug,
  dead_code: Skull,
  tech_debt: AlertTriangle,
  security: Shield,
  performance: Zap,
  style: Tag,
  complexity: Layers,
  duplication: Copy,
  circular_dependency: Layers,
  magic_number: Hash,
  naming: Tag,
  deprecated: Info,
};

const CATEGORY_LABELS: Record<FindingCategory, string> = {
  bug: "Bugs",
  dead_code: "Dead Code",
  tech_debt: "Tech Debt",
  security: "Security",
  performance: "Performance",
  style: "Style",
  complexity: "Complexity",
  duplication: "Duplication",
  circular_dependency: "Circular Deps",
  magic_number: "Magic Numbers",
  naming: "Naming",
  deprecated: "Deprecated",
};

const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export function FindingsList({ findings, onFileClick }: FindingsListProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Group by category and count
  const categories = findings.reduce((acc, f) => {
    acc[f.category] = (acc[f.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Filter and sort findings
  const filteredFindings = findings
    .filter(
      (f) => selectedCategory === "all" || f.category === selectedCategory
    )
    .sort((a, b) => {
      const sevDiff =
        SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
      if (sevDiff !== 0) return sevDiff;
      return b.confidence - a.confidence;
    });

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {/* Category Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory("all")}
          className={cn(
            "px-3 py-1.5 rounded-lg text-sm transition-all",
            selectedCategory === "all"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:text-foreground"
          )}
        >
          All ({findings.length})
        </button>
        {Object.entries(categories)
          .sort(([, a], [, b]) => b - a)
          .map(([cat, count]) => {
            const Icon = CATEGORY_ICONS[cat as FindingCategory] || Info;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all",
                  selectedCategory === cat
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                {CATEGORY_LABELS[cat as FindingCategory] || cat} ({count})
              </button>
            );
          })}
      </div>

      {/* Findings List */}
      <div className="space-y-2">
        {filteredFindings.length === 0 ? (
          <div className="text-center py-10 text-muted-foreground">
            No findings in this category.
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const isExpanded = expandedIds.has(finding.id);
            const Icon = CATEGORY_ICONS[finding.category] || Info;

            return (
              <Card
                key={finding.id}
                className="hover:border-primary/20 transition-all cursor-pointer"
                onClick={() => toggleExpand(finding.id)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          className={cn("text-[10px]", getSeverityColor(finding.severity))}
                        >
                          {finding.severity}
                        </Badge>
                        <Badge variant="outline" className="text-[10px]">
                          {CATEGORY_LABELS[finding.category] || finding.category}
                        </Badge>
                        {finding.location && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onFileClick(finding.location!.file_path);
                            }}
                            className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1"
                          >
                            {finding.location.file_path}:
                            {finding.location.line_start}
                            <ExternalLink className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                      <h4 className="text-sm font-medium">{finding.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        {finding.description}
                      </p>

                      {isExpanded && (
                        <div className="mt-3 space-y-2">
                          {finding.location?.code_snippet && (
                            <pre className="text-xs bg-muted p-3 rounded-lg overflow-x-auto font-mono">
                              {finding.location.code_snippet}
                            </pre>
                          )}
                          {finding.suggestion && (
                            <div className="text-xs bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                              <span className="text-blue-400 font-medium">
                                Suggestion:{" "}
                              </span>
                              {finding.suggestion}
                            </div>
                          )}
                          <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
                            <span>
                              Confidence:{" "}
                              {(finding.confidence * 100).toFixed(0)}%
                            </span>
                            {finding.auto_fixable && (
                              <Badge variant="outline" className="text-[10px]">
                                Auto-fixable
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
