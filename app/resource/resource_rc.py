# coding:utf-8
"""
This file contains the compiled resources for the application.
Normally it would be generated using:
pyrcc5 -o resource_rc.py resources.qrc

For now, it's a placeholder with a simple icon.
"""

from PyQt5.QtCore import QObject

# We would normally use pyrcc5 to compile resource files,
# but for this example, we can create a simple function
# to load icons from the project folder

def get_app_icon():
    """Return the path to the app icon"""
    return "app/resource/images/icon.png"
