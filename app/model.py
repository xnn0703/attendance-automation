# -*- coding: utf-8 -*-
"""考勤表数据模型：QAbstractTableModel。
列：0=姓名(冻结)，1..days=每天。行：每人占 2 行（偶=打卡行，奇=加班行）。
delegate 通过 cell_at(index) 取该格的结构化信息绘制。"""
from PySide6 import QtCore
from PySide6.QtCore import Qt, QModelIndex
import theme

WEEK_CN = '一二三四五六日'


class AttendanceModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emps = []
        self.cal = {}
        self.days = 0
        self.active = None          # (gh, day)
        self.full_set = set()

    def set_data(self, data):
        self.beginResetModel()
        self.emps = data['employees']
        self.cal = {c['day']: c for c in data['calendar']}
        self.days = data['days']
        self.full_set = data['stats']['full_set']
        self.endResetModel()

    def set_active(self, gh, day):
        self.active = (gh, day) if gh else None
        # 触发整表重绘选中态（轻量）
        if self.emps:
            self.dataChanged.emit(self.index(0, 0),
                                  self.index(self.rowCount() - 1, self.columnCount() - 1),
                                  [Qt.DisplayRole])

    # ---- 维度 ----
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.emps) * 2

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else (1 + self.days)

    def data(self, index, role=Qt.DisplayRole):
        return None              # 全部由 delegate 自绘

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return None              # 水平表头由 DateHeader 自绘；垂直表头隐藏

    # ---- 取格 ----
    def employee_at_row(self, row):
        i = row // 2
        return self.emps[i] if 0 <= i < len(self.emps) else None

    def is_active(self, emp, day):
        return self.active is not None and emp is not None and emp['gh'] == self.active[0] and day == self.active[1]

    def cell_at(self, index):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        emp = self.employee_at_row(row)
        if emp is None:
            return None
        punch_row = (row % 2 == 0)
        if col == 0:
            return {'kind': 'name', 'emp': emp, 'punch_row': punch_row, 'full': emp['full']}
        day = col
        cell = emp['cells'].get(day, {'status': 'pre'})
        return {'kind': 'cell', 'emp': emp, 'day': day, 'punch_row': punch_row,
                'cell': cell, 'cal': self.cal.get(day), 'active': self.is_active(emp, day)}

    def index_for(self, gh, day, punch_row=True):
        """返回某人某天的 QModelIndex（用于定位/滚动）。"""
        for i, e in enumerate(self.emps):
            if e['gh'] == gh:
                return self.index(i * 2 + (0 if punch_row else 1), day)
        return QModelIndex()

    def day_info(self, day):
        return self.cal.get(day)
