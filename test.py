import mido
import os
import argparse
import re

def sanitize_filename(name):
    """Removes or replaces characters invalid for filenames."""
    # Remove characters that are definitely invalid on Windows/Linux/Mac
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Replace sequences of whitespace with a single underscore
    name = re.sub(r'\s+', '_', name)
    # Remove leading/trailing whitespace/underscores
    name = name.strip(' _')
    # Limit length if necessary (optional)
    # max_len = 100
    # name = name[:max_len]
    if not name:
        return "Unnamed"
    return name

def extract_lyrics_from_midi(midi_filepath):
    """
    Extracts lyrics and timestamps from a MIDI file and saves them to text files
    in the 'output' directory.

    Args:
        midi_filepath (str): Path to the input MIDI file.
    """
    if not os.path.isfile(midi_filepath):
        print(f"错误：文件未找到 {midi_filepath}")
        return

    try:
        mid = mido.MidiFile(midi_filepath)
    except Exception as e:
        print(f"错误：读取 MIDI 文件时出错 {midi_filepath}: {e}")
        return

    output_dir = "output"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"错误：无法创建输出目录 {output_dir}: {e}")
        return

    midi_filename_base = os.path.splitext(os.path.basename(midi_filepath))[0]
    sanitized_midi_filename = sanitize_filename(midi_filename_base)

    print(f"正在处理 MIDI 文件: {midi_filepath}")
    print(f"每拍的 tick 数: {mid.ticks_per_beat}")

    for i, track in enumerate(mid.tracks):
        track_name_from_meta = f"Track_{i}"
        lyrics_data = []
        current_time_ticks = 0
        # Default MIDI tempo (120 BPM) = 500,000 microseconds per beat
        current_tempo = 500000

        # Try to find a track name early
        for msg in track:
             if msg.is_meta and msg.type == 'track_name':
                 try:
                     # Decode if bytes, otherwise use as is. Handle potential errors.
                     name_bytes = getattr(msg, 'name', None)
                     if isinstance(name_bytes, bytes):
                         try:
                             track_name_from_meta = name_bytes.decode('utf-8')
                         except UnicodeDecodeError:
                             try:
                                 track_name_from_meta = name_bytes.decode('latin1')
                             except UnicodeDecodeError:
                                 try:
                                     track_name_from_meta = name_bytes.decode('shift_jis') # Common for Japanese MIDI
                                 except UnicodeDecodeError:
                                     track_name_from_meta = f"Track_{i}_undecodable"
                     elif isinstance(name_bytes, str):
                         track_name_from_meta = name_bytes
                     else:
                         track_name_from_meta = f"Track_{i}"

                     track_name_from_meta = track_name_from_meta.strip()
                     if not track_name_from_meta: # Handle empty names
                         track_name_from_meta = f"Track_{i}"
                     break # Use the first track name found
                 except Exception:
                     track_name_from_meta = f"Track_{i}_error"
                     break


        print(f"\n正在处理轨道 {i} ({track_name_from_meta})")

        has_lyrics = False
        current_time_ticks = 0 # Reset time for processing lyrics

        for msg in track:
            # Update absolute time in ticks
            current_time_ticks += msg.time

            if msg.is_meta:
                if msg.type == 'set_tempo':
                    current_tempo = msg.tempo
                elif msg.type == 'lyrics':
                    has_lyrics = True
                    # Calculate time in seconds
                    time_seconds = mido.tick2second(current_time_ticks, mid.ticks_per_beat, current_tempo)

                    # Get lyric text. Mido usually decodes to latin1 by default if bytes.
                    lyric_text = getattr(msg, 'text', '')

                    # Attempt re-decoding if it looks like bytes or common encoding issues
                    raw_bytes = getattr(msg, 'data', None) # Mido might store raw bytes here
                    if isinstance(lyric_text, str) and raw_bytes:
                         # Try common encodings if default decoding seems wrong or bytes available
                         try:
                             lyric_text = raw_bytes.decode('utf-8').strip()
                         except UnicodeDecodeError:
                             try:
                                 lyric_text = raw_bytes.decode('shift_jis').strip()
                             except UnicodeDecodeError:
                                 try:
                                     # Fallback to latin1 if others fail
                                     lyric_text = raw_bytes.decode('latin1').strip()
                                 except UnicodeDecodeError:
                                      lyric_text = "[解码错误]" # Give up if all fail
                    elif isinstance(lyric_text, bytes): # If mido returned bytes directly
                         try:
                             lyric_text = lyric_text.decode('utf-8').strip()
                         except UnicodeDecodeError:
                             try:
                                 lyric_text = lyric_text.decode('shift_jis').strip()
                             except UnicodeDecodeError:
                                 try:
                                     lyric_text = lyric_text.decode('latin1').strip()
                                 except UnicodeDecodeError:
                                     lyric_text = "[解码错误]"
                    elif isinstance(lyric_text, str):
                        lyric_text = lyric_text.strip() # Clean up existing string
                    else:
                        lyric_text = "" # Ensure it's a string

                    if lyric_text: # Only add non-empty lyrics
                        lyrics_data.append((time_seconds, lyric_text))
                        # print(f"  发现歌词 @ {time_seconds:.3f}s: {lyric_text}")


        if has_lyrics and lyrics_data:
            safe_track_name = sanitize_filename(track_name_from_meta)
            output_filename = f"{sanitized_midi_filename}_{safe_track_name}.txt"
            output_filepath = os.path.join(output_dir, output_filename)

            print(f"  找到歌词。正在保存到: {output_filepath}")
            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    for time_sec, lyric in lyrics_data:
                        # Format: time (seconds, 3 decimal places) followed by tab, then lyric
                        f.write(f"{time_sec:.3f}\t{lyric}\n")
                print(f"  成功保存轨道 {i} 的歌词。")
            except IOError as e:
                print(f"  错误：写入文件时出错 {output_filepath}: {e}")
            except Exception as e:
                 print(f"  保存轨道 {i} 歌词时发生未知错误: {e}")
        elif has_lyrics:
             print(f"  轨道 {i} ({track_name_from_meta}) 包含歌词事件，但未能提取到有效文本。")
        else:
            print(f"  在轨道 {i} ({track_name_from_meta}) 中未找到歌词。")

if __name__ == "__main__":
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="从 MIDI 文件中提取歌词并保存到文本文件。")
    # 添加一个必需的位置参数 'midi_file'，用于指定输入的 MIDI 文件路径
    parser.add_argument("midi_file", help="输入的 MIDI 文件路径")
    # 解析命令行传入的参数
    args = parser.parse_args()

    # 调用主函数，传入解析到的 MIDI 文件路径
    extract_lyrics_from_midi(args.midi_file)