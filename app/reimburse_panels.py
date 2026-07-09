# -*- coding: utf-8 -*-
"""报销汇总工作台：扫描凭证、复核字段、导出汇总表。"""
import os
import subprocess

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

import reimburse
import reimburse_ocr
import theme
from widgets import make_card


def _lab(text, size=12, weight=400, color=theme.INK):
    lb = QtWidgets.QLabel(text)
    lb.setStyleSheet('color:%s;font-size:%spx;font-weight:%d;background:transparent;border:none;' % (color, size, weight))
    return lb


def _money(value):
    return '' if value is None else ('%.2f' % value)


def _to_float(text):
    text = (text or '').strip().replace(',', '')
    if not text:
        return None
    try:
        return round(float(text), 2)
    except ValueError:
        return None


def _to_int(text):
    text = (text or '').strip().replace(',', '')
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


class ReimburseView(QtWidgets.QWidget):
    """独立报销汇总页，不触碰考勤三阶段状态。"""

    INVOICE_HEADERS = ['状态', '发票类型', '开票日期', '发票代码', '发票号码', '项目名称', '金额', '税额', '价税合计', '科目', '来源']
    TRIP_HEADERS = ['状态', '日期', '出发公里数', '回司公里数', '用车公里数', '地址/目的地', '出发图', '结束图']
    PENDING_HEADERS = ['类型', '日期', '文件', '说明']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder = None
        self.report = None
        self.last_outputs = {}
        self._updating = False
        self._current_preview_path = ''
        self._selection_context = ('', -1, '', -1)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(14)

        head = make_card()
        hv = QtWidgets.QVBoxLayout(head)
        hv.setContentsMargins(18, 16, 18, 16)
        hv.setSpacing(12)
        top = QtWidgets.QHBoxLayout()
        title_col = QtWidgets.QVBoxLayout()
        title_col.setSpacing(3)
        title_col.addWidget(_lab('报销汇总', 22, 800))
        title_col.addWidget(_lab('离线解析 PDF 电子发票；图片发票和外访截图进入人工复核后导出。', 12.5, 400, theme.INK_2))
        top.addLayout(title_col, 1)
        self.btn_choose = QtWidgets.QPushButton('选择报销目录…')
        self.btn_choose.setProperty('primary', '1')
        self.btn_choose.clicked.connect(self._browse)
        self.btn_export = QtWidgets.QPushButton('导出汇总表')
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_outputs)
        self.btn_open = QtWidgets.QPushButton('打开输出目录')
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._open_output_dir)
        top.addWidget(self.btn_choose)
        top.addWidget(self.btn_export)
        top.addWidget(self.btn_open)
        hv.addLayout(top)
        self.dir_lb = _lab('未选择目录', 12, 400, theme.INK_3)
        self.dir_lb.setWordWrap(True)
        self.dir_lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.summary_lb = _lab('PDF 发票会自动解析；图片行可直接在表格里补录字段。', 12, 600, theme.ACCENT_STRONG)
        hv.addWidget(self.dir_lb)
        hv.addWidget(self.summary_lb)
        root.addWidget(head)

        split = QtWidgets.QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        left = QtWidgets.QWidget()
        lv = QtWidgets.QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(12)

        self.invoice_table = self._make_table(self.INVOICE_HEADERS, 260)
        self.invoice_table.currentCellChanged.connect(lambda *_: self._preview_from_invoice())
        lv.addWidget(self._section('发票明细（PDF 自动填，图片手工补）', self.invoice_table), 3)

        self.trip_table = self._make_table(self.TRIP_HEADERS, 170)
        self.trip_table.itemChanged.connect(self._on_trip_item_changed)
        self.trip_table.currentCellChanged.connect(lambda *_: self._preview_from_trip())
        lv.addWidget(self._section('外访行程（确认公里数和地址）', self.trip_table), 2)

        self.pending_table = self._make_table(self.PENDING_HEADERS, 120)
        self.pending_table.currentCellChanged.connect(lambda *_: self._preview_from_pending())
        lv.addWidget(self._section('其他图片凭证', self.pending_table), 1)
        split.addWidget(left)

        right = make_card()
        rv = QtWidgets.QVBoxLayout(right)
        rv.setContentsMargins(14, 14, 14, 14)
        rv.setSpacing(10)
        preview_head = QtWidgets.QHBoxLayout()
        preview_head.addWidget(_lab('图片预览', 13, 700))
        preview_head.addStretch(1)
        self.btn_ocr_current = QtWidgets.QPushButton('OCR 识别当前图片')
        self.btn_ocr_current.setToolTip('只预填当前选中图片对应的可编辑字段，导出前仍需人工核对')
        self.btn_ocr_current.clicked.connect(self.ocr_current_image)
        self.btn_ocr_batch = QtWidgets.QPushButton('批量 OCR 预填')
        self.btn_ocr_batch.setProperty('primary', '1')
        self.btn_ocr_batch.setToolTip('预填图片发票、外访出发/结束公里数和目的地地址')
        self.btn_ocr_batch.clicked.connect(self.ocr_batch_prefill)
        preview_head.addWidget(self.btn_ocr_current)
        preview_head.addWidget(self.btn_ocr_batch)
        rv.addLayout(preview_head)
        self.ocr_lb = _lab('OCR 结果只做预填，导出前请逐项核对。', 11.5, 400, theme.INK_3)
        self.ocr_lb.setWordWrap(True)
        rv.addWidget(self.ocr_lb)
        if not reimburse_ocr.is_available():
            self.btn_ocr_current.setEnabled(False)
            self.btn_ocr_batch.setEnabled(False)
            self.ocr_lb.setText('本地 OCR 依赖未安装：请安装 rapidocr / onnxruntime 后重启。')
        self.preview = QtWidgets.QLabel('选择左侧图片行后预览')
        self.preview.setMinimumSize(260, 360)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet('background:%s;border:1px solid %s;border-radius:10px;color:%s;font-size:12px;'
                                   % (theme.SURFACE_2, theme.LINE, theme.INK_3))
        rv.addWidget(self.preview, 1)
        self.export_lb = _lab('', 11.5, 400, theme.INK_2)
        self.export_lb.setWordWrap(True)
        self.export_lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
        rv.addWidget(self.export_lb)
        split.addWidget(right)
        split.setSizes([900, 320])
        root.addWidget(split, 1)

    def _make_table(self, headers, min_h):
        t = QtWidgets.QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setMinimumHeight(min_h)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(False)
        t.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        t.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        t.setWordWrap(False)
        t.setTextElideMode(Qt.ElideRight)
        t.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        t.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        t.horizontalHeader().setStretchLastSection(True)
        t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        t.setStyleSheet('QTableWidget{background:%s;border:1px solid %s;border-radius:10px;}'
                        'QTableWidget::item{padding:4px;color:%s;}'
                        'QTableWidget::item:selected{background:%s;color:%s;}'
                        'QTableWidget::item:focus{outline:none;}'
                        % (theme.SURFACE, theme.LINE, theme.INK, theme.ACCENT_SOFT, theme.INK))
        return t

    def _section(self, title, table):
        box = make_card()
        v = QtWidgets.QVBoxLayout(box)
        v.setContentsMargins(14, 12, 14, 14)
        v.setSpacing(9)
        v.addWidget(_lab(title, 13, 700))
        v.addWidget(table, 1)
        return box

    def _browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, '选择报销凭证目录', os.getcwd())
        if d:
            self.scan_dir(d)

    def scan_dir(self, folder):
        self.folder = folder
        self.dir_lb.setText(folder)
        try:
            self.report = reimburse.scan_reimburse_dir(folder)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, '扫描失败', str(e))
            return
        self._populate()
        self.btn_export.setEnabled(True)
        self.summary_lb.setText('已扫描：PDF 发票 %d 张，图片发票待录入 %d 张，外访行程 %d 天，其他图片 %d 张。'
                                % (self.report.pdf_count, self.report.image_invoice_count,
                                   len(self.report.trips), len(self.report.pending_images)))

    def _populate(self):
        self._updating = True
        try:
            self._populate_invoices()
            self._populate_trips()
            self._populate_pending()
        finally:
            self._updating = False

    def _populate_invoices(self):
        self.invoice_table.setRowCount(0)
        for rec in self.report.invoices:
            row = self.invoice_table.rowCount()
            self.invoice_table.insertRow(row)
            values = [
                rec.status, rec.invoice_type, rec.issue_date, rec.invoice_code, rec.invoice_number,
                rec.item_name, _money(rec.amount), _money(rec.tax), _money(rec.total),
                rec.category, os.path.basename(rec.source_file),
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                if col in (0, 10):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 10:
                    item.setData(Qt.UserRole, rec.source_file)
                    item.setData(Qt.UserRole + 1, rec.source_kind)
                    item.setToolTip(rec.source_file)
                if col in (6, 7, 8):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.invoice_table.setItem(row, col, item)
            self._shade_invoice_row(row, rec.status)
        self._set_widths(self.invoice_table, [76, 250, 112, 124, 210, 290, 82, 82, 98, 100, 190])

    def _populate_trips(self):
        self.trip_table.setRowCount(0)
        for trip in self.report.trips:
            row = self.trip_table.rowCount()
            self.trip_table.insertRow(row)
            values = [
                trip.status, trip.date, '', '', '', trip.address,
                os.path.basename(trip.start_file) if trip.start_file else '',
                os.path.basename(trip.end_file) if trip.end_file else '',
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                if col in (0, 1, 4, 6, 7):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 6:
                    item.setData(Qt.UserRole, trip.start_file)
                    item.setToolTip(trip.start_file)
                if col == 7:
                    item.setData(Qt.UserRole, trip.end_file)
                    item.setToolTip(trip.end_file)
                if col in (2, 3, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trip_table.setItem(row, col, item)
            self._shade_trip_row(row, trip.status)
        self._set_widths(self.trip_table, [92, 120, 96, 96, 96, 300, 130, 130])

    def _populate_pending(self):
        self.pending_table.setRowCount(0)
        for img in self.report.pending_images:
            row = self.pending_table.rowCount()
            self.pending_table.insertRow(row)
            values = [img.kind, img.date, os.path.basename(img.source_file), img.note]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 2:
                    item.setData(Qt.UserRole, img.source_file)
                    item.setToolTip(img.source_file)
                self.pending_table.setItem(row, col, item)
        self._set_widths(self.pending_table, [90, 120, 180, 420])

    def _set_widths(self, table, widths):
        for col, width in enumerate(widths):
            table.setColumnWidth(col, width)
        table.resizeRowsToContents()
        for row in range(table.rowCount()):
            table.setRowHeight(row, max(30, min(58, table.rowHeight(row))))

    def _shade_invoice_row(self, row, status):
        color = None
        if status == '已解析':
            color = QtGui.QColor('#FFFFFF')
        elif status == '重复':
            color = QtGui.QColor('#FDECEA')
        else:
            color = QtGui.QColor('#FEF6E7')
        for col in range(self.invoice_table.columnCount()):
            it = self.invoice_table.item(row, col)
            if it:
                it.setBackground(color)

    def _shade_trip_row(self, row, status):
        color = QtGui.QColor('#FFFFFF' if status == '已确认' else '#FEF6E7')
        for col in range(self.trip_table.columnCount()):
            it = self.trip_table.item(row, col)
            if it:
                it.setBackground(color)

    def ocr_current_image(self):
        kind, row, path, source_col = self._selected_image_context()
        if not path:
            QtWidgets.QMessageBox.information(self, 'OCR', '请先选择一行图片凭证或外访出发/结束图。')
            return
        try:
            result = reimburse_ocr.recognize_image(path)
            self._apply_ocr_result(kind, row, path, result, source_col)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'OCR 失败', str(e))

    def ocr_batch_prefill(self):
        if not self.report:
            return
        try:
            self.btn_ocr_batch.setEnabled(False)
            self.ocr_lb.setText('正在批量 OCR 预填，请稍候...')
            QtWidgets.QApplication.processEvents()
            n = 0
            for row in range(self.invoice_table.rowCount()):
                src_item = self.invoice_table.item(row, 10)
                if not src_item or src_item.data(Qt.UserRole + 1) != 'image':
                    continue
                path = src_item.data(Qt.UserRole)
                if path:
                    result = reimburse_ocr.recognize_image(path)
                    self._apply_invoice_ocr(row, path, result)
                    n += 1
                    QtWidgets.QApplication.processEvents()
            for row in range(self.trip_table.rowCount()):
                start_item = self.trip_table.item(row, 6)
                end_item = self.trip_table.item(row, 7)
                start = start_item.data(Qt.UserRole) if start_item else ''
                end = end_item.data(Qt.UserRole) if end_item else ''
                if start:
                    result = reimburse_ocr.recognize_image(start)
                    self._apply_trip_ocr(row, start, result, 6)
                    n += 1
                    QtWidgets.QApplication.processEvents()
                if end:
                    result = reimburse_ocr.recognize_image(end)
                    self._apply_trip_ocr(row, end, result, 7)
                    n += 1
                    QtWidgets.QApplication.processEvents()
            self.ocr_lb.setText('OCR 已预填 %d 张图片。请核对黄色/预填行后再导出。' % n)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'OCR 失败', str(e))
        finally:
            self.btn_ocr_batch.setEnabled(reimburse_ocr.is_available())

    def _selected_image_context(self):
        ctx = self._selection_context
        if ctx[2] and os.path.splitext(ctx[2])[1].lower() in reimburse.IMAGE_EXTS:
            return ctx
        table = self.focusWidget()
        if table is not self.invoice_table and table is not self.trip_table and table is not self.pending_table:
            # 鼠标点预览区后焦点可能不在表格，按当前选区推断。
            if self.invoice_table.currentRow() >= 0:
                table = self.invoice_table
            elif self.trip_table.currentRow() >= 0:
                table = self.trip_table
            else:
                table = self.pending_table
        if table is self.invoice_table:
            row = self.invoice_table.currentRow()
            item = self.invoice_table.item(row, 10) if row >= 0 else None
            path = item.data(Qt.UserRole) if item else ''
            if path and os.path.splitext(path)[1].lower() in reimburse.IMAGE_EXTS:
                return 'invoice', row, path, 10
        if table is self.trip_table:
            row = self.trip_table.currentRow()
            if row >= 0:
                col = self.trip_table.currentColumn()
                source_col = 7 if col == 7 else 6
                item = self.trip_table.item(row, source_col)
                path = item.data(Qt.UserRole) if item else ''
                if path and os.path.splitext(path)[1].lower() in reimburse.IMAGE_EXTS:
                    return 'trip', row, path, source_col
        if table is self.pending_table:
            row = self.pending_table.currentRow()
            item = self.pending_table.item(row, 2) if row >= 0 else None
            path = item.data(Qt.UserRole) if item else ''
            if path and os.path.splitext(path)[1].lower() in reimburse.IMAGE_EXTS:
                return 'pending', row, path, 2
        return '', -1, '', -1

    def _apply_ocr_result(self, kind, row, path, result, source_col):
        if kind == 'invoice':
            self._apply_invoice_ocr(row, path, result)
        elif kind == 'trip':
            self._apply_trip_ocr(row, path, result, source_col)
        else:
            self.ocr_lb.setText('OCR 文本：\n' + result.text[:600])
        self._show_preview(path)

    def _apply_invoice_ocr(self, row, path, result):
        rec = reimburse_ocr.invoice_suggestion(result, path)
        values = {
            0: 'OCR预填待确认' if rec.invoice_number or rec.total else 'OCR未识别',
            1: rec.invoice_type,
            2: rec.issue_date,
            3: rec.invoice_code,
            4: rec.invoice_number,
            5: rec.item_name,
            6: _money(rec.amount),
            7: _money(rec.tax),
            8: _money(rec.total),
            9: rec.category,
        }
        self._updating = True
        try:
            for col, value in values.items():
                if value:
                    self.invoice_table.item(row, col).setText(value)
            self._shade_invoice_row(row, '需复核')
            self.ocr_lb.setText('图片发票 OCR 已预填：%s。请核对票号、金额和项目名称。' % os.path.basename(path))
        finally:
            self._updating = False

    def _apply_trip_ocr(self, row, path, result, source_col):
        sug = reimburse_ocr.trip_suggestion(result)
        self._updating = True
        try:
            if sug.odometer is not None:
                target_col = 3 if source_col == 7 else 2
                self.trip_table.item(row, target_col).setText(str(sug.odometer))
            # 目的地优先取结束图；只有没有结束图时才用出发图地址兜底。
            if sug.address and (source_col == 7 or not self.trip_table.item(row, 7).data(Qt.UserRole)):
                self.trip_table.item(row, 5).setText(sug.address)
            self._update_trip_km(row)
            self.trip_table.item(row, 0).setText('OCR预填待确认')
            self._shade_trip_row(row, '需复核')
            self.ocr_lb.setText('行程 OCR 已预填：%s（%s）。请核对公里数和目的地。' % (os.path.basename(path), sug.note))
        finally:
            self._updating = False

    def _update_trip_km(self, row):
        start = _to_int(self._text(self.trip_table, row, 2))
        end = _to_int(self._text(self.trip_table, row, 3))
        km_item = self.trip_table.item(row, 4)
        if start is not None and end is not None and end >= start:
            km_item.setText(str(end - start))
        else:
            km_item.setText('')

    def _on_trip_item_changed(self, item):
        if self._updating or item.column() not in (2, 3, 5):
            return
        self._updating = True
        try:
            row = item.row()
            start = _to_int(self._text(self.trip_table, row, 2))
            end = _to_int(self._text(self.trip_table, row, 3))
            status_item = self.trip_table.item(row, 0)
            self._update_trip_km(row)
            status_item.setText('待导出校验')
            self._shade_trip_row(row, '需复核')
        finally:
            self._updating = False

    def _collect_invoice_records(self):
        rows = []
        for row in range(self.invoice_table.rowCount()):
            src_item = self.invoice_table.item(row, 10)
            source = src_item.data(Qt.UserRole) if src_item else ''
            kind = src_item.data(Qt.UserRole + 1) if src_item else 'pdf'
            rec = reimburse.InvoiceRecord(
                source_file=source or self._text(self.invoice_table, row, 10),
                invoice_type=self._text(self.invoice_table, row, 1),
                issue_date=self._normalize_date(self._text(self.invoice_table, row, 2)),
                invoice_code=self._text(self.invoice_table, row, 3),
                invoice_number=self._text(self.invoice_table, row, 4),
                item_name=self._text(self.invoice_table, row, 5),
                amount=_to_float(self._text(self.invoice_table, row, 6)),
                tax=_to_float(self._text(self.invoice_table, row, 7)),
                total=_to_float(self._text(self.invoice_table, row, 8)),
                category=self._text(self.invoice_table, row, 9) or '其他',
                source_kind=kind or 'pdf',
            )
            rows.append(rec)
        return rows

    def _collect_trips(self):
        rows = []
        for row in range(self.trip_table.rowCount()):
            start_item = self.trip_table.item(row, 6)
            end_item = self.trip_table.item(row, 7)
            start = start_item.data(Qt.UserRole) if start_item else ''
            end = end_item.data(Qt.UserRole) if end_item else ''
            trip = reimburse.TripRecord(
                date=self._normalize_date(self._text(self.trip_table, row, 1)),
                start_file=start or self._text(self.trip_table, row, 6),
                end_file=end or self._text(self.trip_table, row, 7),
                start_odometer=_to_int(self._text(self.trip_table, row, 2)),
                end_odometer=_to_int(self._text(self.trip_table, row, 3)),
                address=self._text(self.trip_table, row, 5),
            )
            rows.append(trip)
        return rows

    def export_outputs(self):
        if not self.folder:
            return
        records = self._collect_invoice_records()
        trips = self._collect_trips()
        out_dir = os.path.join(self.folder, reimburse.OUT_DIR_NAME)
        try:
            self.last_outputs = reimburse.build_reimburse_outputs(records, trips, out_dir, template_dir=self.folder)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, '导出失败', str(e))
            return
        self._refresh_status(records, trips)
        self.btn_open.setEnabled(True)
        out_dir = os.path.join(self.folder, reimburse.OUT_DIR_NAME)
        names = [os.path.basename(p) for p in self.last_outputs.values()]
        self.export_lb.setText('已导出到：\n%s\n\n%s' % (out_dir, '\n'.join('· ' + n for n in names)))
        self.export_lb.setToolTip('\n'.join(self.last_outputs.values()))

    def _refresh_status(self, records, trips):
        self._updating = True
        try:
            reimburse.validate_invoice_records(records)
            for row, rec in enumerate(records):
                self.invoice_table.item(row, 0).setText(rec.status)
                self._shade_invoice_row(row, rec.status)
            for row, trip in enumerate(trips):
                status = trip.status
                if trip.error:
                    status += '：' + trip.error
                self.trip_table.item(row, 0).setText(status)
                self._shade_trip_row(row, trip.status)
                if trip.trip_km is not None:
                    self.trip_table.item(row, 4).setText(str(trip.trip_km))
            self._set_widths(self.trip_table, [92, 120, 96, 96, 96, 300, 130, 130])
        finally:
            self._updating = False

    def _open_output_dir(self):
        if not self.folder:
            return
        out = os.path.join(self.folder, reimburse.OUT_DIR_NAME)
        if not os.path.isdir(out):
            return
        if os.sys.platform == 'win32':
            os.startfile(out)
        elif os.sys.platform == 'darwin':
            subprocess.run(['open', out])
        else:
            subprocess.run(['xdg-open', out])

    def _preview_from_invoice(self):
        row = self.invoice_table.currentRow()
        if row < 0:
            return
        item = self.invoice_table.item(row, 10)
        path = item.data(Qt.UserRole) if item else ''
        self._selection_context = ('invoice', row, path, 10)
        self._show_preview(path)

    def _preview_from_trip(self):
        row = self.trip_table.currentRow()
        col = self.trip_table.currentColumn()
        if row < 0:
            return
        source_col = 7 if col == 7 else 6
        item = self.trip_table.item(row, source_col)
        path = item.data(Qt.UserRole) if item else ''
        self._selection_context = ('trip', row, path, source_col)
        self._show_preview(path)

    def _preview_from_pending(self):
        row = self.pending_table.currentRow()
        if row < 0:
            return
        item = self.pending_table.item(row, 2)
        path = item.data(Qt.UserRole) if item else ''
        self._selection_context = ('pending', row, path, 2)
        self._show_preview(path)

    def _show_preview(self, path):
        self._current_preview_path = path or ''
        if not path or os.path.splitext(path)[1].lower() not in reimburse.IMAGE_EXTS:
            self.preview.setPixmap(QtGui.QPixmap())
            self.preview.setText('选择左侧图片行后预览')
            return
        pm = QtGui.QPixmap(path)
        if pm.isNull():
            self.preview.setPixmap(QtGui.QPixmap())
            self.preview.setText('无法预览图片：\n%s' % path)
            return
        scaled = pm.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setText('')
        self.preview.setPixmap(scaled)

    def _text(self, table, row, col):
        item = table.item(row, col)
        return item.text().strip() if item else ''

    def _normalize_date(self, text):
        text = (text or '').strip()
        if not text:
            return ''
        text = text.replace('.', '-').replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '')
        parts = [p for p in text.split('-') if p]
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            return '%04d-%02d-%02d' % (int(parts[0]), int(parts[1]), int(parts[2]))
        return text
