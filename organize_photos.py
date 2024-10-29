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
    """Get the date when the photo was taken using exiftool."""
    try:
        # Run exiftool to get DateTimeOriginal
        result = subprocess.run(
            ['exiftool', '-DateTimeOriginal', '-d', '%Y:%m:%d %H:%M:%S', str(image_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            # Extract date from output
            date_str = result.stdout.split(': ')[1].strip()
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        debug_print(f"Error reading EXIF data from {image_path}: {e}")
    return None

def organize_dng_files(source_dir, debug=False):
    """Organize .dng files into directories based on creation date.
    
    Parameters
    ----------
    source_dir : str
        Source directory containing .dng files
    debug : bool, optional
        If True, print debug information
    """
    global DEBUG  # Use the global DEBUG variable
    DEBUG = debug  # Set debug flag based on parameter
    
    source_path = Path(source_dir)
    debug_print(f"Processing directory: {source_path}")
    
    # Process only files in the root directory
    for file_path in source_path.glob("*.DNG"):
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
        debug_print(f"Folder name will be: {date_str}")

        # Create target directory if it doesn't exist
        target_dir = source_path / date_str
        target_dir.mkdir(exist_ok=True)
        
        # Move file to target directory
        target_path = target_dir / file_path.name
        debug_print(f"Moving {file_path.name} to {date_str}/")
        shutil.move(str(file_path), str(target_path))

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
        description='Organize DNG files into directories based on creation date.'
    )
    parser.add_argument(
        'source_dir',
        help='Directory containing DNG files to organize'
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
    
    # Organize files
    organize_dng_files(args.source_dir, debug=args.debug)