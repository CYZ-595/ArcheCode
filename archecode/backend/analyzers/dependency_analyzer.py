"""
Dependency and relationship analyzer.
Analyzes import dependencies, function calls, class hierarchies,
and module relationships.
"""

import re
import ast
import uuid
from pathlib import Path
from typing import Optional

from models.analysis import ModuleDependency, FunctionInfo, ClassInfo


class DependencyAnalyzer:
    """Analyzes module dependencies, function calls, and class relationships."""

    def analyze(
        self, root: Path, source_files: list[Path]
    ) -> tuple[list[ModuleDependency], list[FunctionInfo], list[ClassInfo]]:
        """Analyze all source files for dependencies and relationships."""
        all_deps: list[ModuleDependency] = []
        all_functions: list[FunctionInfo] = []
        all_classes: list[ClassInfo] = []

        # Map of file paths for resolving imports
        file_map: dict[str, Path] = {}
        for fp in source_files:
            rel = str(fp.relative_to(root))
            file_map[rel] = fp

        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(file_path.relative_to(root))
                ext = file_path.suffix.lower()

                if ext == ".py":
                    deps, funcs, classes = self._analyze_python(root, file_path, content, rel_path)
                elif ext in (".js", ".ts", ".jsx", ".tsx"):
                    deps, funcs, classes = self._analyze_javascript(root, file_path, content, rel_path)
                elif ext == ".java":
                    deps, funcs, classes = self._analyze_java(content, rel_path)
                else:
                    continue

                all_deps.extend(deps)
                all_functions.extend(funcs)
                all_classes.extend(classes)
            except Exception:
                continue

        return all_deps, all_functions, all_classes

    def _analyze_python(
        self, root: Path, file_path: Path, content: str, rel_path: str
    ) -> tuple[list[ModuleDependency], list[FunctionInfo], list[ClassInfo]]:
        """Analyze a Python file using AST."""
        deps: list[ModuleDependency] = []
        funcs: list[FunctionInfo] = []
        classes: list[ClassInfo] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return deps, funcs, classes

        # Analyze imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    deps.append(ModuleDependency(
                        source=rel_path,
                        target=module,
                        dependency_type="import",
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module
                    # Check if it's a local import
                    is_local = self._is_local_import(root, module, file_path)
                    deps.append(ModuleDependency(
                        source=rel_path,
                        target=module,
                        dependency_type="import",
                        weight=2.0 if is_local else 1.0,
                    ))

        # Analyze functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = []
                for arg in node.args.args:
                    params.append(arg.arg)

                return_type = None
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        return_type = node.returns.id
                    elif isinstance(node.returns, ast.Constant):
                        return_type = str(node.returns.value)

                docstring = ast.get_docstring(node)
                is_exported = not node.name.startswith("_")

                funcs.append(FunctionInfo(
                    name=node.name,
                    file_path=rel_path,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    parameters=params,
                    return_type=return_type,
                    docstring=docstring,
                    is_exported=is_exported,
                ))

        # Analyze classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(ast.dump(base))

                methods = []
                attributes = []

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = [arg.arg for arg in item.args.args]
                        methods.append(FunctionInfo(
                            name=item.name,
                            file_path=rel_path,
                            line_start=item.lineno,
                            line_end=getattr(item, "end_lineno", item.lineno),
                            parameters=params,
                            docstring=ast.get_docstring(item),
                        ))
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)

                classes.append(ClassInfo(
                    name=node.name,
                    file_path=rel_path,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    methods=methods,
                    base_classes=base_classes,
                    attributes=attributes,
                    docstring=ast.get_docstring(node),
                ))

        return deps, funcs, classes

    def _analyze_javascript(
        self, root: Path, file_path: Path, content: str, rel_path: str
    ) -> tuple[list[ModuleDependency], list[FunctionInfo], list[ClassInfo]]:
        """Analyze a JavaScript/TypeScript file using regex."""
        deps: list[ModuleDependency] = []
        funcs: list[FunctionInfo] = []
        classes: list[ClassInfo] = []

        lines = content.split("\n")

        # Analyze imports
        for line in lines:
            stripped = line.strip()
            # ES6 imports
            import_match = re.match(
                r'''(?:import|export)\s+.*\s+from\s+['"]([^'"]+)['"]''', stripped
            )
            if import_match:
                module = import_match.group(1)
                deps.append(ModuleDependency(
                    source=rel_path,
                    target=module,
                    dependency_type="import",
                    weight=2.0 if module.startswith(".") else 1.0,
                ))
                continue

            # require()
            require_match = re.match(r'''(?:const|let|var)\s+\w+\s*=\s*require\s*\(\s*['"]([^'"]+)['"]''', stripped)
            if require_match:
                deps.append(ModuleDependency(
                    source=rel_path,
                    target=require_match.group(1),
                    dependency_type="require",
                ))

        # Analyze functions
        func_patterns = [
            # function declaration
            (r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', "function"),
            # arrow function assigned to const/let/var
            (r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', "arrow"),
            # arrow function with single param
            (r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(\w+)\s*=>', "arrow_single"),
            # method definition
            (r'(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*\{', "method"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, ftype in func_patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    if name in ("if", "for", "while", "switch", "catch", "constructor"):
                        continue
                    params_str = match.group(2) if ftype != "arrow_single" else match.group(2)
                    params = [p.strip().split(":")[0].strip().split("=")[0].strip()
                              for p in params_str.split(",") if p.strip()] if params_str else []

                    funcs.append(FunctionInfo(
                        name=name,
                        file_path=rel_path,
                        line_start=i,
                        line_end=i,
                        parameters=params,
                        is_exported="export" in line,
                    ))
                    break

        # Analyze classes
        class_pattern = r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for i, line in enumerate(lines, 1):
            match = re.search(class_pattern, line)
            if match:
                class_name = match.group(1)
                base_class = match.group(2) if match.group(2) else None

                # Find methods within class (simple heuristic)
                methods = []
                brace_depth = 0
                in_class = False
                for j in range(i - 1, min(i + 500, len(lines))):
                    brace_depth += lines[j].count("{") - lines[j].count("}")
                    if j == i - 1:
                        in_class = True
                        continue
                    if brace_depth <= 0 and in_class:
                        break
                    method_match = re.search(
                        r'(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*\{', lines[j]
                    )
                    if method_match and method_match.group(1) not in ("if", "for", "while"):
                        methods.append(FunctionInfo(
                            name=method_match.group(1),
                            file_path=rel_path,
                            line_start=j + 1,
                            line_end=j + 1,
                        ))

                classes.append(ClassInfo(
                    name=class_name,
                    file_path=rel_path,
                    line_start=i,
                    line_end=i,
                    methods=methods,
                    base_classes=[base_class] if base_class else [],
                ))

        return deps, funcs, classes

    def _analyze_java(
        self, content: str, rel_path: str
    ) -> tuple[list[ModuleDependency], list[FunctionInfo], list[ClassInfo]]:
        """Analyze a Java file using regex."""
        deps: list[ModuleDependency] = []
        funcs: list[FunctionInfo] = []
        classes: list[ClassInfo] = []

        lines = content.split("\n")

        # Imports
        for line in lines:
            match = re.match(r'import\s+(?:static\s+)?([^;]+);', line.strip())
            if match:
                deps.append(ModuleDependency(
                    source=rel_path,
                    target=match.group(1),
                    dependency_type="import",
                    weight=2.0 if not match.group(1).startswith("java.") else 1.0,
                ))

        # Classes
        for i, line in enumerate(lines, 1):
            match = re.search(
                r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?',
                line,
            )
            if match:
                base_classes = []
                if match.group(2):
                    base_classes.append(match.group(2))
                if match.group(3):
                    base_classes.extend(m.strip() for m in match.group(3).split(","))

                classes.append(ClassInfo(
                    name=match.group(1),
                    file_path=rel_path,
                    line_start=i,
                    line_end=i,
                    base_classes=base_classes,
                ))

        # Methods
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        for i, line in enumerate(lines, 1):
            match = re.search(method_pattern, line)
            if match and match.group(1) not in ("if", "for", "while", "class"):
                params = [p.strip().split()[-1] for p in match.group(2).split(",") if p.strip()]
                funcs.append(FunctionInfo(
                    name=match.group(1),
                    file_path=rel_path,
                    line_start=i,
                    line_end=i,
                    parameters=params,
                ))

        return deps, funcs, classes

    def _is_local_import(self, root: Path, module: str, current_file: Path) -> bool:
        """Check if a Python import refers to a local module."""
        parts = module.split(".")
        # Try to resolve the import to a file
        candidates = [
            root / "/".join(parts) / "__init__.py",
            root / "/".join(parts) + ".py",
        ]
        # Also try relative to current file
        parent = current_file.parent
        candidates.extend([
            parent / "/".join(parts) / "__init__.py",
            parent / "/".join(parts) + ".py",
        ])

        return any(c.exists() for c in candidates)
