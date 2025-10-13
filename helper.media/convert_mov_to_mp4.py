import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from tqdm import tqdm

# Configuration Parameters
SOURCE_PATH = "input"          # Source folder for MOV files
DESTINATION_PATH = "output"     # Destination folder for MP4 files
FILE_EXTENSIONS = [".mov", ".MOV"]  # File extensions to process
QUALITY_LEVEL = "high"          # Quality level: high, medium, low
USE_HEVC = False                # Use H.265/HEVC for better compression (slower, not all devices support)

# Quality settings - optimized for compression with slower encoding
# CRF: Lower = better quality (18=very high, 23=good, 28=acceptable)
# Preset: slower = better compression (slow, medium, fast)
# Max bitrate prevents excessive file sizes
QUALITY_SETTINGS = {
    'high': {
        'crf': '18',
        'preset': 'slow',
        'audio_bitrate': '192k',
        'max_video_bitrate': '8M',  # Max 8 Mbps for video
        'bufsize': '16M'
    },
    'medium': {
        'crf': '23',
        'preset': 'slow',
        'audio_bitrate': '128k',
        'max_video_bitrate': '5M',  # Max 5 Mbps for video
        'bufsize': '10M'
    },
    'low': {
        'crf': '28',
        'preset': 'medium',
        'audio_bitrate': '96k',
        'max_video_bitrate': '3M',  # Max 3 Mbps for video
        'bufsize': '6M'
    }
}

def get_ffmpeg_path():
    """Get the path to ffmpeg executable"""
    script_dir = Path(__file__).parent
    ffmpeg_path = script_dir / 'bin' / 'ffmpeg.exe'

    if ffmpeg_path.exists():
        return str(ffmpeg_path)

    # Fallback to system ffmpeg
    if shutil.which('ffmpeg'):
        return 'ffmpeg'

    return None

def get_exiftool_path():
    """Get the path to exiftool executable"""
    script_dir = Path(__file__).parent
    exiftool_path = script_dir / 'bin' / 'exiftool.exe'

    if exiftool_path.exists():
        return str(exiftool_path)

    return None

