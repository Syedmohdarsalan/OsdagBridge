"""Inline editing for explicitly enabled dimensions in the template CAD."""
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget


class CADDimensionCanvas(QWidget):
    dimension_edited = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dimension_editing_enabled = lambda: False
        self.dimension_labels = []
        self._dimension_editor = None
        self._dimension_key = None

    def register_dimension_label(self, rect, dimension):
        if dimension is not None:
            self.dimension_labels.append((rect.toAlignedRect(), *dimension))

    def mouseDoubleClickEvent(self, event):
        if (event.button() == Qt.LeftButton and self.dimension_editing_enabled()
                and self._dimension_editor is None):
            point = event.position().toPoint()
            for rect, key, value, unit in reversed(self.dimension_labels):
                if rect.contains(point):
                    editor = QLineEdit(f"{value:.10g}", self)
                    editor.setAccessibleName(f"Dimension value in {unit}")
                    editor.setToolTip(f"Enter a value in {unit}. Press Esc to cancel.")
                    editor.setStyleSheet("background: white; border: 1px solid #738b10; padding: 2px;")
                    width = min(self.width(), max(rect.width(), 84))
                    height = max(rect.height(), editor.sizeHint().height())
                    editor.setGeometry(min(rect.x(), self.width() - width),
                                       max(0, rect.y()), width, height)
                    self._dimension_editor = editor
                    self._dimension_key = key
                    # Blank canvas and some toolbar controls do not take focus.
                    QApplication.instance().installEventFilter(self)
                    editor.editingFinished.connect(self._finish_dimension_edit)
                    editor.show()
                    editor.setFocus()
                    editor.selectAll()
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)

    def eventFilter(self, obj, event):
        editor = self._dimension_editor
        if editor is not None:
            if obj is editor and event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                self._finish_dimension_edit(commit=False)
                return True
            if event.type() == QEvent.MouseButtonPress and isinstance(obj, QWidget):
                point = editor.mapFromGlobal(event.globalPosition().toPoint())
                if not editor.rect().contains(point):
                    self._finish_dimension_edit()
        return super().eventFilter(obj, event)

    def _finish_dimension_edit(self, *, commit=True):
        editor = self._dimension_editor
        if editor is None:
            return
        key = self._dimension_key
        self._dimension_editor = None
        self._dimension_key = None
        QApplication.instance().removeEventFilter(self)
        text = editor.text().strip()
        editor.hide()
        editor.deleteLater()
        if commit and self.dimension_editing_enabled():
            self.dimension_edited.emit(key, text)
