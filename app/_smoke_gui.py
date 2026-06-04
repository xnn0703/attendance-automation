# -*- coding: utf-8 -*-
"""Headless smoke test: drive the GUI handlers (offscreen) end-to-end, no display."""
import os, sys, shutil, glob
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PySide6 import QtWidgets
import gui, engine, tempfile

SRC = r'D:\考勤'; T = os.path.join(SRC, '_smoke')
if os.path.exists(T):
    shutil.rmtree(T)
os.makedirs(T)
for f in glob.glob(os.path.join(SRC, '*.xlsx')):
    b = os.path.basename(f)
    if ('初表' in b) or ('考勤' in b):
        continue
    if ('原表' in b) or ('花名册' in b) or ('调班' in b):
        shutil.copy(f, T)

iss = engine.validate(T)
print('validate(inputs ready):', iss)
assert iss == [], iss
_empty = tempfile.mkdtemp()
iss2 = engine.validate(_empty)
print('validate(empty dir):', iss2)
assert iss2, 'empty dir should report issues'
shutil.rmtree(_empty)

app = QtWidgets.QApplication([])
w = gui.MainWindow()
assert w.set_dir(T), 'dir invalid'
w.confirm_dir()
w.run_prep()
print('after prep: kept=%d cand=%d' % (w.kept_tbl.rowCount(), w.cand_tbl.rowCount()))
w.apply_keep()
w.run_worklist()
print('worklist rows=%d' % w.work_tbl.rowCount())
w.save_classify()
print('classify size=%d' % len(w.classify))
w.run_build()
print('build out exists=%s summary rows=%d preview rows=%d cell_to_key=%d' % (
    os.path.exists(getattr(w, 'out_path', '')), w.sum_tbl.rowCount(), w.preview.rowCount(), len(w.cell_to_key)))
assert w.preview.rowCount() == 54, 'preview not rendered'
assert len(w.cell_to_key) > 0, 'cell_to_key empty (re-judge mapping missing)'
# 改判→即时重算 路径（绕过模态弹窗，直接改 classify 再 run_build）
k0 = next(iter(w.cell_to_key.values()))['key']
w.classify[k0] = 'B'
w.run_build()
print('re-judge rebuild: preview rows=%d cell_to_key=%d %s=%s' % (
    w.preview.rowCount(), len(w.cell_to_key), k0, w.classify[k0]))
assert w.preview.rowCount() == 54 and len(w.cell_to_key) > 0
# 保存/载入决策
w.save_decisions()
saved = all(os.path.exists(os.path.join(T, n)) for n in ('kq_keep.txt', 'kq_classify.txt', 'kq_config.txt'))
print('save decisions -> txt exists=%s' % saved)
assert saved
w.classify = {}; w.keep = set()
w.load_decisions()
print('load back: classify=%d (Y17074|9=%s)' % (len(w.classify), w.classify.get('Y17074|9')))
assert len(w.classify) > 0 and w.classify.get('Y17074|9') == 'B'
print('SMOKE OK')
shutil.rmtree(T)