def get_video_info(file_path):
    """
    Get video codec and bitrate information using ffprobe

    Returns:
        dict: Video information including codec, bitrate, audio codec, etc.
    """
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return None

    # Use ffprobe (comes with ffmpeg) to get detailed video info
    ffprobe_path = str(Path(ffmpeg_path).parent / 'ffprobe.exe') if 'bin' in ffmpeg_path else 'ffprobe'

    try:
        cmd = [
            ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        video_info = {
            'video_codec': None,
            'video_bitrate': 0,
            'audio_codec': None,
            'audio_bitrate': 0,
            'duration': 0,
            'width': 0,
            'height': 0
        }

        # Extract video stream info
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_info['video_codec'] = stream.get('codec_name', 'unknown')
                video_info['width'] = stream.get('width', 0)
                video_info['height'] = stream.get('height', 0)
                # Get bitrate from stream or calculate from file size
                if 'bit_rate' in stream:
                    video_info['video_bitrate'] = int(stream['bit_rate'])
            elif stream.get('codec_type') == 'audio':
                video_info['audio_codec'] = stream.get('codec_name', 'unknown')
                if 'bit_rate' in stream:
                    video_info['audio_bitrate'] = int(stream['bit_rate'])

        # Get overall bitrate from format if not found in streams
        if 'format' in data:
            if 'duration' in data['format']:
                video_info['duration'] = float(data['format']['duration'])
            if 'bit_rate' in data['format'] and video_info['video_bitrate'] == 0:
                total_bitrate = int(data['format']['bit_rate'])
                video_info['video_bitrate'] = total_bitrate - video_info['audio_bitrate']

        return video_info

    except Exception as e:
        print(f"  [WARNING] Could not get video info: {e}")
        return None

def preserve_metadata(source_file, target_file):
    """
    Preserve metadata from source to target file using exiftool
    """
    exiftool_path = get_exiftool_path()
    if not exiftool_path:
        print("Warning: exiftool not found, metadata may not be preserved")
        return False

    try:
        # Copy all metadata from source to target
        cmd = [exiftool_path, '-TagsFromFile', str(source_file), '-all:all', str(target_file), '-overwrite_original']
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True
        else:
            print(f"Warning: Failed to preserve metadata: {result.stderr}")
            return False
    except Exception as e:
        print(f"Warning: Error preserving metadata: {e}")
        return False

def files_are_identical(file1, file2):
    """
    Check if two files are identical by comparing size, modification time, and content hash
    """
    if not file2.exists():
        return False

    # Quick checks first
    stat1 = file1.stat()
    stat2 = file2.stat()

    # Check file size
    if stat1.st_size != stat2.st_size:
        return False

    # Check modification time (within 1 second tolerance)
    if abs(stat1.st_mtime - stat2.st_mtime) > 1:
        return False

    # For small files, do content comparison
    if stat1.st_size < 50 * 1024 * 1024:  # Less than 50MB
        import hashlib
        try:
            print(f"  [DEBUG] Comparing file content for {file1.name}...", end='', flush=True)
            hash1 = hashlib.md5()
            hash2 = hashlib.md5()

            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                # Read in chunks to handle large files
                while True:
                    chunk1 = f1.read(8192)
                    chunk2 = f2.read(8192)
                    if not chunk1 and not chunk2:
                        break
                    if not chunk1 or not chunk2 or chunk1 != chunk2:
                        print(" Different content found")
                        return False
                    hash1.update(chunk1)
                    hash2.update(chunk2)

            result = hash1.hexdigest() == hash2.hexdigest()
            print(f" {'Identical' if result else 'Different'}")
            return result
        except Exception as e:
            print(f" Error: {e}")
            return False

    # For large files, assume identical if size and mtime match
    return True

def create_backup(source_file, output_folder):
    """
    Create a backup by copying original file to output folder only if it doesn't already exist
    """
    try:
        backup_path = output_folder / source_file.name

        # Check if identical file already exists
        if backup_path.exists() and files_are_identical(source_file, backup_path):
            print(f"[SKIP] Backup already exists: {source_file.name}")
            return backup_path

        # Remove existing file if it exists but is different
        if backup_path.exists():
            backup_path.unlink()
            print(f"[INFO] Replacing different backup: {source_file.name}")

        shutil.copy2(source_file, backup_path)
        print(f"[OK] Backup created: {source_file.name}")
        return backup_path
    except Exception as e:
        print(f"[ERROR] Failed to create backup: {e}")
        return None

def get_file_metadata(file_path):
    """
    Extract metadata from file using exiftool
    """
    exiftool_path = get_exiftool_path()
    if not exiftool_path:
        return {}

    try:
        cmd = [exiftool_path, '-j', str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            metadata = json.loads(result.stdout)[0]
            return metadata
    except Exception:
        pass
    return {}

def compare_metadata(source_file, target_file):
    """
    Compare metadata between source and target files
    """
    source_meta = get_file_metadata(source_file)
    target_meta = get_file_metadata(target_file)

    important_fields = [
        'CreateDate', 'ModifyDate', 'DateTimeOriginal', 'FileModifyDate',
        'GPSLatitude', 'GPSLongitude', 'GPSPosition', 'Model', 'Make',
        'Duration', 'ImageWidth', 'ImageHeight', 'VideoFrameRate'
    ]

    comparison = {
        'preserved': [],
        'missing': [],
        'different': []
    }

    for field in important_fields:
        if field in source_meta:
            if field in target_meta:
                if str(source_meta[field]) == str(target_meta[field]):
                    comparison['preserved'].append(field)
                else:
                    comparison['different'].append({
                        'field': field,
                        'source': source_meta[field],
                        'target': target_meta[field]
                    })
            else:
                comparison['missing'].append(field)

    return comparison

def convert_mov_to_mp4(input_file, output_folder):
    """
    Convert a single MOV file to MP4 with size reduction and metadata preservation

    Args:
        input_file (Path): Path to the input MOV file
        output_folder (Path): Folder for the output MP4 file

    Returns:
        dict: Conversion results with metadata comparison
    """
    result = {
        'success': False,
        'input_file': input_file.name,
        'original_size': 0,
        'converted_size': 0,
        'backup_created': False,
        'metadata_comparison': None,
        'video_info': None
    }

    if not input_file.exists():
        print(f"Error: Input file '{input_file}' does not exist.")
        return result

    if input_file.suffix.lower() not in [ext.lower() for ext in FILE_EXTENSIONS]:
        print(f"Error: Input file '{input_file}' is not a supported file type.")
        return result

    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print("Error: ffmpeg not found in bin folder or system PATH")
        return result

    # Get video information first
    print(f"Analyzing {input_file.name}...")
    video_info = get_video_info(input_file)
    result['video_info'] = video_info

    if video_info:
        print(f"  Source codec: {video_info['video_codec']} @ {video_info['video_bitrate'] / 1_000_000:.1f} Mbps")
        print(f"  Audio codec: {video_info['audio_codec']} @ {video_info['audio_bitrate'] / 1000:.0f} kbps")
        print(f"  Resolution: {video_info['width']}x{video_info['height']}")

    # Create backup first
    backup_path = create_backup(input_file, output_folder)
    if backup_path:
        result['backup_created'] = True

    # Set output path
    output_file = output_folder / input_file.with_suffix('.MP4').name

    # Remove existing output file if it exists (with retry for Windows file locking)
    if output_file.exists():
        try:
            output_file.unlink()
        except PermissionError:
            print(f"  [WARNING] Could not delete existing {output_file.name}, ffmpeg will overwrite it")

    # Get quality settings
    quality_config = QUALITY_SETTINGS.get(QUALITY_LEVEL, QUALITY_SETTINGS['medium'])

    # Determine video encoding strategy
    video_codec_args = []
    should_reencode_video = True

    if video_info:
        source_codec = video_info['video_codec']
        source_bitrate = video_info['video_bitrate']

        # Determine target codec
        if USE_HEVC:
            target_codec = 'libx265'
            target_codec_name = 'H.265/HEVC'
        else:
            target_codec = 'libx264'
            target_codec_name = 'H.264'

        # Check if we can copy the video stream (already optimal)
        max_bitrate_bps = int(quality_config['max_video_bitrate'].rstrip('M')) * 1_000_000

        if not USE_HEVC and source_codec in ['h264', 'avc1'] and source_bitrate <= max_bitrate_bps * 1.1:
            # Source is already H.264 and within reasonable bitrate, just copy it
            print(f"  Video: Copying stream (already H.264 at acceptable bitrate)")
            video_codec_args = ['-c:v', 'copy']
            should_reencode_video = False
        else:
            # Re-encode with target codec
            print(f"  Video: Re-encoding to {target_codec_name} (preset: {quality_config['preset']}, CRF: {quality_config['crf']})")
            video_codec_args = [
                '-c:v', target_codec,
                '-crf', quality_config['crf'],
                '-preset', quality_config['preset'],
                '-maxrate', quality_config['max_video_bitrate'],
                '-bufsize', quality_config['bufsize']
            ]

            # Add x265-specific params for better compression
            if USE_HEVC:
                video_codec_args.extend(['-x265-params', 'log-level=error'])
    else:
        # No video info available, use default encoding
        target_codec = 'libx265' if USE_HEVC else 'libx264'
        print(f"  Video: Re-encoding to {target_codec} (no source info available)")
        video_codec_args = [
            '-c:v', target_codec,
            '-crf', quality_config['crf'],
            '-preset', quality_config['preset'],
            '-maxrate', quality_config['max_video_bitrate'],
            '-bufsize', quality_config['bufsize']
        ]
        if USE_HEVC:
            video_codec_args.extend(['-x265-params', 'log-level=error'])

    # Determine audio encoding strategy
    audio_codec_args = []
    if video_info and video_info['audio_codec'] in ['aac']:
        target_audio_bitrate_bps = int(quality_config['audio_bitrate'].rstrip('k')) * 1000
        if video_info['audio_bitrate'] <= target_audio_bitrate_bps * 1.1:
            # Audio is already AAC at acceptable bitrate, copy it
            print(f"  Audio: Copying stream (already AAC at acceptable bitrate)")
            audio_codec_args = ['-c:a', 'copy']
        else:
            print(f"  Audio: Re-encoding to AAC @ {quality_config['audio_bitrate']}")
            audio_codec_args = ['-c:a', 'aac', '-b:a', quality_config['audio_bitrate']]
    else:
        print(f"  Audio: Re-encoding to AAC @ {quality_config['audio_bitrate']}")
        audio_codec_args = ['-c:a', 'aac', '-b:a', quality_config['audio_bitrate']]

    # Build optimized ffmpeg command
    cmd = [
        ffmpeg_path,
        '-i', str(input_file),
        '-threads', '0',                 # Use all available CPU cores
    ]

    # Add video encoding args
    cmd.extend(video_codec_args)

    # Add audio encoding args
    cmd.extend(audio_codec_args)

    # Add common flags
    cmd.extend([
        '-map_metadata', '0',            # Copy all metadata
        '-movflags', '+faststart',       # Optimize for streaming
        '-avoid_negative_ts', 'make_zero', # Fix timestamp issues
        '-fflags', '+genpts',            # Generate presentation timestamps
        '-y', str(output_file)
    ])

    try:
        print(f"Converting {input_file.name} to {output_file.name}...")

        # Get video duration first for percentage calculation
        duration_cmd = [ffmpeg_path, '-i', str(input_file), '-f', 'null', '-']
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration_seconds = 0
        duration_output = duration_result.stderr if duration_result.stderr else duration_result.stdout
        for line in duration_output.split('\n'):
            if 'Duration:' in line:
                duration_str = line.split('Duration: ')[1].split(',')[0]
                time_parts = duration_str.split(':')
                if len(time_parts) == 3:
                    hours, minutes, seconds = time_parts
                    duration_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                break

        # Simple progress monitoring using stderr parsing
        import time
        import threading
        import re

        start_time = time.time()

        try:
            print(f"  Progress: Starting conversion...", flush=True)

            # Run ffmpeg with simple output
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, universal_newlines=True, bufsize=1)

            # Monitor output for progress information
            last_update_time = time.time()

            for line in iter(process.stdout.readline, ''):
                current_time = time.time()

                # Look for time progress in ffmpeg output
                time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', line)
                if time_match and current_time - last_update_time > 2.0:  # Update every 2 seconds
                    hours, minutes, seconds, centiseconds = time_match.groups()
                    current_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(centiseconds) / 100

                    # Calculate percentage
                    percentage = 0
                    if duration_seconds > 0:
                        percentage = min(100, (current_seconds / duration_seconds) * 100)

                    # Look for speed in the same line
                    speed_match = re.search(r'speed=\s*(\S+)', line)
                    speed = speed_match.group(1) if speed_match else 'N/A'

                    # Create simple progress display
                    if percentage > 0:
                        filled = int(percentage / 5)  # 20 chars
                        progress_bar = f"[{'#' * filled}{'.' * (20 - filled)}] {percentage:5.1f}%"

                        # Calculate ETA
                        elapsed = current_time - start_time
                        if percentage > 1:
                            eta_seconds = (elapsed / percentage) * (100 - percentage)
                            eta_min = int(eta_seconds // 60)
                            eta_sec = int(eta_seconds % 60)
                            eta = f"{eta_min:02d}:{eta_sec:02d}"
                        else:
                            eta = "N/A"

                        current_time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

                        progress_text = f"\r  {progress_bar} | Time: {current_time_str}"
                        if speed != 'N/A':
                            progress_text += f" | Speed: {speed}"
                        if eta != "N/A":
                            progress_text += f" | ETA: {eta}"

                        print(progress_text, end='', flush=True)
                        last_update_time = current_time

                # Show dots for activity even without time updates
                elif current_time - last_update_time > 5.0:
                    print(".", end='', flush=True)
                    last_update_time = current_time

            print()  # New line after progress

            # Wait for process completion
            process.wait()

            if process.returncode == 0:
                print(f"  [OK] Conversion completed successfully!")
            else:
                print(f"  [ERROR] Conversion failed (exit code: {process.returncode})")
                return result

        except Exception as e:
            print(f"  [ERROR] Error during conversion: {e}")
            return result


        # Preserve additional metadata using exiftool
        preserve_metadata(input_file, output_file)

        # Set file timestamps to match original creation datetime
        if output_file.exists():
            try:
                # First try to get creation date from metadata using exiftool
                creation_time = None
                exiftool_path = get_exiftool_path()

                if exiftool_path:
                    try:
                        cmd = [exiftool_path, '-CreateDate', '-s3', str(input_file)]
                        exif_result = subprocess.run(cmd, capture_output=True, text=True)
                        if exif_result.returncode == 0 and exif_result.stdout.strip():
                            # Parse creation date (format: YYYY:MM:DD HH:MM:SS)
                            from datetime import datetime
                            date_str = exif_result.stdout.strip()
                            creation_time = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').timestamp()
                    except Exception:
                        pass

                # Fallback to original file modification time if metadata extraction fails
                if creation_time is None:
                    original_stat = input_file.stat()
                    creation_time = original_stat.st_mtime

                # Set both access time and modification time to creation time
                # This ensures modify datetime matches create datetime
                os.utime(output_file, (creation_time, creation_time))

                # Format timestamp for display
                from datetime import datetime
                formatted_time = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  [OK] File timestamps set to creation date: {formatted_time}")

            except Exception as e:
                print(f"  [WARNING] Could not set timestamps: {e}")

        # Get file sizes and show results
        if output_file.exists():
            result['original_size'] = input_file.stat().st_size
            result['converted_size'] = output_file.stat().st_size
            reduction = (1 - result['converted_size'] / result['original_size']) * 100

            print(f"  Original size: {result['original_size'] / (1024*1024):.1f} MB")
            print(f"  New size: {result['converted_size'] / (1024*1024):.1f} MB")
            print(f"  Size reduction: {reduction:.1f}%")

            # Compare metadata
            result['metadata_comparison'] = compare_metadata(input_file, output_file)
            result['success'] = True
        else:
            print(f"  [ERROR] Output file was not created")

        return result

    except Exception as e:
        print(f"  [ERROR] Error during conversion: {e}")
        return result

def print_metadata_comparison(comparison, filename):
    """
    Print metadata comparison results
    """
    print(f"\n  Metadata Analysis for {filename}:")
    print(f"    Preserved: {len(comparison['preserved'])} fields")

    if comparison['preserved']:
        print(f"      {', '.join(comparison['preserved'][:5])}{'...' if len(comparison['preserved']) > 5 else ''}")

    if comparison['missing']:
        print(f"    Missing: {len(comparison['missing'])} fields")
        print(f"      {', '.join(comparison['missing'][:3])}{'...' if len(comparison['missing']) > 3 else ''}")

    if comparison['different']:
        print(f"    Different: {len(comparison['different'])} fields")
        for diff in comparison['different'][:2]:  # Show first 2 differences
            print(f"      {diff['field']}: {diff['source']} -> {diff['target']}")

def convert_all_mov_files():
    """
    Convert all MOV files from source folder to destination folder
    Creates backups by copying originals to destination folder

    Returns:
        dict: Detailed conversion results
    """
    script_dir = Path(__file__).parent
    input_folder = script_dir / SOURCE_PATH
    output_folder = script_dir / DESTINATION_PATH

    # Create folders if they don't exist
    input_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)

    if not input_folder.exists():
        print(f"Error: Source folder '{input_folder}' does not exist.")
        return {'success': False, 'results': []}

    # Find all specified files (case-insensitive to avoid duplicates)
    target_files = []
    seen_files = set()

    for ext in FILE_EXTENSIONS:
        for file_path in input_folder.glob(f'*{ext}'):
            # Use lowercase name as key to avoid case-sensitive duplicates
            file_key = file_path.name.lower()
            if file_key not in seen_files:
                seen_files.add(file_key)
                target_files.append(file_path)

    if not target_files:
        print(f"No files with extensions {FILE_EXTENSIONS} found in '{input_folder}'")
        return {'success': False, 'results': []}

    print(f"Found {len(target_files)} files to convert")
    print(f"Source folder: {input_folder}")
    print(f"Destination folder: {output_folder}")
    print(f"Quality level: {QUALITY_LEVEL} (preset: {QUALITY_SETTINGS[QUALITY_LEVEL]['preset']}, CRF: {QUALITY_SETTINGS[QUALITY_LEVEL]['crf']})")
    print(f"Max bitrate: {QUALITY_SETTINGS[QUALITY_LEVEL]['max_video_bitrate']}")
    print(f"Target codec: {'H.265/HEVC' if USE_HEVC else 'H.264'}")
    print(f"File extensions: {FILE_EXTENSIONS}")
    print()

    results = []
    total_original_size = 0
    total_converted_size = 0
    successful_conversions = 0

    # Convert each file with progress bar
    for target_file in tqdm(target_files, desc="Processing files"):
        result = convert_mov_to_mp4(target_file, output_folder)
        results.append(result)

        if result['success']:
            successful_conversions += 1
            total_original_size += result['original_size']
            total_converted_size += result['converted_size']

            # Show metadata comparison
            if result['metadata_comparison']:
                print_metadata_comparison(result['metadata_comparison'], result['input_file'])

        print()  # Add spacing between files

    # Final Summary
    print(f"\n{'='*60}")
    print(f"CONVERSION SUMMARY")
    print(f"{'='*60}")
    print(f"Files processed: {len(target_files)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {len(target_files) - successful_conversions}")

    if total_original_size > 0:
        total_reduction = (1 - total_converted_size / total_original_size) * 100
        print(f"\nSize Analysis:")
        print(f"  Total original size: {total_original_size / (1024*1024):.1f} MB")
        print(f"  Total converted size: {total_converted_size / (1024*1024):.1f} MB")
        print(f"  Total size reduction: {total_reduction:.1f}%")

    # Metadata Summary
    total_preserved = sum(len(r['metadata_comparison']['preserved']) for r in results if r['metadata_comparison'])
    total_missing = sum(len(r['metadata_comparison']['missing']) for r in results if r['metadata_comparison'])
    total_different = sum(len(r['metadata_comparison']['different']) for r in results if r['metadata_comparison'])

    if any(r['metadata_comparison'] for r in results):
        print(f"\nMetadata Summary:")
        print(f"  Total preserved fields: {total_preserved}")
        print(f"  Total missing fields: {total_missing}")
        print(f"  Total different fields: {total_different}")

    return {'success': True, 'results': results}

def main():
    """Main function"""
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print("Error: ffmpeg.exe not found in bin folder")
        print("Please ensure ffmpeg.exe is in the 'bin' folder")
        sys.exit(1)

    exiftool_path = get_exiftool_path()
    if not exiftool_path:
        print("Warning: exiftool.exe not found in bin folder")
        print("Metadata preservation may be limited")
        print()

    print("MOV to MP4 Converter with Intelligent Compression")
    print("==================================================")
    print("Configuration:")
    print(f"  Source path: {SOURCE_PATH}")
    print(f"  Destination path: {DESTINATION_PATH}")
    print(f"  File extensions: {FILE_EXTENSIONS}")
    print(f"  Quality level: {QUALITY_LEVEL}")
    print(f"  Encoding preset: {QUALITY_SETTINGS[QUALITY_LEVEL]['preset']}")
    print(f"  Max bitrate: {QUALITY_SETTINGS[QUALITY_LEVEL]['max_video_bitrate']}")
    print(f"  Use HEVC (H.265): {'Yes' if USE_HEVC else 'No (H.264)'}")
    print("\nFeatures:")
    print("- Intelligent codec detection (skips re-encoding if already optimal)")
    print("- Reduces file size with better compression settings")
    print("- Bitrate limits to prevent excessive file sizes")
    print("- Preserves all metadata (dates, location, etc.)")
    print("- Creates backups by copying originals to output folder")
    print("- Shows detailed conversion progress")
    print("- Compares metadata between source and target")
    print()

    convert_all_mov_files()

if __name__ == "__main__":
    main()