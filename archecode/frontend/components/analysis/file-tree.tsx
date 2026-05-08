"use client";

import { useState, useCallback } from "react";
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  File,
  FileCode2,
  FileJson,
  FileText,
  FileCog,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { FileNode } from "@/types";

interface FileTreeProps {
  node: FileNode;
  selectedFile: string | null;
  onSelectFile: (path: string) => void;
  depth?: number;
}

function getFileIcon(name: string, isDirectory: boolean) {
  if (isDirectory) return null;

  const ext = name.split(".").pop()?.toLowerCase() || "";
  const iconMap: Record<string, typeof File> = {
    py: FileCode2,
    js: FileCode2,
    ts: FileCode2,
    tsx: FileCode2,
    jsx: FileCode2,
    java: FileCode2,
    go: FileCode2,
    rs: FileCode2,
    rb: FileCode2,
    json: FileJson,
    yaml: FileCog,
    yml: FileCog,
    toml: FileCog,
    md: FileText,
    txt: FileText,
    html: FileCode2,
    css: FileCode2,
    sql: FileCode2,
  };

  return iconMap[ext] || File;
}

export function FileTree({ node, selectedFile, onSelectFile, depth = 0 }: FileTreeProps) {
  const [expanded, setExpanded] = useState(depth < 2);

  if (!node.is_directory) {
    const Icon = getFileIcon(node.name, false) || File;
    const isSelected = selectedFile === node.path;

    return (
      <button
        onClick={() => onSelectFile(node.path)}
        className={cn(
          "flex items-center gap-2 w-full px-2 py-1 text-left text-sm hover:bg-muted/50 transition-colors group",
          isSelected && "bg-primary/10 text-primary",
          !isSelected && "text-muted-foreground hover:text-foreground"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <Icon className="w-3.5 h-3.5 shrink-0" />
        <span className="truncate">{node.name}</span>
        {node.language && (
          <span className="text-[10px] text-muted-foreground/50 ml-auto shrink-0">
            {node.line_count}
          </span>
        )}
      </button>
    );
  }

  // Sort: directories first, then files, both alphabetically
  const sortedChildren = [...(node.children || [])].sort((a, b) => {
    if (a.is_directory !== b.is_directory) return a.is_directory ? -1 : 1;
    return a.name.localeCompare(b.name);
  });

  // Filter out empty directories and very deep structures
  if (sortedChildren.length === 0 && depth > 0) return null;

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 w-full px-2 py-1 text-left text-sm hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 shrink-0" />
        )}
        {expanded ? (
          <FolderOpen className="w-3.5 h-3.5 text-yellow-400/70 shrink-0" />
        ) : (
          <Folder className="w-3.5 h-3.5 text-yellow-400/70 shrink-0" />
        )}
        <span className="truncate font-medium">{node.name}</span>
        <span className="text-[10px] text-muted-foreground/50 ml-auto">
          {sortedChildren.length}
        </span>
      </button>

      {expanded && (
        <div>
          {sortedChildren.map((child) => (
            <FileTree
              key={child.path}
              node={child}
              selectedFile={selectedFile}
              onSelectFile={onSelectFile}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
