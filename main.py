import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentTranslator

from app.config import cfg
from app.view.main_window import MainWindow

if __name__ == '__main__':
    # Enable high DPI scaling
    if cfg.get(cfg.dpiScale) == "Auto":
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    else:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Create necessary directories
    os.makedirs('config', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # Create application instance
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    
    # Internationalization
    locale = cfg.get(cfg.language).value
    fluentTranslator = FluentTranslator(locale)
    app.installTranslator(fluentTranslator)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())