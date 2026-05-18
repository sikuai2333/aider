# Aider Enhanced - 自主编程系统

基于 [aider](https://github.com/Aider-AI/aider) 的增强版本，添加了自主探索和持续改进能力。

## 新增功能

### 🤖 自主探索模式 (`/autonomous`)

启动后会自动：
1. **扫描项目** - 分析结构、依赖、代码质量
2. **审阅模块** - 5维度深度评分（可读性、可维护性、性能、安全性、可测试性）
3. **生成计划** - 按优先级排序改进任务
4. **执行改进** - 逐个完成改进任务
5. **验证结果** - 确保改进不引入新问题

```bash
# 在 aider 中使用
> /autonomous 5    # 启动5轮自主探索
> /autonomous      # 默认5轮

# 或使用便捷脚本
aider-autonomous /path/to/project 5
```

### 📋 模块审阅 (`/review`)

深度审阅单个文件，生成详细评分报告：

```bash
> /review myfile.py
> /review           # 审阅当前聊天中的所有文件
```

输出包含：
- 综合评分（0-10分）
- 5个维度的详细评分
- 具体问题清单
- 改进建议
- 重构机会

### 🔍 项目扫描 (`/scan`)

快速扫描整个项目：

```bash
> /scan
```

输出包含：
- 文件总数统计
- 质量问题数量
- 安全问题数量
- 性能问题数量
- 优先级排序的改进建议

## 架构设计

```
aider/
├── project_analyzer.py   # 项目扫描器
├── module_reviewer.py    # 模块审阅器
├── autonomous.py         # 自主探索引擎
├── autonomous_prompts.py # 提示词模板
└── enhanced_commands.py  # 新增命令
```

### 核心组件

1. **ProjectAnalyzer** - 扫描项目结构、代码质量、安全漏洞
2. **ModuleReviewer** - 5维度深度审阅单个模块
3. **AutonomousEngine** - 自主循环引擎，管理探索流程

## 使用场景

### 场景1：接手新项目
```bash
aider /path/to/new/project
> /scan              # 快速了解项目状况
> /autonomous 10     # 自动改进10轮
```

### 场景2：代码审查
```bash
aider /path/to/project
> /review src/main.py
> /review src/utils.py
```

### 场景3：持续改进
```bash
# 在开发过程中定期运行
> /autonomous 3      # 每次迭代改进3轮
```

## 改进优先级

系统按以下优先级处理改进任务：

1. **CRITICAL** - 安全漏洞、数据丢失风险
2. **HIGH** - 严重bug、性能瓶颈
3. **MEDIUM** - 代码质量问题、缺少测试
4. **LOW** - 代码风格、文档完善

## 搜索策略

每次改进前，系统会搜索更好的解决方案：

1. 项目内搜索 - 是否有现成实现
2. 标准库 - Python是否内置支持
3. 已安装依赖 - 现有库是否支持
4. 开源社区 - 搜索成熟方案
5. 最佳实践 - 参考行业标准

## 安全机制

- **最大迭代限制** - 防止无限循环
- **紧急停止** - Ctrl+C 随时中断
- **失败保护** - 连续失败自动停止
- **验证检查** - 每次改进后验证

## 安装

```bash
# 克隆增强版
git clone https://github.com/sikuai2333/aider.git
cd aider

# 安装
pip install -e .

# 或直接使用已安装的版本（文件已复制到 aider 包目录）
```

## 配置

无需额外配置，使用 aider 现有的模型配置即可。

```bash
# 使用自定义 API
aider --api-base https://your-api.com/v1 --api-key your-key

# 使用增强功能
> /autonomous 5
```

## 注意事项

1. 自主模式会自动修改代码，建议在 git 仓库中使用
2. 首次运行建议设置较小的迭代次数（如3-5轮）
3. 大型项目扫描可能需要较长时间
4. 建议在运行前备份重要代码

## 许可证

继承自 [aider](https://github.com/Aider-AI/aider) 的 Apache 2.0 许可证。
