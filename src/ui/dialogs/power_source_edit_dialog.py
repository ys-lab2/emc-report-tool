from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from models.power_source import FREQUENCY_OPTIONS, POWER_SOURCE_KINDS, PowerSource


class PowerSourceEditDialog(QDialog):
    """電源(PowerSource)の種類・周波数・試験電圧をまとめて入力するダイアログ。
    構成図上には「AC100V 50Hz」のようにラベル表示される。"""

    def __init__(self, power_source: PowerSource | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("電源を編集" if power_source else "電源を追加")

        self._power_source = power_source or PowerSource(power_source_id="", project_id="")

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(POWER_SOURCE_KINDS)
        index = self.kind_combo.findText(self._power_source.kind)
        if index >= 0:
            self.kind_combo.setCurrentIndex(index)

        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("（未設定）", "")
        for freq in FREQUENCY_OPTIONS:
            self.frequency_combo.addItem(freq, freq)
        freq_index = self.frequency_combo.findData(self._power_source.frequency_hz)
        if freq_index >= 0:
            self.frequency_combo.setCurrentIndex(freq_index)

        self.test_voltage_edit = QLineEdit(self._power_source.test_voltage)
        self.test_voltage_edit.setPlaceholderText("例）AC100V、DC24V")

        self.label_edit = QLineEdit(self._power_source.label)
        self.label_edit.setPlaceholderText("任意の補足表示（未入力なら種類を表示）")

        form = QFormLayout()
        form.addRow("種類", self.kind_combo)
        form.addRow("周波数", self.frequency_combo)
        form.addRow("Test Voltage", self.test_voltage_edit)
        form.addRow("補足ラベル", self.label_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def apply_to(self, power_source: PowerSource) -> None:
        power_source.kind = self.kind_combo.currentText()
        power_source.frequency_hz = self.frequency_combo.currentData() or ""
        power_source.test_voltage = self.test_voltage_edit.text()
        power_source.label = self.label_edit.text()
