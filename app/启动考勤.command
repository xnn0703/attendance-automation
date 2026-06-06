#!/bin/bash
# macOS 双击启动脚本：在 Finder 中双击即用 python3 启动考勤 GUI。
cd "$(dirname "$0")"
python3 gui.py
