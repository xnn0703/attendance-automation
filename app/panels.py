# -*- coding: utf-8 -*-
"""三阶段面板：ReadyView(就绪) · TodoPanel(左) · Inspector(右) · AdvancedDrawer · Workbench · Dashboard(完成)。
严格对照 docs/attendance-automation/handoff/prototype/*.jsx 的视觉与交互。"""
import datetime
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
import theme
import engine
from widgets import make_card, h2, muted, Banner, ProgressRing, Swatch

WEEK_CN = '一二三四五六日'
CLS_DISP = {'G': '缺卡', 'B': '公出', 'R': '未出勤'}
DISP_CLS = {v: k for k, v in CLS_DISP.items()}
CLS_KIND = {'G': 'miss', 'B': 'biz', 'R': 'absent'}   # 归类码 → 语义色 kind


def _lab(text, size=12, weight=400, color=theme.INK, mono=False):
    lb = QtWidgets.QLabel(text)
    lb.setStyleSheet('color:%s;font-size:%spx;font-weight:%d;background:transparent;border:none;' % (color, size, weight))
    return lb


def _section_head(title, count, total):
    w = QtWidgets.QWidget()
    h = QtWidgets.QHBoxLayout(w)
    h.setContentsMargins(2, 2, 2, 0)
    h.setSpacing(7)
    h.addWidget(_lab(title, 12, 700, theme.INK))
    h.addStretch(1)
    h.addWidget(_lab('%d/%d' % (count, total), 11, 600, theme.INK_3))
    return w


