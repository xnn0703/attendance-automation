# -*- coding: utf-8 -*-
"""无头端到端冒烟：驱动新三栏工作台全流程（就绪→复核→改判→撤销→完成→导出→决策存载→跨月记忆）。
需要数据目录（设 KQ_DIR；无真实数据时先跑 app/_make_sample.py 造合成三表）。"""
import os, sys
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PySide6 import QtWidgets
import engine, theme
import gui

theme.MOTION = False
SRC = engine.default_data_dir()


def main():
    if not engine.find_inputs(SRC)['ros']:
        print('SMOKE SKIP: 数据目录无三表（设 KQ_DIR 或先跑 _make_sample.py）：', SRC)
        return 0
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setStyleSheet(theme.build_qss())
    w = gui.MainWindow()
    w.headless = True

    # 阶段① 就绪
    w.choose_dir(SRC)
    assert w.ready.btn_start.isEnabled(), '就绪页未通过校验'

    # 阶段② 复核
    w.begin_review()
    assert w.data and w.data['employees'], 'analyze 无数据'
    n_people = len(w.data['employees'])
    pend0 = w.data['stats']['pending']
    print('就绪→复核：people=%d pending=%d' % (n_people, pend0))

    # 选中联动
    gh0 = w.data['employees'][0]['gh']
    w.on_cell_selected(gh0, 8)
    assert w.active == (gh0, 8), '选中联动失败'

    # 改判即时重算
    if pend0:
        case = w.data['pending'][0]
        w.do_reclassify(case['gh'], case['day'], 'B')
        assert w.data['stats']['pending'] == pend0 - 1, '改判未减少待归类'
        # 撤销 / 重做
        w.undo_action()
        assert w.data['stats']['pending'] == pend0, '撤销未恢复'
        w.redo_action()
        assert w.data['stats']['pending'] == pend0 - 1, '重做未生效'

    # 批量采纳 → pending 0
    w.do_adopt_all()
    assert w.data['stats']['pending'] == 0, '批量采纳后仍有待归类'

    # 搜索 / 筛选
    g = w.workbench.grid
    g._on_filter('anomaly')
    g._on_filter('all')
    g.goto_next_anomaly()
    assert w.active is not None, '跳异常未定位'

    # 高级设置抽屉
    w.show_drawer()
    assert not w.drawer.isHidden(), '抽屉未打开'
    w.apply_config({'excl': set(), 'strict': {}, 'font_only': set()})
    assert w.drawer.isHidden(), '应用配置后抽屉未关闭'

    # 阶段③ 完成 + 导出
    w.goto_done()
    assert w.stack.currentIndex() == gui.DONE
    w.do_export()
    assert os.path.exists(w.out_path), '导出文件不存在'

    # 决策存载 + 跨月记忆
    w.save_decisions()
    assert all(os.path.exists(os.path.join(SRC, f)) for f in
               ('kq_keep.txt', 'kq_classify.txt', 'kq_config.txt', 'kq_memory.json')), '决策/记忆未写盘'

    print('SMOKE OK: people=%d pending(after adopt)=%d out=%s memory=%s' % (
        n_people, w.data['stats']['pending'], os.path.basename(w.out_path),
        memory_summary()))
    return 0


def memory_summary():
    import memory
    m = memory.load(SRC)
    return 'habitualBiz=%s' % (m.get('habitualBiz') if m else None)


if __name__ == '__main__':
    sys.exit(main())
