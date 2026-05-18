"""
Enhanced commands for aider - Autonomous, Review, Scan
This file adds new commands to aider's command system.
Import and register these commands in your aider setup.
"""

from aider.commands import Commands


def cmd_autonomous(self, args=""):
    "Start autonomous exploration mode - AI scans, reviews, and improves project automatically"
    from aider.autonomous import AutonomousEngine

    if not self.coder:
        self.io.tool_error("No active coder.")
        return

    # Parse args
    arg_parts = args.strip().split()
    max_iterations = 5
    if arg_parts:
        try:
            max_iterations = int(arg_parts[0])
        except ValueError:
            pass

    engine = AutonomousEngine(self.coder, self.io)
    engine.max_iterations = max_iterations

    try:
        engine.start()
    except KeyboardInterrupt:
        engine.stop()


def cmd_review(self, args=""):
    "Deep review of a specific file or all in-chat files"
    from aider.module_reviewer import ModuleReviewer

    reviewer = ModuleReviewer(self.coder.main_model)

    # Get files to review
    if args.strip():
        fnames = [args.strip()]
    else:
        fnames = self.coder.get_inchat_relative_files()

    if not fnames:
        self.io.tool_error("No files to review. Add files to chat first or specify a file.")
        return

    for fname in fnames:
        fpath = self.coder.root / fname
        if not fpath.exists():
            self.io.tool_error(f"File not found: {fname}")
            continue

        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            result = reviewer.review_module(str(fpath), content)
            report = reviewer.generate_review_report(result)
            self.io.tool_output(report)
        except Exception as e:
            self.io.tool_error(f"Error reviewing {fname}: {e}")


def cmd_scan(self, args=""):
    "Scan project for issues, improvements, and opportunities"
    from aider.project_analyzer import ProjectAnalyzer

    analyzer = ProjectAnalyzer(self.coder.root)
    result = analyzer.scan_project()

    stats = result["stats"]
    self.io.tool_output("## 项目扫描报告")
    self.io.tool_output(f"- 文件总数: {stats['total_files']}")
    self.io.tool_output(f"- 质量问题: {stats['quality_issues']}")
    self.io.tool_output(f"- 安全问题: {stats['security_issues']}")
    self.io.tool_output(f"- 性能问题: {stats['performance_issues']}")
    self.io.tool_output(f"- 改进机会: {stats['improvement_count']}")

    if result["improvement_opportunities"]:
        self.io.tool_output("")
        self.io.tool_output("### 改进建议 (按优先级)")
        for i, sug in enumerate(result["improvement_opportunities"][:15], 1):
            self.io.tool_output(f"{i}. [{sug['priority']}] {sug['suggestion'][:80]}")


# Register commands
Commands.cmd_autonomous = cmd_autonomous
Commands.cmd_review = cmd_review
Commands.cmd_scan = cmd_scan
