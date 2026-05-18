"""
Project Analyzer for Autonomous Exploration
Scans project structure, analyzes code quality, finds improvement opportunities.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict


class ProjectAnalyzer:
    """Analyzes a project to find improvement opportunities."""

    # Code quality patterns
    QUALITY_PATTERNS = {
        "long_function": {"pattern": r"def \w+.*?(?=\ndef |\Z)", "threshold": 50, "desc": "函数过长(>50行)"},
        "deep_nesting": {"pattern": r"(\s{16,})(if|for|while|try)", "threshold": 4, "desc": "嵌套过深(>4层)"},
        "magic_number": {"pattern": r"(?<!\w)(\d{2,})(?!\w)", "desc": "魔法数字"},
        "todo_fixme": {"pattern": r"#\s*(TODO|FIXME|HACK|XXX)", "desc": "未解决的TODO/FIXME"},
        "bare_except": {"pattern": r"except\s*:", "desc": "裸except(应指定异常类型)"},
        "global_var": {"pattern": r"^[A-Z_][A-Z_0-9]+\s*=", "desc": "全局变量"},
        "print_debug": {"pattern": r"print\s*\(", "desc": "print调试(应用logging)"},
        "hardcoded_path": {"pattern": r"""['"][/\\][a-zA-Z]:|['"]/home/|['"]/usr/|['"]C:\\\\""", "desc": "硬编码路径"},
    }

    # Security patterns
    SECURITY_PATTERNS = {
        "eval_exec": {"pattern": r"\b(eval|exec)\s*\(", "severity": "HIGH", "desc": "eval/exec注入风险"},
        "sql_inject": {"pattern": r"""f["'].*SELECT|\.format\(.*SELECT""", "severity": "HIGH", "desc": "SQL注入风险"},
        "hardcoded_secret": {"pattern": r"""(password|secret|token|api_key)\s*=\s*['"][^'"]+['"]""", "severity": "HIGH", "desc": "硬编码密钥"},
        "unsafe_yaml": {"pattern": r"yaml\.load\s*\((?!.*Loader)", "severity": "MEDIUM", "desc": "不安全的YAML加载"},
        "pickle_load": {"pattern": r"pickle\.load", "severity": "MEDIUM", "desc": "pickle反序列化风险"},
        "temp_file": {"pattern": r"tempfile\.(mktemp|NamedTemporaryFile)", "severity": "LOW", "desc": "临时文件安全"},
        "subprocess_shell": {"pattern": r"subprocess\.(run|call|Popen).*shell\s*=\s*True", "severity": "MEDIUM", "desc": "shell注入风险"},
    }

    # Performance patterns
    PERFORMANCE_PATTERNS = {
        "n_plus_one": {"pattern": r"for.*in.*:\s*\n\s*.*\.query|\.get\(", "desc": "N+1查询风险"},
        "string_concat_loop": {"pattern": r"for.*:\s*\n\s*\w+\s*\+=\s*['\"]", "desc": "循环中字符串拼接(用join)"},
        "list_append_loop": {"pattern": r"for.*:\s*\n\s*\w+\.append", "desc": "循环append(考虑列表推导)"},
        "import_in_loop": {"pattern": r"for.*:\s*\n\s*import\s+", "desc": "循环内import"},
        "re_compile_missing": {"pattern": r"re\.(match|search|sub|findall)\s*\(", "desc": "正则未预编译"},
    }

    # Project structure patterns
    STRUCTURE_INDICATORS = {
        "has_tests": ["test_*.py", "*_test.py", "tests/", "test/"],
        "has_docs": ["docs/", "doc/", "*.md", "README*"],
        "has_ci": [".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile", ".circleci/"],
        "has_lint": [".flake8", ".pylintrc", "pyproject.toml", "setup.cfg", ".ruff.toml"],
        "has_types": ["py.typed", "*.pyi", "mypy.ini"],
        "has_docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "has_precommit": [".pre-commit-config.yaml"],
        "has_security": [".safety", "safety.ini", "bandit.yaml"],
    }

    # Dependency analysis
    DEPENDENCY_FILES = [
        "requirements.txt", "requirements*.txt", "setup.py", "setup.cfg",
        "pyproject.toml", "Pipfile", "poetry.lock", "package.json",
        "go.mod", "Cargo.toml", "pom.xml", "build.gradle"
    ]

    def __init__(self, root_dir, aider_ignore=None):
        self.root = Path(root_dir)
        self.ignore_patterns = aider_ignore or []
        self.analysis_cache = {}

    def should_ignore(self, path):
        """Check if path should be ignored."""
        path_str = str(path)
        for pat in self.ignore_patterns:
            if pat in path_str:
                return True
        # Default ignores
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv',
                      'dist', 'build', '.tox', '.mypy_cache', '.pytest_cache'}
        parts = Path(path_str).parts
        return any(p in ignore_dirs for p in parts)

    def scan_project(self):
        """Full project scan returning structured analysis."""
        result = {
            "structure": self.analyze_structure(),
            "files": self.scan_files(),
            "dependencies": self.analyze_dependencies(),
            "quality_issues": [],
            "security_issues": [],
            "performance_issues": [],
            "improvement_opportunities": [],
            "stats": {},
        }

        # Analyze each source file
        source_files = self._get_source_files()
        for fpath in source_files:
            rel = fpath.relative_to(self.root)
            try:
                content = fpath.read_text(encoding='utf-8', errors='ignore')
                file_analysis = self.analyze_file(str(fpath), content)
                file_analysis["path"] = str(rel)
                result["quality_issues"].extend(file_analysis.get("quality", []))
                result["security_issues"].extend(file_analysis.get("security", []))
                result["performance_issues"].extend(file_analysis.get("performance", []))
            except Exception:
                pass

        # Generate improvement suggestions
        result["improvement_opportunities"] = self._generate_suggestions(result)
        result["stats"] = self._compute_stats(result)

        return result

    def analyze_structure(self):
        """Analyze project structure and completeness."""
        structure = {"type": "unknown", "completeness": {}, "suggestions": []}

        # Detect project type
        if (self.root / "package.json").exists():
            structure["type"] = "javascript"
        elif (self.root / "pyproject.toml").exists() or (self.root / "setup.py").exists():
            structure["type"] = "python"
        elif (self.root / "go.mod").exists():
            structure["type"] = "go"
        elif (self.root / "Cargo.toml").exists():
            structure["type"] = "rust"

        # Check completeness
        for indicator, patterns in self.STRUCTURE_INDICATORS.items():
            found = False
            for pat in patterns:
                if list(self.root.glob(pat)):
                    found = True
                    break
            structure["completeness"][indicator] = found
            if not found:
                structure["suggestions"].append(self._structure_suggestion(indicator))

        return structure

    def _structure_suggestion(self, indicator):
        """Generate suggestion for missing structure component."""
        suggestions = {
            "has_tests": "添加测试框架 (pytest + 测试文件)",
            "has_docs": "添加文档 (README.md, docs/)",
            "has_ci": "添加 CI/CD (GitHub Actions)",
            "has_lint": "添加代码检查 (ruff/flake8)",
            "has_types": "添加类型标注 (mypy/pyright)",
            "has_docker": "添加容器化 (Dockerfile)",
            "has_precommit": "添加 pre-commit hooks",
            "has_security": "添加安全扫描 (bandit/safety)",
        }
        return suggestions.get(indicator, f"添加 {indicator}")

    def scan_files(self):
        """Scan all source files and categorize them."""
        files = {"total": 0, "by_type": defaultdict(int), "large_files": [], "empty_files": []}

        for fpath in self._get_all_files():
            rel = fpath.relative_to(self.root)
            ext = fpath.suffix.lower()
            files["total"] += 1
            files["by_type"][ext] += 1

            try:
                size = fpath.stat().st_size
                lines = len(fpath.read_text(encoding='utf-8', errors='ignore').splitlines())

                if lines > 500:
                    files["large_files"].append({"path": str(rel), "lines": lines})
                if lines == 0 and ext in {'.py', '.js', '.ts', '.go', '.rs'}:
                    files["empty_files"].append(str(rel))
            except Exception:
                pass

        files["by_type"] = dict(files["by_type"])
        return files

    def analyze_dependencies(self):
        """Analyze project dependencies."""
        deps = {"files": [], "issues": []}

        for dep_file in self.DEPENDENCY_FILES:
            for fpath in self.root.glob(dep_file):
                if self.should_ignore(fpath):
                    continue
                deps["files"].append(str(fpath.relative_to(self.root)))
                try:
                    content = fpath.read_text()
                    # Check for unpinned versions
                    if fpath.name == "requirements.txt":
                        unpinned = [l.strip() for l in content.splitlines()
                                   if l.strip() and not l.startswith('#') and '==' not in l and '>=' not in l]
                        if unpinned:
                            deps["issues"].append({
                                "file": str(fpath.relative_to(self.root)),
                                "issue": "未固定版本号",
                                "items": unpinned[:5]
                            })
                except Exception:
                    pass

        return deps

    def analyze_file(self, filepath, content):
        """Analyze a single file for issues."""
        result = {"quality": [], "security": [], "performance": []}
        lines = content.splitlines()

        # Quality checks
        for name, pat_info in self.QUALITY_PATTERNS.items():
            for i, line in enumerate(lines, 1):
                if re.search(pat_info["pattern"], line):
                    result["quality"].append({
                        "file": filepath,
                        "line": i,
                        "type": name,
                        "desc": pat_info["desc"],
                        "code": line.strip()[:100]
                    })

        # Security checks
        for name, pat_info in self.SECURITY_PATTERNS.items():
            for i, line in enumerate(lines, 1):
                if re.search(pat_info["pattern"], line):
                    result["security"].append({
                        "file": filepath,
                        "line": i,
                        "type": name,
                        "severity": pat_info["severity"],
                        "desc": pat_info["desc"],
                        "code": line.strip()[:100]
                    })

        # Performance checks
        content_multiline = content
        for name, pat_info in self.PERFORMANCE_PATTERNS.items():
            matches = re.finditer(pat_info["pattern"], content_multiline, re.MULTILINE)
            for m in matches:
                line_num = content[:m.start()].count('\n') + 1
                result["performance"].append({
                    "file": filepath,
                    "line": line_num,
                    "type": name,
                    "desc": pat_info["desc"]
                })

        return result

    def _generate_suggestions(self, analysis):
        """Generate prioritized improvement suggestions."""
        suggestions = []

        # From structure
        for s in analysis["structure"].get("suggestions", []):
            suggestions.append({"priority": "MEDIUM", "category": "structure", "suggestion": s})

        # From security (highest priority)
        for issue in analysis["security_issues"]:
            suggestions.append({
                "priority": issue.get("severity", "HIGH"),
                "category": "security",
                "suggestion": f"修复安全问题: {issue['desc']} ({issue['file']}:{issue['line']})",
                "file": issue["file"],
                "line": issue["line"]
            })

        # From quality
        quality_by_type = defaultdict(list)
        for issue in analysis["quality_issues"]:
            quality_by_type[issue["type"]].append(issue)
        for issue_type, issues in quality_by_type.items():
            suggestions.append({
                "priority": "MEDIUM" if len(issues) > 3 else "LOW",
                "category": "quality",
                "suggestion": f"{issues[0]['desc']}: {len(issues)}处 ({', '.join(set(i['file'] for i in issues[:3]))})"
            })

        # From performance
        for issue in analysis["performance_issues"]:
            suggestions.append({
                "priority": "LOW",
                "category": "performance",
                "suggestion": f"性能优化: {issue['desc']} ({issue['file']}:{issue['line']})"
            })

        # From dependencies
        for dep_issue in analysis["dependencies"].get("issues", []):
            suggestions.append({
                "priority": "MEDIUM",
                "category": "dependency",
                "suggestion": f"依赖问题: {dep_issue['issue']} ({dep_issue['file']})"
            })

        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 3))

        return suggestions

    def _compute_stats(self, analysis):
        """Compute summary statistics."""
        return {
            "total_files": analysis["files"]["total"],
            "quality_issues": len(analysis["quality_issues"]),
            "security_issues": len(analysis["security_issues"]),
            "performance_issues": len(analysis["performance_issues"]),
            "improvement_count": len(analysis["improvement_opportunities"]),
            "high_priority": len([s for s in analysis["improvement_opportunities"] if s["priority"] == "HIGH"]),
            "medium_priority": len([s for s in analysis["improvement_opportunities"] if s["priority"] == "MEDIUM"]),
            "low_priority": len([s for s in analysis["improvement_opportunities"] if s["priority"] == "LOW"]),
        }

    def _get_source_files(self):
        """Get all source code files."""
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.c', '.cpp', '.h'}
        files = []
        for ext in extensions:
            for fpath in self.root.rglob(f"*{ext}"):
                if not self.should_ignore(fpath):
                    files.append(fpath)
        return files

    def _get_all_files(self):
        """Get all files in project."""
        files = []
        for fpath in self.root.rglob("*"):
            if fpath.is_file() and not self.should_ignore(fpath):
                files.append(fpath)
        return files

    def get_file_summary(self, filepath):
        """Get a summary of a single file."""
        try:
            content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            return {
                "path": filepath,
                "lines": len(lines),
                "size": Path(filepath).stat().st_size,
                "has_docstring": '"""' in content or "'''" in content,
                "has_type_hints": ": " in content and "->" in content,
                "has_tests": "test_" in content or "assert " in content,
                "imports": [l.strip() for l in lines if l.strip().startswith(("import ", "from "))],
                "functions": [l.strip() for l in lines if l.strip().startswith("def ")],
                "classes": [l.strip() for l in lines if l.strip().startswith("class ")],
            }
        except Exception as e:
            return {"path": filepath, "error": str(e)}
