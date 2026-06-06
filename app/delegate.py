# -*- coding: utf-8 -*-
"""考勤单元自绘委托：底色 + 45°斜纹 + 左竖条 + 角标 + 双行文本 + 待定虚线 + 选中描边 + 调班三角 + 全勤紫名。
三重编码（色+角标+纹理）色弱友好。所有颜色取自 theme.SEM。"""
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QRectF, QPointF
import theme
import icons


def _qc(hex_):
    return QtGui.QColor(hex_)


def _blend(hex_, t, other='#FFFFFF'):
    """hex_ 与 other 按 (1-t):t 混合（t 越大越接近 other）。"""
    a, b = _qc(hex_), _qc(other)
    return QtGui.QColor(int(a.red() * (1 - t) + b.red() * t),
                        int(a.green() * (1 - t) + b.green() * t),
                        int(a.blue() * (1 - t) + b.blue() * t))


def _tint(bg):
    """加班副行底色：白/灰 → 次表面；其余 → 与白混合 55%。"""
    if bg.upper() in ('#FFFFFF', theme.SURFACE_3.upper(), theme.SURFACE.upper()):
        return _qc(theme.SURFACE_2)
    return _blend(bg, 0.55)


_FILL_STATUS = ('absent', 'biz')   # 实底（白字）


class AttendanceDelegate(QtWidgets.QStyledItemDelegate):
    BADGE_STATUSES = {'late', 'lateheavy', 'early', 'absent', 'miss', 'biz', 'field', 'pending'}

    def paint(self, painter, option, index):
        m = index.model()
        info = m.cell_at(index)
        if info is None:
            return
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        rect = QRectF(option.rect)
        if info['kind'] == 'name':
            self._paint_name(painter, rect, info)
        else:
            self._paint_cell(painter, rect, info)
        painter.restore()

    # ---------------- 姓名格（冻结列）----------------
    def _paint_name(self, painter, rect, info):
        emp = info['emp']
        full = info['full']
        bg = _qc(theme.SEM['full']['bg']) if full else _qc(theme.SURFACE)
        painter.fillRect(rect, bg)
        painter.setPen(QtGui.QPen(_qc(theme.LINE), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        inner = rect.adjusted(10, 0, -8, 0)
        # 姓名
        painter.setPen(_qc(theme.SEM['full']['fg'] if full else theme.INK))
        f = painter.font()
        f.setPixelSize(13)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(QRectF(inner.left(), inner.top(), inner.width(), inner.height() / 2),
                         Qt.AlignLeft | Qt.AlignBottom, emp['name'])
        # 工号 + 职位
        f.setPixelSize(10)
        f.setBold(False)
        painter.setFont(f)
        painter.setPen(_qc(theme.INK_3))
        sub = '%s · %s' % (emp['gh'], emp.get('pos') or '')
        painter.drawText(QRectF(inner.left(), inner.center().y(), inner.width(), inner.height() / 2),
                         Qt.AlignLeft | Qt.AlignTop, sub)
        # 全勤星
        if full:
            br = QRectF(rect.right() - 20, rect.top() + 6, 13, 13)
            icons.paint_badge(painter, br, 'star', theme.SEM['full']['fg'])

    # ---------------- 日格 ----------------
    def _paint_cell(self, painter, rect, info):
        cell = info['cell']
        st = cell.get('status', 'rest')
        punch = info['punch_row']
        sem = theme.SEM.get(st, theme.SEM['rest'])
        bg = _qc(sem['bg'])
        if not punch:
            bg = _tint(sem['bg'])
        painter.fillRect(rect, bg)

        # 斜纹（absent / field）
        if sem.get('hatch') and punch:
            self._hatch(painter, rect, _qc(sem['border']))
        # 左竖条（field）
        if sem.get('bar') and punch:
            painter.fillRect(QRectF(rect.left(), rect.top(), 3, rect.height()), _qc(sem['bar']))

        # 边框
        pen = QtGui.QPen(_qc(sem['border']), 1)
        if sem.get('dashed'):
            pen.setStyle(Qt.DashLine)
            pen.setColor(_qc(theme.ACCENT))
            pen.setWidthF(1.4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        # 文本
        fg = _qc('#FFFFFF') if (st in _FILL_STATUS and punch) else _qc(sem['fg'])
        if not punch:
            fg = _qc(theme.INK_2)
        self._draw_text(painter, rect, cell, st, punch, fg)

        # 角标（打卡行）
        if punch and st in self.BADGE_STATUSES and sem.get('icon'):
            badge_color = _qc('#FFFFFF') if st in _FILL_STATUS else _qc(sem['fg'])
            icons.paint_badge(painter, QRectF(rect.right() - 13, rect.top() + 2, 10, 10), sem['icon'], badge_color)
        # 调班三角（左上）
        if punch and cell.get('swap'):
            tri = QtGui.QPolygonF([QPointF(rect.left(), rect.top()),
                                   QPointF(rect.left() + 11, rect.top()),
                                   QPointF(rect.left(), rect.top() + 11)])
            painter.setBrush(_qc(theme.SWAP_TRI))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(tri)

        # 选中描边（覆盖打卡+加班两行视觉）
        if info.get('active'):
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QtGui.QPen(_qc(theme.ACCENT), 2))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))

    def _hatch(self, painter, rect, color):
        painter.save()
        painter.setClipRect(rect)
        pen = QtGui.QPen(color, 1)
        painter.setPen(pen)
        step = 5
        x = rect.left() - rect.height()
        while x < rect.right():
            painter.drawLine(QPointF(x, rect.bottom()), QPointF(x + rect.height(), rect.top()))
            x += step
        painter.restore()

    def _draw_text(self, painter, rect, cell, st, punch, fg):
        f = painter.font()
        f.setPixelSize(9)
        painter.setPen(fg)
        if not punch:
            ot = cell.get('ot', 0)
            if ot and ot > 0:
                f.setBold(True)
                painter.setFont(f)
                txt = str(int(ot)) if ot == int(ot) else ('%g' % ot)
                painter.drawText(rect, Qt.AlignCenter, txt)
            elif st not in ('rest', 'pre', 'post'):
                dot = _qc(theme.INK_3)
                dot.setAlphaF(0.25)
                painter.setPen(dot)
                painter.setFont(f)
                painter.drawText(rect, Qt.AlignCenter, '·')
            return
        # 打卡行
        if st in ('pre', 'post'):
            return
        if st == 'rest':
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignCenter, '休')
            return
        if st == 'absent':
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignCenter, '缺')
            return
        if st == 'biz':
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignCenter, '公出')
            return
        in_t = cell.get('in') or ''
        out_t = cell.get('out') or ''
        if st == 'miss':
            top, bot, bold_top, bold_bot = (in_t or '—'), '缺卡', False, False
        elif st == 'pending':
            top, bot, bold_top, bold_bot = (in_t or '—'), '待定', False, False
        else:
            top, bot = in_t, out_t
            bold_top = (st in ('late', 'lateheavy'))
            bold_bot = (st == 'early')
        top_rect = QRectF(rect.left(), rect.top(), rect.width(), rect.height() / 2)
        bot_rect = QRectF(rect.left(), rect.center().y(), rect.width(), rect.height() / 2)
        f.setBold(bold_top)
        painter.setFont(f)
        painter.drawText(top_rect, Qt.AlignCenter, top)
        f.setBold(bold_bot)
        painter.setFont(f)
        painter.drawText(bot_rect, Qt.AlignCenter, bot)
