# coding:utf-8
import os
import mido


class MidiReader:
    """MIDI file reader class"""
    
    def __init__(self):
        self.midi = None
        self.filepath = None
        self.lyrics = {}  # Store lyrics by time
        
    def load_midi(self, filepath):
        """Load a MIDI file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            self.midi = mido.MidiFile(filepath)
            self.filepath = filepath
            self._extract_lyrics()
            return True
        except Exception as e:
            print(f"Error loading MIDI file: {str(e)}")
            raise
    
    def _extract_lyrics(self):
        """Extract lyrics from MIDI file"""
        if not self.midi:
            return
            
        self.lyrics = {}
        
        for track_idx, track in enumerate(self.midi.tracks):
            time = 0
            for msg in track:
                time += msg.time
                if hasattr(msg, 'type') and msg.type == 'lyrics':
                    self.lyrics[time] = {
                        'text': msg.text,
                        'track': track_idx
                    }
    
    def get_file_info(self):
        """Get basic information about the loaded MIDI file"""
        if not self.midi:
            return {
                'format': 0,
                'num_tracks': 0,
                'ticks_per_beat': 480,
                'length': 0,
                'filename': None
            }
        
        return {
            'format': self.midi.type,
            'num_tracks': len(self.midi.tracks),
            'ticks_per_beat': self.midi.ticks_per_beat,
            'length': self.get_length_seconds(),
            'filename': os.path.basename(self.filepath) if self.filepath else None
        }
    
    def get_tracks(self):
        """Get all tracks in the MIDI file"""
        if not self.midi:
            return []
        
        return self.midi.tracks
    
    def get_track_info(self, track_index):
        """Get information about a specific track"""
        if not self.midi or track_index >= len(self.midi.tracks):
            return {
                'name': f"Track {track_index}",
                'instrument': None,
                'notes_count': 0,
                'events_count': 0,
                'has_lyrics': False
            }
        
        track = self.midi.tracks[track_index]
        info = {
            'name': None,
            'instrument': None,
            'notes_count': 0,
            'events_count': len(track),
            'has_lyrics': False
        }
        
        # Extract track name and instrument if available
        for msg in track:
            if hasattr(msg, 'type'):
                if msg.type == 'track_name':
                    info['name'] = msg.name
                elif msg.type == 'program_change':
                    info['instrument'] = msg.program
                elif msg.type == 'note_on':
                    info['notes_count'] += 1
                elif msg.type == 'lyrics':
                    info['has_lyrics'] = True
        
        return info
    
    def get_length_seconds(self):
        """Get the length of the MIDI file in seconds"""
        if not self.midi:
            return 0
        
        try:
            return self.midi.length
        except Exception:
            # Some MIDI files might not have proper length information
            return 0
    
    def get_tempo_changes(self):
        """Get all tempo changes in the MIDI file"""
        if not self.midi:
            return []
        
        tempo_changes = []
        
        for track in self.midi.tracks:
            track_time = 0
            for msg in track:
                track_time += msg.time
                if hasattr(msg, 'type') and msg.type == 'set_tempo':
                    tempo_bpm = mido.tempo2bpm(msg.tempo)
                    tempo_changes.append({
                        'time': track_time,
                        'tempo': msg.tempo,
                        'bpm': tempo_bpm
                    })
        
        return tempo_changes
    
    def get_track_lyrics(self, track_index):
        """Get lyrics for a specific track"""
        if not self.midi:
            return {}
            
        track_lyrics = {}
        for time, lyric_info in self.lyrics.items():
            if lyric_info['track'] == track_index:
                track_lyrics[time] = lyric_info['text']
                
        return track_lyrics
    
    def get_lyric_at_time(self, track_index, time, tolerance=10):
        """Get a lyric at the specified time with tolerance"""
        if not self.midi:
            return None
            
        # Find the closest lyric within tolerance
        closest_time = None
        closest_dist = tolerance + 1
        
        for lyric_time, lyric_info in self.lyrics.items():
            if lyric_info['track'] == track_index:
                dist = abs(lyric_time - time)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_time = lyric_time
        
        if closest_time is not None:
            return self.lyrics[closest_time]['text']
            
        return None
