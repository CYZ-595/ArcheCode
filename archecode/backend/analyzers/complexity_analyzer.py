"""
Code complexity analyzer.
Measures cyclomatic complexity, cognitive complexity,
detects circular dependencies, and identifies technical debt.
"""

import ast
import re
import uuid
from pathlib import Path
from typing import Optional

import networkx as nx

from models.analysis import (
    AnalysisFinding, Severity, FindingCategory, CodeLocation,
)


class ComplexityAnalyzer:
    """Analyzes code complexity and detects structural issues."""

    def analyze(self, root: Path, source_files: list[Path]) -> list[AnalysisFinding]:
        """Run complexity analysis on all source files."""
        findings: list[AnalysisFinding] = []

        # Build import graph for circular dependency detection
        import_graph = self._build_import_graph(root, source_files)
        findings.extend(self._detect_circular_dependencies(import_graph))

        # Analyze individual files
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(file_path.relative_to(root))
                ext = file_path.suffix.lower()

                if ext == ".py":
                    findings.extend(self._analyze_python_complexity(rel_path, content))
                elif ext in (".js", ".ts", ".jsx", ".tsx"):
                    findings.extend(self._analyze_js_complexity(rel_path, content))

                findings.extend(self._check_file_length(rel_path, content))
                findings.extend(self._check_nesting_depth(rel_path, content))
            except Exception:
                continue

        return findings

    def _build_import_graph(
        self, root: Path, source_files: list[Path]
    ) -> nx.DiGraph:
        """Build a directed graph of import relationships."""
        graph = nx.DiGraph()

        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(file_path.relative_to(root))
                ext = file_path.suffix.lower()

                graph.add_node(rel_path)

                if ext == ".py":
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    graph.add_edge(rel_path, alias.name)
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                graph.add_edge(rel_path, node.module)
                    except SyntaxError:
                        pass

                elif ext in (".js", ".ts", ".jsx", ".tsx"):
                    for line in content.split("\n"):
                        match = re.search(
                            r'''from\s+['"]([^'"]+)['"]''', line
                        )
                        if match:
                            module = match.group(1)
                            if module.startswith("."):
                                graph.add_edge(rel_path, module)
            except Exception:
                continue

        return graph

    def _detect_circular_dependencies(
        self, graph: nx.DiGraph
    ) -> list[AnalysisFinding]:
        """Detect circular dependencies in the import graph."""
        findings = []

        try:
            cycles = list(nx.simple_cycles(graph))
            # Limit to reasonable cycles (2-5 nodes)
            short_cycles = [c for c in cycles if 2 <= len(c) <= 5]

            for cycle in short_cycles[:10]:  # Limit to 10 cycles
                cycle_str = " -> ".join(cycle)
                findings.append(AnalysisFinding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.TECH_DEBT,
                    severity=Severity.HIGH,
                    title="Circular dependency detected",
                    description=f"Circular import chain: {cycle_str}",
                    location=CodeLocation(file_path=cycle[0], line_start=1),
                    suggestion="Break the circular dependency by introducing an interface or restructuring the modules.",
                    confidence=0.9,
                ))
        except nx.NetworkXError:
            pass

        return findings

    def _analyze_python_complexity(
        self, file_path: str, content: str
    ) -> list[AnalysisFinding]:
        """Analyze cyclomatic complexity of Python functions."""
        findings = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cyclomatic_complexity(node)

                if complexity > 15:
                    severity = Severity.HIGH
                elif complexity > 10:
                    severity = Severity.MEDIUM
                elif complexity > 7:
                    severity = Severity.LOW
                else:
                    continue

                findings.append(AnalysisFinding(
                    id=str(uuid.uuid4()),
                    category=FindingCategory.COMPLEXITY,
                    severity=severity,
                    title=f"High complexity: `{node.name}` (CC={complexity})",
                    description=f"Function `{node.name}` has cyclomatic complexity of {complexity}. "
                                f"Recommended maximum is 10.",
                    location=CodeLocation(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                    ),
                    suggestion="Reduce complexity by extracting logic into helper functions or using early returns.",
                    confidence=0.95,
                ))

        return findings

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST node (function/method)."""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.IfExp)):
                complexity += 1
            elif isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def _analyze_js_complexity(
        self, file_path: str, content: str
    ) -> list[AnalysisFinding]:
        """Analyze complexity of JavaScript/TypeScript code."""
        findings = []
        lines = content.split("\n")

        # Count decision points per function (simplified)
        func_complexity: dict[str, dict] = {}
        current_func = None
        brace_depth = 0
        func_start = 0

        decision_keywords = [
            r'\bif\s*\(', r'\belse\s+if\s*\(', r'\bfor\s*\(',
            r'\bwhile\s*\(', r'\bcatch\s*\(', r'\bcase\s+',
            r'\?\s*', r'\&\&', r'\|\|',
        ]

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect function start
            func_match = re.search(
                r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=.*(?:function|=>))', stripped
            )
            if func_match and current_func is None:
                current_func = func_match.group(1) or func_match.group(2)
                brace_depth = 0
                func_start = i
                func_complexity[current_func] = {"start": i, "complexity": 1}

            if current_func:
                brace_depth += line.count("{") - line.count("}")

                # Count complexity
                for kw in decision_keywords:
                    func_complexity[current_func]["complexity"] += len(re.findall(kw, line))

                if brace_depth <= 0 and func_complexity.get(current_func):
                    cc = func_complexity[current_func]["complexity"]
                    if cc > 10:
                        severity = Severity.HIGH if cc > 15 else Severity.MEDIUM
                        findings.append(AnalysisFinding(
                            id=str(uuid.uuid4()),
                            category=FindingCategory.COMPLEXITY,
                            severity=severity,
                            title=f"High complexity: `{current_func}` (CC~{cc})",
                            description=f"Function `{current_func}` has high cyclomatic complexity (~{cc}).",
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=func_start,
                                line_end=i,
                            ),
                            suggestion="Reduce complexity by extracting logic or using early returns.",
                            confidence=0.7,
                        ))
                    current_func = None

        return findings

    def _check_file_length(
        self, file_path: str, content: str
    ) -> list[AnalysisFinding]:
        """Check if a file is too long."""
        findings = []
        line_count = content.count("\n") + 1

        if line_count > 500:
            severity = Severity.HIGH if line_count > 1000 else Severity.MEDIUM
            findings.append(AnalysisFinding(
                id=str(uuid.uuid4()),
                category=FindingCategory.COMPLEXITY,
                severity=severity,
                title=f"Large file: {line_count} lines",
                description=f"File `{file_path}` has {line_count} lines. Large files are harder to maintain.",
                location=CodeLocation(file_path=file_path, line_start=1),
                suggestion="Consider splitting this file into smaller, focused modules.",
                confidence=0.9,
            ))

        return findings

    def _check_nesting_depth(
        self, file_path: str, content: str
    ) -> list[AnalysisFinding]:
        """Check for deeply nested code blocks."""
        findings = []
        lines = content.split("\n")

        max_depth = 0
        max_depth_line = 0
        current_depth = 0

        for i, line in enumerate(lines, 1):
            # Count indentation (simplified - works for consistent indentation)
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            indent = len(line) - len(line.lstrip())
            # Assume 2 or 4 space indentation
            tab_size = 4 if indent % 4 == 0 else 2
            depth = indent // tab_size

            if depth > max_depth:
                max_depth = depth
                max_depth_line = i

        if max_depth > 6:
            severity = Severity.HIGH if max_depth > 8 else Severity.MEDIUM
            findings.append(AnalysisFinding(
                id=str(uuid.uuid4()),
                category=FindingCategory.COMPLEXITY,
                severity=severity,
                title=f"Deeply nested code (depth {max_depth})",
                description=f"Maximum nesting depth of {max_depth} at line {max_depth_line}. "
                            f"Recommended maximum is 4 levels.",
                location=CodeLocation(file_path=file_path, line_start=max_depth_line),
                suggestion="Use early returns, guard clauses, or extract nested logic into functions.",
                confidence=0.8,
            ))

        return findings
