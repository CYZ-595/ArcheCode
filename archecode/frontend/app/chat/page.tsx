"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Send,
  Loader2,
  FileCode2,
  ArrowLeft,
  MessageSquare,
  Sparkles,
  User,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { projectApi, chatApi } from "@/lib/api";
import type { Project, ChatMessage, CodeReference } from "@/types";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectId = searchParams.get("id");

  const [project, setProject] = useState<Project | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load project and suggestions
  useEffect(() => {
    if (!projectId) {
      router.push("/");
      return;
    }

    const loadData = async () => {
      try {
        const proj = await projectApi.get(projectId);
        setProject(proj);

        const suggResult = await chatApi.getSuggestions(projectId);
        setSuggestions(suggResult.suggestions);
      } catch (err) {
        console.error("Failed to load project:", err);
      }
    };

    loadData();
  }, [projectId, router]);

  // Send message
  const sendMessage = useCallback(
    async (text?: string) => {
      const messageText = text || input.trim();
      if (!messageText || !projectId) return;

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: messageText,
        code_references: [],
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput("");
      setIsLoading(true);

      try {
        const response = await chatApi.send(
          projectId,
          messageText,
          conversationId || undefined
        );

        setMessages((prev) => [...prev, response.message]);
        if (response.conversation_id) {
          setConversationId(response.conversation_id);
        }
      } catch (err: any) {
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
          code_references: [],
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
        inputRef.current?.focus();
      }
    },
    [input, projectId, conversationId]
  );

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {}
  };

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Navigation */}
      <nav className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/analysis?id=${projectId}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Analysis
            </Button>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold">AI Chat</span>
              <span className="text-sm text-muted-foreground">
                - {project.name}
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold mb-2">
                Ask about {project.name}
              </h2>
              <p className="text-muted-foreground mb-8 text-center max-w-md">
                I can help you understand this codebase. Ask me anything about
                the architecture, code patterns, or specific files.
              </p>

              {/* Suggested Questions */}
              {suggestions.length > 0 && (
                <div className="w-full max-w-2xl space-y-2">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider text-center mb-3">
                    Suggested questions
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => sendMessage(suggestion)}
                        className="text-left p-3 rounded-lg border border-border/50 hover:border-primary/30 hover:bg-muted/50 transition-all text-sm text-muted-foreground hover:text-foreground"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${
                    msg.role === "user" ? "justify-end" : ""
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shrink-0">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] ${
                      msg.role === "user" ? "order-1" : ""
                    }`}
                  >
                    <div
                      className={`rounded-2xl px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground ml-auto"
                          : "bg-muted"
                      }`}
                    >
                      {msg.role === "assistant" ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap">
                          {msg.content}
                        </p>
                      )}
                    </div>

                    {/* Code References */}
                    {msg.code_references.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {msg.code_references.map((ref, i) => (
                          <button
                            key={i}
                            onClick={() =>
                              router.push(
                                `/analysis?id=${projectId}&file=${ref.file_path}`
                              )
                            }
                            className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            <FileCode2 className="w-3 h-3" />
                            <span className="font-mono">
                              {ref.file_path}:{ref.line_start}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Copy button for assistant messages */}
                    {msg.role === "assistant" && (
                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="mt-1 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check className="w-3 h-3" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            Copy
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0 order-2">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-muted rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">
                        Thinking...
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t border-border/50 p-4">
          <div className="flex gap-3">
            <Input
              ref={inputRef}
              placeholder="Ask anything about this codebase..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={isLoading}
              className="h-12"
            />
            <Button
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              variant="glow"
              className="h-12 px-5"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
