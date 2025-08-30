#!/usr/bin/env python3
"""
Wrapper to automatically convert the most recent Xert workout from ~/Downloads
Finds matching .tcx and .erg files, converts them, and opens Share sheet for AirDrop
"""

import os
import sys
import subprocess
from pathlib import Path
import glob
from datetime import datetime

def find_matching_workout_files():
    """Find the most recent pair of .tcx and .erg files with the same base name"""
    downloads = Path.home() / "Downloads"
    
    # Find all TCX and ERG files
    tcx_files = list(downloads.glob("*.tcx"))
    erg_files = list(downloads.glob("*.erg"))
    
    if not tcx_files:
        print("No .tcx files found in ~/Downloads")
        return None, None
    if not erg_files:
        print("No .erg files found in ~/Downloads")
        return None, None
    
    # Find matching pairs (same base name)
    matching_pairs = []
    for tcx in tcx_files:
        tcx_base = tcx.stem  # filename without extension
        for erg in erg_files:
            if erg.stem == tcx_base:
                # Get the most recent modification time between the two
                latest_mtime = max(tcx.stat().st_mtime, erg.stat().st_mtime)
                matching_pairs.append((tcx, erg, latest_mtime))
                break
    
    if not matching_pairs:
        print("No matching .tcx/.erg file pairs found in ~/Downloads")
        print(f"TCX files: {[f.name for f in tcx_files[:5]]}")
        print(f"ERG files: {[f.name for f in erg_files[:5]]}")
        return None, None
    
    # Sort by modification time and get the most recent
    matching_pairs.sort(key=lambda x: x[2], reverse=True)
    most_recent = matching_pairs[0]
    
    return most_recent[0], most_recent[1]

def run_converter(tcx_file, erg_file):
    """Run the converter script"""
    # Output filename in the same directory as the source files
    output_file = tcx_file.parent / f"{tcx_file.stem}.csv"
    
    # Get the script directory
    script_dir = Path(__file__).parent
    converter_script = script_dir / "tcx_erg_to_pbintervals.py"
    
    # Run the converter
    cmd = [
        sys.executable,
        str(converter_script),
        str(tcx_file),
        str(erg_file),
        "-o", str(output_file)
    ]
    
    print(f"Converting: {tcx_file.name} + {erg_file.name}")
    print(f"Output: {output_file.name}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error running converter: {e}")
        print(f"stderr: {e.stderr}")
        return None

def open_share_sheet(file_path):
    """Open macOS Share sheet for the file (for AirDrop)"""
    # First, try to use the AppleScript to open Share menu
    script_dir = Path(__file__).parent
    applescript_file = script_dir / "share_file.applescript"
    
    if applescript_file.exists():
        try:
            subprocess.run(["osascript", str(applescript_file), str(file_path)], 
                         capture_output=True, check=False)
        except:
            pass
    
    # Always reveal in Finder as fallback
    subprocess.run(["open", "-R", str(file_path)])
    
    print(f"\nFile revealed in Finder: {file_path.name}")
    print("Right-click the file and select 'Share' > 'AirDrop' to send to your iPhone")
    
    # Also copy the path to clipboard for convenience
    subprocess.run(["pbcopy"], input=str(file_path), text=True)
    print(f"File path copied to clipboard")

def main():
    """Main workflow"""
    print("Xert to PB Intervals Converter - Auto Wrapper")
    print("=" * 50)
    
    # Find the most recent matching workout files
    tcx_file, erg_file = find_matching_workout_files()
    
    if not tcx_file or not erg_file:
        print("\nMake sure you've exported both .tcx and .erg files from Xert Online")
        print("They should have the same filename (e.g., 'VIRTUAL - Ellis.tcx' and 'VIRTUAL - Ellis.erg')")
        sys.exit(1)
    
    print(f"\nFound matching workout files:")
    print(f"  TCX: {tcx_file.name}")
    print(f"  ERG: {erg_file.name}")
    print(f"  Modified: {datetime.fromtimestamp(tcx_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the converter
    output_file = run_converter(tcx_file, erg_file)
    
    if output_file and output_file.exists():
        print(f"\n✓ Conversion successful!")
        
        # Open Share sheet for AirDrop
        open_share_sheet(output_file)
    else:
        print("\n✗ Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()