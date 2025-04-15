# coding:utf-8
import sys
import os
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget, QFileDialog

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, 
                           FluentIcon as FIF, SplitFluentWindow, isDarkTheme,
                           SubtitleLabel, InfoBar)
from qfluentwidgets import FluentTranslator

from ..config import cfg
from ..core.midi_reader import MidiReader
from .home_interface import HomeInterface
from .midi_interface import MidiInterface
from .lyric_interface import LyricInterface
from .setting_interface import SettingInterface


class MainWindow(SplitFluentWindow):
    """ Main window of the application """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MID Reader')
        self.setWindowIcon(QIcon(':/app/icon.png'))
        
        # MIDI data storage
        self.midiReader = MidiReader()
        self.currentMidiFile = None
        self.currentTrackIndex = 0
        
        # Create interfaces
        self.homeInterface = HomeInterface(self)
        self.midiInterface = MidiInterface(self)
        self.lyricInterface = LyricInterface(self)
        self.settingInterface = SettingInterface(self)
        
        # Initialize window
        self.initWindow()
        
        # Add items to navigation bar
        self.initNavigation()
        
        # Connect signals to slots
        self.connectSignalToSlot()

    def initWindow(self):
        """ Initialize window """
        self.resize(1100, 750)
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        
        # Set theme
        theme = 'dark' if isDarkTheme() else 'light'

    def initNavigation(self):
        """ Initialize navigation """
        # Add navigation items and their corresponding interfaces
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))
        self.addSubInterface(self.midiInterface, FIF.MUSIC, self.tr('MIDI'))
        self.addSubInterface(self.lyricInterface, FIF.EDIT, self.tr('Lyrics'))
        self.navigationInterface.addSeparator()
        
        # Add file operations to the sidebar
        self.navigationInterface.addItem(
            routeKey='openMidi',
            icon=FIF.FOLDER,
            text=self.tr('Open MIDI'),
            onClick=self.openMidiFile,
            position=NavigationItemPosition.SCROLL
        )
        
        # Add settings item to the bottom
        self.addSubInterface(
            self.settingInterface, FIF.SETTING, self.tr('Settings'),
            NavigationItemPosition.BOTTOM)

    def connectSignalToSlot(self):
        """ Connect signals to slots """
        # Connect settings changed signals to appropriate slots
        self.settingInterface.musicFoldersChanged.connect(
            lambda folders: self.midiInterface.updateMusicFolders(folders))
        
        # Connect acrylic effect change signal
        self.settingInterface.acrylicEnableChanged.connect(
            lambda isEnabled: self.setMicaEffectEnabled(isEnabled))
        
        # Connect minimize to tray signal
        self.settingInterface.minimizeToTrayChanged.connect(
            lambda isEnabled: self.setMinimizeToTray(isEnabled))
            
        # Connect lyric interface signals
        self.lyricInterface.lyricSaved.connect(self.onLyricSaved)
            
    def openMidiFile(self):
        """ Open a MIDI file from the sidebar """
        filePath, _ = QFileDialog.getOpenFileName(
            self, self.tr('Open MIDI File'),
            cfg.midiFolders.value[0] if cfg.midiFolders.value else os.path.expanduser('~'),
            self.tr('MIDI Files (*.mid *.midi)')
        )
        
        if not filePath:
            return
            
        try:
            # Load the MIDI file
            success = self.midiReader.load_midi(filePath)
            if success:
                self.currentMidiFile = filePath
                self.currentTrackIndex = 0
                
                # Update title
                self.setWindowTitle(f'MID Reader - {os.path.basename(filePath)}')
                
                # Show success message
                InfoBar.success(
                    title=self.tr('Success'),
                    content=self.tr('MIDI file loaded successfully'),
                    parent=self
                )
                
                # Update both interfaces
                self.midiInterface.updatePianoRoll()
                self.lyricInterface.updateTrackComboBox()
                
                # Switch to MIDI interface
                self.switchTo(self.midiInterface)
                
        except Exception as e:
            InfoBar.error(
                title=self.tr('Error'),
                content=self.tr(f'Failed to load MIDI file: {str(e)}'),
                parent=self
            )
            print(f"Error details: {str(e)}")
    
    def setCurrentTrack(self, trackIndex):
        """ Set the current MIDI track """
        if self.midiReader.midi and trackIndex >= 0 and trackIndex < len(self.midiReader.get_tracks()):
            self.currentTrackIndex = trackIndex
            self.midiInterface.updatePianoRoll()
            return True
        return False
        
    def onLyricSaved(self, filepath):
        """ Handle when lyrics are saved """
        # Option to reload the modified MIDI file
        if os.path.exists(filepath):
            dialog = MessageBox(
                self.tr('Reload Modified MIDI'),
                self.tr('Would you like to load the modified MIDI file?'),
                self
            )
            
            if dialog.exec():
                try:
                    success = self.midiReader.load_midi(filepath)
                    if success:
                        self.currentMidiFile = filepath
                        self.setWindowTitle(f'MID Reader - {os.path.basename(filepath)}')
                        self.midiInterface.updatePianoRoll()
                except Exception as e:
                    InfoBar.error(
                        title=self.tr('Error'),
                        content=self.tr(f'Failed to reload MIDI file: {str(e)}'),
                        parent=self
                    )
