# coding:utf-8
import os
import sys
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

def setup_global_exception_handler():
    """
    Set up a global exception handler to catch unhandled exceptions
    and display them instead of silently crashing
    """
    def excepthook(exc_type, exc_value, exc_traceback):
        # Format the exception details
        exception_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Log the error to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"error_{timestamp}.log")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Error occurred at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Platform: {sys.platform}\n")
            f.write(f"Exception details:\n{exception_text}\n")
        
        # Show error dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Application Error")
        msg_box.setText(f"An unexpected error occurred: {str(exc_value)}")
        msg_box.setInformativeText(f"The error has been logged to: {log_file}")
        msg_box.setDetailedText(exception_text)
        msg_box.exec_()
        
    # Set the exception hook
    sys.excepthook = excepthook
