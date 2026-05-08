"use client";

import ReactMarkdown from "react-markdown";

interface MarkdownPreviewProps {
  content: string;
}

export function MarkdownPreview({ content }: MarkdownPreviewProps) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:scroll-m-20 prose-headings:font-semibold prose-h1:text-xl prose-h2:text-lg prose-h3:text-base prose-p:leading-relaxed prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-pre:rounded-lg prose-table:border-collapse prose-th:border prose-th:border-border prose-th:p-2 prose-td:border prose-td:border-border prose-td:p-2 prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline">
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            return inline ? (
              <code className={className} {...props}>
                {children}
              </code>
            ) : (
              <pre className={className}>
                <code {...props}>{children}</code>
              </pre>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
