"""
AI service for intelligent code analysis.
Integrates with OpenAI API for project summaries, README generation,
architecture analysis, refactoring suggestions, and contextual Q&A.
"""

import json
from typing import Optional

from openai import AsyncOpenAI

from models.project import Project
from models.analysis import AnalysisFinding
from models.chat import ChatMessage, MessageRole, CodeReference
from core.config import settings


class AIService:
    """Handles all AI-powered analysis via OpenAI API."""

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self._init_client()

    def _init_client(self):
        """Initialize the OpenAI async client."""
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def is_configured(self) -> bool:
        """Check if the AI service is properly configured."""
        return self.client is not None

    async def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Send a chat completion request."""
        if not self.client:
            return ""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"AI analysis error: {str(e)}"

    async def generate_project_summary(self, project: Project) -> str:
        """Generate a comprehensive project summary using AI."""
        if not project.metadata:
            return ""

        meta = project.metadata
        tech_list = ", ".join(t.name for t in meta.tech_stack) or "Unknown"
        lang_list = ", ".join(f"{k} ({v} lines)" for k, v in sorted(meta.languages.items(), key=lambda x: -x[1]))

        # Collect some sample files for context
        sample_files = []
        if project.upload_path:
            from pathlib import Path
            root = Path(project.upload_path)
            entry_points = meta.entry_points[:3]
            for ep in entry_points:
                fp = root / ep
                if fp.exists():
                    try:
                        content = fp.read_text(encoding="utf-8", errors="replace")[:3000]
                        sample_files.append(f"--- {ep} ---\n{content}")
                    except Exception:
                        pass

        context = f"""Project: {project.name}
Type: {meta.project_type.value}
Architecture: {meta.architecture_pattern.value}
Tech Stack: {tech_list}
Languages: {lang_list}
Total Files: {meta.total_files}
Total Lines: {meta.total_lines}
Has Tests: {meta.has_tests}
Has Docker: {meta.has_docker}
Entry Points: {', '.join(meta.entry_points)}

Sample Entry Files:
{chr(10).join(sample_files[:3]) if sample_files else 'No entry files found'}
"""

        system = """You are a senior software architect providing a project overview.
Generate a concise, professional summary of this codebase covering:
1. What the project does (inferred from tech stack and structure)
2. Key technologies and why they were chosen
3. Architecture overview
4. Notable patterns or design decisions
5. Quick assessment of project maturity

Keep it under 500 words. Be direct and technical."""

        return await self._chat(system, context)

    async def generate_readme(self, project: Project) -> str:
        """Generate a comprehensive README.md for the project."""
        meta = project.metadata
        if not meta:
            return ""

        tech_table = "| Technology | Category |\n|---|---|\n"
        for t in meta.tech_stack:
            tech_table += f"| {t.name} | {t.category} |\n"

        lang_table = "| Language | Lines of Code |\n|---|---|\n"
        for lang, count in sorted(meta.languages.items(), key=lambda x: -x[1]):
            lang_table += f"| {lang} | {count:,} |\n"

        # Collect file tree outline
        tree_preview = ""
        if project.file_tree:
            tree_preview = self._format_tree_preview(project.file_tree, max_depth=2)

        context = f"""Generate a complete README.md for this project:

Project Name: {project.name}
Type: {meta.project_type.value}
Total Files: {meta.total_files}
Total Lines: {meta.total_lines}
Has Tests: {meta.has_tests}
Has Docker: {meta.has_docker}
Has CI/CD: {meta.has_ci}

Tech Stack:
{tech_table}

Languages:
{lang_table}

Project Structure:
```
{tree_preview}
```
"""

        system = """You are a technical writer creating a professional README.md.
Generate a complete, well-structured README with these sections:
1. Title and badges
2. Description (one paragraph)
3. Features
4. Tech Stack (table)
5. Project Structure
6. Getting Started (Prerequisites, Installation, Running)
7. API Overview (if applicable)
8. Architecture
9. Testing
10. Deployment
11. Contributing
12. License

Use proper Markdown formatting. Be concise but thorough.
Include realistic code blocks for commands. Assume npm/pip for installation."""

        return await self._chat(system, context, max_tokens=4096)

    async def analyze_architecture(self, project: Project) -> str:
        """Generate an architecture analysis description."""
        meta = project.metadata
        if not meta:
            return ""

        context = f"""Analyze the architecture of this project:

Project: {project.name}
Type: {meta.project_type.value}
Detected Pattern: {meta.architecture_pattern.value}
Tech Stack: {', '.join(t.name for t in meta.tech_stack)}
Total Files: {meta.total_files}
Entry Points: {', '.join(meta.entry_points)}
"""

        system = """You are a software architect analyzing a codebase's architecture.
Provide a clear architectural analysis covering:
1. Architecture pattern identification and assessment
2. Module organization and layer boundaries
3. Data flow patterns
4. API design approach
5. Dependency management strategy
6. Strengths and potential improvements

Be specific and actionable. Keep under 600 words."""

        return await self._chat(system, context)

    async def generate_refactoring_suggestions(
        self, project: Project, findings: list[AnalysisFinding]
    ) -> list[str]:
        """Generate AI-powered refactoring suggestions based on findings."""
        if not findings:
            return []

        findings_summary = []
        for f in findings[:20]:
            loc = f"{f.location.file_path}:{f.location.line_start}" if f.location else "N/A"
            findings_summary.append(f"- [{f.severity.value}] {f.title} ({loc})")

        context = f"""Based on these code analysis findings for project '{project.name}',
provide prioritized refactoring suggestions:

Findings:
{chr(10).join(findings_summary)}
"""

        system = """You are a senior developer providing refactoring advice.
