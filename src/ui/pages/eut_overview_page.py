from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.eut_overview import EutOverview
from repositories import eut_overview_repository
from services.project_service import ProjectHandle

POWER_SUPPLY_OPTIONS = [
    ("dc_2p", "DC (2P)"),
    ("dc_2p_e", "DC (2P+E)"),
    ("single_phase_2p", "1phase (2P)"),
    ("single_phase_2p_e", "1phase (2P+E)"),
    ("three_phase_3p_e", "3phase (3P(Δ)+E)"),
    ("three_phase_4p_e", "3phase (4P(Y)+E)"),
]


class EutOverviewPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._overview: EutOverview | None = None
        self._loading = False

        self.kind_edit = QLineEdit()
        self.model_name_edit = QLineEdit()
        self.serial_edit = QLineEdit()
        self.operating_program_edit = QLineEdit()

        self.mass_production_radio = QRadioButton("Mass-production")
        self.pre_production_radio = QRadioButton("Pre-production")
        self.sample_type_group = QButtonGroup(self)
        self.sample_type_group.addButton(self.mass_production_radio)
        self.sample_type_group.addButton(self.pre_production_radio)

        self.width_edit = QLineEdit()
        self.depth_edit = QLineEdit()
        self.height_edit = QLineEdit()

        self.max_frequency_edit = QLineEdit()
        self.wireless_frequency_edit = QLineEdit()

        self.power_checkboxes: dict[str, QCheckBox] = {
            code: QCheckBox(label) for code, label in POWER_SUPPLY_OPTIONS
        }
        self.rating_power_value_edit = QLineEdit()
        self.rating_power_value_edit.setPlaceholderText("例）DC 24V, 2A")

        self.tested_condition_edit = QLineEdit()
        self.date_of_manufacture_edit = QLineEdit()
        self.date_of_manufacture_edit.setPlaceholderText("例）2025年3月")

        self.manufacturer_name_edit = QLineEdit()
        self.manufacturer_address_edit = QLineEdit()

        self.attachment_edit = QLineEdit()
        self.option_edit = QLineEdit()

        self.date_sample_received_edit = QLineEdit()
        self.test_engineer_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("A) Kind of Equipment", self.kind_edit)
        form.addRow("B) Model name", self.model_name_edit)
        form.addRow("C) Serial No", self.serial_edit)
        form.addRow("D) Operating program used", self.operating_program_edit)

        sample_type_row = QHBoxLayout()
        sample_type_row.addWidget(self.mass_production_radio)
        sample_type_row.addWidget(self.pre_production_radio)
        sample_type_row.addStretch(1)
        form.addRow("E) Type of Sample Tested", sample_type_row)

        dimension_row = QHBoxLayout()
        dimension_row.addWidget(QLabel("W"))
        dimension_row.addWidget(self.width_edit)
        dimension_row.addWidget(QLabel("D"))
        dimension_row.addWidget(self.depth_edit)
        dimension_row.addWidget(QLabel("H"))
        dimension_row.addWidget(self.height_edit)
        dimension_row.addWidget(QLabel("mm"))
        form.addRow("F) Dimension(mm)", dimension_row)

        form.addRow("G) Max Frequency", self.max_frequency_edit)
        form.addRow("H) Wireless frequency", self.wireless_frequency_edit)

        power_box = QGroupBox()
        power_layout = QVBoxLayout(power_box)
        for checkbox in self.power_checkboxes.values():
            power_layout.addWidget(checkbox)
        power_layout.addWidget(self.rating_power_value_edit)
        form.addRow("I) Rating Power Supply", power_box)

        form.addRow("J) Tested Condition", self.tested_condition_edit)
        form.addRow("K) Date of Manufacture", self.date_of_manufacture_edit)
        form.addRow("L) Manufacturer 会社名", self.manufacturer_name_edit)
        form.addRow("L) Manufacturer 住所", self.manufacturer_address_edit)
        form.addRow("M) Attachment", self.attachment_edit)
        form.addRow("N) Option", self.option_edit)
        form.addRow("P) Date of Sample Received", self.date_sample_received_edit)
        form.addRow("Q) Test Engineer", self.test_engineer_edit)

        form_widget = QWidget()
        form_widget.setLayout(form)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll)

        for edit in (
            self.kind_edit,
            self.model_name_edit,
            self.serial_edit,
            self.operating_program_edit,
            self.width_edit,
            self.depth_edit,
            self.height_edit,
            self.max_frequency_edit,
            self.wireless_frequency_edit,
            self.rating_power_value_edit,
            self.tested_condition_edit,
            self.date_of_manufacture_edit,
            self.manufacturer_name_edit,
            self.manufacturer_address_edit,
            self.attachment_edit,
            self.option_edit,
            self.date_sample_received_edit,
            self.test_engineer_edit,
        ):
            edit.editingFinished.connect(self._save)

        self.mass_production_radio.toggled.connect(self._save)
        self.pre_production_radio.toggled.connect(self._save)
        for checkbox in self.power_checkboxes.values():
            checkbox.toggled.connect(self._save)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        conn = self._handle.connection
        overview = eut_overview_repository.get_by_project(conn, self._handle.project.project_id)
        if overview is None:
            overview = EutOverview(eut_overview_id="", project_id=self._handle.project.project_id)
        self._overview = overview

        self.kind_edit.setText(overview.kind_of_equipment)
        self.model_name_edit.setText(overview.model_name)
        self.serial_edit.setText(overview.serial_no)
        self.operating_program_edit.setText(overview.operating_program)

        self.mass_production_radio.setChecked(overview.sample_type == "mass_production")
        self.pre_production_radio.setChecked(overview.sample_type == "pre_production")

        self.width_edit.setText(_format_dimension(overview.width_mm))
        self.depth_edit.setText(_format_dimension(overview.depth_mm))
        self.height_edit.setText(_format_dimension(overview.height_mm))

        self.max_frequency_edit.setText(overview.max_frequency)
        self.wireless_frequency_edit.setText(overview.wireless_frequency)

        for code, checkbox in self.power_checkboxes.items():
            checkbox.setChecked(code in overview.rating_power_supply_types)
        self.rating_power_value_edit.setText(overview.rating_power_supply_value)

        self.tested_condition_edit.setText(overview.tested_condition)
        self.date_of_manufacture_edit.setText(overview.date_of_manufacture)
        self.manufacturer_name_edit.setText(overview.manufacturer_name)
        self.manufacturer_address_edit.setText(overview.manufacturer_address)
        self.attachment_edit.setText(overview.attachment)
        self.option_edit.setText(overview.option)
        self.date_sample_received_edit.setText(overview.date_sample_received)
        self.test_engineer_edit.setText(overview.test_engineer)

        self._loading = False

    def _save(self) -> None:
        if self._handle is None or self._loading or self._overview is None:
            return

        overview = self._overview
        overview.kind_of_equipment = self.kind_edit.text()
        overview.model_name = self.model_name_edit.text()
        overview.serial_no = self.serial_edit.text()
        overview.operating_program = self.operating_program_edit.text()

        if self.mass_production_radio.isChecked():
            overview.sample_type = "mass_production"
        elif self.pre_production_radio.isChecked():
            overview.sample_type = "pre_production"
        else:
            overview.sample_type = ""

        overview.width_mm = _parse_dimension(self.width_edit.text())
        overview.depth_mm = _parse_dimension(self.depth_edit.text())
        overview.height_mm = _parse_dimension(self.height_edit.text())

        overview.max_frequency = self.max_frequency_edit.text()
        overview.wireless_frequency = self.wireless_frequency_edit.text()

        overview.rating_power_supply_types = [
            code for code, checkbox in self.power_checkboxes.items() if checkbox.isChecked()
        ]
        overview.rating_power_supply_value = self.rating_power_value_edit.text()

        overview.tested_condition = self.tested_condition_edit.text()
        overview.date_of_manufacture = self.date_of_manufacture_edit.text()
        overview.manufacturer_name = self.manufacturer_name_edit.text()
        overview.manufacturer_address = self.manufacturer_address_edit.text()
        overview.attachment = self.attachment_edit.text()
        overview.option = self.option_edit.text()
        overview.date_sample_received = self.date_sample_received_edit.text()
        overview.test_engineer = self.test_engineer_edit.text()

        self._overview = eut_overview_repository.upsert(self._handle.connection, overview)


def _format_dimension(value: float | None) -> str:
    if value is None:
        return ""
    if value == int(value):
        return str(int(value))
    return str(value)


def _parse_dimension(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