# ============================ 阶段① 就绪页 ============================
class ReadyView(QtWidgets.QWidget):
    dirChosen = QtCore.Signal(str)
    startReview = QtCore.Signal()
    REC_ROWS = [('原表（钉钉打卡）', 'yuan'), ('员工花名册', 'ros'), ('调班表', 'tiao')]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        host = QtWidgets.QWidget()
        hl = QtWidgets.QVBoxLayout(host)
        hl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.card = make_card()
        self.card.setFixedWidth(620)
        cl = QtWidgets.QVBoxLayout(self.card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # 头部
        head = QtWidgets.QFrame()
        head.setObjectName('readyHead')
        head.setStyleSheet('QFrame#readyHead{background:%s;border-top-left-radius:%dpx;border-top-right-radius:%dpx;'
                           'border-bottom:1px solid %s;}' % (theme.SURFACE_2, theme.R_LG, theme.R_LG, theme.LINE))
        hh = QtWidgets.QHBoxLayout(head)
        hh.setContentsMargins(24, 18, 24, 18)
        hh.setSpacing(14)
        self.month_box = QtWidgets.QLabel('—')
        self.month_box.setFixedSize(46, 46)
        self.month_box.setAlignment(Qt.AlignCenter)
        self.month_box.setStyleSheet('background:%s;color:#fff;border-radius:13px;font-size:18px;font-weight:800;' % theme.ACCENT)
        hh.addWidget(self.month_box)
        tcol = QtWidgets.QVBoxLayout()
        tcol.setSpacing(2)
        self.title_lb = _lab('准备数据', 16, 700)
        self.dir_lb = _lab('请选择含三张输入表的文件夹', 12, 400, theme.INK_3)
        tcol.addWidget(self.title_lb)
        tcol.addWidget(self.dir_lb)
        hh.addLayout(tcol, 1)
        pcol = QtWidgets.QVBoxLayout()
        pcol.setSpacing(0)
        self.people_lb = QtWidgets.QLabel('—')
        self.people_lb.setAlignment(Qt.AlignRight)
        self.people_lb.setStyleSheet('font-size:26px;font-weight:800;color:%s;' % theme.INK)
        pcol.addWidget(self.people_lb)
        pl = _lab('纳入人数', 11, 400, theme.INK_3)
        pl.setAlignment(Qt.AlignRight)
        pcol.addWidget(pl)
        hh.addLayout(pcol)
        cl.addWidget(head)

        # body
        body = QtWidgets.QWidget()
        bl = QtWidgets.QVBoxLayout(body)
        bl.setContentsMargins(24, 18, 24, 18)
        bl.setSpacing(16)
        # 拖入区
        self.drop = QtWidgets.QFrame()
        self.drop.setObjectName('dropZone')
        self.drop.setMinimumHeight(96)
        self._drop_normal()
        dl = QtWidgets.QVBoxLayout(self.drop)
        dl.setAlignment(Qt.AlignCenter)
        dl.setSpacing(8)
        tip = _lab('选择或拖入本月数据文件夹', 14, 700)
        tip.setAlignment(Qt.AlignCenter)
        dl.addWidget(tip)
        browse = QtWidgets.QPushButton('选择文件夹…')
        browse.setProperty('primary', '1')
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self._browse)
        brow = QtWidgets.QHBoxLayout()
        brow.addStretch(1)
        brow.addWidget(browse)
        brow.addStretch(1)
        dl.addLayout(brow)
        bl.addWidget(self.drop)

        self.banner = Banner()
        bl.addWidget(self.banner)

        bl.addWidget(_lab('识别到的输入表', 11, 700, theme.INK_3))
        self.files_box = QtWidgets.QFrame()
        self.files_box.setObjectName('filesBox')
        self.files_box.setStyleSheet('QFrame#filesBox{border:1px solid %s;border-radius:11px;}' % theme.LINE)
        self.files_l = QtWidgets.QVBoxLayout(self.files_box)
        self.files_l.setContentsMargins(0, 0, 0, 0)
        self.files_l.setSpacing(0)
        self._file_rows = {}
        for i, (lab, key) in enumerate(self.REC_ROWS):
            row = QtWidgets.QWidget()
            rl = QtWidgets.QHBoxLayout(row)
            rl.setContentsMargins(14, 10, 14, 10)
            name = _lab(lab, 12.5, 600)
            val = _lab('— 未选择 —', 11, 400, theme.INK_3)
            stat = _lab('', 11, 700, theme.INK_3)
            self._file_rows[key] = (val, stat)
            rl.addWidget(name)
            rl.addStretch(1)
            rl.addWidget(val)
            rl.addWidget(stat)
            self.files_l.addWidget(row)
            if i < len(self.REC_ROWS) - 1:
                sep = QtWidgets.QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet('background:%s;border:none;' % theme.LINE)
                self.files_l.addWidget(sep)
        bl.addWidget(self.files_box)

        self.todo_wrap = QtWidgets.QWidget()
        twl = QtWidgets.QVBoxLayout(self.todo_wrap)
        twl.setContentsMargins(0, 0, 0, 0)
        twl.setSpacing(8)
        twl.addWidget(_lab('待你处理', 11, 700, theme.INK_3))
        grid = QtWidgets.QHBoxLayout()
        grid.setSpacing(10)
        self.todo_leaver = self._todo_big('离职取舍', '离职且打卡 < 7 天', '👤')
        self.todo_pending = self._todo_big('逐条归类', '当天打卡 < 2 次', '☰')
        grid.addWidget(self.todo_leaver[0])
        grid.addWidget(self.todo_pending[0])
        twl.addLayout(grid)
        bl.addWidget(self.todo_wrap)
        cl.addWidget(body)

        # 底部
        foot = QtWidgets.QFrame()
        foot.setObjectName('readyFoot')
        foot.setStyleSheet('QFrame#readyFoot{background:%s;border-bottom-left-radius:%dpx;border-bottom-right-radius:%dpx;'
                           'border-top:1px solid %s;}' % (theme.SURFACE_2, theme.R_LG, theme.R_LG, theme.LINE))
        fh = QtWidgets.QHBoxLayout(foot)
        fh.setContentsMargins(24, 14, 24, 14)
        self.foot_lb = _lab('', 12, 400, theme.INK_3)
        fh.addWidget(self.foot_lb)
        fh.addStretch(1)
        self.btn_start = QtWidgets.QPushButton('开始复核  →')
        self.btn_start.setProperty('primary', '1')
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.startReview.emit)
        fh.addWidget(self.btn_start)
        cl.addWidget(foot)

        hl.addWidget(self.card)
        scroll.setWidget(host)
        outer.addWidget(scroll)

    def _todo_big(self, label, sub, icon_char=''):
        card = make_card()
        h = QtWidgets.QHBoxLayout(card)
        h.setContentsMargins(14, 12, 14, 12)
        h.setSpacing(12)
        icon = QtWidgets.QLabel(icon_char)
        icon.setFixedSize(38, 38)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet('background:%s;color:%s;border-radius:10px;font-size:18px;' % (theme.ACCENT_SOFT, theme.ACCENT_STRONG))
        h.addWidget(icon)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(0)
        n = QtWidgets.QLabel('0')
        n.setStyleSheet('font-size:22px;font-weight:800;color:%s;' % theme.INK)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(n)
        row.addWidget(_lab(label, 13, 600))
        row.addStretch(1)
        col.addLayout(row)
        col.addWidget(_lab(sub, 11, 400, theme.INK_3))
        h.addLayout(col, 1)
        return card, n

    def _drop_normal(self):
        self.drop.setStyleSheet('QFrame#dropZone{background:%s;border:2px dashed %s;border-radius:%dpx;}'
                                % (theme.SURFACE_2, theme.LINE_2, theme.R_LG))

    def _drop_over(self):
        self.drop.setStyleSheet('QFrame#dropZone{background:%s;border:2px dashed %s;border-radius:%dpx;}'
                                % (theme.ACCENT_SOFT, theme.ACCENT, theme.R_LG))

    def _browse(self):
        import os
        d = QtWidgets.QFileDialog.getExistingDirectory(self, '选择含三张输入表的目录', os.getcwd())
        if d:
            self.dirChosen.emit(d)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._drop_over()

    def dragLeaveEvent(self, _):
        self._drop_normal()

    def dropEvent(self, e):
        import os
        self._drop_normal()
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p and os.path.isdir(p):
                self.dirChosen.emit(p)
                return

    def set_recognition(self, inp):
        import os
        self.drop.hide()          # 已选目录 → 隐藏拖入虚线区（设计稿 ReadyCard 态无 DropZone）
        for key, (val, stat) in self._file_rows.items():
            path = inp.get(key)
            if path:
                val.setText(os.path.basename(path))
                val.setStyleSheet('color:%s;font-size:11px;background:transparent;' % theme.INK_3)
                stat.setText('✓ 识别')
                stat.setStyleSheet('color:%s;font-size:11px;font-weight:700;background:transparent;' % theme.OK)
            else:
                val.setText('—— 未找到 ——')
                stat.setText('✕ 缺失')
                stat.setStyleSheet('color:%s;font-size:11px;font-weight:700;background:transparent;' % theme.ERR)

    def set_state(self, kind, title, body, people=None, month=None, leaver_n=0, pending_n=0, can_start=False):
        self.banner.set_msg(kind, '')      # 用富 banner 标题+正文
        self.banner.setVisible(bool(title))
        self._set_banner(kind, title, body)
        if month:
            self.month_box.setText(str(month))
            self.title_lb.setText('%d 月 · 考勤已就绪' % month if can_start else '请检查输入')
        if people is not None:
            self.people_lb.setText(str(people))
        self.todo_wrap.setVisible(can_start)
        self.todo_leaver[1].setText(str(leaver_n))
        self.todo_pending[1].setText(str(pending_n))
        self.foot_lb.setText(('共 %d 项需要你判断，其余已自动完成' % (leaver_n + pending_n)) if can_start else '解决上述问题后即可开始')
        self.btn_start.setEnabled(can_start)

    def set_dir_text(self, d):
        self.dir_lb.setText(d)

    def _set_banner(self, kind, title, body):
        self.banner.set_msg(kind, ('%s\n%s' % (title, body)) if body else title)


