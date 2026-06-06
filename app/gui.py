# -*- coding: utf-8 -*-
"""南京六部考勤 GUI 上位机 (PySide6) —— 三阶段三栏「活的彩色工作台」。
入口 + MainWindow：阶段路由(QStackedWidget) + 顶部状态条 + recompute 重算中枢 + 信号槽编排。
业务判定全部走 engine（权威），界面只做展示与交互。"""
import sys, os, subprocess
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
import theme
import undo
import memory
from widgets import Stepper, Toast, Chip2
from panels import ReadyView, Workbench, Dashboard, AdvancedDrawer

VAL_CN = {'R': '未出勤', 'G': '缺卡', 'B': '公出'}

READY, REVIEW, DONE = 0, 1, 2


def _open_file(path):
    """跨平台用系统默认程序打开文件（Windows/macOS/Linux）。"""
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.run(['open', path])
    else:
        subprocess.run(['xdg-open', path])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('南京六部考勤 · 工作台')
        self.resize(1280, 800)
        self.headless = False
        # ---- 状态 ----
        self.dir = None
        self.data = None
        self.keep = set()
        self.classify = {}
        self.config = engine.default_config()
        self.leaver_cands = []
        self.active = None          # (gh, day)
        self.search = ''
        self.filter = 'all'
        self.out_path = None
        self.undo = undo.UndoStack()
        self.kbd_idx = -1           # 键盘流当前待办指针
        self.memory = None          # 跨月决策档

        root = QtWidgets.QWidget()
        root.setObjectName('root')
        self.setCentralWidget(root)
        v = QtWidgets.QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ---- 顶部 Toolbar（单行：Stepper 左 + Chip2/按钮 右，52px）----
        toolbar = QtWidgets.QFrame()
        toolbar.setObjectName('toolbar')
        toolbar.setStyleSheet('QFrame#toolbar{background:%s;border-bottom:1px solid %s;}' % (theme.SURFACE, theme.LINE))
        toolbar.setFixedHeight(52)
        tb = QtWidgets.QHBoxLayout(toolbar)
        tb.setContentsMargins(8, 0, 14, 0)
        tb.setSpacing(10)
        self.stepper = Stepper()
        self.stepper.stepClicked.connect(self.goto_step)
        tb.addWidget(self.stepper)
        tb.addStretch(1)
        self.ready_hint = QtWidgets.QLabel('选择文件夹后自动就绪')
        self.ready_hint.setStyleSheet('color:%s;font-size:11.5px;' % theme.INK_3)
        tb.addWidget(self.ready_hint)
        self.chip_dir = Chip2('', mono=True)
        self.chip_meta = Chip2('')
        self.chip_todo = Chip2('', tone='accent')
        for c in (self.chip_dir, self.chip_meta, self.chip_todo):
            c.hide()
            tb.addWidget(c)
        self.btn_undo = QtWidgets.QPushButton('↶')
        self.btn_redo = QtWidgets.QPushButton('↷')
        for b in (self.btn_undo, self.btn_redo):
            b.setProperty('ghost', '1')
            b.setEnabled(False)
            b.setFixedWidth(32)
            b.hide()
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_redo.clicked.connect(self.redo_action)
        self.btn_done = QtWidgets.QPushButton('完成并汇总  →')
        self.btn_done.setProperty('primary', '1')
        self.btn_done.setEnabled(False)
        self.btn_done.hide()
        self.btn_done.clicked.connect(self.goto_done)
        tb.addWidget(self.btn_undo)
        tb.addWidget(self.btn_redo)
        tb.addWidget(self.btn_done)
        v.addWidget(toolbar)

        # ---- 阶段栈 ----
        self.stack = QtWidgets.QStackedWidget()
        self.ready = ReadyView()
        self.workbench = Workbench()
        self.dashboard = Dashboard()
        self.stack.addWidget(self.ready)
        self.stack.addWidget(self.workbench)
        self.stack.addWidget(self.dashboard)
        v.addWidget(self.stack, 1)

        # ---- Toast ----
        self.toast_w = Toast(root)

        # ---- 高级设置抽屉 + 背景遮罩 ----
        self.backdrop = QtWidgets.QWidget(root)
        self.backdrop.setStyleSheet('background:rgba(15,23,42,0.42);')
        self.backdrop.hide()
        self.backdrop.mousePressEvent = lambda e: self.hide_drawer()
        self.drawer = AdvancedDrawer(root)
        self.drawer.hide()
        self.drawer.closed.connect(self.hide_drawer)
        self.drawer.applied.connect(self.apply_config)

        # ---- 信号 ----
        self.ready.dirChosen.connect(self.choose_dir)
        self.ready.startReview.connect(self.begin_review)
        self.workbench.todo.locate.connect(self.on_locate)
        self.workbench.todo.reclassify.connect(self.do_reclassify)
        self.workbench.todo.keepDecide.connect(self.do_keep)
        self.workbench.todo.adoptAll.connect(self.do_adopt_all)
        self.workbench.grid.cellSelected.connect(self.on_cell_selected)
        self.workbench.grid.reclassify.connect(self.do_reclassify)
        self.workbench.todo.openAdvanced.connect(self.show_drawer)
        self.dashboard.exportRequested.connect(self.do_export)
        self.dashboard.openRequested.connect(self.open_result)
        self.dashboard.backRequested.connect(lambda: self.goto_step(REVIEW))
        self.dashboard.saveDecisions.connect(self.save_decisions)
        self.dashboard.loadDecisions.connect(self.load_decisions)

        self._sync_stepper()

        # ---- 快捷键 ----
        self._add_shortcut('Ctrl+Z', self.undo_action)
        self._add_shortcut('Ctrl+Y', self.redo_action)
        self._add_shortcut('Ctrl+Shift+Z', self.redo_action)
        self._add_shortcut('Ctrl+E', self.do_export)
        self._add_shortcut('/', self._focus_search)
        self._add_shortcut('N', self.workbench.grid.goto_next_anomaly)
        self._add_shortcut('Escape', self._on_escape)

    def _add_shortcut(self, seq, slot):
        sc = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
        sc.activated.connect(slot)
        return sc

    # ---------------- 工具 ----------------
    def toast(self, msg):
        self.toast_w.show_msg(msg)

    def err(self, e):
        if self.headless:
            print('ERROR:', e)
        else:
            QtWidgets.QMessageBox.critical(self, '错误', str(e))

    def _sync_stepper(self):
        cur = self.stack.currentIndex()
        mx = DONE if self.data is not None else (READY if self.dir is None else REVIEW)
        self.stepper.set_state(cur, mx)
        in_wb = self.data is not None and cur in (REVIEW, DONE)
        self.ready_hint.setVisible(not in_wb)
        for c in (self.chip_dir, self.chip_meta, self.chip_todo):
            c.setVisible(in_wb)
        self.btn_done.setVisible(cur == REVIEW and self.data is not None)
        self.btn_undo.setVisible(cur == REVIEW)
        self.btn_redo.setVisible(cur == REVIEW)
        self.btn_done.setEnabled(self.data is not None and cur == REVIEW)

    # ---------------- 阶段① 就绪 ----------------
    def choose_dir(self, d):
        self.dir = d
        self.chip_dir.setText(os.path.basename(d.rstrip('/')) or d)
        self.ready.set_dir_text(d)
        inp = engine.find_inputs(d)
        self.ready.set_recognition(inp)
        miss = []
        if not inp['ros']:
            miss.append('花名册')
        if not inp['tiao']:
            miss.append('调班表')
        if not inp['yuan'] and not inp['chu']:
            miss.append('原表')
        if miss:
            self.ready.set_state('err', '缺少「%s」' % '、'.join(miss), '该表缺失将无法判断当月班休/对齐人员，请补齐后重新选择文件夹。', can_start=False)
            self._sync_stepper()
            return
        try:
            issues = engine.validate(d)
        except Exception as e:
            issues = ['校验异常：%s' % e]
        if any('月份' in s for s in issues):
            self.ready.set_state('warn', '月份不一致 — 请先更换文件', '；'.join(issues), can_start=False)
            self._sync_stepper()
            return
        # 跨月决策档：检测到则套用名单/阈值
        self.memory = memory.load(d)
        memo_note = ''
        if self.memory:
            self.config = memory.to_config(self.memory)
            memo_note = '已检测到上月决策档，沿用名单/阈值与公出习惯。'
        # 三表齐 → prep 预览待办数（顺便生成初表）
        try:
            people = 0
            if inp['yuan']:
                rep = engine.prep(d, self.keep)
                self.leaver_cands = rep['lizhi_candidates']
                people = len(rep['kept'])
            wl = engine.worklist(d)
            body = '《初表》已整理，能自动算的（工作日/加班/迟到/外勤/全勤）已全部算完。' + memo_note
            self.ready.set_state('ok', '三张表均已识别，月份一致', body,
                                 people=people, month=wl['month'],
                                 leaver_n=len(self.leaver_cands), pending_n=len(wl['cases']),
                                 can_start=True)
        except Exception as e:
            self.ready.set_state('err', '解析失败', str(e), can_start=False)
        self._sync_stepper()

    def begin_review(self):
        try:
            self.recompute()
        except Exception as e:
            self.err(e)
            return
        self.stack.setCurrentIndex(REVIEW)
        self._sync_stepper()
        self.toast('已就绪，请在工作台复核')

    # ---------------- 重算中枢 ----------------
    def recompute(self):
        self.data = engine.analyze(self.dir, self.classify, self.config)
        # 跨月记忆：常态公出人的待定项 → 预选公出建议（仅预填，仍需确认）
        hb = memory.habitual_biz(self.memory)
        if hb:
            for c in self.data['pending']:
                if c['gh'] in hb and c['key'] not in self.classify:
                    c['suggest'] = 'B'
                    c['memo'] = True
        st = self.data['stats']
        self.chip_meta.setText('%d 月 · %d 人 · 加班 %g h' % (self.data['month'], st['people'], st['ot_total']))
        done = sum(1 for c in self.leaver_cands if c['gh'] in self.keep) + \
            sum(1 for c in self.data['pending'] if c['key'] in self.classify)
        total = len(self.leaver_cands) + len(self.data['pending'])
        self.chip_todo.setText('待办 %d/%d' % (done, total))
        self.chip_todo.set_tone('ok' if done == total else 'accent')
        # 刷新三栏
        self.workbench.todo.refresh(self.data, self.leaver_cands, self.keep, self.classify)
        self.workbench.grid.set_data(self.data, self.search, self.filter)
        if self.active:
            self.workbench.inspector.show_cell(self.data, *self.active)

    # ---------------- 决策动作（撤销栈包裹）----------------
    def _after_decision(self, label, before):
        after = undo.snapshot(self.classify, self.keep, self.config)
        self.undo.push(undo.Command(label, before, after))
        self.recompute()
        self._update_undo_buttons()
        self.toast(label + '，已重算')

    def do_reclassify(self, gh, day, val):
        before = undo.snapshot(self.classify, self.keep, self.config)
        self.classify['%s|%d' % (gh, day)] = val
        self._after_decision('归类 %s %d日 → %s' % (gh, day, VAL_CN.get(val, val)), before)

    def do_keep(self, gh, keep):
        before = undo.snapshot(self.classify, self.keep, self.config)
        if keep:
            self.keep.add(gh)
        else:
            self.keep.discard(gh)
        try:
            engine.prep(self.dir, self.keep)
        except Exception as e:
            self.err(e)
            return
        self._after_decision('离职取舍 %s → %s' % (gh, '保留' if keep else '删除'), before)

    def do_adopt_all(self):
        before = undo.snapshot(self.classify, self.keep, self.config)
        wl = engine.worklist(self.dir)
        n = 0
        for c in wl['cases']:
            if c['key'] not in self.classify:
                self.classify[c['key']] = c['suggest']
                n += 1
        self._after_decision('批量采纳建议 %d 项' % n, before)

    # ---------------- 撤销 / 重做 ----------------
    def _restore(self, state):
        self.classify = dict(state['classify'])
        self.keep = set(state['keep'])
        self.config = {'excl': set(state['config']['excl']), 'strict': dict(state['config']['strict']),
                       'font_only': set(state['config']['font_only'])}
        try:
            engine.prep(self.dir, self.keep)
        except Exception:
            pass
        self.recompute()
        if self.stack.currentIndex() == DONE:
            self.dashboard.refresh(self.data)
        self._update_undo_buttons()

    def undo_action(self):
        cmd = self.undo.undo()
        if cmd:
            self._restore(cmd.before)
            self.toast('已撤销：' + cmd.label)

    def redo_action(self):
        cmd = self.undo.redo()
        if cmd:
            self._restore(cmd.after)
            self.toast('已重做：' + cmd.label)

    def _update_undo_buttons(self):
        self.btn_undo.setEnabled(self.undo.can_undo())
        self.btn_redo.setEnabled(self.undo.can_redo())
        self.btn_undo.setToolTip(('撤销：' + self.undo.undo_label()) if self.undo.can_undo() else '无可撤销')
        self.btn_redo.setToolTip(('重做：' + self.undo.redo_label()) if self.undo.can_redo() else '无可重做')

    def on_locate(self, gh, day):
        self.active = (gh, day)
        if hasattr(self.workbench, 'grid') and self.workbench.grid is not None:
            self.workbench.grid.locate(gh, day)
        if self.data:
            self.workbench.inspector.show_cell(self.data, gh, day)

    def on_cell_selected(self, gh, day):
        self.active = (gh, day)
        if self.data:
            self.workbench.inspector.show_cell(self.data, gh, day)

    # ---------------- 高级设置抽屉 ----------------
    def show_drawer(self):
        self.drawer.set_config(self.config, self.data['employees'] if self.data else [])
        root = self.centralWidget()
        w, h = self.drawer.width(), root.height()
        self.backdrop.setGeometry(0, 0, root.width(), root.height())
        self.backdrop.show()
        self.backdrop.raise_()
        self.drawer.raise_()
        self.drawer.show()
        target = QtCore.QRect(root.width() - w, 0, w, h)
        if theme.MOTION:
            self._drawer_anim = QtCore.QPropertyAnimation(self.drawer, b'geometry', self)
            self._drawer_anim.setDuration(240)
            self._drawer_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self._drawer_anim.setStartValue(QtCore.QRect(root.width(), 0, w, h))
            self._drawer_anim.setEndValue(target)
            self._drawer_anim.start()
        else:
            self.drawer.setGeometry(target)

    def hide_drawer(self):
        self.drawer.hide()
        self.backdrop.hide()

    def apply_config(self, cfg):
        before = undo.snapshot(self.classify, self.keep, self.config)
        self.config = cfg
        self.hide_drawer()
        self._after_decision('应用高级设置', before)

    # ---------------- 阶段切换 ----------------
    def goto_step(self, idx):
        if idx == READY:
            self.stack.setCurrentIndex(READY)
        elif idx == REVIEW and self.data is not None:
            self.stack.setCurrentIndex(REVIEW)
        elif idx == DONE and self.data is not None:
            self.goto_done()
        self._sync_stepper()

    def goto_done(self):
        if self.data is None:
            return
        self.recompute()
        self.dashboard.refresh(self.data)
        self.stack.setCurrentIndex(DONE)
        self._sync_stepper()

    # ---------------- 导出 ----------------
    def do_export(self):
        try:
            rep = engine.build(self.dir, classify=self.classify or None, config=self.config)
            self.out_path = rep['out']
            memory.save(self.dir, self.config, self.classify)
            self.toast('已导出：%s' % os.path.basename(rep['out']))
            if hasattr(self.dashboard, 'set_exported'):
                self.dashboard.set_exported(rep['out'])
        except Exception as e:
            self.err(e)

    def open_result(self):
        if self.out_path and os.path.exists(self.out_path):
            _open_file(self.out_path)

    # ---------------- 决策存载（与 skill 共用 kq_*.txt）----------------
    def save_decisions(self):
        if not self.dir:
            return
        try:
            engine.write_keep(self.dir, self.keep)
            engine.write_classify(self.dir, self.classify)
            engine.write_config(self.dir, self.config)
            memory.save(self.dir, self.config, self.classify)
            self.toast('已保存决策：kq_keep / kq_classify / kq_config.txt')
        except Exception as e:
            self.err(e)

    def load_decisions(self):
        if not self.dir:
            return
        self.keep = engine.read_keep(self.dir)
        self.classify = engine.read_classify(self.dir)
        self.config = engine.read_config(self.dir)
        try:
            engine.prep(self.dir, self.keep)
        except Exception:
            pass
        self.recompute()
        self.dashboard.refresh(self.data)
        self.toast('已载入决策并重算')

    # ---------------- 键盘流 ----------------
    def _focus_search(self):
        if self.stack.currentIndex() == REVIEW:
            self.workbench.grid.header.search.setFocus()
            self.workbench.grid.header.search.selectAll()

    def _on_escape(self):
        if self.drawer.isVisible():
            self.hide_drawer()
            return
        h = self.workbench.grid.header.search
        if h.text():
            h.clear()

    def _todo_items(self):
        if not self.data:
            return []
        items = [('leaver', c) for c in self.leaver_cands]
        items += [('case', c) for c in self.data['pending'] if c['key'] not in self.classify]
        return items

    def _goto_kbd(self, items):
        if not items:
            self.kbd_idx = -1
            self.workbench.todo.set_current(None)
            return
        self.kbd_idx = max(0, min(self.kbd_idx, len(items) - 1))
        kind, c = items[self.kbd_idx]
        if kind == 'case':
            self.on_locate(c['gh'], c['day'])
            self.workbench.todo.set_current('case:%s' % c['key'])
        else:
            day = c.get('pd') and None
            self.workbench.todo.set_current('leaver:%s' % c['gh'])

    def keyPressEvent(self, e):
        if self.stack.currentIndex() != REVIEW:
            return super().keyPressEvent(e)
        if self.workbench.grid.header.search.hasFocus():
            return super().keyPressEvent(e)
        items = self._todo_items()
        k = e.key()
        cur = items[self.kbd_idx] if 0 <= self.kbd_idx < len(items) else (None, None)
        # 离职取舍 K/J
        if cur[0] == 'leaver' and k in (Qt.Key_K, Qt.Key_J):
            self.do_keep(cur[1]['gh'], k == Qt.Key_K)
            return self._goto_kbd(self._todo_items())
        # 归类 1/2/3/Enter
        if cur[0] == 'case' and k in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_Return, Qt.Key_Enter):
            val = {Qt.Key_1: 'G', Qt.Key_2: 'B', Qt.Key_3: 'R'}.get(k, cur[1]['suggest'])
            self.do_reclassify(cur[1]['gh'], cur[1]['day'], val)
            return self._goto_kbd(self._todo_items())
        # 上下移动
        if k == Qt.Key_Down and items:
            self.kbd_idx = min(self.kbd_idx + 1, len(items) - 1) if self.kbd_idx >= 0 else 0
            return self._goto_kbd(items)
        if k == Qt.Key_Up and items:
            self.kbd_idx = max(self.kbd_idx - 1, 0)
            return self._goto_kbd(items)
        super().keyPressEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.toast_w._reposition()


def _run_smoke(d):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    theme.MOTION = False
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setStyleSheet(theme.build_qss())
    w = MainWindow()
    w.headless = True
    w.choose_dir(d)
    if not w.ready.btn_start.isEnabled():
        print('SMOKE FAIL: 就绪页未通过校验')
        return 1
    w.begin_review()
    ok_review = w.data is not None and len(w.data['employees']) > 0
    w.goto_done()
    ok = ok_review and w.stack.currentIndex() == DONE
    print('SMOKE %s: people=%d month=%s pending=%d full=%s' % (
        'OK' if ok else 'FAIL', len(w.data['employees']) if w.data else 0,
        w.data['month'] if w.data else '?', w.data['stats']['pending'] if w.data else -1,
        w.data['stats']['full_list'] if w.data else []))
    return 0 if ok else 1


def main():
    if '--smoke' in sys.argv:
        i = sys.argv.index('--smoke')
        d = sys.argv[i + 1] if i + 1 < len(sys.argv) else os.getcwd()
        sys.exit(_run_smoke(d))
    if os.environ.get('KQ_NO_MOTION'):
        theme.MOTION = False        # 尊重「减少动态效果」偏好
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(theme.build_qss())
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
