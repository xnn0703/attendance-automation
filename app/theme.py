# -*- coding: utf-8 -*-
"""设计系统：浅色中性盘 + 石板灰强调 + 语义数据色（三重编码）+ 尺寸/圆角 + 全局 QSS。
色值/尺寸取自 docs/attendance-automation/handoff/设计交付说明.html。深色/暖白主题留后续。"""

# ---------- 中性盘（浅色默认）----------
BG = '#EEF1F5'
SURFACE = '#FFFFFF'
SURFACE_2 = '#F8FAFC'
SURFACE_3 = '#F1F5F9'
LINE = '#E2E8F0'
LINE_2 = '#CBD5E1'
INK = '#0F172A'
INK_2 = '#475569'
INK_3 = '#94A3B8'

# ---------- 石板灰强调（界面状态专用，不用于考勤结论）----------
ACCENT = '#475569'
ACCENT_STRONG = '#334155'
ACCENT_DEEP = '#1E293B'
ACCENT_SOFT = '#E8EDF3'
ACCENT_RING = 'rgba(71,85,105,0.30)'

# ---------- 状态反馈色 ----------
OK = '#1A7544'
WARN = '#B45309'
ERR = '#B42318'

# ---------- 语义数据色 · 三重编码（底色/字色/边框 + 角标 icon + 纹理）----------
# fill=True 表示实底（深色块、白字）；hatch=斜纹；bar=左侧竖条颜色
SEM = {
    'late':      {'bg': '#FEF6E7', 'fg': '#B45309', 'border': '#F0C66B', 'icon': 'clock'},
    'lateheavy': {'bg': '#FDECEA', 'fg': '#B42318', 'border': '#F1B0A8', 'icon': 'clock2'},
    'early':     {'bg': '#FDECEA', 'fg': '#B42318', 'border': '#F1B0A8', 'icon': 'exit'},
    'absent':    {'bg': '#D92D20', 'fg': '#FFFFFF', 'border': '#B42318', 'icon': 'cross', 'fill': True, 'hatch': True},
    'miss':      {'bg': '#E3F5E9', 'fg': '#1A7544', 'border': '#8BD3A6', 'icon': 'half'},
    'biz':       {'bg': '#DBE7FB', 'fg': '#1D4ED8', 'border': '#9EC0F5', 'icon': 'bag', 'fill': True},
    'field':     {'bg': '#E6F4F9', 'fg': '#0E6F8A', 'border': '#7CC4D8', 'icon': 'pin', 'bar': '#0891B2', 'hatch': True},
    'full':      {'bg': '#F4E9FB', 'fg': '#7E22CE', 'border': '#D9B4EF', 'icon': 'star'},
    'swap':      {'bg': '#FDECD9', 'fg': '#C2410C', 'border': '#F3C08A', 'icon': 'swap'},
    'pending':   {'bg': '#FFFFFF', 'fg': '#475569', 'border': '#475569', 'icon': 'question', 'dashed': True},
    'rest':      {'bg': '#F1F5F9', 'fg': '#94A3B8', 'border': '#E2E8F0'},
    'normal':    {'bg': '#FFFFFF', 'fg': '#0F172A', 'border': '#E2E8F0'},
    'pre':       {'bg': '#FFFFFF', 'fg': '#94A3B8', 'border': '#E2E8F0'},
    'post':      {'bg': '#FFFFFF', 'fg': '#94A3B8', 'border': '#E2E8F0'},
}
SWAP_TRI = '#F3C08A'   # 调班上班日左上三角（s-swap-line）
OT_FG = '#334155'      # 加班数字色 (s-ot-fg)

# 结论中文名（图例 / 检查器用）
LABELS = {
    'late': '迟到', 'lateheavy': '迟到较重', 'early': '早退', 'absent': '未出勤',
    'miss': '缺卡', 'biz': '公出', 'field': '外勤日', 'full': '全勤',
    'pending': '待归类', 'rest': '休息', 'normal': '正常',
}
# 图例固定顺序
LEGEND_ORDER = ['late', 'lateheavy', 'early', 'absent', 'miss', 'biz', 'field', 'full', 'pending']