# ============================ 左栏：待办清单 ============================
class TodoPanel(QtWidgets.QWidget):
    locate = QtCore.Signal(str, int)
    reclassify = QtCore.Signal(str, int, str)
    keepDecide = QtCore.Signal(str, bool)
    adoptAll = QtCore.Signal()
    openAdvanced = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(theme.COL_LEFT_W)
        self.setObjectName('todoPanel')
        self.setStyleSheet('QWidget#todoPanel{background:%s;border-right:1px solid %s;}' % (theme.SURFACE_2, theme.LINE))
        self._rebuilding = False
        self._cards = {}
        self._current = None
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 头部
        head = QtWidgets.QFrame()
        head.setStyleSheet('background:%s;border-bottom:1px solid %s;' % (theme.SURFACE, theme.LINE))
        hh = QtWidgets.QHBoxLayout(head)
        hh.setContentsMargins(14, 13, 14, 13)
        hh.setSpacing(12)
        self.ring = ProgressRing(size=38)
        hh.addWidget(self.ring)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(_lab('待办清单', 13.5, 700))
        self.progress_lb = _lab('—', 11.5, 400, theme.INK_2)
        col.addWidget(self.progress_lb)
        hh.addLayout(col, 1)
        outer.addWidget(head)

        # 滚动区
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setStyleSheet('QScrollArea{background:transparent;}')
        self.body = QtWidgets.QWidget()
        self.body.setStyleSheet('background:transparent;')
        self.vbox = QtWidgets.QVBoxLayout(self.body)
        self.vbox.setContentsMargins(12, 12, 12, 16)
        self.vbox.setSpacing(16)
        self.vbox.addStretch(1)
        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll, 1)

        # 高级设置
        adv = QtWidgets.QPushButton('⚙   高级设置                                           ›')
        adv.setStyleSheet('QPushButton{text-align:left;border:none;border-top:1px solid %s;background:%s;'
                          'color:%s;font-size:12.5px;font-weight:600;padding:11px 14px;}'
                          'QPushButton:hover{background:%s;}' % (theme.LINE, theme.SURFACE, theme.INK_2, theme.SURFACE_3))
        adv.clicked.connect(self.openAdvanced.emit)
        outer.addWidget(adv)

    def _clear(self):
        self._cards = {}
        while self.vbox.count() > 1:
            it = self.vbox.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def set_current(self, key):
        self._current = key
        for k, card in self._cards.items():
            card.setStyleSheet(card._active_qss if k == key else card._default_qss)

    def refresh(self, data, leaver_cands, keep, classify):
        self._rebuilding = True
        self._clear()
        y, mo = data['year'], data['month']
        cases = data['pending']
        if leaver_cands:
            grp = QtWidgets.QWidget()
            gl = QtWidgets.QVBoxLayout(grp)
            gl.setContentsMargins(0, 0, 0, 0)
            gl.setSpacing(8)
            ld = sum(1 for c in leaver_cands if c['gh'] in keep)
            gl.addWidget(_section_head('离职取舍', ld, len(leaver_cands)))
            for c in leaver_cands:
                card = self._leaver_card(c, c['gh'] in keep)
                self._cards['leaver:%s' % c['gh']] = card
                gl.addWidget(card)
            self.vbox.insertWidget(self.vbox.count() - 1, grp)
        if cases:
            grp = QtWidgets.QWidget()
            gl = QtWidgets.QVBoxLayout(grp)
            gl.setContentsMargins(0, 0, 0, 0)
            gl.setSpacing(8)
            cd = sum(1 for c in cases if c['key'] in classify)
            head = QtWidgets.QHBoxLayout()
            head.setContentsMargins(0, 0, 0, 0)
            head.addWidget(_section_head('逐条归类（打卡 < 2 次）', cd, len(cases)), 1)
            if cd < len(cases):
                adopt = QtWidgets.QPushButton('✓ 全部采纳建议')
                adopt.setStyleSheet('QPushButton{border:1px solid %s;background:%s;color:%s;border-radius:7px;'
                                    'padding:4px 9px;font-size:11px;font-weight:700;}' % (theme.ACCENT, theme.ACCENT_SOFT, theme.ACCENT_STRONG))
                adopt.clicked.connect(self.adoptAll.emit)
                head.addWidget(adopt)
            gl.addLayout(head)
            unresolved = [c for c in cases if c['key'] not in classify]
            resolved = [c for c in cases if c['key'] in classify]
            for c in unresolved + resolved:
                card = self._classify_card(c, y, mo, classify.get(c['key']))
                self._cards['case:%s' % c['key']] = card
                gl.addWidget(card)
            self.vbox.insertWidget(self.vbox.count() - 1, grp)
        if not leaver_cands and not cases:
            self.vbox.insertWidget(self.vbox.count() - 1, _lab('✓ 没有需要人工判断的待办。', 12, 600, theme.OK))
        total = len(leaver_cands) + len(cases)
        done = sum(1 for c in leaver_cands if c['gh'] in keep) + sum(1 for c in cases if c['key'] in classify)
        self.ring.set_progress(done, total)
        if total and done == total:
            self.progress_lb.setText('全部处理完成 ✓')
            self.progress_lb.setStyleSheet('color:%s;font-size:11.5px;font-weight:600;background:transparent;' % theme.OK)
        else:
            self.progress_lb.setText('剩 %d 项待定 · 已处理 %d/%d' % (total - done, done, total) if total else '无待办')
            self.progress_lb.setStyleSheet('color:%s;font-size:11.5px;background:transparent;' % theme.INK_2)
        self._rebuilding = False
        self.set_current(self._current)

    def _card_base(self):
        card = make_card()
        card._default_qss = 'background:%s;border:1px solid %s;border-radius:10px;' % (theme.SURFACE, theme.LINE)
        card._active_qss = 'background:%s;border:1px solid %s;border-radius:10px;' % (theme.ACCENT_SOFT, theme.ACCENT)
        card.setStyleSheet(card._default_qss)
        card.setCursor(Qt.PointingHandCursor)
        return card

    def _badge(self, text, fg, bg, line):
        b = QtWidgets.QLabel(text)
        b.setStyleSheet('background:%s;color:%s;border:1px solid %s;border-radius:5px;padding:1px 6px;'
                        'font-size:9.5px;font-weight:700;' % (bg, fg, line))
        return b

    def _leaver_card(self, c, kept):
        card = self._card_base()
        card.mousePressEvent = lambda e, gh=c['gh']: self.locate.emit(gh, c.get('leave') or 1)
        v = QtWidgets.QVBoxLayout(card)
        v.setContentsMargins(10, 9, 10, 9)
        v.setSpacing(6)
        r1 = QtWidgets.QHBoxLayout()
        r1.setSpacing(6)
        r1.addWidget(_lab(c['name'], 12.5, 650))
        r1.addStretch(1)
        if kept:
            r1.addWidget(_lab('✓ 保留', 10.5, 700, theme.OK))
        v.addLayout(r1)
        v.addWidget(_lab('本月离职，仅打卡 %d 天（< 7 天）' % c['pd'], 11, 400, theme.INK_2))
        r3 = QtWidgets.QHBoxLayout()
        r3.setSpacing(7)
        bk = QtWidgets.QPushButton('保留')
        bd = QtWidgets.QPushButton('删除')
        for b, on in ((bk, kept), (bd, not kept)):
            b.setStyleSheet(self._seg_qss(on))
        bk.clicked.connect(lambda: self.keepDecide.emit(c['gh'], True))
        bd.clicked.connect(lambda: self.keepDecide.emit(c['gh'], False))
        r3.addWidget(bk)
        r3.addWidget(bd)
        v.addLayout(r3)
        return card

    def _seg_qss(self, on):
        if on:
            return ('QPushButton{flex:1;background:%s;color:#fff;border:none;border-radius:8px;padding:7px 0;'
                    'font-size:12.5px;font-weight:600;}' % theme.ACCENT)
        return ('QPushButton{background:%s;color:%s;border:1px solid %s;border-radius:8px;padding:7px 0;'
                'font-size:12.5px;font-weight:600;}QPushButton:hover{background:%s;}'
                % (theme.SURFACE, theme.INK_2, theme.LINE_2, theme.SURFACE_3))

    def _classify_card(self, c, y, mo, resolved_val):
        card = self._card_base()
        card.mousePressEvent = lambda e, gh=c['gh'], dd=c['day']: self.locate.emit(gh, dd)
        v = QtWidgets.QVBoxLayout(card)
        v.setContentsMargins(10, 9, 10, 9)
        v.setSpacing(5)
        wd = WEEK_CN[datetime.date(y, mo, c['day']).weekday()]
        r1 = QtWidgets.QHBoxLayout()
        r1.setSpacing(6)
        r1.addWidget(_lab(c['name'], 12.5, 650))
        r1.addWidget(_lab('· %d/%d（周%s）' % (mo, c['day'], wd), 11, 400, theme.INK_3))
        r1.addStretch(1)
        if resolved_val:
            r1.addWidget(_lab('✓ 已定', 10.5, 700, theme.OK))
        elif c.get('memo'):
            r1.addWidget(self._badge('沿用上月', theme.ACCENT_STRONG, theme.ACCENT_SOFT, theme.ACCENT_SOFT))
        elif c['wq']:
            r1.addWidget(self._badge('疑似公出', theme.SEM['biz']['fg'], theme.SEM['biz']['bg'], theme.SEM['biz']['border']))
        v.addLayout(r1)
        punch = (c['punch'] or '无记录').replace(' | ', '  ·  ')
        v.addWidget(_lab('当天打卡：' + punch, 11, 400, theme.INK_2))
        # 操作行
        op = QtWidgets.QHBoxLayout()
        op.setSpacing(7)
        if resolved_val:
            kind = CLS_KIND.get(resolved_val, 'miss')
            tag = QtWidgets.QWidget()
            tl = QtWidgets.QHBoxLayout(tag)
            tl.setContentsMargins(9, 3, 9, 3)
            tl.setSpacing(6)
            tag.setStyleSheet('background:%s;border-radius:7px;' % theme.SURFACE_3)
            tl.addWidget(Swatch(kind))
            tl.addWidget(_lab(CLS_DISP[resolved_val], 12, 600))
            op.addWidget(tag)
            op.addStretch(1)
            rebtn = QtWidgets.QPushButton('改判')
            rebtn.setStyleSheet(self._ghost_qss())
            rebtn.clicked.connect(lambda _=0, gh=c['gh'], dd=c['day']: self._emit_reclass(gh, dd, None))
            op.addWidget(rebtn)
        else:
            adopt = QtWidgets.QPushButton('✓  采纳建议：' + CLS_DISP[c['suggest']])
            adopt.setStyleSheet('QPushButton{background:%s;color:#fff;border:none;border-radius:8px;padding:7px 10px;'
                                'font-size:12px;font-weight:600;}QPushButton:hover{background:%s;}' % (theme.ACCENT, theme.ACCENT_STRONG))
            adopt.clicked.connect(lambda _=0, gh=c['gh'], dd=c['day'], s=c['suggest']: self._emit_reclass(gh, dd, s))
            op.addWidget(adopt, 1)
            chg = QtWidgets.QPushButton('改 ▾')
            chg.setStyleSheet(self._ghost_qss())
            chg.clicked.connect(lambda _=0, gh=c['gh'], dd=c['day'], s=c['suggest'], b=chg: self._open_menu(b, gh, dd, s))
            op.addWidget(chg)
        v.addLayout(op)
        return card

    def _ghost_qss(self):
        return ('QPushButton{background:%s;color:%s;border:1px solid %s;border-radius:8px;padding:6px 9px;'
                'font-size:12px;font-weight:600;}QPushButton:hover{background:%s;}'
                % (theme.SURFACE, theme.INK_2, theme.LINE_2, theme.SURFACE_3))

    def _open_menu(self, anchor, gh, day, suggest):
        from widgets import swatch_pixmap
        menu = QtWidgets.QMenu(self)
        for code in ('G', 'B', 'R'):
            label = CLS_DISP[code] + ('     建议' if code == suggest else '')
            act = menu.addAction(QtGui.QIcon(swatch_pixmap(CLS_KIND[code])), label)
            act.setData(code)
        chosen = menu.exec(anchor.mapToGlobal(QtCore.QPoint(0, anchor.height())))
        if chosen:
            self._emit_reclass(gh, day, chosen.data())

    def _emit_reclass(self, gh, day, val):
        if self._rebuilding:
            return
        self.reclassify.emit(gh, day, val if val else 'pending')


