"""
Module Reviewer - Deep code review for individual modules.
Analyzes code quality, suggests alternatives, checks patterns.
"""


class ModuleReviewer:
    """Reviews individual modules for improvement opportunities."""

    REVIEW_CRITERIA = {
        "readability": {
            "weight": 0.25,
            "checks": [
                "函数命名是否清晰",
                "变量命名是否有意义",
                "注释是否充分且有用",
                "代码结构是否易读",
                "是否有不必要的复杂度",
            ]
        },
        "maintainability": {
            "weight": 0.25,
            "checks": [
                "函数是否单一职责",
                "是否有适当的错误处理",
                "是否遵循DRY原则",
                "是否容易修改和扩展",
                "是否有充分的文档字符串",
            ]
        },
        "performance": {
            "weight": 0.20,
            "checks": [
                "是否有不必要的循环",
                "数据结构选择是否合理",
                "是否有缓存机会",
                "IO操作是否高效",
                "是否有N+1查询问题",
            ]
        },
        "security": {
            "weight": 0.15,
            "checks": [
                "输入是否经过验证",
                "是否有注入风险",
                "敏感数据是否安全处理",
                "权限检查是否充分",
                "是否有安全的默认配置",
            ]
        },
        "testability": {
            "weight": 0.15,
            "checks": [
                "函数是否易于单元测试",
                "依赖是否可以mock",
                "是否有副作用",
                "测试覆盖率是否足够",
                "边界条件是否处理",
            ]
        }
    }

    def __init__(self, aider_model=None):
        self.model = aider_model

    def review_module(self, filepath, content, project_context=None):
        """Perform deep review of a single module."""
        lines = content.splitlines()
        result = {
            "file": filepath,
            "total_lines": len(lines),
            "scores": {},
            "issues": [],
            "suggestions": [],
            "alternatives": [],
            "refactoring_opportunities": [],
        }

        # Analyze structure
        structure = self._analyze_structure(content)
        result["structure"] = structure

        # Score each criterion
        for criterion, config in self.REVIEW_CRITERIA.items():
            score, issues = self._score_criterion(criterion, content, structure)
            result["scores"][criterion] = {
                "score": score,
                "weight": config["weight"],
                "weighted": score * config["weight"],
                "issues": issues
            }
            result["issues"].extend(issues)

        # Overall score
        result["overall_score"] = sum(s["weighted"] for s in result["scores"].values())

        # Generate suggestions
        result["suggestions"] = self._generate_suggestions(result, structure)
        result["refactoring_opportunities"] = self._find_refactoring(content, structure)

        return result

    def _analyze_structure(self, content):
        """Analyze code structure."""
        lines = content.splitlines()
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "global_vars": [],
            "complexity_hotspots": [],
        }

        current_func = None
        func_start = 0
        indent_level = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track functions
            if stripped.startswith("def "):
                if current_func:
                    current_func["lines"] = i - func_start
                    structure["functions"].append(current_func)
                func_name = stripped.split("(")[0].replace("def ", "")
                current_func = {"name": func_name, "start": i, "args": self._extract_args(stripped)}
                func_start = i

            # Track classes
            if stripped.startswith("class "):
                class_name = stripped.split("(")[0].split(":")[0].replace("class ", "")
                structure["classes"].append({"name": class_name, "start": i})

            # Track imports
            if stripped.startswith(("import ", "from ")):
                structure["imports"].append({"line": i, "import": stripped})

            # Track global vars
            if not line.startswith((" ", "\t")) and "=" in stripped and not stripped.startswith(("def ", "class ", "#", "if ", "for ", "while ", "import ", "from ")):
                structure["global_vars"].append({"line": i, "var": stripped.split("=")[0].strip()})

            # Detect complexity hotspots
            if stripped.startswith(("if ", "for ", "while ", "try:", "except")):
                current_indent = len(line) - len(line.lstrip())
                if current_indent >= 12:  # 3+ levels deep
                    structure["complexity_hotspots"].append({"line": i, "depth": current_indent // 4})

        # Don't forget last function
        if current_func:
            current_func["lines"] = len(lines) - func_start
            structure["functions"].append(current_func)

        return structure

    def _extract_args(self, func_def):
        """Extract function arguments."""
        try:
            args_str = func_def.split("(", 1)[1].split(")")[0]
            return [a.strip().split(":")[0].split("=")[0].strip() for a in args_str.split(",") if a.strip()]
        except (IndexError, ValueError):
            return []

    def _score_criterion(self, criterion, content, structure):
        """Score a specific criterion."""
        lines = content.splitlines()
        issues = []
        score = 10.0

        if criterion == "readability":
            # Check function length
            for func in structure["functions"]:
                if func.get("lines", 0) > 50:
                    score -= 0.5
                    issues.append({"type": "long_function", "func": func["name"], "lines": func["lines"],
                                  "desc": f"函数 {func['name']} 有 {func['lines']} 行，建议拆分"})

            # Check naming
            for func in structure["functions"]:
                if len(func["name"]) < 3 and func["name"] not in ("do", "go", "up"):
                    score -= 0.3
                    issues.append({"type": "short_name", "name": func["name"],
                                  "desc": f"函数名 '{func['name']}' 太短，建议使用描述性名称"})

            # Check comments ratio
            comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
            code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
            if code_lines > 0 and comment_lines / code_lines < 0.05:
                score -= 1.0
                issues.append({"type": "few_comments", "desc": "注释过少，建议添加说明性注释"})

        elif criterion == "maintainability":
            # Check for DRY violations
            line_counts = {}
            for line in lines:
                stripped = line.strip()
                if len(stripped) > 20 and not stripped.startswith("#"):
                    line_counts[stripped] = line_counts.get(stripped, 0) + 1
            duplicates = {l: c for l, c in line_counts.items() if c > 2}
            for dup_line, count in duplicates.items():
                score -= 0.3
                issues.append({"type": "duplicate_code", "count": count,
                              "desc": f"重复代码出现 {count} 次: {dup_line[:60]}..."})

            # Check for docstrings
            funcs_with_doc = sum(1 for f in structure["functions"]
                                if self._has_docstring(content, f["start"]))
            if structure["functions"]:
                doc_ratio = funcs_with_doc / len(structure["functions"])
                if doc_ratio < 0.5:
                    score -= 1.0
                    issues.append({"type": "missing_docstrings", "ratio": f"{doc_ratio:.0%}",
                                  "desc": f"仅 {doc_ratio:.0%} 的函数有文档字符串"})

        elif criterion == "performance":
            # Check for string concatenation in loops
            for i, line in enumerate(lines):
                if "for " in line or "while " in line:
                    # Look ahead for string concat
                    for j in range(i+1, min(i+20, len(lines))):
                        if "+=" in lines[j] and ("'" in lines[j] or '"' in lines[j]):
                            score -= 0.5
                            issues.append({"type": "string_concat_loop", "line": j+1,
                                          "desc": "循环中字符串拼接，建议使用 join()"})
                            break

        elif criterion == "security":
            # Check for eval/exec
            for i, line in enumerate(lines, 1):
                if "eval(" in line or "exec(" in line:
                    score -= 2.0
                    issues.append({"type": "eval_exec", "line": i,
                                  "desc": "使用了 eval/exec，存在代码注入风险"})
                if "pickle.load" in line:
                    score -= 1.5
                    issues.append({"type": "pickle", "line": i,
                                  "desc": "pickle 反序列化可能执行任意代码"})

        elif criterion == "testability":
            # Check for side effects in functions
            for func in structure["functions"]:
                func_lines = self._get_function_lines(content, func["start"])
                has_io = any("open(" in l or "requests." in l or "print(" in l for l in func_lines)
                has_return = any("return " in l for l in func_lines)
                if has_io and not has_return:
                    score -= 0.5
                    issues.append({"type": "side_effect", "func": func["name"],
                                  "desc": f"函数 {func['name']} 有IO副作用且无返回值，难以测试"})

        return max(0, score), issues

    def _has_docstring(self, content, func_line):
        """Check if function has a docstring."""
        lines = content.splitlines()
        func_idx = func_line - 1
        if func_idx + 1 < len(lines):
            next_line = lines[func_idx + 1].strip()
            return next_line.startswith('"""') or next_line.startswith("'''")
        return False

    def _get_function_lines(self, content, start_line):
        """Get lines of a function."""
        lines = content.splitlines()
        result = []
        for i in range(start_line - 1, len(lines)):
            if i > start_line - 1 and lines[i].strip().startswith("def "):
                break
            result.append(lines[i])
        return result

    def _generate_suggestions(self, review_result, structure):
        """Generate improvement suggestions based on review."""
        suggestions = []
        score = review_result["overall_score"]

        # Priority suggestions based on lowest scores
        sorted_scores = sorted(review_result["scores"].items(), key=lambda x: x[1]["score"])
        for criterion, data in sorted_scores:
            if data["score"] < 7:
                for issue in data["issues"][:3]:
                    suggestions.append({
                        "priority": "HIGH" if data["score"] < 5 else "MEDIUM",
                        "category": criterion,
                        "description": issue.get("desc", ""),
                        "file": review_result["file"],
                        "line": issue.get("line"),
                    })

        # Structural suggestions
        if len(structure.get("functions", [])) > 15:
            suggestions.append({
                "priority": "MEDIUM",
                "category": "structure",
                "description": f"文件包含 {len(structure['functions'])} 个函数，考虑拆分为多个模块",
                "file": review_result["file"],
            })

        if structure.get("complexity_hotspots"):
            suggestions.append({
                "priority": "HIGH",
                "category": "complexity",
                "description": f"发现 {len(structure['complexity_hotspots'])} 个复杂度热点，需要重构",
                "file": review_result["file"],
                "details": structure["complexity_hotspots"][:5],
            })

        return suggestions

    def _find_refactoring(self, content, structure):
        """Find refactoring opportunities."""
        opportunities = []

        # Long parameter lists
        for func in structure.get("functions", []):
            if len(func.get("args", [])) > 5:
                opportunities.append({
                    "type": "parameter_object",
                    "func": func["name"],
                    "args": func["args"],
                    "suggestion": f"函数 {func['name']} 有 {len(func['args'])} 个参数，考虑使用参数对象模式"
                })

        # God classes (too many methods)
        for cls in structure.get("classes", []):
            class_methods = [f for f in structure.get("functions", [])
                           if f["start"] > cls["start"]]
            if len(class_methods) > 10:
                opportunities.append({
                    "type": "god_class",
                    "class": cls["name"],
                    "methods": len(class_methods),
                    "suggestion": f"类 {cls['name']} 有 {len(class_methods)} 个方法，考虑拆分职责"
                })

        # Extract method opportunities (long blocks of code)
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith(("if ", "for ", "while ")) and len(line) - len(line.lstrip()) >= 8:
                # Check if this block is long
                block_start = i
                block_lines = 0
                for j in range(i+1, min(i+30, len(lines))):
                    if lines[j].strip() and not lines[j].startswith(" " * (len(line) - len(line.lstrip()) + 4)):
                        break
                    block_lines += 1
                if block_lines > 15:
                    opportunities.append({
                        "type": "extract_method",
                        "line": i+1,
                        "block_size": block_lines,
                        "suggestion": f"第 {i+1} 行的代码块有 {block_lines} 行，考虑提取为独立方法"
                    })

        return opportunities

    def generate_review_report(self, review_result):
        """Generate human-readable review report."""
        report = []
        report.append(f"## 模块审阅报告: {review_result['file']}")
        report.append(f"总行数: {review_result['total_lines']}")
        report.append(f"综合评分: {review_result['overall_score']:.1f}/10")
        report.append("")

        report.append("### 评分明细")
        for criterion, data in review_result["scores"].items():
            emoji = "✅" if data["score"] >= 7 else "⚠️" if data["score"] >= 5 else "❌"
            report.append(f"{emoji} {criterion}: {data['score']:.1f}/10 (权重: {data['weight']:.0%})")
            for issue in data["issues"][:2]:
                report.append(f"   - {issue.get('desc', '')}")
        report.append("")

        if review_result.get("suggestions"):
            report.append("### 改进建议")
            for i, sug in enumerate(review_result["suggestions"][:5], 1):
                report.append(f"{i}. [{sug['priority']}] {sug['description']}")
            report.append("")

        if review_result.get("refactoring_opportunities"):
            report.append("### 重构机会")
            for i, opp in enumerate(review_result["refactoring_opportunities"][:3], 1):
                report.append(f"{i}. {opp['suggestion']}")
            report.append("")

        return "\n".join(report)
