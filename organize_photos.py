import os
from datetime import datetime
import shutil
from pathlib import Path
import subprocess
import argparse

# Approach 1: Using a global debug flag
DEBUG = True  # Set to False to disable debug prints

# Approach 2: Using a debug function
def debug_print(*args, **kwargs):
    """Print only if DEBUG is True."""
    if DEBUG:
        print(*args, **kwargs)

def get_date_taken(image_path):
    """Get the date when the photo/video was taken using exiftool."""
    # MP4s often lack DateTimeOriginal; fall back to CreateDate
    tags = ['-DateTimeOriginal', '-CreateDate']
    for tag in tags:
        try:
            result = subprocess.run(
                ['exiftool', tag, '-d', '%Y:%m:%d %H:%M:%S', str(image_path)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                date_str = result.stdout.split(': ')[1].strip()
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            debug_print(f"Error reading EXIF data from {image_path}: {e}")
    return None

def organize_dng_files(source_dir, debug=False, tag=None):
    global DEBUG
    DEBUG = debug

    source_path = Path(source_dir)
    debug_print(f"Processing directory: {source_path}")

    files = (list(source_path.glob("*.DNG")) + list(source_path.glob("*.dng"))
             + list(source_path.glob("*.JPG")) + list(source_path.glob("*.jpg"))
             + list(source_path.glob("*.MP4")) + list(source_path.glob("*.mp4")))

    for file_path in files:
        if not file_path.is_file():  # Skip if not a file
            continue
            
        debug_print(f"\nProcessing file: {file_path.name}")
        
        # Get date from EXIF data
        date_taken = get_date_taken(file_path)
        if date_taken is None:
            debug_print(f"Could not get creation date for {file_path.name}, skipping...")
            continue
            
        debug_print(f"Original photo date: {date_taken}")
        date_str = date_taken.strftime("%Y-%m-%d")
        if tag:
            date_str = f"{date_str}-{tag}"
        debug_print(f"Folder name will be: {date_str}")

        # Create target directory if it doesn't exist
        target_dir = source_path / date_str
        target_dir.mkdir(exist_ok=True)
        
        # Move file to target directory
        target_path = target_dir / file_path.name
        debug_print(f"Moving {file_path.name} to {date_str}/")
        shutil.move(str(file_path), str(target_path))

def retag_existing_dirs(source_dir, tag, debug=False):
    global DEBUG
    DEBUG = debug

    import re
    source_path = Path(source_dir)
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    for d in sorted(source_path.iterdir()):
        if not d.is_dir() or not date_pattern.match(d.name):
            continue
        new_name = f"{d.name}-{tag}"
        new_path = source_path / new_name
        if new_path.exists():
            # Merge: move all files from d into new_path
            print(f"Merging {d.name}/ into {new_name}/")
            for f in d.iterdir():
                dest = new_path / f.name
                if dest.exists():
                    print(f"  Skipping {f.name} (already exists in {new_name}/)")
                else:
                    shutil.move(str(f), str(dest))
                    debug_print(f"  Moved {f.name}")
            d.rmdir()
        else:
            print(f"Renaming {d.name}/ → {new_name}/")
            d.rename(new_path)

def check_exiftool():
    """Check if exiftool is installed."""
    try:
        subprocess.run(['exiftool', '-ver'], capture_output=True)
        return True
    except FileNotFoundError:
        print("Error: exiftool is not installed. Please install it first:")
        print("  macOS: brew install exiftool")
        print("  Linux: sudo apt-get install exiftool")
        print("  Windows: Download from https://exiftool.org")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Organize DNG/JPG/MP4 files into directories based on creation date.'
    )
    parser.add_argument(
        'source_dir',
        help='Directory containing DNG/JPG files to organize'
    )
    parser.add_argument(
        '--tag',
        help='Tag to append to date folder names (e.g. m10p → 2026-03-25-m10p)',
        default=None
    )
    parser.add_argument(
        '--retag',
        action='store_true',
        help='Rename existing plain date folders (YYYY-MM-DD) to add --tag suffix'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    return parser.parse_args()

# Usage
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Check for exiftool
    if not check_exiftool():
        exit(1)

    # Check if source directory exists
    if not os.path.exists(args.source_dir):
        print(f"Error: Directory '{args.source_dir}' does not exist.")
        exit(1)
    
    if args.retag:
        if not args.tag:
            print("Error: --retag requires --tag")
            exit(1)
        retag_existing_dirs(args.source_dir, args.tag, debug=args.debug)
    else:
        organize_dng_files(args.source_dir, debug=args.debug, tag=args.tag)