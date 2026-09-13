from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

import config as config_module
from logging_setup import setup_logging
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> int:
    setup_logging()
    logger.info("Application starting")

    app = QApplication(sys.argv)

    config = config_module.load_config()
    app.setFont(QFont(config.font_family, config.font_size))

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    logger.info("Application exiting with code %s", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