# ============================ 右栏：检查器 ============================
class Inspector(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(theme.COL_RIGHT_W)
        self.setObjectName('inspector')
        self.setStyleSheet('QWidget#inspector{background:%s;border-left:1px solid %s;}' % (theme.SURFACE, theme.LINE))
        self.v = QtWidgets.QVBoxLayout(self)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(0)
        self._build_empty()

    def _clear(self):
        while self.v.count():
            it = self.v.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                self._del_layout(it.layout())

    def _del_layout(self, lay):
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                self._del_layout(it.layout())

    def _build_empty(self):
        self._clear()
        box = QtWidgets.QWidget()
        bl = QtWidgets.QVBoxLayout(box)
        bl.setAlignment(Qt.AlignCenter)
        bl.setSpacing(12)
        ic = QtWidgets.QLabel('▦')
        ic.setFixedSize(46, 46)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet('background:%s;color:%s;border-radius:12px;font-size:20px;' % (theme.SURFACE_3, theme.INK_3))
        bl.addWidget(ic, 0, Qt.AlignHCenter)
        bl.addWidget(_lab('检查器', 13, 600, theme.INK_2), 0, Qt.AlignHCenter)
        tip = _lab('点击网格中任意单元格，这里会显示原始打卡、判定原因、加班算式，以及该员工本月小结。', 12, 400, theme.INK_3)
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignCenter)
        tip.setMaximumWidth(220)
        bl.addWidget(tip, 0, Qt.AlignHCenter)
        self.v.addStretch(1)
        self.v.addWidget(box, 0, Qt.AlignHCenter)
        self.v.addStretch(2)

    def clear(self):
        self._build_empty()

    def show_cell(self, data, gh, day):
        emp = next((e for e in data['employees'] if e['gh'] == gh), None)
        if emp is None:
            return
        cell = emp['cells'].get(day, {'status': 'rest'})
        st = cell.get('status', 'rest')
        ps = engine.person_summary(emp)
        self._clear()
        # 头
        head = QtWidgets.QFrame()
        head.setStyleSheet('background:%s;border-bottom:1px solid %s;' % (theme.SURFACE_2, theme.LINE))
        hh = QtWidgets.QHBoxLayout(head)
        hh.setContentsMargins(16, 14, 16, 14)
        hh.setSpacing(10)
        av = QtWidgets.QLabel(emp['name'][0])
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignCenter)
        if emp['full']:
            av.setStyleSheet('background:%s;color:%s;border-radius:9px;font-size:14px;font-weight:700;' % (theme.SEM['full']['bg'], theme.SEM['full']['fg']))
        else:
            av.setStyleSheet('background:%s;color:%s;border-radius:9px;font-size:14px;font-weight:700;' % (theme.ACCENT_SOFT, theme.ACCENT_STRONG))
        hh.addWidget(av)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(1)
        nrow = QtWidgets.QHBoxLayout()
        nrow.setSpacing(6)
        nrow.addWidget(_lab(emp['name'], 14.5, 700))
        if emp['full']:
            star = QtWidgets.QLabel('★ 全勤')
            star.setStyleSheet('background:%s;color:%s;border:1px solid %s;border-radius:5px;padding:1px 6px;font-size:10px;font-weight:700;'
                               % (theme.SEM['full']['bg'], theme.SEM['full']['fg'], theme.SEM['full']['border']))
            nrow.addWidget(star)
        nrow.addStretch(1)
        col.addLayout(nrow)
        col.addWidget(_lab('%s · %s · %s' % (emp['gh'], emp.get('pos') or '', emp.get('yong') or ''), 11, 400, theme.INK_3))
        hh.addLayout(col, 1)
        self.v.addWidget(head)

        # 内容滚动
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        host = QtWidgets.QWidget()
        body = QtWidgets.QVBoxLayout(host)
        body.setContentsMargins(16, 14, 16, 14)
        body.setSpacing(16)

        # 选中日
        body.addWidget(_lab('选中：%d 月 %d 日 · 周%s' % (data['month'], day, WEEK_CN[datetime.date(data['year'], data['month'], day).weekday()]), 11, 700, theme.INK_3))
        daycard = QtWidgets.QFrame()
        daycard.setStyleSheet('border:1px solid %s;border-radius:11px;' % theme.LINE)
        dv = QtWidgets.QVBoxLayout(daycard)
        dv.setContentsMargins(0, 0, 0, 0)
        dv.setSpacing(0)
        dhead = QtWidgets.QFrame()
        dhead.setStyleSheet('background:%s;border-bottom:1px solid %s;border-top-left-radius:11px;border-top-right-radius:11px;' % (theme.SURFACE_2, theme.LINE))
        dhl = QtWidgets.QHBoxLayout(dhead)
        dhl.setContentsMargins(12, 10, 12, 10)
        dhl.setSpacing(9)
        sw_kind = CLS_KIND.get(cell.get('suggest'), 'miss') if st == 'pending' else st
        if st not in ('normal', 'rest', 'pre', 'post') or cell.get('swap'):
            if sw_kind in theme.SEM and theme.SEM[sw_kind].get('icon'):
                dhl.addWidget(Swatch(sw_kind))
        dhl.addWidget(_lab(theme.LABELS.get(st, st), 14, 700))
        dhl.addStretch(1)
        if cell.get('swap'):
            sw = QtWidgets.QLabel('⇄ 调班')
            sw.setStyleSheet('background:%s;color:%s;border:1px solid %s;border-radius:5px;padding:1px 6px;font-size:10px;font-weight:700;'
                             % (theme.SEM['swap']['bg'], theme.SEM['swap']['fg'], theme.SEM['swap']['border']))
            dhl.addWidget(sw)
        dv.addWidget(dhead)
        dbody = QtWidgets.QWidget()
        dbl = QtWidgets.QVBoxLayout(dbody)
        dbl.setContentsMargins(12, 11, 12, 11)
        dbl.setSpacing(9)
        dbl.addLayout(self._defrow('判定原因', cell.get('reason') or '—'))
        punches = cell.get('punches') or []
        dbl.addLayout(self._defrow('原始打卡', '    '.join(punches) if punches else '无任何打卡记录'))
        if cell.get('ot'):
            dbl.addLayout(self._defrow('加班', '%g h' % cell['ot']))
        if st == 'pending':
            hint = _lab('需归类为 缺卡 / 公出 / 未出勤。工具建议：%s。' % CLS_DISP.get(cell.get('suggest'), ''), 11.5, 400, theme.ACCENT_STRONG)
            hint.setWordWrap(True)
            hint.setStyleSheet('background:%s;color:%s;border-radius:8px;padding:7px 9px;font-size:11.5px;' % (theme.ACCENT_SOFT, theme.ACCENT_STRONG))
            dbl.addWidget(hint)
        dv.addWidget(dbody)
        body.addWidget(daycard)

        # 本月小结
        body.addWidget(_lab('本月小结', 11, 700, theme.INK_3))
        stat_row = QtWidgets.QHBoxLayout()
        stat_row.setSpacing(8)
        stat_row.addWidget(self._stat('出勤天数', ps['work_days']))
        stat_row.addWidget(self._stat('加班合计 (h)', ('%g' % ps['ot']), theme.OT_FG))
        body.addLayout(stat_row)
        chips = QtWidgets.QHBoxLayout()
        chips.setSpacing(7)
        chips.setContentsMargins(0, 4, 0, 0)
        cw = QtWidgets.QWidget()
        flow = QtWidgets.QHBoxLayout(cw)
        flow.setContentsMargins(0, 0, 0, 0)
        flow.setSpacing(7)
        for key, lab in (('lateheavy', '迟到'), ('early', '早退'), ('miss', '缺卡'), ('absent', '未出勤'), ('biz', '公出'), ('field', '外勤')):
            n = ps['counts'].get(key, 0) + (ps['counts'].get('late', 0) if key == 'lateheavy' else 0)
            flow.addWidget(self._chip(lab, n, key))
        flow.addStretch(1)
        body.addWidget(cw)

        # 异常明细
        anoms = []
        for d in sorted(emp['cells']):
            c = emp['cells'][d]
            if c.get('status') in engine.ANOMALY_STATUS:
                k = CLS_KIND.get(c.get('suggest'), 'miss') if c['status'] == 'pending' else c['status']
                anoms.append((d, theme.LABELS.get(c['status'], c['status']), k))
        if anoms:
            body.addWidget(_lab('异常明细（%d）' % len(anoms), 11, 700, theme.INK_3))
            for d, lab, k in anoms:
                r = QtWidgets.QWidget()
                rl = QtWidgets.QHBoxLayout(r)
                rl.setContentsMargins(8, 5, 8, 5)
                rl.setSpacing(8)
                r.setStyleSheet('background:%s;border-radius:7px;' % theme.SURFACE_2)
                rl.addWidget(Swatch(k))
                rl.addWidget(_lab('%d/%d' % (data['month'], d), 12, 400, theme.INK_2))
                rl.addWidget(_lab(lab, 12, 400))
                rl.addStretch(1)
                body.addWidget(r)
        else:
            none = _lab('本月无异常记录 🎉', 12, 400, theme.INK_3)
            none.setAlignment(Qt.AlignCenter)
            none.setStyleSheet('background:%s;color:%s;border:1px dashed %s;border-radius:9px;padding:12px;font-size:12px;' % (theme.SURFACE_2, theme.INK_3, theme.LINE_2))
            body.addWidget(none)

        body.addStretch(1)
        scroll.setWidget(host)
        self.v.addWidget(scroll, 1)

    def _defrow(self, k, v):
        h = QtWidgets.QHBoxLayout()
        h.setSpacing(10)
        kk = _lab(k, 12.5, 400, theme.INK_3)
        kk.setFixedWidth(60)
        vv = _lab(v, 12.5, 400, theme.INK)
        vv.setWordWrap(True)
        h.addWidget(kk)
        h.addWidget(vv, 1)
        return h

    def _stat(self, label, value, color=None):
        card = QtWidgets.QFrame()
        card.setStyleSheet('background:%s;border:1px solid %s;border-radius:9px;' % (theme.SURFACE_2, theme.LINE))
        v = QtWidgets.QVBoxLayout(card)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(1)
        v.addWidget(_lab(str(value), 18, 700, color or theme.INK))
        v.addWidget(_lab(label, 10.5, 400, theme.INK_3))
        return card

    def _chip(self, label, n, kind):
        w = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(9, 4, 9, 4)
        h.setSpacing(5)
        dim = (n == 0)
        w.setStyleSheet('background:%s;border:1px solid %s;border-radius:7px;' % (theme.SURFACE_2 if dim else theme.SURFACE_3, theme.LINE))
        if not dim:
            h.addWidget(Swatch(kind))
        h.addWidget(_lab(label, 11.5, 600, theme.INK_3 if dim else theme.INK))
        h.addWidget(_lab(str(n), 11.5, 700, theme.INK_3 if dim else theme.INK))
        return w


