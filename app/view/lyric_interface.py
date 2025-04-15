# coding:utf-8
import os
import time
from datetime import datetime
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
                            QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
                            QTextEdit, QComboBox, QPushButton, QMessageBox, QCheckBox)

from qfluentwidgets import (ScrollArea, PushButton, ToolButton, ComboBox, LineEdit,
                           FluentIcon as FIF, CardWidget, InfoBar, IconWidget,
                           TextEdit, TableWidget, Dialog, MessageBox, RadioButton,
                           CheckBox)

from ..config import cfg


class LyricTableWidget(TableWidget):
    """Custom table widget for editing lyrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels([
            self.tr("Time"), 
            self.tr("Original Lyric"), 
            self.tr("Modified Lyric")
        ])
        
        # Set column widths
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Set selection behavior
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        # Enable editing for modified lyric column only
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
    def setReadOnly(self, column, readonly=True):
        """Set a column to be read-only"""
        for row in range(self.rowCount()):
            item = self.item(row, column)
            if item:
                if readonly:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)


class ExportOptionsDialog(Dialog):
    """Dialog for selecting lyrics export options"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = QLabel(self.tr("Export Lyrics Options"), self)
        
        # Content layout
        self.contentLayout = QVBoxLayout()
        
        # Export format group
        self.formatGroupLabel = QLabel(self.tr("Lyrics Source:"))
        self.formatGroupLabel.setStyleSheet("font-weight: bold;")
        self.formatGroup = RadioButtonGroup(self)
        self.originalRadio = RadioButton(self.tr("Original Lyrics"), self)
        self.modifiedRadio = RadioButton(self.tr("Modified Lyrics"), self)
        self.bothRadio = RadioButton(self.tr("Both (Side by Side)"), self)
        
        self.formatGroup.addButton(self.originalRadio, 0)
        self.formatGroup.addButton(self.modifiedRadio, 1)
        self.formatGroup.addButton(self.bothRadio, 2)
        self.formatGroup.setCurrentIndex(1)  # Default to modified lyrics
        
        # File format group
        self.fileFormatLabel = QLabel(self.tr("File Format:"))
        self.fileFormatLabel.setStyleSheet("font-weight: bold;")
        self.fileFormatGroup = RadioButtonGroup(self)
        self.plainTextRadio = RadioButton(self.tr("Plain Text (.txt)"), self)
        self.lrcRadio = RadioButton(self.tr("LRC Format (.lrc)"), self)
        
        self.fileFormatGroup.addButton(self.plainTextRadio, 0)
        self.fileFormatGroup.addButton(self.lrcRadio, 1)
        self.fileFormatGroup.setCurrentIndex(0)  # Default to plain text
        
        # Add timestamp option
        self.timestampCheck = CheckBox(self.tr("Include timestamps"), self)
        self.timestampCheck.setChecked(True)
        
        # Initialize the dialog
        self.initDialog()
        
    def initDialog(self):
        """Initialize the dialog"""
        # Size and title
        self.resize(400, 320)
        self.setWindowTitle(self.tr("Export Options"))
        
        # Title label
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        
        # Format group layout
        formatLayout = QVBoxLayout()
        formatLayout.addWidget(self.formatGroupLabel)
        formatLayout.addWidget(self.originalRadio)
        formatLayout.addWidget(self.modifiedRadio)
        formatLayout.addWidget(self.bothRadio)
        formatLayout.setContentsMargins(0, 10, 0, 10)
        
        # File format layout
        fileFormatLayout = QVBoxLayout()
        fileFormatLayout.addWidget(self.fileFormatLabel)
        fileFormatLayout.addWidget(self.plainTextRadio)
        fileFormatLayout.addWidget(self.lrcRadio)
        fileFormatLayout.setContentsMargins(0, 10, 0, 10)
        
        # Options layout
        optionsLayout = QVBoxLayout()
        optionsLayout.addWidget(self.timestampCheck)
        optionsLayout.setContentsMargins(0, 10, 0, 10)
        
        # Add to content layout
        self.contentLayout.addWidget(self.titleLabel)
        self.contentLayout.addLayout(formatLayout)
        self.contentLayout.addLayout(fileFormatLayout)
        self.contentLayout.addLayout(optionsLayout)

        # Set content layout
        self.setContentLayout(self.contentLayout)

    def getExportOptions(self):
        """Get the selected export options"""
        return {
            'format': ['original', 'modified', 'both'][self.formatGroup.checkedIndex()],
            'file_format': ['txt', 'lrc'][self.fileFormatGroup.checkedIndex()],
            'timestamp': self.timestampCheck.isChecked()
        }


