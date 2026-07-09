# -*- coding: utf-8 -*-
"""无头端到端冒烟：驱动新三栏工作台全流程（就绪→复核→改判→撤销→完成→导出→决策存载→跨月记忆）。
默认优先使用 KQ_DIR/default_data_dir；若目录无三表，则自动生成临时合成数据并清理。"""
import os, sys, tempfile, shutil
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PySide6 import QtWidgets
import engine, theme
import gui
import _make_sample

theme.MOTION = False
SRC = engine.default_data_dir()


def make_temp_src():
    tmp = tempfile.mkdtemp(prefix='kq_smoke_')
    _make_sample.make_yuan(os.path.join(tmp, '南京六部（原表）.xlsx'))
    _make_sample.make_roster(os.path.join(tmp, '员工花名册.xlsx'))
    _make_sample.make_tiao(os.path.join(tmp, '调班表.xlsx'))
    return tmp


def main():
    src = SRC
    cleanup = False
    reim_tmp = None
    inp = engine.find_inputs(src)
    if not (inp['ros'] and inp['tiao'] and (inp['yuan'] or inp['chu'])):
        src = make_temp_src()
        cleanup = True
        print('SMOKE DATA: 默认目录无三表，已生成临时合成数据：', src)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setStyleSheet(theme.build_qss())
    w = gui.MainWindow()
    w.headless = True

    try:
        # 阶段① 就绪
        w.choose_dir(src)
        assert w.ready.btn_start.isEnabled(), '就绪页未通过校验'
        w.clear_current_data()
        assert w.dir is None and w.data is None, '清除数据未清空主状态'
        assert not w.ready.btn_start.isEnabled(), '清除数据后开始按钮仍可用'
        assert not w.ready.drop.isHidden(), '清除数据后未恢复选择/拖入区'
        w.choose_dir(src)
        assert w.ready.btn_start.isEnabled(), '清除后重新选择未通过校验'

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
        assert all(os.path.exists(os.path.join(src, f)) for f in
                   ('kq_keep.txt', 'kq_classify.txt', 'kq_config.txt', 'kq_memory.json')), '决策/记忆未写盘'

        # 报销汇总入口：最小无头流程
        reim_tmp = tempfile.mkdtemp(prefix='reim_smoke_')
        trip_dir = os.path.join(reim_tmp, '6.21外访')
        os.makedirs(trip_dir, exist_ok=True)
        for name in ('6.21出发.jpg', '6.21结束.jpg'):
            with open(os.path.join(trip_dir, name), 'wb') as f:
                f.write(b'')
        w.set_mode('reimburse')
        assert w.main_stack.currentIndex() == 1, '未切换到报销汇总'
        w.reimburse.scan_dir(reim_tmp)
        assert w.reimburse.trip_table.rowCount() == 1, '报销行程未识别'
        w.reimburse.trip_table.item(0, 2).setText('131066')
        w.reimburse.trip_table.item(0, 3).setText('131188')
        w.reimburse.trip_table.item(0, 5).setText('中国江苏省南京市浦口区天华北路1号')
        w.reimburse.export_outputs()
        assert all(os.path.exists(p) for p in w.reimburse.last_outputs.values()), '报销汇总导出文件不存在'

        print('SMOKE OK: people=%d pending(after adopt)=%d out=%s memory=%s' % (
            n_people, w.data['stats']['pending'], os.path.basename(w.out_path),
            memory_summary(src)))
        return 0
    finally:
        if cleanup:
            shutil.rmtree(src, ignore_errors=True)
        if reim_tmp:
            shutil.rmtree(reim_tmp, ignore_errors=True)


def memory_summary(src):
    import memory
    m = memory.load(src)
    return 'habitualBiz=%s' % (m.get('habitualBiz') if m else None)


if __name__ == '__main__':
    sys.exit(main())
