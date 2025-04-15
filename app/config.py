# coding:utf-8
from enum import Enum

from PyQt5.QtCore import Qt, QLocale
from PyQt5.QtGui import QGuiApplication, QFont
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            ColorConfigItem, OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, EnumSerializer, FolderValidator, ConfigSerializer)


class Language(Enum):
    """ Language enumeration """
    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """
    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


class Config(QConfig):
    """ Config of application """
    # folders
    midiFolders = ConfigItem(
        "Folders", "LocalMidi", [], FolderListValidator())
    defaultSaveFolder = ConfigItem(
        "Folders", "SaveFolder", "output", FolderValidator())

    # main window
    enableAcrylicBackground = ConfigItem(
        "MainWindow", "EnableAcrylicBackground", False, BoolValidator())
    minimizeToTray = ConfigItem(
        "MainWindow", "MinimizeToTray", True, BoolValidator())
    playBarColor = ColorConfigItem("MainWindow", "PlayBarColor", "#225C7F")
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # midi reading
    defaultTempo = RangeConfigItem(
        "MidiReading", "DefaultTempo", 120, RangeValidator(20, 300))
    autoPlay = ConfigItem(
        "MidiReading", "AutoPlay", False, BoolValidator())
    showTrackInfo = ConfigItem(
        "MidiReading", "ShowTrackInfo", True, BoolValidator())

    # software update
    checkUpdateAtStartUp = ConfigItem(
        "Update", "CheckUpdateAtStartUp", True, BoolValidator())


YEAR = 2023
AUTHOR = "MID Reader Team"
VERSION = "1.0.0"
HELP_URL = "https://github.com/yourusername/mid-reader/wiki"
FEEDBACK_URL = "https://github.com/yourusername/mid-reader/issues"


cfg = Config()
qconfig.load('config/config.json', cfg)
