# AGENTS.md

南京六部考勤自动化项目。Python GUI（PySide6）驱动三阶段工作台：选目录 → 交互复核 → 导出带配色的 Excel 考勤表。

## 开发环境

- **Python 3.9+**，依赖见 `requirements.txt`：`PySide6>=6.5,<6.9 openpyxl>=3.1,<3.2 pyinstaller>=6.0,<6.5`
- **无 pytest**：测试是独立脚本，直接 `python` 跑
- **macOS**：`python` 命令通常需用 `python3`

## 关键命令

| 任务 | 命令 |
|------|------|
| 运行 GUI | `python app/gui.py`（Win: 双击 `app/启动考勤.bat`；Mac: 双击 `app/启动考勤.command`） |
| 造合成测试数据 | `python app/_make_sample.py <DIR>` |
| 引擎单元测试 | `python app/test_engine.py` → 末行 `ALL TESTS PASSED` |
| 金标准回归测试 | `python app/test_golden.py` → 末行 `ZERO-REGRESSION` / `REGRESSION FOUND`（退出码 0/1） |
| 无头冒烟（端到端 GUI） | `KQ_DIR=<DIR> python app/_smoke_gui.py` → 末行 `SMOKE OK` |
| 打包 exe | `app/build_exe.bat`（Win）或 GitHub Actions（推 `v*` tag） |

默认数据目录：环境变量 `KQ_DIR`，否则 macOS/Linux `~/考勤`、Windows `D:\考勤`。

## 架构要点

- **`engine.py`**（~760 行）：纯函数引擎，暴露 `prep / worklist / build / analyze`。内部通过 `_compute_plan()` 公共计算层消除 build/analyze 重复逻辑。`analyze` 返回结构化 dict 供 GUI 渲染，不写盘。**所有考勤判定逻辑的唯一权威来源。**
- **`gui.py`**：PySide6 主控，三阶段路由（`ReadyView` → `Workbench` → `Dashboard`）。用户决策以 dict 传入引擎。
- **辅助模块**：`theme.py` 色板+QSS+归类码常量 · `model.py` 数据模型（增量更新选中态） · `grid.py` 彩色网格 · `delegate.py` 单元自绘 · `undo.py` 撤销栈 · `memory.py` 跨月决策记忆
- **两套实现同源**：Python `engine.py` 与 PowerShell skill（`.agents/skills/nanjing-kaoqin/scripts/kq_run.ps1`）规则一致，改规则需两边同步

## 代码约定

- **中文注释**，保留 `外勤`/`离职` 等术语原文
- 着色样式索引（cellXfs）：`12`红底 `13`绿底 `14`蓝底 `15`紫底(全勤) `16`红字 `17`红字绿底 `18`红字蓝底 `19`红字红底
- 颜色常量：`RED='FFFF0000' GREEN='FF92D050' BLUE='FFDDEBF7' PURPLE='FFD09ECE'`
- 工号格式 `Yxxxxx`；离职后缀 `（离职）`；外勤标记 `外勤` 前缀

## 数据文件（.gitignore 排除，不入库）

三张输入表（原表/花名册/调班表）在 `<DIR>` 中，按文件名 token 识别（`engine.find_inputs`）。产出中间件 `初表` 和成品 `考勤`。运行时生成的 `kq_keep.txt` / `kq_classify.txt` / `kq_config.txt` 也是决策文件，按需 `git add -f` 版本化。

## 测试

- `test_engine.py`：引擎单元测试（ru30/rd30、parse_day、ot_val、day_style、breaks_quan、配置解析等），纯函数验证，无需数据
- `test_golden.py`：需**真实数据 + PS 金标准**（逐格比对值/底色/红字），本地跑
- `_smoke_gui.py`：offscreen 模式；若 `KQ_DIR` 无三表会自动生成临时合成数据并清理
- 环境变量 `KQ_NO_MOTION=1` 可关 GUI 动效

## 发版

GitHub Actions（`.github/workflows/build-windows.yml`）：推 `v*` tag → macOS 冒烟测试 → windows-latest PyInstaller 打包 → 自动创建 Release（含 SHA256 校验和）。PR 到 main/master 也会触发冒烟测试。

## Git 双远程

- `origin` → Gitee: `https://gitee.com/unique222/attendance-automation.git`
- `github` → GitHub: `https://github.com/xnn0703/attendance-automation.git`
- 发版只推 GitHub（`git push github v*`），Gitee 为国内镜像

## 配置文件格式（数据目录内，脚本读、Claude/GUI 写）

`kq_keep.txt`（离职<7天保留工号）：
```
Y28068, Y28099
```

`kq_classify.txt`（工作日<2次打卡归类）：
```
# 工号|日 = B(公出/蓝) | G(缺卡/绿) | R(未出勤/红)
Y28001|9=B
Y28005|22=G
```

`kq_config.txt`（人员策略，缺省=南京六部口径）：
```
OT_EXCLUDE=Y17074,Y28001
STRICT_LATE=Y28006:0905
LATE_FONT_ONLY=Y28001
```

## 设计文档

- `docs/attendance-automation/handoff/` — UI 设计交付包（规范+可点击原型）
- `docs/attendance-automation/handoff/设计交付说明.html` — 色彩/组件/动效/交互完整规范
- 原型 `prototype/考勤复核工作台.html` 双击打开可体验三阶段全流程

## 注意事项

- Excel 内联字符串（`inlineStr`）与共享字符串（`t="s"`）两种格式都需支持，`engine.py` 已处理
- `gui.py` 的 `--smoke` 模式用 `QT_QPA_PLATFORM=offscreen` 无头跑，可做 CI 冒烟
- 修改 `engine.py` 后务必跑 `test_golden.py` 和 `_smoke_gui.py` 验证零回归
