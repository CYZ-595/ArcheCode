"""
Code quality analyzer.
Detects dead code, suspicious naming, magic numbers, deprecated patterns,
duplicated code blocks, and oversized functions.
"""

import re
import ast
import uuid
from pathlib import Path
from typing import Optional

from models.analysis import (
    AnalysisFinding, Severity, FindingCategory, CodeLocation,
)


class CodeAnalyzer:
    """Analyzes source code for quality issues."""

    def analyze(self, root: Path, source_files: list[Path]) -> list[AnalysisFinding]:
        """Run all code quality checks on source files."""
        findings: list[AnalysisFinding] = []

        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(file_path.relative_to(root))
                ext = file_path.suffix.lower()

                findings.extend(self._check_magic_numbers(rel_path, content, ext))
                findings.extend(self._check_suspicious_naming(rel_path, content, ext))
                findings.extend(self._check_long_functions(rel_path, content, ext))
                findings.extend(self._check_dead_code(rel_path, content, ext))
                findings.extend(self._check_todo_fixme(rel_path, content))
                findings.extend(self._check_empty_except(rel_path, content, ext))
                findings.extend(self._check_print_statements(rel_path, content, ext))
                findings.extend(self._check_duplicate_blocks(rel_path, content))
            except Exception:
                continue

        return findings

    def _check_magic_numbers(
        self, file_path: str, content: str, ext: str
    ) -> list[AnalysisFinding]:
        """Detect magic numbers in code."""
        findings = []
        if ext not in (".py", ".js", ".ts", ".jsx", ".tsx", ".java"):
            return findings

        lines = content.split("\n")
        allowed_numbers = {"0", "1", "2", "-1", "10", "100", "0.0", "1.0", "0.5"}

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Find numeric literals
            pattern = r'(?<![a-zA-Z_"\'.])(\d+\.?\d*)(?![a-zA-Z_"\'.])'
            for match in re.finditer(pattern, line):
                num = match.group(1)
                if num in allowed_numbers:
                    continue
                # Check if it's in a constant assignment (uppercase)
                if re.match(r'^\s*[A-Z_]+\s*=', line):
                    continue
                # Check if it's a port number, HTTP status, etc.
                if int(float(num)) in {80, 443, 8080, 3000, 5000, 8000, 8443}:
                    continue
                if 100 <= int(float(num)) <= 599:  # HTTP status codes
                    continue

                findings.append(AnalysisFinding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.MAGIC_NUMBER,
                    severity=Severity.LOW,
                    title="Magic number detected",
                    description=f"Numeric literal `{num}` should be extracted to a named constant.",
                    location=CodeLocation(
                        file_path=file_path,
                        line_start=i,
                        code_snippet=stripped[:120],
                    ),
                    suggestion=f"Replace `{num}` with a named constant that explains its meaning.",
                    confidence=0.7,
                ))

        return findings

    def _check_suspicious_naming(
        self, file_path: str, content: str, ext: str
    ) -> list[AnalysisFinding]:
        """Detect suspicious or poor variable/function names."""
        findings = []
        if ext not in (".py", ".js", ".ts", ".jsx", ".tsx", ".java"):
            return findings

        suspicious_patterns = [
            (r'\b(temp|tmp|foo|bar|baz|test|xxx|aaa|bbb)\b', "Generic/placeholder name"),
            (r'\b(data|info|result|val|value|item|thing|obj)\b', "Vague/meaningless name"),
            (r'\b(func|fn|handler|cb|callback)\b', "Abbreviated name"),
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            for pattern, desc in suspicious_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Skip if it's in a comment or string
                    if f'"{match}"' in line or f"'{match}'" in line:
                        continue
                    # Skip common framework patterns
                    if match.lower() in ("data", "val") and ext in (".py", ".java"):
                        continue

                    findings.append(AnalysisFinding(
                        id=str(uuid.uuid4()),
                        category=FindingCategory.NAMING,
                        severity=Severity.INFO,
                        title=f"Suspicious naming: `{match}`",
                        description=f"{desc}: `{match}` may not be descriptive enough.",
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=i,
                            code_snippet=stripped[:120],
                        ),
                        suggestion="Consider using a more descriptive name.",
                        confidence=0.5,
                    ))

        return findings

    def _check_long_functions(
        self, file_path: str, content: str, ext: str
    ) -> list[AnalysisFinding]:
        """Detect functions that are too long."""
        findings = []
        if ext not in (".py", ".js", ".ts", ".jsx", ".tsx", ".java"):
            return findings

        if ext == ".py":
            findings.extend(self._check_long_functions_python(file_path, content))
        else:
            findings.extend(self._check_long_functions_js(file_path, content))

        return findings

    def _check_long_functions_python(
        self, file_path: str, content: str
    ) -> list[AnalysisFinding]:
        """Detect long Python functions using AST."""
        findings = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if hasattr(node, "end_lineno") and node.end_lineno:
                        length = node.end_lineno - node.lineno
                        if length > 50:
                            severity = Severity.HIGH if length > 100 else Severity.MEDIUM
                            findings.append(AnalysisFinding(
                                id=str(uuid.uuid4()),
                                category=FindingCategory.COMPLEXITY,
                                severity=severity,
                                title=f"Long function: `{node.name}` ({length} lines)",
                                description=f"Function `{node.name}` is {length} lines long. Consider breaking it into smaller functions.",
                                location=CodeLocation(
                                    file_path=file_path,
                                    line_start=node.lineno,
                                    line_end=node.end_lineno,
                                ),
                                suggestion="Break into smaller, single-responsibility functions.",
                                confidence=0.9,
                            ))
        except SyntaxError:
            pass
        return findings

    def _check_long_functions_js(
        self, file_path: str, content: str
    ) -> list[AnalysisFinding]:
        """Detect long JS/TS functions using regex-based heuristics."""
        findings = []
        lines = content.split("\n")
        func_pattern = r'(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)\s*=>|function)|^\s*(?:async\s+)?(?:get|set)\s+\w+)'

        func_start = None
        func_name = None
        brace_depth = 0

        for i, line in enumerate(lines, 1):
            if func_start is None:
                match = re.search(func_pattern, line)
                if match:
                    func_start = i
                    func_name = match.group(0).strip()[:40]
                    brace_depth = line.count("{") - line.count("}")
            else:
                brace_depth += line.count("{") - line.count("}")
                if brace_depth <= 0:
                    length = i - func_start
                    if length > 50:
                        severity = Severity.HIGH if length > 100 else Severity.MEDIUM
                        findings.append(AnalysisFinding(
                            id=str(uuid.uuid4()),
                            category=FindingCategory.COMPLEXITY,
                            severity=severity,
                            title=f"Long function: `{func_name}` ({length} lines)",
                            description=f"Function is {length} lines long.",
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=func_start,
                                line_end=i,
                            ),
                            suggestion="Break into smaller, single-responsibility functions.",
                            confidence=0.7,
                        ))
                    func_start = None
                    func_name = None
                    brace_depth = 0

        return findings

    def _check_dead_code(
        self, file_path: str, content: str, ext: str
    ) -> list[AnalysisFinding]:
        """Detect potentially dead code patterns."""
        findings = []
        lines = content.split("\n")

        # Check for commented-out code blocks
        comment_block_start = None
        comment_lines = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            is_comment_line = (
                stripped.startswith("#") and not stripped.startswith("#!") and not stripped.startswith("# TODO") and not stripped.startswith("# FIXME")
            ) or (
                stripped.startswith("//") and not stripped.startswith("// TODO") and not stripped.startswith("// FIXME")
            )

            if is_comment_line:
                if comment_block_start is None:
                    comment_block_start = i
                comment_lines.append(stripped)
            else:
                if comment_block_start and len(comment_lines) >= 3:
                    # Check if commented lines look like code
                    code_indicators = 0
                    for cl in comment_lines:
                        cl_clean = cl.lstrip("#/ ").strip()
                        if any(kw in cl_clean for kw in [
                            "if ", "for ", "while ", "return ", "def ", "function ",
                            "class ", "import ", "const ", "let ", "var ", "try:",
                            "=", "()", "{}", "[]",
                        ]):
                            code_indicators += 1

                    if code_indicators >= 2:
                        findings.append(AnalysisFinding(
                            id=str(uuid.uuid4()),
                            category=FindingCategory.DEAD_CODE,
                            severity=Severity.MEDIUM,
                            title=f"Commented-out code block ({len(comment_lines)} lines)",
                            description="A block of commented-out code was detected. This is likely dead code that should be removed.",
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=comment_block_start,
                                line_end=comment_block_start + len(comment_lines) - 1,
                            ),
                            suggestion="Remove commented-out code. Use version control to preserve history.",
                            confidence=0.7,
                        ))

                comment_block_start = None
                comment_lines = []

        return findings

    def _check_todo_fixme(self, file_path: str, content: str) -> list[AnalysisFinding]:
        """Detect TODO/FIXME/HACK/XXX comments."""
        findings = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for marker in ["TODO", "FIXME", "HACK", "XXX", "BUG", "WORKAROUND"]:
                pattern = rf'\b{marker}\b'
                if re.search(pattern, line, re.IGNORECASE):
                    snippet = line.strip()[:120]
                    severity = Severity.HIGH if marker in ("FIXME", "BUG") else Severity.MEDIUM
                    findings.append(AnalysisFinding(
                        id=str(uuid.uuid4()),
                        category=FindingCategory.TECH_DEBT,
                        severity=severity,
                        title=f"{marker} comment found",
                        description=f"A {marker} marker was found: {snippet}",
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=i,
                            code_snippet=snippet,
                        ),
                        suggestion=f"Address this {marker} or create a ticket to track it.",
                        confidence=0.95,
                    ))
                    break  # One finding per line

        return findings

    def _check_empty_except(
        self, file_path: str, content: str, ext: str
    ) -> list[AnalysisFinding]:
        """Detect empty except/catch blocks."""
        findings = []

        if ext == ".py":
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        # Check if handler body is just 'pass'
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            findings.append(AnalysisFinding(
                                id=str(uuid.uuid4()),
                                category=FindingCategory.BUG,
                                severity=Severity.HIGH,
                                title="Empty except block",
                                description="An empty except block silently swallows exceptions, hiding potential bugs.",
                                location=CodeLocation(
                                    file_path=file_path,
                                    line_start=node.lineno,
                                ),
                                suggestion="At minimum, log the exception. Prefer catching specific exception types.",
                                confidence=0.95,
                            ))
            except SyntaxError:
                pass

        # JS/TS empty catch
        if ext in (".js", ".ts", ".jsx", ".tsx"):
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if re.search(r'catch\s*\([^)]*\)\s*\{?\s*$', line):
                    # Check next line for empty block
                    if i < len(lines) and lines[i].strip() in ("}", "// ignored", ""):
                        findings.append(AnalysisFinding(
                            id=str(uuid.uuid4()),
                            category=FindingCategory.BUG,
                            severity=Severity.HIGH,
                            title="Empty catch block",
                            description="An empty catch block silently swallows errors.",
                            location=CodeLocation(file_path=file_path, line_start=i),
                            suggestion="Handle or log the error.",
                            confidence=0.85,
                        ))

        return findings

    def _check_print_statements(
        self, file_path: str, content: str, ext: str
    ) -> list[AnalysisFinding]:
        """Detect leftover print/console.log statements."""
        findings = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if ext == ".py" and re.match(r'^print\s*\(', stripped):
                if not stripped.startswith("#"):
                    findings.append(AnalysisFinding(
                        id=str(uuid.uuid4()),
                        category=FindingCategory.DEAD_CODE,
                        severity=Severity.LOW,
                        title="Print statement found",
                        description="Leftover print statement may produce unwanted console output.",
                        location=CodeLocation(file_path=file_path, line_start=i, code_snippet=stripped[:120]),
                        suggestion="Replace with proper logging.",
                        confidence=0.6,
                    ))
            elif ext in (".js", ".ts", ".jsx", ".tsx") and re.match(r'^console\.(log|warn|error|debug)\s*\(', stripped):
                findings.append(AnalysisFinding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.DEAD_CODE,
                    severity=Severity.LOW,
                    title="Console statement found",
                    description="Leftover console statement.",
                    location=CodeLocation(file_path=file_path, line_start=i, code_snippet=stripped[:120]),
                    suggestion="Remove or replace with a proper logging solution.",
                    confidence=0.6,
                ))

        return findings

    def _check_duplicate_blocks(self, file_path: str, content: str) -> list[AnalysisFinding]:
        """Detect duplicate code blocks (simple hash-based approach)."""
        findings = []
        lines = content.split("\n")
        block_size = 5
        seen_blocks: dict[str, list[int]] = {}

        for i in range(len(lines) - block_size + 1):
            block = "\n".join(line.strip() for line in lines[i:i + block_size])
            if not block or all(c in " \t\n{}();" for c in block):
                continue
            block_hash = hash(block)

            if block_hash in seen_blocks:
                existing_line = seen_blocks[block_hash][0]
                findings.append(AnalysisFinding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.DUPLICATION,
                    severity=Severity.MEDIUM,
                    title=f"Duplicate code block (line {existing_line} and {i + 1})",
                    description=f"A {block_size}-line block at line {i + 1} is identical to one at line {existing_line}.",
                    location=CodeLocation(
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + block_size,
                    ),
                    suggestion="Extract duplicated code into a shared function.",
                    confidence=0.8,
                ))
                seen_blocks[block_hash].append(i + 1)
            else:
                seen_blocks[block_hash] = [i + 1]

        return findings
