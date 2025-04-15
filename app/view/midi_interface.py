# coding:utf-8
import os
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QFontMetrics
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
                            QSplitter, QListWidget, QListWidgetItem, QComboBox,
                            QSlider, QGraphicsView, QGraphicsScene, QFrame)

from qfluentwidgets import (ScrollArea, PushButton, ToolButton, ComboBox,
                           FluentIcon as FIF, CardWidget, InfoBar, IconWidget,
                           Slider, ExpandLayout)

from ..config import cfg


# Piano roll constants
PIANO_KEY_WIDTH = 40
MIN_NOTE_HEIGHT = 15
HORIZONTAL_ZOOM_LEVELS = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
TIME_DIVISION = 480  # Ticks per quarter note (standard for many MIDI files)


class PianoRollWidget(QWidget):
    """ Piano roll visualization widget """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mainWindow = self.getMainWindow()
        
        # Setup piano roll parameters
        self.pianoKeyWidth = PIANO_KEY_WIDTH
        self.noteHeight = 20  # Default note height
        self.horizontalZoom = 1.0  # Default horizontal zoom level
        self.horizontalScrollPosition = 0
        self.verticalScrollPosition = 60*4  # Start at middle C (MIDI note 60)
        self.timeSignature = (4, 4)  # Default 4/4 time signature
        self.gridDivision = 4  # Default grid division (16th notes)
        self.maxTime = 0  # Maximum time in ticks
        
        # Initialize fonts for rendering
        self.noteFont = QFont("Arial", 8)  # Use Arial as a widely available font
        self.labelFont = QFont("Arial", 9)
        self.measureFont = QFont("Arial", 8)
        
        # Setup widget
        self.setMinimumSize(800, 400)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Setup colors
        self.blackKeyColor = QColor(40, 40, 40)
        self.whiteKeyColor = QColor(220, 220, 220)
        self.currentTrackColor = QColor(0, 200, 0, 180)  # Green for current track
        self.inactiveTrackColor = QColor(180, 180, 180, 100)  # Light gray for inactive tracks
        self.gridColor = QColor(60, 60, 60)
        self.beatLineColor = QColor(100, 100, 100)
        self.measureLineColor = QColor(140, 140, 140)
        self.textColor = QColor(200, 200, 200)
        
    def getMainWindow(self):
        """ Get reference to main window """
        widget = self.parent
        while widget:
            if hasattr(widget, 'midiReader'):
                return widget
            widget = widget.parent()
        return None
        
    def paintEvent(self, event):
        """ Draw the piano roll """
        if not self.mainWindow or not self.mainWindow.midiReader.midi:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get window dimensions
        width = self.width()
        height = self.height()
        
        # Draw piano keys on the left
        self.drawPianoKeys(painter, height)
        
        # Draw grid
        self.drawGrid(painter, width, height)
        
        # Draw MIDI notes
        self.drawMidiNotes(painter, width, height)
        
    def drawPianoKeys(self, painter, height):
        """ Draw piano keyboard on the left side """
        keyPattern = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1]  # 0=white, 1=black
        startNote = max(0, int(self.verticalScrollPosition // self.noteHeight))
        endNote = min(128, startNote + (height // self.noteHeight) + 2)
        
        # Draw white keys first
        for note in range(startNote, endNote):
            y = height - (note - self.verticalScrollPosition // self.noteHeight) * self.noteHeight
            isBlackKey = keyPattern[note % 12] == 1
            
            if not isBlackKey:
                painter.fillRect(0, int(y - self.noteHeight), self.pianoKeyWidth, int(self.noteHeight), self.whiteKeyColor)
                painter.setPen(Qt.black)
                painter.drawRect(0, int(y - self.noteHeight), self.pianoKeyWidth, int(self.noteHeight))
                
                # Draw note name on C notes
                if note % 12 == 0:
                    painter.setPen(Qt.black)
                    painter.setFont(self.labelFont)  # Use our reliable font
                    painter.drawText(
                        5, int(y - 5), 
                        f"C{note//12 - 1}"  # C4 is MIDI note 60
                    )
        
        # Draw black keys on top
        for note in range(startNote, endNote):
            y = height - (note - self.verticalScrollPosition // self.noteHeight) * self.noteHeight
            isBlackKey = keyPattern[note % 12] == 1
            
            if isBlackKey:
                # Convert float to int for width
                blackKeyWidth = int(self.pianoKeyWidth * 0.6)
                painter.fillRect(0, int(y - self.noteHeight), blackKeyWidth, int(self.noteHeight), self.blackKeyColor)
                
    def drawGrid(self, painter, width, height):
        """ Draw the grid lines """
        if not self.mainWindow or not self.mainWindow.midiReader.midi:
            return
            
        # Calculate grid parameters
        ticksPerBeat = self.mainWindow.midiReader.midi.ticks_per_beat
        ticksPerMeasure = ticksPerBeat * self.timeSignature[0]
        pixelsPerTick = self.horizontalZoom * self.pianoKeyWidth / ticksPerBeat
        
        # Set the maximum time
        self.maxTime = 0
        for track in self.mainWindow.midiReader.get_tracks():
            time = 0
            for msg in track:
                time += msg.time
                self.maxTime = max(self.maxTime, time)
        
        # Draw vertical grid lines
        startTick = max(0, int(self.horizontalScrollPosition / pixelsPerTick))
        endTick = min(self.maxTime, int((width + self.horizontalScrollPosition) / pixelsPerTick) + 1)
        
        # Draw horizontal lines for each note
        for note in range(128):
            y = height - (note - self.verticalScrollPosition // self.noteHeight) * self.noteHeight
            if 0 <= y <= height:
                painter.setPen(QPen(self.gridColor, 1))
                painter.drawLine(self.pianoKeyWidth, int(y), width, int(y))
        
        # Draw vertical grid lines (measures and beats)
        for tick in range(startTick - startTick % ticksPerBeat, endTick, ticksPerBeat // self.gridDivision):
            x = self.pianoKeyWidth + (tick - self.horizontalScrollPosition) * pixelsPerTick
            
            if x < self.pianoKeyWidth:
                continue
                
            if tick % ticksPerMeasure == 0:
                # Measure line
                painter.setPen(QPen(self.measureLineColor, 2))
                painter.drawLine(int(x), 0, int(x), height)
                
                # Draw measure number
                painter.setPen(self.textColor)
                painter.setFont(self.measureFont)  # Use our reliable font
                painter.drawText(
                    int(x + 5), 20, 
                    f"{tick // ticksPerMeasure + 1}"
                )
            elif tick % ticksPerBeat == 0:
                # Beat line
                painter.setPen(QPen(self.beatLineColor, 1))
                painter.drawLine(int(x), 0, int(x), height)
            else:
                # Smaller grid division
                painter.setPen(QPen(self.gridColor, 1))
                painter.drawLine(int(x), 0, int(x), height)
        
    def drawMidiNotes(self, painter, width, height):
        """ Draw MIDI notes on the piano roll """
        if not self.mainWindow or not self.mainWindow.midiReader.midi:
            return
            
        # Calculate the visible area
        ticksPerBeat = self.mainWindow.midiReader.midi.ticks_per_beat
        pixelsPerTick = self.horizontalZoom * self.pianoKeyWidth / ticksPerBeat
        
        startTick = max(0, int(self.horizontalScrollPosition / pixelsPerTick))
        endTick = min(self.maxTime, int((width + self.horizontalScrollPosition) / pixelsPerTick) + 1)
        
        startNote = max(0, int(self.verticalScrollPosition // self.noteHeight))
        endNote = min(128, startNote + (height // self.noteHeight) + 2)
        
        # Get all tracks
        tracks = self.mainWindow.midiReader.get_tracks()
        currentTrackIndex = self.mainWindow.currentTrackIndex
        
        # Draw notes for all tracks
        for trackIndex, track in enumerate(tracks):
            # Set color based on whether this is the current track
            if trackIndex == currentTrackIndex:
                painter.setBrush(QBrush(self.currentTrackColor))
                painter.setPen(QPen(QColor(0, 120, 0), 1))
            else:
                painter.setBrush(QBrush(self.inactiveTrackColor))
                painter.setPen(QPen(QColor(120, 120, 120), 1))
            
            # Process messages to find note events
            active_notes = {}
            time = 0
            
            for msg in track:
                time += msg.time
                
                if time > endTick:
                    break
                    
                if hasattr(msg, 'type'):  # Make sure msg has a type attribute
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Start of note
                        note = msg.note
                        if startNote <= note <= endNote:
                            active_notes[note] = time
                            
                    elif (msg.type == 'note_off' or 
                         (msg.type == 'note_on' and msg.velocity == 0)):
                        # End of note
                        note = msg.note
                        if note in active_notes and startNote <= note <= endNote:
                            start_time = active_notes[note]
                            note_length = time - start_time
                            
                            # Draw the note rectangle
                            x = self.pianoKeyWidth + (start_time - self.horizontalScrollPosition) * pixelsPerTick
                            y = height - (note - self.verticalScrollPosition // self.noteHeight) * self.noteHeight
                            width_px = note_length * pixelsPerTick
                            
                            if width_px > 0 and x + width_px >= self.pianoKeyWidth:
                                # Only draw if visible and ensure width is at least 1 pixel
                                note_rect = QRect(
                                    int(x), 
                                    int(y - self.noteHeight + 2), 
                                    max(1, int(width_px)), 
                                    int(self.noteHeight - 4)
                                )
                                painter.drawRoundedRect(note_rect, 3, 3)
                                
                                # Draw lyric text if there's a lyric event
                                if trackIndex == currentTrackIndex:
                                    # Check if there's a lyric associated with this note
                                    lyric = self.getLyricForNote(track, start_time)
                                    if lyric:
                                        # Use our reliable font with appropriate size
                                        fontPointSize = min(8, int(self.noteHeight * 0.6))
                                        lyricFont = QFont("Arial", fontPointSize)
                                        painter.setFont(lyricFont)
                                        fm = QFontMetrics(lyricFont)
                                        
                                        # Truncate lyric if it's too long for the note
                                        text_width = fm.width(lyric)
                                        if text_width > width_px - 6:
                                            # Truncate with ellipsis
                                            lyric = fm.elidedText(lyric, Qt.ElideRight, int(width_px) - 6)
                                        
                                        # Draw the lyric text
                                        painter.setPen(Qt.white)
                                        painter.drawText(
                                            note_rect.adjusted(3, 0, -3, 0),
                                            Qt.AlignVCenter | Qt.AlignLeft,
                                            lyric
                                        )
                            
                            # Remove from active notes
                            del active_notes[note]
    
    def getLyricForNote(self, track, time):
        """ Find lyrics associated with a note at the given time """
        # Look for a lyric event at the same time or slightly before
        current_time = 0
        for i, msg in enumerate(track):
            current_time += msg.time
            if abs(current_time - time) <= 10:  # Allow a small timing difference
                # Check if there's a lyric message near this point
                for j in range(max(0, i-2), min(len(track), i+3)):
                    msg_j = track[j]
                    if hasattr(msg_j, 'type') and msg_j.type == 'lyrics':
                        return msg_j.text
        return None
    
    def setHorizontalZoom(self, zoomIndex):
        """ Set horizontal zoom level """
        if 0 <= zoomIndex < len(HORIZONTAL_ZOOM_LEVELS):
            self.horizontalZoom = HORIZONTAL_ZOOM_LEVELS[zoomIndex]
            self.update()
    
    def setNoteHeight(self, height):
        """ Set the height of notes """
        self.noteHeight = max(MIN_NOTE_HEIGHT, height)
        self.update()
        
    def setHorizontalScroll(self, position):
        """ Set horizontal scroll position """
        self.horizontalScrollPosition = max(0, position)
        self.update()
        
    def setVerticalScroll(self, position):
        """ Set vertical scroll position """
        self.verticalScrollPosition = max(0, min(128 * self.noteHeight - self.height(), position))
        self.update()
        

class MidiInterface(ScrollArea):
    """ MIDI interface with piano roll display """
    trackSelected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("midiInterface")
        
        # Create content widget
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # Track selection area
        self.trackControlCard = CardWidget(self.scrollWidget)
        self.trackControlLayout = QHBoxLayout(self.trackControlCard)
        
        self.trackLabel = QLabel(self.tr('Track:'))
        self.trackComboBox = ComboBox()
        self.trackComboBox.setMinimumWidth(250)
        
        # Zoom controls
        self.zoomLabel = QLabel(self.tr('Zoom:'))
        self.horizontalZoomSlider = Slider(Qt.Horizontal)
        self.horizontalZoomSlider.setRange(0, len(HORIZONTAL_ZOOM_LEVELS) - 1)
        self.horizontalZoomSlider.setValue(2)  # Default to 1.0 zoom (index 2)
        self.horizontalZoomSlider.setMaximumWidth(150)
        
        self.verticalZoomLabel = QLabel(self.tr('Note Height:'))
        self.verticalZoomSlider = Slider(Qt.Horizontal)
        self.verticalZoomSlider.setRange(MIN_NOTE_HEIGHT, 40)
        self.verticalZoomSlider.setValue(20)  # Default height
        self.verticalZoomSlider.setMaximumWidth(150)
        
        # Piano roll area with scrollbars
        self.pianoRollFrame = QFrame()
        self.pianoRollLayout = QVBoxLayout(self.pianoRollFrame)
        self.pianoRollLayout.setContentsMargins(0, 0, 0, 0)
        
        # Create horizontal and vertical scrollbars
        self.pianoRollHorizontalScrollbar = QSlider(Qt.Horizontal)
        self.pianoRollVerticalScrollbar = QSlider(Qt.Vertical)
        
        # Create the piano roll widget
        self.pianoRollWidget = PianoRollWidget(self)
        
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
        
        # Track control layout
        self.trackControlLayout.setContentsMargins(20, 20, 20, 20)
        self.trackControlLayout.addWidget(self.trackLabel)
        self.trackControlLayout.addWidget(self.trackComboBox)
        self.trackControlLayout.addSpacing(20)
        self.trackControlLayout.addWidget(self.zoomLabel)
        self.trackControlLayout.addWidget(self.horizontalZoomSlider)
        self.trackControlLayout.addSpacing(20)
        self.trackControlLayout.addWidget(self.verticalZoomLabel)
        self.trackControlLayout.addWidget(self.verticalZoomSlider)
        self.trackControlLayout.addStretch(1)
        
        # Piano roll widget with scrollbars
        pianoRollContainerLayout = QHBoxLayout()
        pianoRollContainerLayout.setContentsMargins(0, 0, 0, 0)
        pianoRollContainerLayout.setSpacing(0)
        
        # Add piano roll and vertical scrollbar
        pianoRollAndVScrollLayout = QHBoxLayout()
        pianoRollAndVScrollLayout.addWidget(self.pianoRollWidget, 1)
        pianoRollAndVScrollLayout.addWidget(self.pianoRollVerticalScrollbar)
        
        # Create a container for the piano roll and vertical scrollbar
        pianoRollAndVScroll = QWidget()
        pianoRollAndVScroll.setLayout(pianoRollAndVScrollLayout)
        
        # Add the container and horizontal scrollbar to the main layout
        pianoRollWithScrollbarsLayout = QVBoxLayout()
        pianoRollWithScrollbarsLayout.addWidget(pianoRollAndVScroll, 1)
        pianoRollWithScrollbarsLayout.addWidget(self.pianoRollHorizontalScrollbar)
        
        self.pianoRollLayout.addLayout(pianoRollWithScrollbarsLayout)
        
        # Configure scrollbars
        self.pianoRollHorizontalScrollbar.setRange(0, 10000)
        self.pianoRollHorizontalScrollbar.setValue(0)
        self.pianoRollVerticalScrollbar.setRange(0, 128 * 20)  # 128 MIDI notes * default height
        self.pianoRollVerticalScrollbar.setValue(60*4 * 20)  # Start at middle C (MIDI note 60)
        self.pianoRollVerticalScrollbar.setInvertedAppearance(True)  # Invert for MIDI notes (higher = up)
        
        # Main layout
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addWidget(self.trackControlCard)
        self.vBoxLayout.addWidget(self.pianoRollFrame, 1)
        
    def connectSignalToSlot(self):
        """ Connect signals to slots """
        self.trackComboBox.currentIndexChanged.connect(self.onTrackSelected)
        self.horizontalZoomSlider.valueChanged.connect(self.pianoRollWidget.setHorizontalZoom)
        self.verticalZoomSlider.valueChanged.connect(self.pianoRollWidget.setNoteHeight)
        self.pianoRollHorizontalScrollbar.valueChanged.connect(self.pianoRollWidget.setHorizontalScroll)
        self.pianoRollVerticalScrollbar.valueChanged.connect(self.pianoRollWidget.setVerticalScroll)
        
    def onTrackSelected(self, index):
        """ Handle track selection from combo box """
        mainWindow = self.getMainWindow()
        if mainWindow:
            mainWindow.setCurrentTrack(index)
            self.trackSelected.emit(index)
            
    def updatePianoRoll(self):
        """ Update the piano roll when MIDI data changes """
        mainWindow = self.getMainWindow()
        if not mainWindow or not mainWindow.midiReader.midi:
            self.trackComboBox.clear()
            self.pianoRollWidget.update()
            return
            
        # Update track combo box
        self.trackComboBox.blockSignals(True)
        self.trackComboBox.clear()
        
        for i, track in enumerate(mainWindow.midiReader.get_tracks()):
            track_info = mainWindow.midiReader.get_track_info(i)
            track_name = track_info.get('name', f"Track {i}")
            if not track_name:
                track_name = f"Track {i}"
            
            # Add the track to the combo box
            self.trackComboBox.addItem(f"{i}: {track_name}")
        
        # Set the current track
        self.trackComboBox.setCurrentIndex(mainWindow.currentTrackIndex)
        self.trackComboBox.blockSignals(False)
        
        # Update scrollbar range based on MIDI content
        max_time = 0
        for track in mainWindow.midiReader.get_tracks():
            time = 0
            for msg in track:
                time += msg.time
                max_time = max(max_time, time)
                
        if max_time > 0:
            pixelsPerTick = self.pianoRollWidget.horizontalZoom * self.pianoRollWidget.pianoKeyWidth / mainWindow.midiReader.midi.ticks_per_beat
            self.pianoRollHorizontalScrollbar.setMaximum(int(max_time * pixelsPerTick))
        
        # Update vertical scrollbar based on note height
        self.pianoRollVerticalScrollbar.setRange(0, 128 * self.pianoRollWidget.noteHeight - self.pianoRollWidget.height())
        
        # Update the piano roll display
        self.pianoRollWidget.update()
            
    def updateMusicFolders(self, folders):
        """ Update music folder list """
        # This method is called when the music folders are changed in settings
        pass
        
    def getMainWindow(self):
        """ Get reference to main window """
        widget = self.parent()
        while widget:
            if hasattr(widget, 'midiReader'):
                return widget
            widget = widget.parent()
        return None
