# -*- coding: utf-8 -*-
"""通用 UI 小部件：Stepper（步骤条）· Banner（提示条）· Toast · ProgressRing · Chip · Card 辅助。
动效在 M16 增强，这里先做静态/即时版本。"""
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QRectF, QTimer, QPropertyAnimation, QPoint, QEasingCurve
import theme
import icons

EASE = QEasingCurve.OutCubic


def paint_swatch(p, w, h, kind):
    """在 painter 上绘制 26×18 风格色块（kind=语义状态）。"""
    sem = theme.SEM.get(kind)
    if not sem:
        return
    p.setRenderHint(QtGui.QPainter.Antialiasing, True)
    r = QRectF(0.5, 0.5, w - 1, h - 1)
    p.setBrush(QtGui.QColor(sem['bg']))
    p.setPen(QtGui.QPen(QtGui.QColor(sem['border']), 1))
    p.drawRoundedRect(r, 4, 4)
    if kind == 'field':
        p.save()
        p.setClipRect(r)
        p.setPen(QtGui.QPen(QtGui.QColor(theme.SEM['field']['bar']), 1))
        x = -h
        while x < w:
            p.drawLine(QtCore.QPointF(x, h), QtCore.QPointF(x + h, 0))
            x += 5
        p.restore()
        p.fillRect(QRectF(0.5, 0.5, 3, h - 1), QtGui.QColor(theme.SEM['field']['bar']))
    if sem.get('icon'):
        icons.paint_badge(p, QRectF(w / 2 - 5, h / 2 - 5, 10, 10), sem['icon'], sem['fg'])


def swatch_pixmap(kind, w=26, h=18):
    pm = QtGui.QPixmap(w, h)
    pm.fill(Qt.transparent)
    p = QtGui.QPainter(pm)
    paint_swatch(p, w, h, kind)
    p.end()
    return pm


