# -*- coding: utf-8 -*-
"""考勤结论角标图标（QPainter 矢量自绘，不依赖字体字形）。
供 delegate 在单元格角落绘制，也可生成 QPixmap 用于图例/检查器。
kind ∈ clock clock2 exit cross half bag pin star question"""
import math
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QRectF, QPointF, Qt


def paint_badge(painter, rect, kind, color):
    """在 rect（QRect/QRectF）内绘制 kind 角标，主色 color（hex 或 QColor）。"""
    if isinstance(color, str):
        color = QtGui.QColor(color)
    r = QRectF(rect)
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    pen = QtGui.QPen(color)
    w = max(1.0, r.width() / 9.0)
    pen.setWidthF(w)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    cx, cy = r.center().x(), r.center().y()
    rad = min(r.width(), r.height()) / 2.0

    if kind in ('clock', 'clock2'):
        cr = rad * 0.82
        circ = QRectF(cx - cr, cy - cr, cr * 2, cr * 2)
        if kind == 'clock2':
            painter.setBrush(color)
            painter.drawEllipse(circ)
            painter.setPen(QtGui.QPen(QtGui.QColor('#FFFFFF'), w))
        else:
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(circ)
        # 指针：12 点 + 3 点
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - cr * 0.55))
        painter.drawLine(QPointF(cx, cy), QPointF(cx + cr * 0.5, cy))
    elif kind == 'exit':
        # 向右的箭头（离开）
        painter.drawLine(QPointF(cx - rad * 0.7, cy), QPointF(cx + rad * 0.6, cy))
        painter.drawLine(QPointF(cx + rad * 0.1, cy - rad * 0.5), QPointF(cx + rad * 0.6, cy))
        painter.drawLine(QPointF(cx + rad * 0.1, cy + rad * 0.5), QPointF(cx + rad * 0.6, cy))
    elif kind == 'cross':
        d = rad * 0.6
        painter.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
        painter.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
    elif kind == 'half':
        cr = rad * 0.82
        circ = QRectF(cx - cr, cy - cr, cr * 2, cr * 2)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(circ)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        # 左半填充（90° 起，逆时针 180°）
        painter.drawPie(circ, 90 * 16, 180 * 16)
    elif kind == 'bag':
        bw, bh = rad * 1.3, rad * 1.0
        body = QRectF(cx - bw / 2, cy - bh / 2 + rad * 0.18, bw, bh)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(body, w, w)
        # 把手
        painter.setBrush(Qt.NoBrush)
        painter.setPen(pen)
        hw = rad * 0.5
        painter.drawArc(QRectF(cx - hw, cy - bh / 2 - rad * 0.05, hw * 2, hw), 0, 180 * 16)
    elif kind == 'pin':
        # 水滴定位针
        path = QtGui.QPainterPath()
        top = QPointF(cx, cy - rad * 0.85)
        path.moveTo(cx, cy + rad * 0.85)
        path.cubicTo(cx - rad * 1.1, cy - rad * 0.1, cx - rad * 0.5, top.y(), cx, top.y())
        path.cubicTo(cx + rad * 0.5, top.y(), cx + rad * 1.1, cy - rad * 0.1, cx, cy + rad * 0.85)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        painter.setBrush(QtGui.QColor('#FFFFFF'))
        dr = rad * 0.26
        painter.drawEllipse(QRectF(cx - dr, cy - rad * 0.28 - dr, dr * 2, dr * 2))
    elif kind == 'star':
        path = QtGui.QPainterPath()
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = rad * (0.92 if i % 2 == 0 else 0.42)
            pt = QPointF(cx + rr * math.cos(ang), cy + rr * math.sin(ang))
            path.lineTo(pt) if i else path.moveTo(pt)
        path.closeSubpath()
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
    elif kind == 'question':
        f = painter.font()
        f.setPixelSize(int(rad * 1.7))
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QtGui.QPen(color))
        painter.drawText(r, Qt.AlignCenter, '?')
    painter.restore()


def badge_pixmap(kind, color, size=14):
    """生成角标 QPixmap，用于 QLabel（图例/检查器）。"""
    pm = QtGui.QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QtGui.QPainter(pm)
    paint_badge(p, QRectF(0, 0, size, size), kind, color)
    p.end()
    return pm
