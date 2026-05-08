"use client";

import { cn } from "@/lib/utils";

interface HealthScoreProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function HealthScore({ score, size = "md" }: HealthScoreProps) {
  const roundedScore = Math.round(score);

  const getColor = (score: number) => {
    if (score >= 80) return { text: "text-emerald-400", bg: "stroke-emerald-400" };
    if (score >= 60) return { text: "text-yellow-400", bg: "stroke-yellow-400" };
    if (score >= 40) return { text: "text-orange-400", bg: "stroke-orange-400" };
    return { text: "text-red-400", bg: "stroke-red-400" };
  };

  const getLabel = (score: number) => {
    if (score >= 80) return "Healthy";
    if (score >= 60) return "Fair";
    if (score >= 40) return "Needs Work";
    return "Critical";
  };

  const colors = getColor(score);
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const sizeMap = {
    sm: { container: "w-16 h-16", text: "text-lg", label: "text-[10px]" },
    md: { container: "w-20 h-20", text: "text-2xl", label: "text-xs" },
    lg: { container: "w-28 h-28", text: "text-3xl", label: "text-sm" },
  };

  const s = sizeMap[size];

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={cn("relative", s.container)}>
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="6"
          />
          <circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            className={colors.bg}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1s ease-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("font-bold", s.text, colors.text)}>
            {roundedScore}
          </span>
        </div>
      </div>
      <span className={cn("text-muted-foreground", s.label)}>
        {getLabel(score)}
      </span>
    </div>
  );
}
