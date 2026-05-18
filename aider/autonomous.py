"""
Autonomous Exploration Engine
Enables aider to continuously explore and improve projects without user intervention.
Integrates project analysis, module review, and TODO management.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from .project_analyzer import ProjectAnalyzer
from .module_reviewer import ModuleReviewer


class AutonomousEngine:
    """Manages autonomous exploration and improvement of projects."""

    # Exploration phases
    PHASE_IDLE = "idle"
    PHASE_SCAN = "scan"
    PHASE_REVIEW = "review"
    PHASE_PLAN = "plan"
    PHASE_EXECUTE = "execute"
    PHASE_VERIFY = "verify"
    PHASE_REPORT = "report"

    # TODO priorities
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"

    def __init__(self, coder, io=None):
        self.coder = coder
        self.io = io or coder.io
        self.analyzer = ProjectAnalyzer(coder.root)
        self.reviewer = ModuleReviewer(coder.main_model)

        self.phase = self.PHASE_IDLE
        self.todo_list = []
        self.completed_items = []
        self.skipped_items = []
        self.reports = []
        self.iteration = 0
        self.max_iterations = 5  # Max autonomous iterations before pausing
        self.running = False

        # Statistics
        self.stats = {
            "files_reviewed": 0,
            "issues_found": 0,
            "improvements_made": 0,
            "start_time": None,
            "end_time": None,
        }

    def start(self):
        """Start autonomous exploration."""
        self.running = True
        self.stats["start_time"] = datetime.now().isoformat()
        self.io.tool_output("🤖 自主探索模式启动")
        self.io.tool_output(f"   最大迭代次数: {self.max_iterations}")
        self.io.tool_output("   按 Ctrl+C 可随时中断")
        return self._run_loop()

    def stop(self):
        """Stop autonomous exploration."""
        self.running = False
        self.stats["end_time"] = datetime.now().isoformat()
        self.io.tool_output("🛑 自主探索模式停止")
        return self._generate_final_report()

    def _run_loop(self):
        """Main autonomous loop."""
        messages = []

        while self.running and self.iteration < self.max_iterations:
            self.iteration += 1
            self.io.tool_output(f"\n{'='*60}")
            self.io.tool_output(f"📍 迭代 {self.iteration}/{self.max_iterations}")
            self.io.tool_output(f"{'='*60}")

            try:
                # Phase 1: Scan project
                self.phase = self.PHASE_SCAN
                self.io.tool_output("\n🔍 Phase 1: 扫描项目...")
                scan_result = self._scan_project()

                # Phase 2: Review modules
                self.phase = self.PHASE_REVIEW
                self.io.tool_output("\n📋 Phase 2: 审阅模块...")
                review_results = self._review_modules(scan_result)

                # Phase 3: Generate plan
                self.phase = self.PHASE_PLAN
                self.io.tool_output("\n📝 Phase 3: 生成改进计划...")
                self._generate_plan(scan_result, review_results)

                if not self.todo_list:
                    self.io.tool_output("✅ 未发现需要改进的地方，项目状态良好！")
                    break

                # Phase 4: Execute improvements
                self.phase = self.PHASE_EXECUTE
                self.io.tool_output(f"\n⚡ Phase 4: 执行改进 ({len(self.todo_list)} 项待处理)...")
                execution_messages = self._execute_improvements()
                messages.extend(execution_messages)

                # Phase 5: Verify
                self.phase = self.PHASE_VERIFY
                self.io.tool_output("\n✅ Phase 5: 验证改进...")
                self._verify_improvements()

                # Phase 6: Report
                self.phase = self.PHASE_REPORT
                self._iteration_report()

            except KeyboardInterrupt:
                self.io.tool_output("\n⚠️ 用户中断")
                break
            except Exception as e:
                self.io.tool_output(f"\n❌ 迭代 {self.iteration} 出错: {e}")
                continue

        return self.stop()

    def _scan_project(self):
        """Scan entire project."""
        self.io.tool_output("   分析项目结构...")
        result = self.analyzer.scan_project()

        stats = result["stats"]
        self.io.tool_output(f"   📊 项目统计:")
        self.io.tool_output(f"      文件总数: {stats['total_files']}")
        self.io.tool_output(f"      质量问题: {stats['quality_issues']}")
        self.io.tool_output(f"      安全问题: {stats['security_issues']}")
        self.io.tool_output(f"      性能问题: {stats['performance_issues']}")
        self.io.tool_output(f"      改进机会: {stats['improvement_count']}")
        self.io.tool_output(f"         高优先: {stats['high_priority']}")
        self.io.tool_output(f"         中优先: {stats['medium_priority']}")
        self.io.tool_output(f"         低优先: {stats['low_priority']}")

        return result

    def _review_modules(self, scan_result):
        """Deep review of each module."""
        results = []
        source_files = self.analyzer._get_source_files()

        # Prioritize: review files with issues first
        files_with_issues = set()
        for issue in (scan_result.get("quality_issues", []) +
                      scan_result.get("security_issues", []) +
                      scan_result.get("performance_issues", [])):
            files_with_issues.add(issue.get("file", ""))

        # Sort: files with issues first, then by size
        source_files.sort(key=lambda f: (
            0 if str(f) in files_with_issues else 1,
            -f.stat().st_size
        ))

        reviewed = 0
        for fpath in source_files[:20]:  # Review top 20 files per iteration
            rel = fpath.relative_to(self.analyzer.root)
            try:
                content = fpath.read_text(encoding='utf-8', errors='ignore')
                if len(content.strip()) < 10:  # Skip trivial files
                    continue

                self.io.tool_output(f"   审阅: {rel}")
                review = self.reviewer.review_module(str(fpath), content)
                review["relative_path"] = str(rel)
                results.append(review)
                reviewed += 1
                self.stats["files_reviewed"] += 1

                # Show score
                score = review["overall_score"]
                emoji = "✅" if score >= 7 else "⚠️" if score >= 5 else "❌"
                self.io.tool_output(f"      {emoji} 评分: {score:.1f}/10")

            except Exception as e:
                self.io.tool_output(f"   ⚠️ 跳过 {rel}: {e}")

        self.io.tool_output(f"   审阅完成: {reviewed} 个模块")
        return results

    def _generate_plan(self, scan_result, review_results):
        """Generate prioritized improvement plan."""
        self.todo_list = []  # Reset

        # From scan results
        for suggestion in scan_result.get("improvement_opportunities", []):
            self.todo_list.append({
                "id": f"scan-{len(self.todo_list)}",
                "priority": suggestion["priority"],
                "category": suggestion["category"],
                "description": suggestion["suggestion"],
                "file": suggestion.get("file"),
                "line": suggestion.get("line"),
                "source": "project_scan",
                "status": "pending",
            })

        # From module reviews
        for review in review_results:
            for suggestion in review.get("suggestions", []):
                self.todo_list.append({
                    "id": f"review-{len(self.todo_list)}",
                    "priority": suggestion["priority"],
                    "category": suggestion["category"],
                    "description": suggestion["description"],
                    "file": suggestion.get("file"),
                    "line": suggestion.get("line"),
                    "source": "module_review",
                    "status": "pending",
                })

            for opp in review.get("refactoring_opportunities", []):
                self.todo_list.append({
                    "id": f"refactor-{len(self.todo_list)}",
                    "priority": "MEDIUM",
                    "category": "refactoring",
                    "description": opp["suggestion"],
                    "file": review.get("relative_path"),
                    "source": "refactoring_analysis",
                    "status": "pending",
                })

        # Deduplicate
        seen = set()
        unique = []
        for item in self.todo_list:
            key = (item["category"], item["description"][:50])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        self.todo_list = unique

        # Sort by priority
        priority_order = {self.PRIORITY_CRITICAL: 0, self.PRIORITY_HIGH: 1,
                         self.PRIORITY_MEDIUM: 2, self.PRIORITY_LOW: 3}
        self.todo_list.sort(key=lambda x: priority_order.get(x["priority"], 9))

        self.io.tool_output(f"   生成 {len(self.todo_list)} 项改进计划")
        for i, item in enumerate(self.todo_list[:10], 1):
            self.io.tool_output(f"   {i}. [{item['priority']}] {item['description'][:60]}")
        if len(self.todo_list) > 10:
            self.io.tool_output(f"   ... 还有 {len(self.todo_list) - 10} 项")

    def _execute_improvements(self):
        """Execute improvements one by one."""
        messages = []
        executed = 0
        max_per_iteration = 5  # Limit per iteration to avoid runaway

        for item in self.todo_list[:]:
            if item["status"] != "pending":
                continue
            if executed >= max_per_iteration:
                self.io.tool_output(f"   ⏸️ 本轮已执行 {max_per_iteration} 项，下轮继续")
                break

            self.io.tool_output(f"\n   🔧 执行: {item['description'][:60]}")
            item["status"] = "in_progress"

            try:
                # Generate task message for aider
                task_msg = self._generate_task_message(item)

                # Execute via aider's coder
                self.coder.run_one(task_msg, preproc=False)

                item["status"] = "completed"
                self.completed_items.append(item)
                self.todo_list.remove(item)
                executed += 1
                self.stats["improvements_made"] += 1
                messages.append({"role": "autonomous", "content": task_msg})

                self.io.tool_output(f"   ✅ 完成")

            except KeyboardInterrupt:
                item["status"] = "skipped"
                self.skipped_items.append(item)
                self.io.tool_output(f"   ⏭️ 跳过(中断)")
                raise
            except Exception as e:
                item["status"] = "failed"
                self.io.tool_output(f"   ❌ 失败: {e}")

        return messages

    def _generate_task_message(self, item):
        """Generate aider task message for an improvement item."""
        context_parts = []

        context_parts.append(f"## 自主改进任务")
        context_parts.append(f"优先级: {item['priority']}")
        context_parts.append(f"类别: {item['category']}")
        context_parts.append(f"描述: {item['description']}")

        if item.get("file"):
            context_parts.append(f"相关文件: {item['file']}")
        if item.get("line"):
            context_parts.append(f"相关行: {item['line']}")

        # Add improvement guidelines
        context_parts.append("")
        context_parts.append("## 改进要求")
        context_parts.append("1. 分析问题根因，不要只修表面")
        context_parts.append("2. 搜索是否有更好的开源解决方案或库")
        context_parts.append("3. 确保修改不破坏现有功能")
        context_parts.append("4. 添加必要的注释和文档")
        context_parts.append("5. 遵循项目现有代码风格")
        context_parts.append("6. 如果是安全问题，优先修复")

        return "\n".join(context_parts)

    def _verify_improvements(self):
        """Verify improvements don't break anything."""
        if not self.completed_items:
            return

        self.io.tool_output("   检查改进是否引入新问题...")

        # Quick rescan for new issues
        result = self.analyzer.scan_project()
        new_issues = result["stats"]["security_issues"] + result["stats"]["quality_issues"]

        self.io.tool_output(f"   当前问题总数: {new_issues}")

        # Check git status for uncommitted changes
        try:
            git_status = self.coder.repo.git.status("--porcelain") if self.coder.repo else ""
            if git_status.strip():
                self.io.tool_output("   📝 有未提交的更改，建议提交")
        except Exception:
            pass

    def _iteration_report(self):
        """Generate report for current iteration."""
        report = []
        report.append(f"\n📊 迭代 {self.iteration} 报告")
        report.append(f"{'='*40}")
        report.append(f"本轮完成: {len(self.completed_items)} 项")
        report.append(f"本轮跳过: {len(self.skipped_items)} 项")
        report.append(f"剩余待办: {len(self.todo_list)} 项")
        report.append(f"累计审阅: {self.stats['files_reviewed']} 个模块")
        report.append(f"累计改进: {self.stats['improvements_made']} 项")

        for line in report:
            self.io.tool_output(line)

        self.reports.append({
            "iteration": self.iteration,
            "completed": len(self.completed_items),
            "skipped": len(self.skipped_items),
            "remaining": len(self.todo_list),
            "timestamp": datetime.now().isoformat(),
        })

    def _generate_final_report(self):
        """Generate final summary report."""
        report = []
        report.append(f"\n{'='*60}")
        report.append(f"🏁 自主探索完成")
        report.append(f"{'='*60}")
        report.append(f"总迭代次数: {self.iteration}")
        report.append(f"审阅模块数: {self.stats['files_reviewed']}")
        report.append(f"发现问题数: {self.stats['issues_found']}")
        report.append(f"完成改进数: {self.stats['improvements_made']}")
        report.append(f"跳过项目数: {len(self.skipped_items)}")
        report.append(f"开始时间: {self.stats['start_time']}")
        report.append(f"结束时间: {self.stats['end_time']}")

        if self.todo_list:
            report.append(f"\n📋 剩余待办 ({len(self.todo_list)} 项):")
            for item in self.todo_list[:10]:
                report.append(f"   [{item['priority']}] {item['description'][:60]}")

        if self.completed_items:
            report.append(f"\n✅ 已完成改进:")
            for item in self.completed_items:
                report.append(f"   {item['description'][:60]}")

        final_report = "\n".join(report)
        for line in report:
            self.io.tool_output(line)

        # Save report to file
        try:
            report_path = Path(self.coder.root) / ".aider" / "autonomous_report.md"
            report_path.parent.mkdir(exist_ok=True)
            report_path.write_text(final_report, encoding="utf-8")
            self.io.tool_output(f"\n📄 报告已保存: {report_path}")
        except Exception:
            pass

        return final_report

    def get_status(self):
        """Get current status."""
        return {
            "phase": self.phase,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "running": self.running,
            "todo_count": len(self.todo_list),
            "completed_count": len(self.completed_items),
            "stats": self.stats,
        }
