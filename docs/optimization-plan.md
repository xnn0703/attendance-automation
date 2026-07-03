# 工程化优化状态

本文件记录当前工程化收敛方案。业务规则不在这里变更，考勤判定仍以 `app/engine.py` 和 Skill 规则文档为权威。

## 已完成 / 本轮收敛

1. **依赖入口**
   - `requirements.txt` 作为 CI 和用户快速安装入口。
   - `pyproject.toml` 提供标准包元数据与 `pip install .` 能力。
   - 不引入 pytest，继续使用直接 `python` 运行的独立测试脚本。

2. **引擎公共计算层**
   - `engine._compute_plan()` 作为 `build()` 与 `analyze()` 的公共判定层。
   - `build()` 只负责写 Excel。
   - `analyze()` 只返回结构化 dict，不写盘，供 GUI 渲染。
   - 合成数据回归覆盖 `stats.full_list` / `stats.full_set` 与逐格样式一致性。

3. **测试脚本**
   - `app/test_engine.py`：纯函数与合成数据回归，直接 `python` 运行。
   - `app/_smoke_gui.py`：若默认目录无三表，会自动生成临时合成数据并清理。
   - `app/test_golden.py`：真实数据 + PS 金标准，本地零回归验证，失败时退出码为 1。

4. **CI / 发版**
   - PR 到 `main/master`：macOS 跑 `test_engine.py` + GUI smoke。
   - 推 `v*` tag：先跑测试，再在 Windows runner 上 PyInstaller 打包。
   - Release 附 `nanjing_kaoqin.exe` 与 `SHA256.txt`。

## 验收命令

```bash
python3 -m py_compile app/*.py
python3 app/test_engine.py
tmp=$(mktemp -d /tmp/kq_opt_XXXXXX)
python3 app/_make_sample.py "$tmp"
KQ_DIR="$tmp" KQ_NO_MOTION=1 python3 app/_smoke_gui.py
rm -rf "$tmp"
```

如本机有真实数据和 PS 金标准，再跑：

```bash
KQ_DIR=<真实数据目录> python3 app/test_golden.py
```

## 后续可选优化

1. **时间参数配置化**
   - 将午休区间、下班基准、默认迟到加重阈值从硬编码提取到 config。
   - 默认值必须保持现有行为不变。
   - 做之前先扩充 `test_engine.py` 覆盖默认值与覆盖值。

2. **Engine 拆分**
   - 当前 `engine.py` 仍可维护，暂不拆。
   - 若超过 1500 行或规则扩展明显增加，再拆成 `calendar/punch/roster/config/build` 等模块。

3. **真实数据回归自动化**
   - 真实数据不入库，仍需本地跑。
   - 可考虑在私有环境加一套脱敏 golden 数据，但不放公开仓库。
