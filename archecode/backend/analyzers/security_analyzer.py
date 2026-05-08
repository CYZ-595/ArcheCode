"""
Security vulnerability analyzer.
Detects SQL injection, XSS, eval usage, token leakage, hardcoded secrets,
and other security anti-patterns.
"""

import re
import uuid
from pathlib import Path

from models.analysis import SecurityIssue, Severity, CodeLocation


class SecurityAnalyzer:
    """Scans source code for security vulnerabilities."""

    # Patterns for security issues
    PATTERNS: list[dict] = [
        # SQL Injection
        {
            "title": "Potential SQL Injection",
            "description": "String formatting or concatenation used in SQL query construction.",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-89",
            "recommendation": "Use parameterized queries or an ORM instead of string formatting.",
            "patterns": [
                r'''(?:execute|cursor\.execute|query)\s*\(\s*[f"'].*(?:\{|\%s|\+)''',
                r'''(?:execute|query)\s*\(\s*["\'].*\+.*\+''',
                r'''(?:execute|query)\s*\(\s*["\'].*\.format\(''',
                r'''(?:SELECT|INSERT|UPDATE|DELETE).*\+.*(?:request|params|input)''',
            ],
            "file_types": [".py", ".js", ".ts", ".java", ".php", ".rb"],
        },
        # XSS
        {
            "title": "Potential Cross-Site Scripting (XSS)",
            "description": "User input may be rendered without proper sanitization.",
            "severity": Severity.HIGH,
            "cwe_id": "CWE-79",
            "recommendation": "Sanitize all user input before rendering. Use template engine auto-escaping.",
            "patterns": [
                r'dangerouslySetInnerHTML',
                r'v-html\s*=',
                r'\.innerHTML\s*=',
                r'document\.write\s*\(',
                r'\.html\s*\(',
                r'render_template_string\s*\(',
            ],
            "file_types": [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".vue"],
        },
        # eval() usage
        {
            "title": "Dangerous eval() usage",
            "description": "eval() or equivalent can execute arbitrary code and is a severe security risk.",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-95",
            "recommendation": "Remove eval() usage. Use safer alternatives like JSON.parse() or ast.literal_eval().",
            "patterns": [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'compile\s*\(.*"exec"',
                r'new\s+Function\s*\(',
                r'setTimeout\s*\(\s*["\']',
                r'setInterval\s*\(\s*["\']',
            ],
            "file_types": [".py", ".js", ".ts", ".jsx", ".tsx"],
        },
        # Hardcoded secrets / tokens
        {
            "title": "Hardcoded secret or API key",
            "description": "A potential secret, API key, or password is hardcoded in source code.",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-798",
            "recommendation": "Move secrets to environment variables or a secrets manager.",
            "patterns": [
                r'''(?:api[_-]?key|apikey|secret[_-]?key|secret|password|passwd|token|auth[_-]?token)\s*[=:]\s*["\'][A-Za-z0-9+/=_\-]{8,}["\']''',
                r'''(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{20,}''',
                r'''Bearer\s+[A-Za-z0-9\-._~+/]+=*''',
                r'''(?:AKIA|ASIA)[A-Z0-9]{16}''',  # AWS access key
                r'''-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----''',
            ],
            "file_types": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".env", ".json", ".yaml", ".yml"],
        },
        # Command injection
        {
            "title": "Potential Command Injection",
            "description": "User input may be passed to a shell command.",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-78",
            "recommendation": "Use subprocess with list arguments and shell=False.",
            "patterns": [
                r'os\.system\s*\(',
                r'os\.popen\s*\(',
                r'subprocess\.(?:call|run|Popen)\s*\(.*shell\s*=\s*True',
                r'child_process\.exec\s*\(',
                r'Runtime\.getRuntime\(\)\.exec\s*\(',
            ],
            "file_types": [".py", ".js", ".ts", ".java"],
        },
        # Path traversal
        {
            "title": "Potential Path Traversal",
            "description": "File paths constructed from user input may allow directory traversal.",
            "severity": Severity.HIGH,
            "cwe_id": "CWE-22",
            "recommendation": "Validate and sanitize file paths. Use os.path.realpath() and verify the result is within expected directories.",
            "patterns": [
                r'open\s*\(.*(?:request|params|input|args)',
                r'(?:send_file|send_from_directory)\s*\(.*(?:request|params)',
                r'Path\s*\(.*(?:request|params)',
                r'fs\.(?:read|write).*\+',
            ],
            "file_types": [".py", ".js", ".ts", ".java"],
        },
        # Insecure crypto
        {
            "title": "Weak or Insecure Cryptography",
            "description": "Use of weak cryptographic algorithms or insecure random number generation.",
            "severity": Severity.HIGH,
            "cwe_id": "CWE-327",
            "recommendation": "Use SHA-256 or stronger. Use cryptographically secure random generators.",
            "patterns": [
                r'hashlib\.md5\s*\(',
                r'hashlib\.sha1\s*\(',
                r'Math\.random\s*\(',
                r'random\.random\s*\(',
                r'DES\.|Blowfish\.',
                r'MD5\s*\(',
            ],
            "file_types": [".py", ".js", ".ts", ".java", ".go"],
        },
        # Debug mode in production
        {
            "title": "Debug mode enabled",
            "description": "Debug mode should not be enabled in production.",
            "severity": Severity.MEDIUM,
            "cwe_id": "CWE-489",
            "recommendation": "Disable debug mode in production configurations.",
            "patterns": [
                r'DEBUG\s*=\s*True',
                r'debug\s*=\s*True',
                r'app\.run\s*\(.*debug\s*=\s*True',
                r'reactStrictMode:\s*true',
            ],
            "file_types": [".py", ".js", ".ts", ".cfg", ".ini"],
        },
        # Unsafe deserialization
        {
            "title": "Unsafe Deserialization",
            "description": "Unsafe deserialization can lead to remote code execution.",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-502",
            "recommendation": "Use safe deserialization methods. Avoid pickle.loads with untrusted data.",
            "patterns": [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\([^)]*(?!Loader)',
                r'yaml\.unsafe_load\s*\(',
                r'Object\.assign\s*\(.*req',
                r'\$\{.*\}',
            ],
            "file_types": [".py", ".js", ".ts"],
        },
        # CORS misconfiguration
        {
            "title": "Overly permissive CORS",
            "description": "CORS is configured to allow all origins.",
            "severity": Severity.MEDIUM,
            "cwe_id": "CWE-942",
            "recommendation": "Restrict CORS to specific trusted origins.",
            "patterns": [
                r'allow_origins\s*=\s*\["?\*"?\]',
                r'Access-Control-Allow-Origin.*\*',
                r'cors\s*\(\s*\)',
                r'origin\s*:\s*["\']?\*["\']?',
            ],
            "file_types": [".py", ".js", ".ts", ".json", ".yaml"],
        },
    ]

    def analyze(self, root: Path, source_files: list[Path]) -> list[SecurityIssue]:
        """Scan all source files for security issues."""
        issues: list[SecurityIssue] = []

        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(file_path.relative_to(root))
                ext = file_path.suffix.lower()

                for pattern_group in self.PATTERNS:
                    if ext not in pattern_group["file_types"]:
                        continue

                    for regex in pattern_group["patterns"]:
                        for match in re.finditer(regex, content, re.IGNORECASE):
                            # Calculate line number
                            line_num = content[:match.start()].count("\n") + 1
                            line_start = max(0, content.rfind("\n", 0, match.start())) + 1
                            line_end = content.find("\n", match.end())
                            if line_end == -1:
                                line_end = len(content)
                            snippet = content[line_start:line_end].strip()[:200]

                            issues.append(SecurityIssue(
                                id=str(uuid.uuid4()),
                                title=pattern_group["title"],
                                description=pattern_group["description"],
                                severity=pattern_group["severity"],
                                location=CodeLocation(
                                    file_path=rel_path,
                                    line_start=line_num,
                                    code_snippet=snippet,
                                ),
                                cwe_id=pattern_group.get("cwe_id"),
                                recommendation=pattern_group["recommendation"],
                            ))
            except Exception:
                continue

        # Deduplicate by file + line + title
        seen = set()
        unique_issues = []
        for issue in issues:
            key = (issue.location.file_path, issue.location.line_start, issue.title)
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        return unique_issues
