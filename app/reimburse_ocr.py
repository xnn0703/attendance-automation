# -*- coding: utf-8 -*-
"""本地 OCR 预填：RapidOCR/ONNX Runtime 适配 + 报销字段候选提取。

OCR 结果只用于预填，GUI 必须让用户复核后再导出。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Optional, Sequence, Tuple

import reimburse


@dataclass
class OcrWord:
    text: str
    score: float = 0.0
    box: Optional[Tuple[Tuple[float, float], ...]] = None


@dataclass
class OcrResult:
    words: List[OcrWord]
    text: str
    engine: str = 'RapidOCR'


@dataclass
class TripSuggestion:
    odometer: Optional[int] = None
    odometer_score: float = 0.0
    address: str = ''
    address_score: float = 0.0
    note: str = ''


class OcrUnavailable(RuntimeError):
    pass


def is_available() -> bool:
    try:
        import rapidocr  # noqa: F401
        import onnxruntime  # noqa: F401
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def _engine():
    try:
        from rapidocr import RapidOCR
    except Exception as e:
        raise OcrUnavailable('未安装本地 OCR 依赖 rapidocr/onnxruntime：%s' % e)
    return RapidOCR()


def recognize_image(path: str) -> OcrResult:
    if not is_available():
        raise OcrUnavailable('本地 OCR 依赖未安装，请安装 rapidocr 和 onnxruntime 后重试')
    out = _engine()(path)
    txts = tuple(getattr(out, 'txts', ()) or ())
    scores = tuple(getattr(out, 'scores', ()) or ())
    boxes = getattr(out, 'boxes', None)
    words: List[OcrWord] = []
    for idx, text in enumerate(txts):
        score = float(scores[idx]) if idx < len(scores) else 0.0
        box = None
        if boxes is not None and idx < len(boxes):
            try:
                box = tuple((float(p[0]), float(p[1])) for p in boxes[idx])
            except Exception:
                box = None
        words.append(OcrWord(str(text).strip(), score, box))
    return OcrResult(words=words, text='\n'.join(w.text for w in words))


def trip_suggestion(result: OcrResult) -> TripSuggestion:
    addr_word = _best_address(result.words)
    odo_word = _best_odometer(result.words)
    note = []
    if odo_word:
        note.append('公里数 %.0f%%' % (odo_word.score * 100))
    if addr_word:
        note.append('地址 %.0f%%' % (addr_word.score * 100))
    return TripSuggestion(
        odometer=_parse_odometer(odo_word.text) if odo_word else None,
        odometer_score=odo_word.score if odo_word else 0.0,
        address=addr_word.text if addr_word else '',
        address_score=addr_word.score if addr_word else 0.0,
        note='，'.join(note) if note else '未识别到可靠公里数/地址',
    )


def invoice_suggestion(result: OcrResult, source_file: str) -> reimburse.InvoiceRecord:
    rec = reimburse._parse_invoice_text(result.text, source_file)
    rec.source_kind = 'image'
    rec.category = reimburse.infer_category(source_file, rec.item_name, result.text)
    _repair_ocr_invoice_amounts(rec, result.words)
    reimburse.validate_invoice_records([rec])
    if rec.status == '已解析':
        rec.status = 'OCR预填'
        rec.error = '请人工核对后再导出'
    elif rec.error:
        rec.error = 'OCR预填不完整：' + rec.error
    return rec


def _best_address(words: Sequence[OcrWord]) -> Optional[OcrWord]:
    cands = []
    for w in words:
        text = w.text.strip()
        if not text.startswith('中国'):
            continue
        if len(text) < 10:
            continue
        if not any(x in text for x in ('省', '市', '区', '县', '路', '号')):
            continue
        cands.append(w)
    if not cands:
        return None
    return max(cands, key=lambda w: (w.score, len(w.text)))


def _best_odometer(words: Sequence[OcrWord]) -> Optional[OcrWord]:
    cands = []
    for w in words:
        n = _parse_odometer(w.text)
        if n is None:
            continue
        y = _box_center_y(w.box)
        # 仪表盘总里程在照片上半部；过滤相册日期、分辨率、发票号等下半部数字。
        if y is not None and y > 950:
            continue
        cands.append((w, n))
    if not cands:
        return None
    return max(cands, key=lambda item: (item[0].score, item[1]))[0]


def _parse_odometer(text: str) -> Optional[int]:
    s = text.replace(' ', '').replace(',', '')
    m = re.search(r'(?<!\d)(\d{5,7})(?:km)?(?!\d)', s, re.I)
    if not m:
        return None
    n = int(m.group(1))
    if 10000 <= n <= 9999999:
        return n
    return None


def _box_center_y(box) -> Optional[float]:
    if not box:
        return None
    try:
        return sum(p[1] for p in box) / len(box)
    except Exception:
        return None


def _repair_ocr_invoice_amounts(rec: reimburse.InvoiceRecord, words: Sequence[OcrWord]) -> None:
    lines = [w.text for w in words]
    if not rec.invoice_type and any('发票号码' in line for line in lines):
        if any('成品油' in line for line in lines):
            rec.invoice_type = '成品油电子发票（普通发票）'
        elif any(line.startswith('电子发') for line in lines) or any('税务局' in line for line in lines):
            rec.invoice_type = '电子发票（普通发票）'

    total = _small_total(lines)
    pair = _amount_tax_pair_near_item(lines, total)
    if total is not None:
        rec.total = total
    if pair:
        rec.amount, rec.tax = pair


def _small_total(lines: Sequence[str]) -> Optional[float]:
    for line in lines:
        if '小写' not in line:
            continue
        nums = _line_numbers(line)
        if nums:
            return nums[-1]
    return None


def _amount_tax_pair_near_item(lines: Sequence[str], total: Optional[float]) -> Optional[Tuple[float, float]]:
    if total is None:
        return None
    start = next((i for i, line in enumerate(lines) if line.strip().startswith('*')), None)
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.search(r'合\s*计|价税合计|备注|开票人', lines[i]):
            end = i
            break
    nums: List[float] = []
    for line in lines[start + 1:end]:
        if '%' in line:
            continue
        for n in _line_numbers(line):
            nums.append(n)
    for i, a in enumerate(nums):
        for b in nums[i + 1:]:
            if abs((a + b) - total) <= 0.02:
                return (round(max(a, b), 2), round(min(a, b), 2))
    return None


def _line_numbers(line: str) -> List[float]:
    vals = []
    for m in re.finditer(r'(?:[¥￥]\s*)?([0-9]+(?:\.[0-9]{1,2})?)', line):
        try:
            vals.append(round(float(m.group(1)), 2))
        except ValueError:
            pass
    return vals
