# -*- coding: utf-8 -*-
"""彩色考勤网格：QTableView + 冻结姓名列(叠加视图) + 自绘日期表头 + 底部图例 + 悬浮解释卡 + 改判菜单。
对外信号：cellSelected(gh,day)、reclassify(gh,day,val)。"""
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QRectF
import theme
import icons
from model import AttendanceModel, WEEK_CN
from delegate import AttendanceDelegate, _qc
from engine import ANOMALY_STATUS

CLS_DISP = theme.CLS_CODE
DISP_CLS = {v: k for k, v in CLS_DISP.items()}


# ---------------- 自绘日期表头 ----------------
class DateHeader(QtWidgets.QHeaderView):
    def __init__(self, model, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._m = model
        self.setSectionsClickable(False)
        self.setHighlightSections(False)
        self.setDefaultAlignment(Qt.AlignCenter)
        self.setFixedHeight(theme.HEADER_H)

    def paintSection(self, painter, rect, idx):
        painter.save()
        r = QRectF(rect)
        if idx == 0:
            painter.fillRect(r, _qc(theme.SURFACE_2))
            painter.setPen(_qc(theme.INK_2))
            f = painter.font(); f.setPixelSize(12); f.setBold(True); painter.setFont(f)
            painter.drawText(r, Qt.AlignCenter, '姓名')
        else:
            info = self._m.day_info(idx)
            is_work = info['is_work'] if info else True
            wd = info['weekday'] if info else 0
            painter.fillRect(r, _qc(theme.SURFACE_2 if is_work else theme.SURFACE_3))
            painter.setPen(_qc(theme.INK if is_work else theme.INK_3))
            f = painter.font(); f.setPixelSize(12); f.setBold(True); painter.setFont(f)
            painter.drawText(QRectF(r.left(), r.top() + 2, r.width(), 16), Qt.AlignCenter, str(idx))
            f.setPixelSize(9); f.setBold(False); painter.setFont(f)
            painter.setPen(_qc(theme.INK_3))
            painter.drawText(QRectF(r.left(), r.top() + 18, r.width(), 11), Qt.AlignCenter, '周' + WEEK_CN[wd])
            # 班/休 药丸（底色圆角）
            tag = '班' if is_work else '休'
            tbg, tfg = ('#E3F5E9', theme.OK) if is_work else ('#E8ECF2', theme.INK_2)
            pill = QRectF(r.center().x() - 10, r.top() + 28, 20, 13)
            painter.setBrush(_qc(tbg))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(pill, 3, 3)
            f.setPixelSize(8); f.setBold(True); painter.setFont(f)
            painter.setPen(_qc(tfg))
            painter.drawText(pill, Qt.AlignCenter, tag)
        painter.setPen(QtGui.QPen(_qc(theme.LINE), 1))
        painter.drawLine(r.bottomLeft(), r.bottomRight())
        painter.drawLine(r.topRight(), r.bottomRight())
        painter.restore()


# ---------------- 悬浮解释卡 ----------------
class HoverCard(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFixedWidth(232)
        self.setStyleSheet('background:%s;border:1px solid %s;border-radius:%dpx;' % (
            theme.SURFACE, theme.LINE_2, theme.R_MD))
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        self._title = QtWidgets.QLabel(''); self._title.setStyleSheet('font-weight:700;font-size:13px;')
        self._concl = QtWidgets.QLabel(''); self._concl.setStyleSheet('font-size:12px;')
        self._reason = QtWidgets.QLabel(''); self._reason.setWordWrap(True); self._reason.setStyleSheet('color:%s;font-size:12px;' % theme.INK_2)
        self._punch = QtWidgets.QLabel(''); self._punch.setStyleSheet('color:%s;font-size:11px;' % theme.INK_3)
        self._ot = QtWidgets.QLabel(''); self._ot.setStyleSheet('color:%s;font-size:11px;' % theme.INK_3)
        for w in (self._title, self._concl, self._reason, self._punch, self._ot):
            lay.addWidget(w)

    def set_cell(self, emp, day, cell, month):
        st = cell.get('status', 'rest')
        self._title.setText('%s · %d/%d' % (emp['name'], month, day))
        lab = theme.LABELS.get(st, st)
        self._concl.setText('结论：%s' % lab)
        self._concl.setStyleSheet('font-size:12px;font-weight:600;color:%s;' % theme.SEM.get(st, theme.SEM['rest'])['fg'])
        self._reason.setText(cell.get('reason', ''))
        punches = cell.get('punches') or []
        self._punch.setText('打卡：' + ('  '.join(punches) if punches else '（无）'))
        ot = cell.get('ot', 0)
        self._ot.setText('加班：%g h' % ot if ot else '')
        self._ot.setVisible(bool(ot))
        self.adjustSize()


# ---------------- 主表（含冻结列）----------------
class AttTable(QtWidgets.QTableView):
    cellSelected = QtCore.Signal(str, int)
    reclassify = QtCore.Signal(str, int, str)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._m = model
        self.setModel(model)
        self.setItemDelegate(AttendanceDelegate(self))
        self.setHorizontalHeader(DateHeader(model, self))
        self.verticalHeader().hide()
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setMouseTracking(True)
        self.setShowGrid(False)
        self._hover = HoverCard(self)
        self._hover_key = None

        # 冻结姓名列
        self.frozen = QtWidgets.QTableView(self)
        self.frozen.setModel(model)
        self.frozen.setItemDelegate(self.itemDelegate())
        self.frozen.setHorizontalHeader(DateHeader(model, self.frozen))
        self.frozen.verticalHeader().hide()
        self.frozen.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.frozen.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.frozen.setFocusPolicy(Qt.NoFocus)
        self.frozen.setShowGrid(False)
        self.frozen.setStyleSheet('QTableView{border:none;background:%s;}' % theme.SURFACE)
        self.frozen.horizontalScrollBar().setDisabled(True)
        self.frozen.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalScrollBar().valueChanged.connect(self.frozen.verticalScrollBar().setValue)
        self.frozen.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.frozen.show()
        self.viewport().stackUnder(self.frozen)

    # ---- 几何同步 ----
    def _apply_sizes(self):
        n = self._m.rowCount()
        self.setColumnWidth(0, theme.NAME_COL_W)
        for c in range(1, self._m.columnCount()):
            self.setColumnWidth(c, theme.DAY_COL_W)
        for r in range(n):
            h = theme.PUNCH_ROW_H if r % 2 == 0 else theme.OT_ROW_H
            self.setRowHeight(r, h)
        # 名格跨两行
        for i in range(n // 2):
            self.setSpan(i * 2, 0, 2, 1)
            self.frozen.setSpan(i * 2, 0, 2, 1)
        for c in range(1, self._m.columnCount()):
            self.frozen.setColumnHidden(c, True)
        self.frozen.setColumnWidth(0, theme.NAME_COL_W)
        for r in range(n):
            self.frozen.setRowHeight(r, theme.PUNCH_ROW_H if r % 2 == 0 else theme.OT_ROW_H)
        self._update_frozen_geom()

    def set_row_hidden(self, row, hidden):
        self.setRowHidden(row, hidden)
        self.frozen.setRowHidden(row, hidden)

    def _update_frozen_geom(self):
        self.frozen.setGeometry(self.frameWidth(), self.frameWidth(),
                                theme.NAME_COL_W + self.frameWidth(),
                                self.viewport().height() + self.horizontalHeader().height())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_frozen_geom()

    def scrollTo(self, index, hint=QtWidgets.QAbstractItemView.EnsureVisible):
        if index.column() == 0:
            return
        super().scrollTo(index, hint)

    # ---- 交互 ----
    def mouseMoveEvent(self, e):
        idx = self.indexAt(e.pos())
        info = self._m.cell_at(idx)
        if info and info['kind'] == 'cell' and info['cell'].get('status') not in ('rest', 'pre', 'post'):
            key = (info['emp']['gh'], info['day'])
            if key != self._hover_key:
                self._hover_key = key
                self._hover.set_cell(info['emp'], info['day'], info['cell'], self._m_month())
            gp = e.globalPosition().toPoint() if hasattr(e, 'globalPosition') else e.globalPos()
            self._place_hover(gp)
            self._hover.show()
        else:
            self._hover_key = None
            self._hover.hide()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self._hover.hide()
        self._hover_key = None
        super().leaveEvent(e)

    def _m_month(self):
        return getattr(self._m, '_month', 0)

    def _place_hover(self, gp):
        scr = self.screen().availableGeometry() if self.screen() else None
        x, y = gp.x() + 16, gp.y() + 12
        self._hover.adjustSize()
        if scr and x + self._hover.width() > scr.right():
            x = gp.x() - self._hover.width() - 12
        if scr and y + self._hover.height() > scr.bottom():
            y = gp.y() - self._hover.height() - 12
        self._hover.move(x, y)

    def mousePressEvent(self, e):
        idx = self.indexAt(e.pos())
        info = self._m.cell_at(idx)
        if info and info['kind'] == 'cell':
            st = info['cell'].get('status')
            if st in ('rest', 'pre', 'post'):
                return
            gh, day = info['emp']['gh'], info['day']
            self._m.set_active(gh, day)
            self.cellSelected.emit(gh, day)
            if st == 'pending':
                self._show_reclass(e, gh, day, info['cell'].get('suggest', 'G'))
            return
        super().mousePressEvent(e)

    def _show_reclass(self, e, gh, day, suggest):
        from widgets import swatch_pixmap
        cls_kind = {'G': 'miss', 'B': 'biz', 'R': 'absent'}
        menu = QtWidgets.QMenu(self)
        for code in ('G', 'B', 'R'):
            label = CLS_DISP[code] + ('     建议' if code == suggest else '')
            act = menu.addAction(QtGui.QIcon(swatch_pixmap(cls_kind[code])), label)
            act.setData(code)
        gp = e.globalPosition().toPoint() if hasattr(e, 'globalPosition') else e.globalPos()
        chosen = menu.exec(gp)
        if chosen:
            self.reclassify.emit(gh, day, chosen.data())


# ---------------- 图例条 ----------------
class LegendBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(14)
        for st in theme.LEGEND_ORDER:
            sem = theme.SEM[st]
            item = QtWidgets.QWidget()
            il = QtWidgets.QHBoxLayout(item)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(5)
            sw = QtWidgets.QLabel()
            sw.setFixedSize(14, 14)
            sw.setStyleSheet('background:%s;border:1px solid %s;border-radius:3px;' % (sem['bg'], sem['border']))
            if sem.get('icon'):
                sw.setPixmap(icons.badge_pixmap(sem['icon'], sem['fg'] if not sem.get('fill') else '#FFFFFF', 14))
            lb = QtWidgets.QLabel(theme.LABELS[st])
            lb.setStyleSheet('color:%s;font-size:11px;' % theme.INK_2)
            il.addWidget(sw)
            il.addWidget(lb)
            lay.addWidget(item)
        lay.addStretch(1)


# ---------------- 中栏顶部：搜索 / 筛选 / 跳异常 ----------------
class CenterHeader(QtWidgets.QWidget):
    searchChanged = QtCore.Signal(str)
    filterChanged = QtCore.Signal(str)
    nextAnomaly = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('centerHeader')
        self.setStyleSheet('QWidget#centerHeader{background:%s;border-bottom:1px solid %s;}' % (theme.SURFACE, theme.LINE))
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(14, 9, 14, 9)
        lay.setSpacing(10)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText('🔍  搜索姓名 / 工号 / 职位')
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(200)
        self.search.setStyleSheet('QLineEdit{background:%s;}' % theme.SURFACE_2)
        self.search.textChanged.connect(self.searchChanged)
        lay.addWidget(self.search)
        # 分段控件
        seg = QtWidgets.QFrame()
        seg.setObjectName('seg')
        seg.setStyleSheet('QFrame#seg{background:%s;border:1px solid %s;border-radius:8px;}' % (theme.SURFACE_2, theme.LINE))
        sl = QtWidgets.QHBoxLayout(seg)
        sl.setContentsMargins(2, 2, 2, 2)
        sl.setSpacing(2)
        self._btns = {}
        self._labels = {'all': '全部', 'anomaly': '有异常', 'pending': '待归类'}
        for key in ('all', 'anomaly', 'pending'):
            b = QtWidgets.QPushButton(self._labels[key])
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=0, k=key: self._pick(k))
            self._btns[key] = b
            sl.addWidget(b)
        self._btns['all'].setChecked(True)
        lay.addWidget(seg)
        lay.addStretch(1)
        self.nbtn = QtWidgets.QPushButton('⤼  跳到下一个异常')
        self.nbtn.clicked.connect(self.nextAnomaly)
        lay.addWidget(self.nbtn)
        self._restyle()

    def _pick(self, key):
        for k, b in self._btns.items():
            b.setChecked(k == key)
        self._restyle()
        self.filterChanged.emit(key)

    def set_counts(self, anomaly, pending):
        self._btns['anomaly'].setText('有异常 %d' % anomaly)
        self._btns['pending'].setText('待归类 %d' % pending)

    def _restyle(self):
        for b in self._btns.values():
            on = b.isChecked()
            if on:
                css = 'background:%s;color:%s;' % (theme.SURFACE, theme.INK)
            else:
                css = 'background:transparent;color:%s;' % theme.INK_3
            b.setStyleSheet('QPushButton{border:none;border-radius:6px;padding:5px 11px;'
                            'font-size:12px;font-weight:600;%s}' % css)


# ---------------- 网格容器 ----------------
class AttGrid(QtWidgets.QWidget):
    cellSelected = QtCore.Signal(str, int)
    reclassify = QtCore.Signal(str, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = AttendanceModel(self)
        self._data = None
        self._search = ''
        self._filter = 'all'
        self._anom_list = []
        self._anom_idx = 0
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.header = CenterHeader()
        self.header.searchChanged.connect(self._on_search)
        self.header.filterChanged.connect(self._on_filter)
        self.header.nextAnomaly.connect(self.goto_next_anomaly)
        lay.addWidget(self.header)
        self.table = AttTable(self.model)
        self.table.cellSelected.connect(self.cellSelected)
        self.table.reclassify.connect(self.reclassify)
        lay.addWidget(self.table, 1)
        lay.addWidget(LegendBar())

    def set_data(self, data, search='', filt='all'):
        self._data = data
        self.model._month = data['month']
        self.model.set_data(data)
        self.table._apply_sizes()
        self.header.set_counts(len(data['stats']['anomaly_set']), data['stats']['pending'])
        self.apply_filter(self._search, self._filter)

    def _on_search(self, text):
        self._search = text
        self.apply_filter(text, self._filter)

    def _on_filter(self, key):
        self._filter = key
        self.apply_filter(self._search, key)

    def _emp_visible(self, e, search, filt):
        if search:
            hay = (e['name'] + e['gh'] + (e.get('pos') or ''))
            if search not in hay:
                return False
        if filt == 'anomaly':
            return e['gh'] in self._data['stats']['anomaly_set']
        if filt == 'pending':
            return any(c.get('status') == 'pending' for c in e['cells'].values())
        return True

    def apply_filter(self, search, filt):
        self._search, self._filter = search, filt
        if not self._data:
            return
        for i, e in enumerate(self.model.emps):
            vis = self._emp_visible(e, search, filt)
            self.table.set_row_hidden(i * 2, not vis)
            self.table.set_row_hidden(i * 2 + 1, not vis)

    def goto_next_anomaly(self):
        if not self._data:
            return
        anoms = []
        for e in self.model.emps:
            if not self._emp_visible(e, self._search, self._filter):
                continue
            for day in sorted(e['cells']):
                if e['cells'][day].get('status') in ANOMALY_STATUS:
                    anoms.append((e['gh'], day))
        if not anoms:
            return
        self._anom_idx %= len(anoms)
        gh, day = anoms[self._anom_idx]
        self._anom_idx += 1
        self.locate(gh, day)
        self.cellSelected.emit(gh, day)

    def locate(self, gh, day):
        self.model.set_active(gh, day)
        idx = self.model.index_for(gh, day, punch_row=True)
        if idx.isValid():
            self.table.scrollTo(idx, QtWidgets.QAbstractItemView.PositionAtCenter)