# ============================ 高级设置抽屉 ============================
class AdvancedDrawer(QtWidgets.QFrame):
    applied = QtCore.Signal(dict)
    closed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(theme.DRAWER_W)
        self.setObjectName('drawer')
        self.setStyleSheet('QFrame#drawer{background:%s;border-left:1px solid %s;}' % (theme.SURFACE, theme.LINE_2))
        self._g2n = {}        # 工号→姓名
        self._name_ghs = {}   # 姓名→[工号,...]（可能重名）
        self._gh_desc = {}    # 工号→“工号 · 职位”描述
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QtWidgets.QFrame()
        head.setObjectName('drawerHead')
        head.setStyleSheet('QFrame#drawerHead{background:%s;border-bottom:1px solid %s;}' % (theme.SURFACE, theme.LINE))
        hh = QtWidgets.QHBoxLayout(head)
        hh.setContentsMargins(18, 16, 18, 16)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(_lab('高级设置', 14.5, 700))
        col.addWidget(_lab('多数月份无需改动', 11.5, 400, theme.INK_3))
        hh.addLayout(col, 1)
        x = QtWidgets.QPushButton('✕')
        x.setProperty('ghost', '1')
        x.setFixedWidth(34)
        x.clicked.connect(self.closed.emit)
        hh.addWidget(x)
        v.addWidget(head)
        body = QtWidgets.QWidget()
        bl = QtWidgets.QVBoxLayout(body)
        bl.setContentsMargins(18, 18, 18, 18)
        bl.setSpacing(20)
        self.excl = self._field(bl, '不计加班名单', '名单内人员本月加班一律不计（直接填姓名，逗号分隔）')
        self.strict = self._field(bl, '个别人迟到阈值', '默认 09:00；个别人可单独放宽（姓名:HHMM，如 刘莹:0905）')
        self.font = self._field(bl, '只红字（不加底色）名单', '名单内人员迟到只标红字（直接填姓名，逗号分隔）')
        bl.addStretch(1)
        v.addWidget(body, 1)
        foot = QtWidgets.QFrame()
        foot.setObjectName('drawerFoot')
        foot.setStyleSheet('QFrame#drawerFoot{background:%s;border-top:1px solid %s;}' % (theme.SURFACE_2, theme.LINE))
        fh = QtWidgets.QHBoxLayout(foot)
        fh.setContentsMargins(18, 14, 18, 14)
        fh.addStretch(1)
        cl = QtWidgets.QPushButton('关闭')
        cl.clicked.connect(self.closed.emit)
        ap = QtWidgets.QPushButton('应用并重算')
        ap.setProperty('primary', '1')
        ap.clicked.connect(self._apply)
        fh.addWidget(cl)
        fh.addWidget(ap)
        v.addWidget(foot)

    def _field(self, parent_layout, label, hint):
        parent_layout.addWidget(_lab(label, 12.5, 700))
        parent_layout.addWidget(_lab(hint, 11, 400, theme.INK_3))
        edit = QtWidgets.QLineEdit()
        parent_layout.addWidget(edit)
        return edit

    def set_config(self, cfg, employees=None):
        emps = employees or []
        self._g2n = {e['gh']: e['name'] for e in emps}
        self._name_ghs = {}
        self._gh_desc = {}
        for e in emps:
            self._name_ghs.setdefault(e['name'], []).append(e['gh'])
            self._gh_desc[e['gh']] = '%s · %s' % (e['gh'], e.get('pos') or '—')
        nm = lambda g: self._g2n.get(g, g)
        self.excl.setText('，'.join(nm(g) for g in sorted(cfg['excl'])))
        self.strict.setText('，'.join('%s:%02d%02d' % (nm(g), m // 60, m % 60) for g, m in cfg['strict'].items()))
        self.font.setText('，'.join(nm(g) for g in sorted(cfg['font_only'])))

    @staticmethod
    def _split(text):
        import re
        return [x.strip() for x in re.split(r'[,，、]', text) if x.strip()]

    def _resolve_name(self, name):
        """姓名 → 工号列表。重名时弹窗让用户选具体一位或全部；未匹配则原样（容错直填工号）。"""
        ghs = self._name_ghs.get(name)
        if not ghs:
            return [name]
        if len(ghs) == 1:
            return ghs
        items = ['全部（%d 人）' % len(ghs)] + [self._gh_desc.get(g, g) for g in ghs]
        choice, ok = QtWidgets.QInputDialog.getItem(
            self, '“%s”有重名' % name,
            '“%s”有 %d 位，请选择具体哪一位（或全部）：' % (name, len(ghs)), items, 0, False)
        if not ok:
            return []
        if choice.startswith('全部'):
            return list(ghs)
        return [choice.split(' · ')[0].strip()]

    def _apply(self):
        excl = set()
        for x in self._split(self.excl.text()):
            excl.update(self._resolve_name(x))
        font = set()
        for x in self._split(self.font.text()):
            font.update(self._resolve_name(x))
        strict = {}
        for pair in self._split(self.strict.text()):
            pp = pair.replace('：', ':')
            if ':' not in pp:
                continue
            name, hm = pp.split(':', 1)
            hm = hm.strip()
            try:
                mins = int(hm[:2]) * 60 + int(hm[2:4])
            except ValueError:
                continue
            for g in self._resolve_name(name.strip()):
                strict[g] = mins
        self.applied.emit({'excl': excl, 'strict': strict, 'font_only': font})


# ============================ 阶段② 三栏工作台 ============================
class Workbench(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.todo = TodoPanel()
        self.inspector = Inspector()
        from grid import AttGrid
        self.center = QtWidgets.QWidget()
        self.center.setStyleSheet('background:%s;' % theme.SURFACE)
        cv = QtWidgets.QVBoxLayout(self.center)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        self.grid = AttGrid()
        cv.addWidget(self.grid)
        lay.addWidget(self.todo)
        lay.addWidget(self.center, 1)
        lay.addWidget(self.inspector)


# ============================ 阶段③ 完成页 ============================
def _big_stat(value, label, sub='', accent=None):
    card = make_card()
    v = QtWidgets.QVBoxLayout(card)
    v.setContentsMargins(18, 16, 18, 16)
    v.setSpacing(2)
    v.addWidget(_lab(str(value), 30, 800, accent or theme.INK))
    v.addWidget(_lab(label, 12.5, 600))
    if sub:
        v.addWidget(_lab(sub, 11, 400, theme.INK_3))
    return card


def _panel(title, right=None):
    p = QtWidgets.QFrame()
    p.setStyleSheet('background:%s;border:1px solid %s;border-radius:14px;' % (theme.SURFACE_2, theme.LINE))
    v = QtWidgets.QVBoxLayout(p)
    v.setContentsMargins(16, 16, 16, 16)
    v.setSpacing(12)
    head = QtWidgets.QHBoxLayout()
    head.addWidget(_lab(title, 13, 700))
    head.addStretch(1)
    if right:
        head.addWidget(right)
    v.addLayout(head)
    return p, v


class Dashboard(QtWidgets.QWidget):
    exportRequested = QtCore.Signal()
    openRequested = QtCore.Signal()
    backRequested = QtCore.Signal()
    saveDecisions = QtCore.Signal()
    loadDecisions = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('dashboardRoot')
        self.setStyleSheet('QWidget#dashboardRoot{background:%s;}' % theme.BG)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.scroll)
        self.host = QtWidgets.QWidget()
        self.scroll.setWidget(self.host)
        self.exported_path = None

    def set_exported(self, path):
        import os
        self.exported_path = path
        if hasattr(self, 'bopen'):
            self.bopen.setEnabled(True)
            self.exported_lb.setText('已导出：' + os.path.basename(path))

    def refresh(self, data):
        old = self.host.layout()
        if old:
            QtWidgets.QWidget().setLayout(old)
        st = data['stats']
        L = QtWidgets.QVBoxLayout(self.host)
        L.setContentsMargins(28, 26, 28, 40)
        L.setSpacing(14)
        # 标题行
        top = QtWidgets.QHBoxLayout()
        tcol = QtWidgets.QVBoxLayout()
        tcol.setSpacing(3)
        tcol.addWidget(_lab('%d 月 · 考勤汇总' % data['month'], 22, 800))
        tcol.addWidget(_lab('所有待办已处理完成，下面是本月概览与导出。', 13, 400, theme.INK_2))
        top.addLayout(tcol)
        top.addStretch(1)
        back = QtWidgets.QPushButton('← 返回工作台')
        back.clicked.connect(self.backRequested)
        bsave = QtWidgets.QPushButton('保存本月决策')
        bsave.clicked.connect(self.saveDecisions)
        bload = QtWidgets.QPushButton('载入决策')
        bload.clicked.connect(self.loadDecisions)
        self.bopen = QtWidgets.QPushButton('打开考勤表')
        self.bopen.setEnabled(self.exported_path is not None)
        self.bopen.clicked.connect(self.openRequested)
        bexp = QtWidgets.QPushButton('导出《考勤》')
        bexp.setProperty('primary', '1')
        bexp.clicked.connect(self.exportRequested)
        for b in (back, bsave, bload, self.bopen, bexp):
            top.addWidget(b)
        L.addLayout(top)
        # BigStats
        stats_row = QtWidgets.QHBoxLayout()
        stats_row.setSpacing(12)
        stats_row.addWidget(_big_stat(st['people'], '纳入人数', '共识别 %d 人' % st['people']))
        stats_row.addWidget(_big_stat('%g' % st['ot_total'], '加班合计 (h)', '不计名单已排除', theme.OT_FG))
        stats_row.addWidget(_big_stat(len(st['full_list']), '全勤人数', accent=theme.SEM['full']['fg']))
        anom = len(st['anomaly_set'])
        stats_row.addWidget(_big_stat(anom, '有异常人数', '%d 人本月正常' % (st['people'] - anom), theme.WARN if anom else theme.INK))
        L.addLayout(stats_row)
        # 两列
        cols = QtWidgets.QHBoxLayout()
        cols.setSpacing(14)
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(14)
        # 异常计数
        cnt_panel, cv = _panel('异常计数')
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(9)
        c = st['counts']
        items = [('lateheavy', '迟到（含较重）', c['late'] + c['lateheavy']), ('early', '早退', c['early']),
                 ('miss', '缺卡', c['miss']), ('absent', '未出勤', c['absent']),
                 ('biz', '公出', c['biz']), ('field', '外勤日', c['field'])]
        for i, (k, lab, n) in enumerate(items):
            grid.addWidget(self._count_card(k, lab, n), i // 2, i % 2)
        cv.addLayout(grid)
        left.addWidget(cnt_panel)
        # 全勤名单
        full_panel, fv = _panel('全勤名单（%d）' % len(st['full_list']))
        fl = QtWidgets.QHBoxLayout()
        fl.setSpacing(8)
        if st['full_list']:
            for name in st['full_list']:
                pill = QtWidgets.QLabel('★ ' + name)
                pill.setStyleSheet('background:%s;color:%s;border:1px solid %s;border-radius:999px;padding:4px 11px;font-size:12.5px;font-weight:600;'
                                   % (theme.SEM['full']['bg'], theme.SEM['full']['fg'], theme.SEM['full']['border']))
                fl.addWidget(pill)
        else:
            fl.addWidget(_lab('本月无全勤', 12, 400, theme.INK_3))
        fl.addStretch(1)
        fv.addLayout(fl)
        left.addWidget(full_panel)
        left.addStretch(1)
        cols.addLayout(left, 14)
        # 异常清单
        anom_panel, av = _panel('异常清单')
        for e in data['employees']:
            if e['gh'] not in st['anomaly_set']:
                continue
            ps = engine.person_summary(e)
            tags = []
            for k, lab in (('late', '迟到'), ('lateheavy', '迟到较重'), ('early', '早退'), ('absent', '未出勤'), ('miss', '缺卡'), ('pending', '待定')):
                if ps['counts'].get(k):
                    tags.append((CLS_KIND.get(None, k if k != 'pending' else 'miss') if k == 'pending' else ('lateheavy' if k == 'late' else k), lab, ps['counts'][k]))
            if not tags:
                continue
            row = QtWidgets.QFrame()
            row.setStyleSheet('background:%s;border:1px solid %s;border-radius:9px;' % (theme.SURFACE, theme.LINE))
            rl = QtWidgets.QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            rl.setSpacing(9)
            nm = _lab(e['name'], 12.5, 600)
            nm.setFixedWidth(52)
            rl.addWidget(nm)
            for kind, lab, n in tags:
                t = QtWidgets.QWidget()
                tl = QtWidgets.QHBoxLayout(t)
                tl.setContentsMargins(0, 0, 0, 0)
                tl.setSpacing(4)
                tl.addWidget(Swatch(kind))
                tl.addWidget(_lab('%s×%d' % (lab, n), 11, 400, theme.INK_2))
                rl.addWidget(t)
            rl.addStretch(1)
            av.addWidget(row)
        av.addStretch(1)
        cols.addWidget(anom_panel, 10)
        L.addLayout(cols)
        # 导出状态
        self.exported_lb = _lab('', 11, 400, theme.INK_3)
        L.addWidget(self.exported_lb)
        L.addStretch(1)

    def _count_card(self, kind, label, n):
        card = QtWidgets.QFrame()
        card.setStyleSheet('background:%s;border:1px solid %s;border-radius:11px;' % (theme.SURFACE, theme.LINE))
        h = QtWidgets.QHBoxLayout(card)
        h.setContentsMargins(13, 11, 13, 11)
        h.setSpacing(10)
        h.addWidget(Swatch(kind))
        h.addWidget(_lab(label, 12.5, 400, theme.INK_2), 1)
        h.addWidget(_lab(str(n), 18, 700))
        return card