class Swatch(QtWidgets.QWidget):
    """语义色块 26×18：底色+边框+角标，field 加左竖条+斜纹。对应原型 <Swatch>。"""
    def __init__(self, kind, bar=False, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(26, 18)

    def set_kind(self, kind, bar=False):
        self.kind = kind
        self.update()

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        paint_swatch(p, self.width(), self.height(), self.kind)
        p.end()


def make_card(parent=None):
    f = QtWidgets.QFrame(parent)
    f.setProperty('card', '1')
    return f


def h2(text):
    lb = QtWidgets.QLabel(text)
    lb.setStyleSheet('border:none;background:transparent;font-size:16px;font-weight:700;color:%s;' % theme.INK)
    return lb


def muted(text):
    lb = QtWidgets.QLabel(text)
    lb.setStyleSheet('border:none;background:transparent;font-size:12px;color:%s;' % theme.INK_3)
    return lb


class Chip(QtWidgets.QLabel):
    """小标签：底色软、文字主色。用于计数/状态。"""
    def __init__(self, text, fg=theme.INK_2, bg=theme.SURFACE_3, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            'background:%s; color:%s; border-radius:%dpx; padding:2px 8px; font-size:12px; font-weight:600;'
            % (bg, fg, theme.R_SM))
        self.setAlignment(Qt.AlignCenter)


class _Step(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, n, label, parent=None):
        super().__init__(parent)
        self.n = n
        self.setObjectName('stepPill')
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(8, 6, 12, 6)
        h.setSpacing(8)
        self.circle = QtWidgets.QLabel(str(n))
        self.circle.setFixedSize(20, 20)
        self.circle.setAlignment(Qt.AlignCenter)
        self.txt = QtWidgets.QLabel(label)
        h.addWidget(self.circle)
        h.addWidget(self.txt)

    def mousePressEvent(self, e):
        if self.isEnabled():
            self.clicked.emit()

    def set_style(self, active, done, reachable):
        self.setCursor(Qt.PointingHandCursor if reachable else Qt.ArrowCursor)
        self.setEnabled(reachable)
        if active:
            pill = theme.ACCENT_SOFT
            cbg, cfg, cbd = theme.ACCENT, '#FFFFFF', theme.ACCENT
            tcol, tw = theme.ACCENT_STRONG, 650
        elif done:
            pill = 'transparent'
            cbg, cfg, cbd = theme.ACCENT_SOFT, theme.ACCENT_STRONG, theme.ACCENT_SOFT
            tcol, tw = theme.INK_2, 500
        else:
            pill = 'transparent'
            cbg, cfg, cbd = theme.SURFACE_3, (theme.INK_2 if reachable else theme.INK_3), theme.LINE
            tcol, tw = (theme.INK_2 if reachable else theme.INK_3), 500
        self.setStyleSheet('QFrame#stepPill{background:%s;border-radius:13px;}' % pill)
        self.circle.setText('✓' if done else str(self.n))
        self.circle.setStyleSheet(
            'QLabel{background:%s;color:%s;border:1px solid %s;border-radius:10px;font-size:11px;font-weight:700;}'
            % (cbg, cfg, cbd))
        self.txt.setStyleSheet('QLabel{background:transparent;color:%s;font-size:12.5px;font-weight:%d;}' % (tcol, tw))


class Chip2(QtWidgets.QLabel):
    """顶栏信息药丸：surface-2 底 + 边框圆角。tone ∈ default/ok/accent。"""
    def __init__(self, text='', tone='default', mono=False, parent=None):
        super().__init__(text, parent)
        self._mono = mono
        self.set_tone(tone)

    def set_tone(self, tone):
        col = {'ok': theme.OK, 'accent': theme.ACCENT_STRONG}.get(tone, theme.INK_2)
        self.setStyleSheet(
            'QLabel{background:%s;border:1px solid %s;border-radius:7px;padding:5px 9px;'
            'font-size:11.5px;font-weight:600;color:%s;}' % (theme.SURFACE_2, theme.LINE, col))


class Stepper(QtWidgets.QWidget):
    """三步：准备 / 复核与决策 / 完成。序号圈+标签药丸+连接线，max_step 门控。"""
    stepClicked = QtCore.Signal(int)
    TITLES = ['准备', '复核与决策', '完成']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cur = 0
        self._max = 0
        self._steps = []
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        for i, t in enumerate(self.TITLES):
            s = _Step(i + 1, t)
            s.clicked.connect(lambda idx=i: self._on_click(idx))
            self._steps.append(s)
            lay.addWidget(s)
            if i < len(self.TITLES) - 1:
                line = QtWidgets.QFrame()
                line.setFixedSize(16, 1)
                line.setStyleSheet('background:%s;' % theme.LINE_2)
                lay.addWidget(line)
        lay.addStretch(1)
        self._refresh()

    def _on_click(self, idx):
        if idx <= self._max:
            self.stepClicked.emit(idx)

    def set_state(self, cur, mx):
        self._cur, self._max = cur, mx
        self._refresh()

    def _refresh(self):
        for i, s in enumerate(self._steps):
            s.set_style(active=(i == self._cur), done=(i < self._cur), reachable=(i <= self._max))


class Banner(QtWidgets.QFrame):
    """提示条：kind ∈ ok/warn/err/info。"""
    COLORS = {
        'ok':   (theme.OK,  '#E3F5E9'),
        'warn': (theme.WARN, '#FEF6E7'),
        'err':  (theme.ERR, '#FDECEA'),
        'info': (theme.ACCENT, theme.ACCENT_SOFT),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lb = QtWidgets.QLabel('')
        self._lb.setWordWrap(True)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(12, 9, 12, 9)
        lay.addWidget(self._lb)
        self.set_msg('info', '')

    def set_msg(self, kind, text):
        fg, bg = self.COLORS.get(kind, self.COLORS['info'])
        self.setStyleSheet('QFrame{background:%s;border:none;border-radius:%dpx;}' % (bg, theme.R_MD))
        self._lb.setStyleSheet('color:%s;font-size:13px;font-weight:600;background:transparent;' % fg)
        self._lb.setText(text)
        self.setVisible(bool(text))


class Toast(QtWidgets.QLabel):
    """底部居中轻提示，淡入+上移 200ms，2.2s 自动消失。"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet(
            'background:%s;color:#FFFFFF;border-radius:%dpx;padding:8px 16px;font-size:13px;font-weight:600;'
            % (theme.ACCENT_DEEP, theme.R_MD))
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        self._eff = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._fade = QPropertyAnimation(self._eff, b'opacity', self)
        self._slide = QPropertyAnimation(self, b'pos', self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_msg(self, text, ms=2200):
        self.setText('✓  ' + text)
        self.adjustSize()
        tx, ty = self._target()
        self.move(tx, ty)
        self.show()
        self.raise_()
        if theme.MOTION:
            self._eff.setOpacity(0.0)
            self._fade.stop(); self._fade.setDuration(200); self._fade.setStartValue(0.0); self._fade.setEndValue(1.0)
            self._fade.start()
            self._slide.stop(); self._slide.setDuration(200); self._slide.setEasingCurve(EASE)
            self._slide.setStartValue(QPoint(tx, ty + 8)); self._slide.setEndValue(QPoint(tx, ty))
            self._slide.start()
        else:
            self._eff.setOpacity(1.0)
        self._timer.start(ms)

    def _target(self):
        p = self.parent()
        if not p:
            return 0, 0
        return max(0, (p.width() - self.width()) // 2), max(0, p.height() - self.height() - 28)

    def _reposition(self):
        tx, ty = self._target()
        self.move(tx, ty)


class ProgressRing(QtWidgets.QWidget):
    """进度环：显示 done/total，弧长 400ms 增长动画。"""
    def __init__(self, parent=None, size=56):
        super().__init__(parent)
        self._done = 0
        self._total = 0
        self._frac = 0.0
        self.setFixedSize(size, size)
        self._anim = QPropertyAnimation(self, b'frac', self)
        self._anim.setDuration(400)
        self._anim.setEasingCurve(EASE)

    def set_progress(self, done, total):
        self._done, self._total = done, total
        target = (done / total) if total else 0.0
        if theme.MOTION and self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._frac)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._frac = target
            self.update()

    def get_frac(self):
        return self._frac

    def set_frac(self, v):
        self._frac = v
        self.update()

    frac = QtCore.Property(float, get_frac, set_frac)

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        p.setPen(QtGui.QPen(QtGui.QColor(theme.LINE), 4))
        p.drawEllipse(rect)
        if self._total:
            p.setPen(QtGui.QPen(QtGui.QColor(theme.ACCENT), 4, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, 90 * 16, -int(360 * 16 * self._frac))
        p.setPen(QtGui.QColor(theme.INK))
        f = p.font()
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        txt = ('%d' % (self._total - self._done)) if self._total else '—'
        p.drawText(self.rect(), Qt.AlignCenter, txt)
        p.end()