Based on the analysis findings, provide 5-8 specific, actionable refactoring suggestions.
For each suggestion:
1. What to refactor
2. Why it matters
3. How to do it (brief approach)
4. Expected impact

Prioritize by severity. Be practical, not theoretical. Keep each suggestion under 3 sentences."""

        response = await self._chat(system, context)
        if not response:
            return []

        # Split into individual suggestions
        suggestions = [
            s.strip() for s in response.split("\n\n") if s.strip() and len(s.strip()) > 20
        ]
        return suggestions

    async def chat_with_context(
        self,
        project: Project,
        question: str,
        history: list[ChatMessage],
    ) -> ChatMessage:
        """Answer a question about the project using project context."""
        # Build context from project
        meta = project.metadata
        context_parts = []

        if meta:
            context_parts.append(f"Project: {project.name}")
            context_parts.append(f"Type: {meta.project_type.value}")
            context_parts.append(f"Tech Stack: {', '.join(t.name for t in meta.tech_stack)}")
            context_parts.append(f"Architecture: {meta.architecture_pattern.value}")

        # Try to find relevant source files
        relevant_files = await self._find_relevant_files(project, question)
        for file_path, content in relevant_files[:5]:
            context_parts.append(f"\n--- {file_path} ---\n{content[:2000]}")

        # Include conversation history
        messages = [
            {
                "role": "system",
                "content": f"""You are ArcheCode AI, an expert code archaeologist assistant.
You help developers understand unfamiliar codebases quickly.

Project Context:
{chr(10).join(context_parts)}

When answering:
- Be specific and reference actual files and line numbers when possible
- Provide code snippets when relevant
- If you're unsure, say so
- Keep answers focused and actionable
- Use Markdown formatting for readability""",
            }
        ]

        # Add conversation history (last 10 messages)
        for msg in history[-10:]:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        messages.append({"role": "user", "content": question})

        try:
            if not self.client:
                return ChatMessage(
                    id="",
                    role=MessageRole.ASSISTANT,
                    content="AI service is not configured. Please set OPENAI_API_KEY in your environment.",
                )

            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.4,
            )
            answer = response.choices[0].message.content or ""

            # Extract code references from the answer
            refs = self._extract_code_references(answer, project)

            return ChatMessage(
                id="",
                role=MessageRole.ASSISTANT,
                content=answer,
                code_references=refs,
            )
        except Exception as e:
            return ChatMessage(
                id="",
                role=MessageRole.ASSISTANT,
                content=f"I encountered an error: {str(e)}",
            )

    async def _find_relevant_files(
        self, project: Project, question: str
    ) -> list[tuple[str, str]]:
        """Find files most relevant to the user's question."""
        if not project.upload_path:
            return []

        from pathlib import Path
        from services.project_service import SKIP_DIRS, LANGUAGE_MAP

        root = Path(project.upload_path)
        question_lower = question.lower()
        keywords = set(question_lower.split())

        scored_files: list[tuple[float, str, str]] = []

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in LANGUAGE_MAP:
                continue

            # Skip dirs
            skip = False
            for part in file_path.parts:
                if part in SKIP_DIRS:
                    skip = True
                    break
            if skip:
                continue

            rel_path = str(file_path.relative_to(root))
            path_lower = rel_path.lower()

            # Score by path/filename relevance
            score = 0.0
            for kw in keywords:
                if len(kw) < 3:
                    continue
                if kw in path_lower:
                    score += 2.0

            # Score by content relevance
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")[:5000]
                content_lower = content.lower()
                for kw in keywords:
                    if len(kw) < 3:
                        continue
                    count = content_lower.count(kw)
                    score += min(count * 0.5, 3.0)
            except Exception:
                continue

            if score > 0:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")[:5000]
                    scored_files.append((score, rel_path, content))
                except Exception:
                    pass

        scored_files.sort(key=lambda x: -x[0])
        return [(path, content) for _, path, content in scored_files[:10]]

    def _extract_code_references(
        self, text: str, project: Project
    ) -> list[CodeReference]:
        """Extract file references from AI response text."""
        import re
        refs = []

        # Look for file path patterns
        patterns = [
            r'(?:^|\s)([\w/.-]+\.(?:py|js|ts|tsx|jsx|java|go|rs))\s*[:\s](?:line\s*)?(\d+)?',
            r'`([\w/.-]+\.(?:py|js|ts|tsx|jsx|java|go|rs))`',
            r'in\s+([\w/.-]+\.(?:py|js|ts|tsx|jsx|java|go|rs))',
        ]

        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                file_path = match.group(1)
                if file_path not in seen:
                    seen.add(file_path)
                    refs.append(CodeReference(
                        file_path=file_path,
                        line_start=int(match.group(2)) if match.lastindex >= 2 and match.group(2) else 1,
                    ))

        return refs[:10]

    def _format_tree_preview(self, node, prefix: str = "", max_depth: int = 3, depth: int = 0) -> str:
        """Format a file tree into a readable string."""
        if depth > max_depth:
            return ""

        lines = []
        if depth == 0:
            lines.append(f"{node.name}/")

        children = sorted(node.children, key=lambda c: (not c.is_directory, c.name))

        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if child.is_directory:
                lines.append(f"{prefix}{connector}{child.name}/")
                if depth < max_depth:
                    sub = self._format_tree_preview(
                        child, prefix + child_prefix, max_depth, depth + 1
                    )
                    if sub:
                        lines.append(sub)
            else:
                lines.append(f"{prefix}{connector}{child.name}")

        return "\n".join(lines)


# Singleton
ai_service = AIService()
