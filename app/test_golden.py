# -*- coding: utf-8 -*-
"""金标准回归：用 Python 引擎在副本目录跑 prep+build，与 PS 产出的《考勤》逐格比对(值/底色/红字)。"""
import os, sys, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, openpyxl

SRC = engine.default_data_dir()
T = os.path.join(SRC, '_gtest')

MAY = {}
for k in ['Y28001|9', 'Y28001|30', 'Y28001|31', 'Y28002|9', 'Y28002|31', 'Y28006|9', 'Y28006|31', 'Y28008|31']:
    MAY[k] = 'B'
for k in ['Y28002|12', 'Y28005|22', 'Y28005|31', 'Y28008|11', 'Y28020|7', 'Y28053|21', 'Y28073|22']:
    MAY[k] = 'G'
for k in ['Y17074|9', 'Y17074|20', 'Y28006|18', 'Y28006|19', 'Y28006|20', 'Y28006|21', 'Y28020|14',
          'Y28055|13', 'Y28055|22', 'Y28061|13', 'Y28066|15', 'Y28068|11',
          'Y28069|27', 'Y28069|28', 'Y28069|29', 'Y28069|30', 'Y28069|31']:
    MAY[k] = 'R'

def setup():
    if os.path.exists(T):
        shutil.rmtree(T)
    os.makedirs(T)
    for f in glob.glob(os.path.join(SRC, '*.xlsx')):
        b = os.path.basename(f)
        if ('初表' in b) or ('考勤' in b):
            continue
        if ('原表' in b) or ('花名册' in b) or ('调班' in b):
            shutil.copy(f, T)

def info(c):
    fill = None
    try:
        if c.fill is not None and c.fill.patternType == 'solid':
            rgb = c.fill.fgColor.rgb
            fill = rgb if isinstance(rgb, str) else None
    except Exception:
        fill = None
    fred = False
    try:
        col = c.font.color
        if col is not None and getattr(col, 'rgb', None) == 'FFFF0000':
            fred = True
    except Exception:
        pass
    return (c.value, fill, fred)

def norm_val(v):
    if v is None:
        return ''
    if isinstance(v, (int, float)):
        rv = round(float(v), 3)
        return str(int(rv)) if rv == int(rv) else str(rv)
    return str(v).strip()

def main():
    setup()
    engine.prep(T, set())
    rpt = engine.build(T, classify=MAY, config=engine.default_config())
    print('built: total_ot=%g quan=%d -> %s' % (rpt['total_ot'], rpt['quan_count'], os.path.basename(rpt['out'])))
    golden = engine.find_inputs(SRC)['kao']
    g = openpyxl.load_workbook(golden).active
    n = openpyxl.load_workbook(rpt['out']).active
    print('golden dims=%s rows=%d ; new dims=%s rows=%d' % (g.dimensions, g.max_row, n.dimensions, n.max_row))
    maxr = max(g.max_row, n.max_row)
    val_d = fill_d = font_d = ws_d = 0
    shown = 0
    for r in range(1, maxr + 1):
        for col in range(1, 38):
            gi = info(g.cell(r, col)); ni = info(n.cell(r, col))
            gv, nv = norm_val(gi[0]), norm_val(ni[0])
            vdiff = gv != nv
            wsdiff = (vdiff and gv.replace(' ', '') == nv.replace(' ', ''))  # whitespace-only
            if wsdiff:
                ws_d += 1
            elif vdiff:
                val_d += 1
            if gi[1] != ni[1]:
                fill_d += 1
            if gi[2] != ni[2]:
                font_d += 1
            if ((vdiff and not wsdiff) or gi[1] != ni[1] or gi[2] != ni[2]) and shown < 40:
                shown += 1
                print('DIFF r%d c%d | golden v=%r fill=%s fred=%s | new v=%r fill=%s fred=%s'
                      % (r, col, gv, gi[1], gi[2], nv, ni[1], ni[2]))
    print('\nRESULT: value_diffs(non-ws)=%d  whitespace_only=%d  fill_diffs=%d  font_diffs=%d' % (val_d, ws_d, fill_d, font_d))
    if val_d == 0 and fill_d == 0 and font_d == 0:
        print('ZERO-REGRESSION')
        sys.exit(0)
    else:
        print('REGRESSION FOUND')
        sys.exit(1)

main()
