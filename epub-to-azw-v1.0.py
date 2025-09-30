#!/usr/bin/env python3
"""
EPUB to AZW3 Converter
Version: 1.0
Description: Converts EPUB files to AZW3 format using Calibre's ebook-convert
"""

import os
from os import listdir, rename, makedirs
from os.path import isfile, join, exists, expanduser, isdir, basename
import subprocess
import curses
import time
from datetime import datetime
import shutil
import glob

VERSION = "1.0"

# Base directory
BASE_DIR = join(expanduser("~"), "Documents", "Book Conversion")
INPUT_DIR = join(BASE_DIR, "input")
OUTPUT_DIR = join(BASE_DIR, "output")

# Ensure directories exist
def setup_directories():
    """Create the necessary directories if they don't exist"""
    for directory in [BASE_DIR, INPUT_DIR, OUTPUT_DIR]:
        if not exists(directory):
            makedirs(directory)

# Return the name of the file to be kept after conversion by changing the extension to .azw3
def get_final_filename(f):
    f = f.split(".")
    filename = ".".join(f[0:-1])
    processed_file_name = filename + ".azw3"
    return processed_file_name

# Return the file extension
def get_file_extension(f):
    return f.split(".")[-1].lower()

# Check if ebook-convert is available
def check_ebook_convert():
    try:
        subprocess.run(["ebook-convert", "--version"], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Ask user for source directory and copy EPUB files
def ask_for_source_and_copy():
    """Ask user for source directory containing EPUB files and copy them to input"""
    print("\n" + "=" * 80)
    print("EPUB to AZW3 Converter v" + VERSION)
    print("=" * 80)
    print()
    print(f"Input Directory:  {INPUT_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()
    
    while True:
        print("Where are your EPUB files located?")
        print("(Enter full path, or press Enter to skip and use files already in input directory)")
        print()
        source_path = input("Source directory: ").strip()
        
        # If empty, skip copying
        if not source_path:
            print("\nSkipping file copy. Using files already in input directory...")
            return True
        
        # Expand ~ to home directory
        source_path = expanduser(source_path)
        
        # Check if directory exists
        if not exists(source_path):
            print(f"\nError: Directory '{source_path}' does not exist.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return False
            continue
        
        if not isdir(source_path):
            print(f"\nError: '{source_path}' is not a directory.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return False
            continue
        
        # Find EPUB files in source directory
        epub_pattern = join(source_path, "*.epub")
        epub_files = glob.glob(epub_pattern)
        
        # Also check for .EPUB extension
        epub_pattern_upper = join(source_path, "*.EPUB")
        epub_files.extend(glob.glob(epub_pattern_upper))
        
        if not epub_files:
            print(f"\nNo EPUB files found in '{source_path}'")
            retry = input("Try again with a different directory? (y/n): ").strip().lower()
            if retry != 'y':
                return False
            continue
        
        # Show found files
        print(f"\nFound {len(epub_files)} EPUB file(s):")
        for epub in epub_files[:5]:  # Show first 5
            print(f"  - {basename(epub)}")
        if len(epub_files) > 5:
            print(f"  ... and {len(epub_files) - 5} more")
        
        # Confirm copy
        print()
        confirm = input(f"Copy these files to {INPUT_DIR}? (y/n): ").strip().lower()
        if confirm != 'y':
            retry = input("Try a different directory? (y/n): ").strip().lower()
            if retry != 'y':
                return False
            continue
        
        # Copy files
        print("\nCopying files...")
        copied = 0
        skipped = 0
        failed = 0
        
        for epub_file in epub_files:
            filename = basename(epub_file)
            dest_path = join(INPUT_DIR, filename)
            
            try:
                if exists(dest_path):
                    print(f"  Skipped (already exists): {filename}")
                    skipped += 1
                else:
                    shutil.copy2(epub_file, dest_path)
                    print(f"  Copied: {filename}")
                    copied += 1
            except Exception as e:
                print(f"  Failed to copy {filename}: {str(e)}")
                failed += 1
        
        print(f"\nCopy complete: {copied} copied, {skipped} skipped, {failed} failed")
        print()
        input("Press Enter to start conversion...")
        return True
    
    return False

# Main conversion function with curses interface
def main(stdscr):
    # Setup curses
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    # Setup color pairs
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Header
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Info
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
    
    # Get screen dimensions
    max_y, max_x = stdscr.getmaxyx()
    
    # Setup directories
    setup_directories()
    
    # Check if ebook-convert is available
    if not check_ebook_convert():
        stdscr.addstr(0, 0, "ERROR: ebook-convert not found!", curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 0, "Please install Calibre: sudo pacman -S calibre")
        stdscr.addstr(2, 0, "Press any key to exit...")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Draw header
    header = f"EPUB to AZW3 Converter v{VERSION}"
    stdscr.addstr(0, 0, "=" * min(max_x - 1, 80), curses.color_pair(1))
    stdscr.addstr(1, (max_x - len(header)) // 2, header, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(2, 0, "=" * min(max_x - 1, 80), curses.color_pair(1))
    
    # Display directories
    stdscr.addstr(3, 0, f"Input Directory:  {INPUT_DIR}", curses.A_BOLD)
    stdscr.addstr(4, 0, f"Output Directory: {OUTPUT_DIR}", curses.A_BOLD)
    stdscr.addstr(5, 0, "-" * min(max_x - 1, 80))
    
    # Status line
    status_line = 6
    
    # Get list of files
    try:
        raw_files = [f for f in listdir(INPUT_DIR) if isfile(join(INPUT_DIR, f))]
        converted_files = [f for f in listdir(OUTPUT_DIR) if isfile(join(OUTPUT_DIR, f))]
    except Exception as e:
        stdscr.addstr(status_line, 0, f"Error reading directories: {str(e)}", curses.color_pair(4))
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Filter for EPUB files only
    epub_files = [f for f in raw_files if get_file_extension(f) == "epub"]
    
    if not epub_files:
        stdscr.addstr(status_line, 0, "No EPUB files found in input directory.", curses.color_pair(3))
        stdscr.addstr(status_line + 1, 0, "Place EPUB files in the input directory and run again.")
        stdscr.addstr(status_line + 3, 0, "Press any key to exit...")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Display file count
    stdscr.addstr(status_line, 0, f"Found {len(epub_files)} EPUB file(s) to process", curses.color_pair(3) | curses.A_BOLD)
    status_line += 1
    stdscr.addstr(status_line, 0, "-" * min(max_x - 1, 80))
    status_line += 2
    
    # Reserve space for log output (last 10 lines)
    log_start_line = max_y - 11
    stdscr.addstr(log_start_line - 1, 0, "-" * min(max_x - 1, 80))
    stdscr.addstr(log_start_line, 0, "Conversion Log:", curses.A_BOLD)
    
    log_lines = []
    
    def add_log(message):
        """Add a message to the log display"""
        log_lines.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        # Keep only last 9 lines
        if len(log_lines) > 9:
            log_lines.pop(0)
        
        # Clear log area and redraw
        for i in range(9):
            stdscr.move(log_start_line + 1 + i, 0)
            stdscr.clrtoeol()
        
        for i, line in enumerate(log_lines):
            if i < 9:
                display_line = line[:max_x - 1]
                stdscr.addstr(log_start_line + 1 + i, 0, display_line)
        
        stdscr.refresh()
    
    # Process files
    total_files = len(epub_files)
    processed = 0
    successful = 0
    skipped = 0
    failed = 0
    
    for idx, f in enumerate(epub_files):
        final_file_name = get_final_filename(f)
        
        # Clear current file display area
        current_file_line = status_line
        stdscr.move(current_file_line, 0)
        stdscr.clrtoeol()
        stdscr.addstr(current_file_line, 0, f"Processing: {f}", curses.color_pair(3) | curses.A_BOLD)
        
        # Progress bar
        progress_line = current_file_line + 1
        progress = int((idx / total_files) * 50)
        stdscr.move(progress_line, 0)
        stdscr.clrtoeol()
        bar = "[" + "=" * progress + ">" + " " * (50 - progress) + "]"
        stdscr.addstr(progress_line, 0, f"Progress: {bar} {idx}/{total_files}", curses.A_BOLD)
        
        # Stats line
        stats_line = progress_line + 1
        stdscr.move(stats_line, 0)
        stdscr.clrtoeol()
        stdscr.addstr(stats_line, 0, f"Success: {successful} | Skipped: {skipped} | Failed: {failed}", curses.A_BOLD)
        
        stdscr.refresh()
        
        # Check if already converted
        if final_file_name in converted_files:
            add_log(f"Skipped (already exists): {final_file_name}")
            skipped += 1
            processed += 1
            continue
        
        # Convert the file
        add_log(f"Converting: {f}")
        try:
            result = subprocess.run(
                ["ebook-convert", join(INPUT_DIR, f), join(OUTPUT_DIR, final_file_name)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                add_log(f"✓ Success: {final_file_name}")
                successful += 1
            else:
                add_log(f"✗ Failed: {f} - {result.stderr[:50]}")
                failed += 1
                
        except subprocess.TimeoutExpired:
            add_log(f"✗ Timeout: {f}")
            failed += 1
        except Exception as e:
            add_log(f"✗ Error: {f} - {str(e)[:50]}")
            failed += 1
        
        processed += 1
    
    # Final progress bar
    progress_line = status_line + 1
    stdscr.move(progress_line, 0)
    stdscr.clrtoeol()
    bar = "[" + "=" * 50 + "]"
    stdscr.addstr(progress_line, 0, f"Progress: {bar} {total_files}/{total_files}", curses.color_pair(2) | curses.A_BOLD)
    
    # Final stats
    stats_line = progress_line + 1
    stdscr.move(stats_line, 0)
    stdscr.clrtoeol()
    stdscr.addstr(stats_line, 0, f"Success: {successful} | Skipped: {skipped} | Failed: {failed}", curses.color_pair(2) | curses.A_BOLD)
    
    # Completion message
    stdscr.move(stats_line + 2, 0)
    stdscr.clrtoeol()
    stdscr.addstr(stats_line + 2, 0, "Conversion complete! Press any key to exit...", curses.color_pair(2) | curses.A_BOLD)
    
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    try:
        # Setup directories first
        setup_directories()
        
        # Check for ebook-convert before starting
        if not check_ebook_convert():
            print("\nERROR: ebook-convert not found!")
            print("Please install Calibre: sudo pacman -S calibre")
            exit(1)
        
        # Ask user for source directory and copy files
        if not ask_for_source_and_copy():
            print("\nConversion cancelled.")
            exit(0)
        
        # Launch curses interface for conversion
        curses.wrapper(main)
        
    except KeyboardInterrupt:
        print("\nConversion cancelled by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

