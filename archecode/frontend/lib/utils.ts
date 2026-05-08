import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-red-400 bg-red-500/10 border-red-500/20";
    case "high":
      return "text-orange-400 bg-orange-500/10 border-orange-500/20";
    case "medium":
      return "text-yellow-400 bg-yellow-500/10 border-yellow-500/20";
    case "low":
      return "text-blue-400 bg-blue-500/10 border-blue-500/20";
    case "info":
      return "text-gray-400 bg-gray-500/10 border-gray-500/20";
    default:
      return "text-gray-400 bg-gray-500/10 border-gray-500/20";
  }
}

export function getCategoryIcon(category: string): string {
  switch (category) {
    case "bug":
      return "Bug";
    case "dead_code":
      return "Skull";
    case "tech_debt":
      return "AlertTriangle";
    case "security":
      return "ShieldAlert";
    case "performance":
      return "Zap";
    case "complexity":
      return "Layers";
    case "duplication":
      return "Copy";
    case "magic_number":
      return "Hash";
    case "naming":
      return "Tag";
    default:
      return "Info";
  }
}

export function truncatePath(path: string, maxLength: number = 40): string {
  if (path.length <= maxLength) return path;
  const parts = path.split("/");
  if (parts.length <= 2) return "..." + path.slice(-maxLength);
  return parts[0] + "/.../" + parts[parts.length - 1];
}

export function getLanguageColor(language: string): string {
  const colors: Record<string, string> = {
    Python: "#3776AB",
    JavaScript: "#F7DF1E",
    TypeScript: "#3178C6",
    Java: "#ED8B00",
    Go: "#00ADD8",
    Rust: "#DEA584",
    Ruby: "#CC342D",
    PHP: "#777BB4",
    "C#": "#239120",
    "C++": "#00599C",
    HTML: "#E34F26",
    CSS: "#1572B6",
    SCSS: "#CC6699",
    Markdown: "#083FA1",
    YAML: "#CB171E",
    JSON: "#292929",
    Shell: "#89E051",
    SQL: "#CC2927",
  };
  return colors[language] || "#6B7280";
}
