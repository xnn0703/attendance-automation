# -*- coding: utf-8 -*-
"""跨月决策记忆：导出/保存时把名单、阈值、常态公出人写入 kq_memory.json；
下月在同目录检测到后，套用名单/阈值，并把「常态公出人」的待定项预选为公出建议（仅预填，仍需人工确认）。"""
import os
import json

FILE = 'kq_memory.json'


def save(d, config, classify):
    habitual_biz = sorted({k.split('|')[0] for k, v in classify.items() if v == 'B'})
    obj = {
        'noOtList': sorted(config['excl']),
        'lateThresholds': {g: '%02d%02d' % (m // 60, m % 60) for g, m in config['strict'].items()},
        'redOnlyList': sorted(config['font_only']),
        'habitualBiz': habitual_biz,
    }
    with open(os.path.join(d, FILE), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load(d):
    p = os.path.join(d, FILE)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except (ValueError, OSError):
        return None


def to_config(mem):
    strict = {}
    for g, hm in (mem.get('lateThresholds') or {}).items():
        try:
            strict[g] = int(hm[:2]) * 60 + int(hm[2:4])
        except (ValueError, TypeError):
            pass
    return {'excl': set(mem.get('noOtList') or []),
            'strict': strict,
            'font_only': set(mem.get('redOnlyList') or [])}


def habitual_biz(mem):
    return set(mem.get('habitualBiz') or []) if mem else set()