# ---------- 尺寸 / 圆角 ----------
NAME_COL_W = 152
DAY_COL_W = 48
PUNCH_ROW_H = 34
OT_ROW_H = 18
HEADER_H = 44
COL_LEFT_W = 312    # 左栏待办
COL_RIGHT_W = 332   # 右栏检查器
DRAWER_W = 380      # 高级设置抽屉
R_SM, R_MD, R_LG = 6, 9, 14

FONT_STACK = '"Segoe UI","Microsoft YaHei","PingFang SC","Source Han Sans SC",system-ui,-apple-system,sans-serif'

# 动效总开关（headless/冒烟时置 False，或响应系统 reduced-motion）
MOTION = True


def build_qss():
    """全局 QSS（QSS 不支持变量，色值内联）。"""
    return f"""
* {{ font-family: {FONT_STACK}; color: {INK}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QWidget {{ background: transparent; }}
QLabel {{ background: transparent; border: none; }}
QLabel[role="h1"] {{ font-size: 22px; font-weight: 800; }}
QLabel[role="h2"] {{ font-size: 16px; font-weight: 700; }}
QLabel[role="muted"] {{ color: {INK_3}; font-size: 12px; }}

QFrame[card="1"] {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: {R_LG}px; }}

QPushButton {{
  background: {SURFACE}; color: {INK_2}; border: 1px solid {LINE_2};
  border-radius: {R_MD}px; padding: 7px 14px; font-size: 13px; font-weight: 600;
}}
QPushButton:hover {{ background: {SURFACE_3}; }}
QPushButton:disabled {{ color: {INK_3}; border-color: {LINE}; background: {SURFACE_2}; }}
QPushButton[primary="1"] {{ background: {ACCENT}; color: #FFFFFF; border: none; }}
QPushButton[primary="1"]:hover {{ background: {ACCENT_STRONG}; }}
QPushButton[primary="1"]:disabled {{ background: {INK_3}; color: {SURFACE}; }}
QPushButton[ghost="1"] {{ background: transparent; border: none; color: {INK_2}; padding: 4px 8px; }}
QPushButton[ghost="1"]:hover {{ background: {ACCENT_SOFT}; }}

QLineEdit {{
  background: {SURFACE}; border: 1px solid {LINE_2}; border-radius: {R_MD}px;
  padding: 6px 10px; font-size: 13px; selection-background-color: {ACCENT_SOFT};
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}

QComboBox {{ background: {SURFACE}; border: 1px solid {LINE_2}; border-radius: {R_SM}px; padding: 4px 8px; }}
QComboBox:focus {{ border-color: {ACCENT}; }}

QTableView {{
  background: {SURFACE}; gridline-color: {LINE}; border: 1px solid {LINE};
  border-radius: {R_LG}px; selection-background-color: transparent; outline: none;
}}
QHeaderView::section {{
  background: {SURFACE_2}; color: {INK_2}; border: none;
  border-right: 1px solid {LINE}; border-bottom: 1px solid {LINE};
  padding: 2px; font-size: 11px; font-weight: 600;
}}
QTableCornerButton::section {{ background: {SURFACE_2}; border: none; border-right: 1px solid {LINE}; border-bottom: 1px solid {LINE}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {LINE_2}; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {INK_3}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {LINE_2}; border-radius: 5px; min-width: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QPlainTextEdit {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: {R_MD}px; }}
QToolTip {{ background: {ACCENT_DEEP}; color: #FFFFFF; border: none; padding: 6px 8px; border-radius: {R_SM}px; }}

QMenu {{ background: {SURFACE}; border: 1px solid {LINE_2}; border-radius: {R_MD}px; padding: 5px; }}
QMenu::item {{ background: transparent; color: {INK}; padding: 7px 18px 7px 10px; border-radius: {R_SM}px; font-size: 13px; }}
QMenu::item:selected {{ background: {SURFACE_3}; color: {INK}; }}
QMenu::separator {{ height: 1px; background: {LINE}; margin: 4px 6px; }}

QComboBox QAbstractItemView {{ background: {SURFACE}; border: 1px solid {LINE_2}; border-radius: {R_SM}px;
  selection-background-color: {SURFACE_3}; selection-color: {INK}; outline: none; }}
QMessageBox, QDialog {{ background: {SURFACE}; }}
QInputDialog {{ background: {SURFACE}; }}
"""
