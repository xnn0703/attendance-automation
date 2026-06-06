# -*- coding: utf-8 -*-
"""撤销/重做栈：决策动作（归类/离职取舍/批量采纳/配置）以「状态快照」形式入栈。
state = {'classify': dict, 'keep': set, 'config': {excl,strict,font_only}}；上限 50 步。"""


def snapshot(classify, keep, config):
    return {
        'classify': dict(classify),
        'keep': set(keep),
        'config': {'excl': set(config['excl']), 'strict': dict(config['strict']),
                   'font_only': set(config['font_only'])},
    }


class Command:
    def __init__(self, label, before, after):
        self.label = label
        self.before = before
        self.after = after


class UndoStack:
    def __init__(self, limit=50):
        self._undo = []
        self._redo = []
        self.limit = limit

    def push(self, cmd):
        self._undo.append(cmd)
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()

    def can_undo(self):
        return bool(self._undo)

    def can_redo(self):
        return bool(self._redo)

    def undo(self):
        if not self._undo:
            return None
        cmd = self._undo.pop()
        self._redo.append(cmd)
        return cmd

    def redo(self):
        if not self._redo:
            return None
        cmd = self._redo.pop()
        self._undo.append(cmd)
        return cmd

    def undo_label(self):
        return self._undo[-1].label if self._undo else ''

    def redo_label(self):
        return self._redo[-1].label if self._redo else ''