class LyricInterface(ScrollArea):
    """Interface for editing MIDI lyrics"""
    lyricSaved = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("lyricInterface")
        
        # Create content widget
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # Track selection area
        self.trackControlCard = CardWidget(self.scrollWidget)
        self.trackControlLayout = QHBoxLayout(self.trackControlCard)
        
        self.trackLabel = QLabel(self.tr('Track:'))
        self.trackComboBox = ComboBox()
        self.trackComboBox.setMinimumWidth(250)
        
        # Lyric data 
        self.lyricsData = []  # Format: [(start_time, end_time, original_lyric, modified_lyric), ...]
        
        # Lyric editing area
        self.lyricEditCard = CardWidget(self.scrollWidget)
        self.lyricEditLayout = QVBoxLayout(self.lyricEditCard)
        
        # Create a splitter for the lyric editing and reference sections
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Lyric table
        self.lyricTableCard = CardWidget()
        self.lyricTableLayout = QVBoxLayout(self.lyricTableCard)
        self.lyricTable = LyricTableWidget()
        
        # Table control buttons
        self.tableButtonLayout = QHBoxLayout()
        self.addLyricButton = PushButton(self.tr("Add Lyric"))
        self.addLyricButton.setIcon(FIF.ADD)
        self.removeLyricButton = PushButton(self.tr("Remove Lyric"))
        self.removeLyricButton.setIcon(FIF.REMOVE)
        self.copyToModifiedButton = PushButton(self.tr("Copy All to Modified"))
        self.copyToModifiedButton.setIcon(FIF.COPY)
        
        # Right side: Reference lyrics
        self.referenceCard = CardWidget()
        self.referenceLayout = QVBoxLayout(self.referenceCard)
        self.referenceTitle = QLabel(self.tr("Reference Lyrics"))
        self.referenceTextEdit = TextEdit()
        self.referenceTextEdit.setReadOnly(False)  # Make it editable
        self.referenceTextEdit.setPlaceholderText(self.tr("Enter or load reference lyrics here"))
        
        # Reference control buttons
        self.referenceButtonLayout = QHBoxLayout()
        self.loadReferenceButton = PushButton(self.tr("Load Reference File"))
        self.loadReferenceButton.setIcon(FIF.FOLDER)
        self.clearReferenceButton = PushButton(self.tr("Clear"))
        self.clearReferenceButton.setIcon(FIF.DELETE)
        self.applyReferenceButton = PushButton(self.tr("Apply to Selected"))
        self.applyReferenceButton.setIcon(FIF.ACCEPT)
        self.applyReferenceAllButton = PushButton(self.tr("Apply to All Rows"))
        self.applyReferenceAllButton.setIcon(FIF.ACCEPT_MEDIUM)
        
        # Save area
        self.saveCard = CardWidget(self.scrollWidget)
        self.saveLayout = QHBoxLayout(self.saveCard)
        self.saveButton = PushButton(self.tr("Save MIDI with Modified Lyrics"))
        self.saveButton.setIcon(FIF.SAVE)
        self.applyToCurrentBox = QCheckBox(self.tr("Apply changes to current MIDI file in memory"))
        self.applyToCurrentBox.setChecked(True)
        
        # Export lyrics button
        self.exportLyricsButton = PushButton(self.tr("Export Lyrics to Text File"))
        self.exportLyricsButton.setIcon(FIF.DOCUMENT)  # Changed from FIF.TEXT_DOCUMENT to FIF.DOCUMENT
        
        # Initialize widgets
        self.initWidget()
        
        # Connect signals to slots
        self.connectSignalToSlot()
        
    def initWidget(self):
        """Initialize widgets"""
        # Set up the scroll area
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # Track control layout
        self.trackControlLayout.setContentsMargins(20, 20, 20, 20)
        self.trackControlLayout.addWidget(self.trackLabel)
        self.trackControlLayout.addWidget(self.trackComboBox)
        self.trackControlLayout.addStretch(1)
        
        # Table button layout
        self.tableButtonLayout.addWidget(self.addLyricButton)
        self.tableButtonLayout.addWidget(self.removeLyricButton)
        self.tableButtonLayout.addWidget(self.copyToModifiedButton)
        self.tableButtonLayout.addStretch(1)
        
        # Lyric table layout
        self.lyricTableLayout.addLayout(self.tableButtonLayout)
        self.lyricTableLayout.addWidget(self.lyricTable)
        
        # Reference buttons layout
        self.referenceButtonLayout.addWidget(self.loadReferenceButton)
        self.referenceButtonLayout.addWidget(self.clearReferenceButton)
        self.referenceButtonLayout.addWidget(self.applyReferenceButton)
        self.referenceButtonLayout.addWidget(self.applyReferenceAllButton)
        self.referenceButtonLayout.addStretch(1)
        
        # Reference layout
        self.referenceLayout.addWidget(self.referenceTitle)
        self.referenceLayout.addWidget(self.referenceTextEdit)
        self.referenceLayout.addLayout(self.referenceButtonLayout)
        
        # Add the table and reference to the splitter
        self.splitter.addWidget(self.lyricTableCard)
        self.splitter.addWidget(self.referenceCard)
        self.splitter.setStretchFactor(0, 3)  # Table gets more space
        self.splitter.setStretchFactor(1, 2)  # Reference gets less space
        
        # Add the splitter to the lyric edit card
        self.lyricEditLayout.addWidget(self.splitter)
        
        # Save layout
        self.saveLayout.addWidget(self.saveButton)
        self.saveLayout.addWidget(self.exportLyricsButton)
        self.saveLayout.addWidget(self.applyToCurrentBox)
        self.saveLayout.addStretch(1)
        
        # Main layout
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addWidget(self.trackControlCard)
        self.vBoxLayout.addWidget(self.lyricEditCard, 1)  # Stretch to fill space
        self.vBoxLayout.addWidget(self.saveCard)
        
        # Set read-only columns
        self.lyricTable.setReadOnly(0, True)  # Time column
        self.lyricTable.setReadOnly(1, True)  # Original lyric column

    def connectSignalToSlot(self):
        """Connect signals to slots"""
        self.trackComboBox.currentIndexChanged.connect(self.onTrackSelected)
        self.addLyricButton.clicked.connect(self.addLyric)
        self.removeLyricButton.clicked.connect(self.removeLyric)
        self.copyToModifiedButton.clicked.connect(self.copyToModified)
        self.loadReferenceButton.clicked.connect(self.loadReferenceFile)
        self.clearReferenceButton.clicked.connect(self.clearReferenceText)
        self.applyReferenceButton.clicked.connect(self.applyReferenceToSelected)
        self.saveButton.clicked.connect(self.saveMidiWithLyrics)
        self.exportLyricsButton.clicked.connect(self.exportLyricsToText)
        self.applyReferenceAllButton.clicked.connect(self.applyReferenceToAll)
        
        # Add context menu for table
        self.lyricTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lyricTable.customContextMenuRequested.connect(self.showTableContextMenu)
        
    def onTrackSelected(self, index):
        """Handle track selection from combo box"""
        if index >= 0:
            self.loadLyricsForTrack(index)
            
    def loadLyricsForTrack(self, trackIndex):
        """Load lyrics for the selected track"""
        mainWindow = self.getMainWindow()
        if not mainWindow or not mainWindow.midiReader.midi:
            return
            
        # Clear existing lyrics
        self.lyricTable.setRowCount(0)
        self.lyricsData = []
        
        # Get track
        tracks = mainWindow.midiReader.get_tracks()
        if trackIndex >= len(tracks):
            return
            
        track = tracks[trackIndex]
        
        # Process track to find lyrics
        absolute_time = 0
        lyrics_events = []
        
        # First pass: collect all lyric events with absolute time
        for msg in track:
            absolute_time += msg.time
            if hasattr(msg, 'type') and msg.type == 'lyrics':
                lyrics_events.append((absolute_time, msg.text))
        
        # Add rows to the table for each lyric
        for i, (time, lyric) in enumerate(lyrics_events):
            # Calculate end time (use next lyric time or add 1 second if last)
            end_time = lyrics_events[i+1][0] if i < len(lyrics_events) - 1 else time + mainWindow.midiReader.midi.ticks_per_beat
            
            # Format for display: convert ticks to mm:ss.ms
            ticks_per_beat = mainWindow.midiReader.midi.ticks_per_beat
            # Estimate seconds (this is approximate without tempo changes)
            seconds_start = time / ticks_per_beat * 60 / 120  # Assuming 120 BPM
            seconds_end = end_time / ticks_per_beat * 60 / 120
            
            time_text = f"{int(seconds_start//60):02d}:{seconds_start%60:05.2f} - {int(seconds_end//60):02d}:{seconds_end%60:05.2f}"
            
            # Store data
            self.lyricsData.append((time, end_time, lyric, lyric))
            
            # Add to table
            row = self.lyricTable.rowCount()
            self.lyricTable.insertRow(row)
            
            # Time cell
            time_item = QTableWidgetItem(time_text)
            time_item.setData(Qt.UserRole, (time, end_time))  # Store raw time values
            self.lyricTable.setItem(row, 0, time_item)
            
            # Original lyric cell
            original_item = QTableWidgetItem(lyric)
            self.lyricTable.setItem(row, 1, original_item)
            
            # Modified lyric cell (editable)
            modified_item = QTableWidgetItem(lyric)
            self.lyricTable.setItem(row, 2, modified_item)
            
        # Set read-only columns
        self.lyricTable.setReadOnly(0, True)
        self.lyricTable.setReadOnly(1, True)
        
    def updateLyricsData(self):
        """Update lyricsData from the table"""
        self.lyricsData = []
        
        for row in range(self.lyricTable.rowCount()):
            # Get time range
            time_item = self.lyricTable.item(row, 0)
            start_time, end_time = time_item.data(Qt.UserRole)
            
            # Get original and modified lyrics
            original_lyric = self.lyricTable.item(row, 1).text()
            modified_lyric = self.lyricTable.item(row, 2).text()
            
            # Store data
            self.lyricsData.append((start_time, end_time, original_lyric, modified_lyric))
            
    def addLyric(self):
        """Add a new lyric entry"""
        mainWindow = self.getMainWindow()
        if not mainWindow or not mainWindow.midiReader.midi:
            return
            
        # Add a new row
        row = self.lyricTable.rowCount()
        self.lyricTable.insertRow(row)
        
        # Default time: After the last lyric or at beginning
        ticks_per_beat = mainWindow.midiReader.midi.ticks_per_beat
        
        if row > 0:
            prev_time_item = self.lyricTable.item(row-1, 0)
            _, prev_end_time = prev_time_item.data(Qt.UserRole)
            start_time = prev_end_time
        else:
            start_time = 0
            
        end_time = start_time + ticks_per_beat * 4  # Add 4 beats
        
        # Format for display
        seconds_start = start_time / ticks_per_beat * 60 / 120
        seconds_end = end_time / ticks_per_beat * 60 / 120
        time_text = f"{int(seconds_start//60):02d}:{seconds_start%60:05.2f} - {int(seconds_end//60):02d}:{seconds_end%60:05.2f}"
        
        # Time cell
        time_item = QTableWidgetItem(time_text)
        time_item.setData(Qt.UserRole, (start_time, end_time))
        self.lyricTable.setItem(row, 0, time_item)
        
        # Original and modified lyric cells
        empty_text = ""
        self.lyricTable.setItem(row, 1, QTableWidgetItem(empty_text))
        self.lyricTable.setItem(row, 2, QTableWidgetItem(empty_text))
        
        # Set read-only columns
        self.lyricTable.setReadOnly(0, True)
        self.lyricTable.setReadOnly(1, True)
        
        # Update data
        self.updateLyricsData()
        
    def removeLyric(self):
        """Remove the selected lyric entry"""
        selected_rows = self.lyricTable.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        self.lyricTable.removeRow(row)
        
        # Update data
        self.updateLyricsData()
        
    def copyToModified(self):
        """Copy all original lyrics to modified lyrics"""
        for row in range(self.lyricTable.rowCount()):
            original_text = self.lyricTable.item(row, 1).text()
            self.lyricTable.item(row, 2).setText(original_text)
            
        # Update data
        self.updateLyricsData()
            
    def loadReferenceFile(self):
        """Load a reference lyric file"""
        filePath, _ = QFileDialog.getOpenFileName(
            self, self.tr('Open Lyric File'),
            cfg.midiFolders.value[0] if cfg.midiFolders.value else os.path.expanduser('~'),
            self.tr('Text Files (*.txt *.lrc)')
        )
        
        if not filePath:
            return
            
        try:
            with open(filePath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.referenceTextEdit.setText(content)
                
            # Show success message
            InfoBar.success(
                title=self.tr('Success'),
                content=self.tr('Reference lyrics loaded successfully'),
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title=self.tr('Error'),
                content=self.tr(f'Failed to load reference file: {str(e)}'),
                parent=self
            )
    
    def clearReferenceText(self):
        """Clear the reference text"""
        self.referenceTextEdit.clear()
        
    def applyReferenceToSelected(self):
        """Apply reference lyrics to the selected row in the table"""
        selected_rows = self.lyricTable.selectedIndexes()
        if not selected_rows:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('No lyric selected. Please select a row in the table.'),
                parent=self
            )
            return
            
        # Get the selected row
        row = selected_rows[0].row()
        
        # Get the reference text
        reference_text = self.referenceTextEdit.toPlainText().strip()
        if not reference_text:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('Reference text is empty.'),
                parent=self
            )
            return
            
        # Find the best matching lyrics from reference based on line breaks
        reference_lines = reference_text.splitlines()
        if not reference_lines:
            return
            
        # Two modes:
        # 1. If only one line in reference, just apply it
        # 2. If multiple lines, try to find the right line based on position
        if len(reference_lines) == 1:
            # Just apply the single line
            self.lyricTable.item(row, 2).setText(reference_lines[0])
        else:
            # Try to determine which line to use based on row index
            # Simple approach: use modulo to cycle through reference lines if there are more rows than lines
            line_index = row % len(reference_lines)
            self.lyricTable.item(row, 2).setText(reference_lines[line_index])
            
        # Update lyrics data
        self.updateLyricsData()
        
    def applyReferenceToAll(self):
        """Apply reference lyrics to all rows in the table"""
        # Get the reference text
        reference_text = self.referenceTextEdit.toPlainText().strip()
        if not reference_text:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('Reference text is empty.'),
                parent=self
            )
            return
            
        # Split reference into lines
        reference_lines = reference_text.splitlines()
        if not reference_lines:
            return
            
        row_count = self.lyricTable.rowCount()
        if row_count == 0:
            return
            
        # Apply each line to a row
        for row in range(row_count):
            # Use modulo to cycle through reference lines if there are more rows than lines
            line_index = row % len(reference_lines)
            self.lyricTable.item(row, 2).setText(reference_lines[line_index])
            
        # Update lyrics data
        self.updateLyricsData()
        
        # Show success message
        InfoBar.success(
            title=self.tr('Success'),
            content=self.tr('Reference lyrics applied to all rows'),
            parent=self
        )
        
    def saveMidiWithLyrics(self):
        """Save a new MIDI file with the modified lyrics"""
        mainWindow = self.getMainWindow()
        if not mainWindow or not mainWindow.midiReader.midi:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('No MIDI file loaded.'),
                parent=self
            )
            return
            
        # Update lyrics data from table
        self.updateLyricsData()
        
        # Get selected track
        track_index = self.trackComboBox.currentIndex()
        if track_index < 0:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('No track selected.'),
                parent=self
            )
            return
            
        # Get output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = os.path.splitext(os.path.basename(mainWindow.currentMidiFile))[0]
        output_dir = os.path.join(os.getcwd(), 'output')
        os.makedirs(output_dir, exist_ok=True)
        default_output_path = os.path.join(output_dir, f"{default_filename}_{timestamp}.mid")
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, self.tr('Save MIDI File'),
            default_output_path,
            self.tr('MIDI Files (*.mid *.midi)')
        )
        
        if not output_path:
            return
            
        try:
            # Create a copy of the MIDI file
            midi_file = mainWindow.midiReader.midi
            
            # Apply modified lyrics to the track
            tracks = midi_file.tracks
            if track_index < len(tracks):
                # Apply lyric changes to track
                modified_track = self.apply_lyric_changes(tracks[track_index], self.lyricsData)
                midi_file.tracks[track_index] = modified_track
                
                # Save the modified MIDI file
                midi_file.save(output_path)
                
                # Apply changes to the current MIDI in memory if requested
                if self.applyToCurrentBox.isChecked():
                    mainWindow.midiReader.midi = midi_file
                    mainWindow.midiReader._extract_lyrics()
                    
                # Show success message
                InfoBar.success(
                    title=self.tr('Success'),
                    content=self.tr(f'MIDI file saved to {output_path}'),
                    parent=self
                )
                
                # Emit signal
                self.lyricSaved.emit(output_path)
        except Exception as e:
            InfoBar.error(
                title=self.tr('Error'),
                content=self.tr(f'Failed to save MIDI file: {str(e)}'),
                parent=self
            )
            print(f"Error details: {str(e)}")
            
    def exportLyricsToText(self):
        """Export lyrics from current track to a text file"""
        mainWindow = self.getMainWindow()
        if not mainWindow or not mainWindow.midiReader.midi:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('No MIDI file loaded.'),
                parent=self
            )
            return
            
        # Update lyrics data from table
        self.updateLyricsData()
        
        # Check if there are any lyrics to export
        if not self.lyricsData:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('No lyrics found in current track.'),
                parent=self
            )
            return
            
        # Get selected track
        track_index = self.trackComboBox.currentIndex()
        if track_index < 0:
            InfoBar.warning(
                title=self.tr('Warning'),
                content=self.tr('No track selected.'),
                parent=self
            )
            return
            
        # Show export options dialog
        dialog = ExportOptionsDialog(self)
        if not dialog.exec():
            return
            
        # Get export options
        export_options = dialog.getExportOptions()
        export_format = export_options['format']
        file_format = export_options['file_format']
        include_timestamp = export_options['timestamp']
            
        # Get track info for filename
        track_info = mainWindow.midiReader.get_track_info(track_index)
        track_name = track_info.get('name', f"Track {track_index}")
        if not track_name:
            track_name = f"Track {track_index}"
            
        # Create default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        midi_filename = os.path.splitext(os.path.basename(mainWindow.currentMidiFile))[0]
        output_dir = os.path.join(os.getcwd(), 'output')
        os.makedirs(output_dir, exist_ok=True)
            
        # Set file extension based on selected format
        file_extension = f".{file_format}"
        default_output_path = os.path.join(output_dir, f"{midi_filename}_{track_name}_{timestamp}{file_extension}")
            
        # Filter based on file format
        file_filter = self.tr('Text Files (*.txt)') if file_format == 'txt' else self.tr('LRC Files (*.lrc)')
            
        # Ask user for save location
        output_path, _ = QFileDialog.getSaveFileName(
            self, self.tr('Export Lyrics'),
            default_output_path,
            file_filter
        )
            
        if not output_path:
            return
            
        try:
            # Prepare lyrics content
            lyrics_content = []
            
            # Add header for txt format
            if file_format == 'txt':
                lyrics_content.append(f"# Lyrics exported from: {midi_filename}")
                lyrics_content.append(f"# Track: {track_name} (Track {track_index})")
                lyrics_content.append(f"# Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                lyrics_content.append("")
                
            # Add lyrics based on selected format
            for start_time, end_time, original_lyric, modified_lyric in self.lyricsData:
                # Format time for display
                ticks_per_beat = mainWindow.midiReader.midi.ticks_per_beat
                seconds_start = start_time / ticks_per_beat * 60 / 120  # Assuming 120 BPM
                
                # Format timestamp based on file format
                if include_timestamp:
                    if file_format == 'txt':
                        time_str = f"[{int(seconds_start//60):02d}:{seconds_start%60:05.2f}]"
                    else:  # LRC format
                        minutes = int(seconds_start // 60)
                        seconds = int(seconds_start % 60)
                        hundredths = int((seconds_start % 1) * 100)
                        time_str = f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]"
                else:
                    time_str = ""
                
                # Add the lyric line based on selected format
                if export_format == "original":
                    lyrics_content.append(f"{time_str} {original_lyric}")
                elif export_format == "modified":
                    lyrics_content.append(f"{time_str} {modified_lyric}")
                else:  # "both"
                    lyrics_content.append(f"{time_str} {original_lyric} | {modified_lyric}")
                
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lyrics_content))
                
            # Show success message
            InfoBar.success(
                title=self.tr('Success'),
                content=self.tr(f'Lyrics exported to {output_path}'),
                parent=self
            )
            
            # Open containing folder
            if os.path.exists(output_path):
                try:
                    # Show the file in file explorer
                    import subprocess
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(f'explorer /select,"{output_path}"')
                    elif os.name == 'posix':  # macOS or Linux
                        subprocess.Popen(['open', '-R', output_path])
                except:
                    pass
                
        except Exception as e:
            InfoBar.error(
                title=self.tr('Error'),
                content=self.tr(f'Failed to export lyrics: {str(e)}'),
                parent=self
            )
            print(f"Error details: {str(e)}")
            
    def apply_lyric_changes(self, track, lyrics_data):
        """Apply lyric changes to a track"""
        import mido
        
        # Find and remove existing lyric events
        filtered_messages = []
        for msg in track:
            if not (hasattr(msg, 'type') and msg.type == 'lyrics'):
                filtered_messages.append(msg)
                
        # Create a new track with non-lyric messages
        new_track = mido.MidiTrack()
        current_time = 0
        last_message_time = 0
        
        # Sort lyric data by start time
        lyrics_data.sort(key=lambda x: x[0])
        
        # Process all messages and insert lyrics at appropriate times
        for msg in filtered_messages:
            current_time += msg.time
            
            # Check if we need to insert any lyrics before this message
            lyrics_to_insert = []
            for start_time, _, _, modified_lyric in lyrics_data:
                if last_message_time < start_time <= current_time and modified_lyric.strip():
                    lyrics_to_insert.append((start_time, modified_lyric))
            
            # Sort lyrics by time
            lyrics_to_insert.sort(key=lambda x: x[0])
            
            # Insert lyrics
            for lyric_time, lyric_text in lyrics_to_insert:
                # Calculate delta time
                delta = lyric_time - last_message_time
                last_message_time = lyric_time
                
                # Create lyric message
                lyric_msg = mido.Message('lyrics', text=lyric_text, time=delta)
                new_track.append(lyric_msg)
            
            # Update message delta time
            if lyrics_to_insert:
                msg_copy = msg.copy()
                msg_copy.time = current_time - last_message_time
                new_track.append(msg_copy)
            else:
                new_track.append(msg)
                
            last_message_time = current_time
            
        # Add any remaining lyrics
        for start_time, _, _, modified_lyric in lyrics_data:
            if start_time > last_message_time and modified_lyric.strip():
                delta = start_time - last_message_time
                last_message_time = start_time
                
                lyric_msg = mido.Message('lyrics', text=modified_lyric, time=delta)
                new_track.append(lyric_msg)
                
        return new_track
        
    def updateTrackComboBox(self):
        """Update the track combo box with available tracks"""
        mainWindow = self.getMainWindow()
        if not mainWindow or not mainWindow.midiReader.midi:
            self.trackComboBox.clear()
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
        
        # Load lyrics for the current track
        self.loadLyricsForTrack(mainWindow.currentTrackIndex)
        
    def getMainWindow(self):
        """Get reference to main window"""
        widget = self.parent()
        while widget:
            if hasattr(widget, 'midiReader'):
                return widget
            widget = widget.parent()
        return None
        
    def showTableContextMenu(self, position):
        """Show context menu for the table"""
        from qfluentwidgets import Action, FluentContextMenu
        
        menu = FluentContextMenu()
        
        # Add actions
        copyToRefAction = Action(FIF.COPY, self.tr('Copy to Reference'))
        applyFromRefAction = Action(FIF.ACCEPT, self.tr('Apply from Reference'))
        
        menu.addAction(copyToRefAction)
        menu.addAction(applyFromRefAction)
        
        # Connect actions
        copyToRefAction.triggered.connect(self.copySelectedToReference)
        applyFromRefAction.triggered.connect(self.applyReferenceToSelected)
        
        # Show menu
        menu.exec_(self.lyricTable.mapToGlobal(position))
    
    def copySelectedToReference(self):
        """Copy selected lyric to reference text"""
        selected_rows = self.lyricTable.selectedIndexes()
        if not selected_rows:
            return
            
        # Get the selected row
        row = selected_rows[0].row()
        
        # Get the modified lyric text
        modified_text = self.lyricTable.item(row, 2).text()
        
        # Set as reference text
        self.referenceTextEdit.setText(modified_text)
