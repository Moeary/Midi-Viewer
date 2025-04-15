# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

from qfluentwidgets import (ScrollArea, TitleLabel, BodyLabel, CardWidget,
                           PushButton, FluentIcon as FIF)


class HomeInterface(ScrollArea):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        
        # Create content widget
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # Create welcome card
        self.welcomeCard = CardWidget(self.scrollWidget)
        self.welcomeCardLayout = QVBoxLayout(self.welcomeCard)
        
        # Add content to the welcome card
        self.titleLabel = TitleLabel(self.tr('Welcome to MID Reader'))
        self.descriptionLabel = BodyLabel(
            self.tr('A modern MIDI file reader with a clean interface.')
        )
        
        # Add buttons to open MIDI files
        self.buttonLayout = QHBoxLayout()
        self.openButton = PushButton(self.tr('Open MIDI File'))
        self.openButton.setIcon(FIF.FOLDER)
        self.buttonLayout.addWidget(self.openButton)
        self.buttonLayout.addStretch(1)
        
        # Initialize widgets
        self.initWidget()
        
        # Connect signals to slots
        self.connectSignalToSlot()
        
    def initWidget(self):
        """ Initialize widgets """
        # Set up the scroll area
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # Welcome card layout
        self.welcomeCardLayout.addWidget(self.titleLabel)
        self.welcomeCardLayout.addWidget(self.descriptionLabel)
        self.welcomeCardLayout.addLayout(self.buttonLayout)
        self.welcomeCardLayout.setContentsMargins(20, 20, 20, 20)
        
        # Main layout
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addWidget(self.welcomeCard)
        
        # Add instructions for using the app
        instructionsCard = CardWidget(self.scrollWidget)
        instructionsLayout = QVBoxLayout(instructionsCard)
        instructionsLayout.setContentsMargins(20, 20, 20, 20)
        
        instructionsTitle = TitleLabel(self.tr('Getting Started'))
        instructionsText = BodyLabel(
            self.tr('1. Use the sidebar to open a MIDI file\n'
                   '2. View the piano roll in the MIDI section\n'
                   '3. Switch between tracks and adjust zoom as needed\n'
                   '4. View lyrics embedded in the MIDI file directly on the notes')
        )
        
        instructionsLayout.addWidget(instructionsTitle)
        instructionsLayout.addWidget(instructionsText)
        
        self.vBoxLayout.addWidget(instructionsCard)
        
    def connectSignalToSlot(self):
        """ Connect signals to slots """
        # Connect open button to main window's open MIDI function
        self.openButton.clicked.connect(self.openMidiFile)
        
    def openMidiFile(self):
        """ Open a MIDI file from the home screen """
        mainWindow = self.window()
        if hasattr(mainWindow, 'openMidiFile'):
            mainWindow.openMidiFile()
