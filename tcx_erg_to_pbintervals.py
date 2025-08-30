#!/usr/bin/env python3
"""
Convert Xert TCX + ERG workout files to PB Intervals CSV format
Uses TCX for interval names/structure and ERG for accurate power data
No heuristics - just shows the power progression for each interval
"""

import xml.etree.ElementTree as ET
import csv
import sys
import os
from datetime import timedelta
import argparse

def seconds_to_hhmmss(seconds):
    """Convert seconds to HH:MM:SS format"""
    td = timedelta(seconds=int(seconds))
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def parse_erg_file(erg_file):
    """Parse ERG file and extract power profile"""
    power_profile = []
    in_data_section = False
    
    with open(erg_file, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line == '[COURSE DATA]':
                in_data_section = True
                continue
            elif line == '[END COURSE DATA]':
                break
            elif in_data_section and line:
                parts = line.split('\t')
                if len(parts) == 2:
                    try:
                        minutes = float(parts[0])
                        watts = float(parts[1])
                        power_profile.append((minutes * 60, watts))  # Convert to seconds
                    except ValueError:
                        continue
    
    return power_profile

def get_power_at_time(power_profile, time_sec, use_end_value=False):
    """Get the power at a specific time, interpolating if necessary
    
    use_end_value: If True, get power AFTER a transition (for interval starts)
                   If False, get power BEFORE a transition (for interval ends)
    """
    # Check for exact matches first (handles duplicate timestamps)
    exact_matches = [(t, p) for t, p in power_profile if abs(t - time_sec) < 0.01]
    if exact_matches:
        if use_end_value:
            # For interval start, use the LAST value at this time (after transition)
            return exact_matches[-1][1]
        else:
            # For interval end, use the FIRST value at this time (before transition)
            return exact_matches[0][1]
    
    # No exact match, need to interpolate
    for i in range(len(power_profile) - 1):
        t1, p1 = power_profile[i]
        t2, p2 = power_profile[i + 1]
        
        if t1 < time_sec < t2:
            # Interpolate
            ratio = (time_sec - t1) / (t2 - t1)
            return p1 + ratio * (p2 - p1)
    
    # If we're past the end, return the last power
    if time_sec >= power_profile[-1][0]:
        return power_profile[-1][1]
    
    # If we're before the start, return the first power
    return power_profile[0][1]

def parse_tcx_workout(tcx_file):
    """Parse TCX file and extract workout steps"""
    tree = ET.parse(tcx_file)
    root = tree.getroot()
    
    # Handle namespace
    ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    
    # Find workout name
    workout_name = root.find('.//tcx:Workout/tcx:Name', ns)
    if workout_name is not None:
        workout_name = workout_name.text
    else:
        workout_name = "Imported Workout"
    
    # Find all steps
    steps = []
    for step in root.findall('.//tcx:Workout/tcx:Step', ns):
        step_data = {}
        
        # Get step name
        name_elem = step.find('tcx:Name', ns)
        if name_elem is not None:
            step_data['name'] = name_elem.text
        else:
            step_data['name'] = "Interval"
        
        # Get duration
        duration_elem = step.find('.//tcx:Seconds', ns)
        if duration_elem is not None:
            step_data['duration'] = int(duration_elem.text)
        else:
            step_data['duration'] = 60  # default 60 seconds
            
        steps.append(step_data)
    
    return workout_name, steps

def get_interval_color(power, ftp=277):
    """Get color based on power zone"""
    if power is None:
        return "#808080"  # Gray for unknown
    
    percentage = (power / ftp) * 100
    
    if percentage < 56:  # Recovery
        return "#00BFFF"  # Light blue
    elif percentage < 76:  # Endurance
        return "#00FF00"  # Green
    elif percentage < 90:  # Tempo
        return "#FFFF00"  # Yellow
    elif percentage < 105:  # Threshold
        return "#FFA500"  # Orange
    elif percentage < 120:  # VO2 Max
        return "#FF4500"  # Red-orange
    else:  # Neuromuscular
        return "#FF0000"  # Red

def create_pbintervals_csv(workout_name, steps, power_profile, output_file, ftp):
    """Create PB Intervals CSV file from workout steps with ERG power data"""
    
    # Add power data from ERG to each step
    current_time = 0
    for step in steps:
        start_sec = current_time
        end_sec = current_time + step['duration']
        
        # Get power at start and end of interval
        # For start, use power AFTER any transition at this time
        start_power = get_power_at_time(power_profile, start_sec, use_end_value=True)
        # For end, use power BEFORE any transition at this time
        end_power = get_power_at_time(power_profile, end_sec, use_end_value=False)
        
        step['start_power'] = int(round(start_power))
        step['end_power'] = int(round(end_power))
        
        # Calculate average for color and for display when it's steady
        step['avg_power'] = int(round((start_power + end_power) / 2))
        
        # Check if it's essentially steady (within 10%)
        if start_power > 0:
            change_percent = abs(end_power - start_power) / start_power * 100
            step['is_steady'] = change_percent < 10
        else:
            step['is_steady'] = True
        
        current_time = end_sec
    
    # Create CSV rows
    rows = []
    
    # Column headers exactly as exported from app (28 columns)
    fieldnames = [
        'TimerName', 'TimerColour', 'Alert', 'Vibration', 'IntervalShuffle',
        'ReactionSessionRound', 'ReactionSessionRoundHundredths',
        'ReactionIntervalDurationMin', 'ReactionIntervalDurationMinHundredths',
        'ReactionIntervalDurationMax', 'ReactionIntervalDurationMaxHundredths',
        'RestBetweenIntervalsMin', 'RestBetweenIntervalsMinHundredths',
        'RestBetweenIntervalsMax', 'RestBetweenIntervalsMaxHundredths',
        'NumberOfRounds', 'RestBetweenRoundsMin', 'RestBetweenRoundsMinHundredths',
        'RestBetweenRoundsMax', 'RestBetweenRoundsMaxHundredths',
        'CallName', 'CallColour', 'ReactionMaxNumberOfCalls',
        'CallDurationMin', 'CallDurationMinHundredths',
        'CallDurationMax', 'CallDurationMaxHundredths', 'HalfWayAlert'
    ]
    
    # Add interval rows
    for i, step in enumerate(steps):
        row = {}
        
        if i == 0:
            # First row includes timer settings
            row['TimerName'] = workout_name
            row['TimerColour'] = '#FFA500'  # Orange for workout
            row['Alert'] = 'Four Beeps (Default)'
            row['Vibration'] = 'One Vibration'
            row['IntervalShuffle'] = 'FALSE'
            row['NumberOfRounds'] = '1'
        else:
            # Subsequent rows have empty timer settings
            row['TimerName'] = ''
            row['TimerColour'] = ''
            row['Alert'] = ''
            row['Vibration'] = ''
            row['IntervalShuffle'] = ''
            row['NumberOfRounds'] = ''
        
        # Empty fields for all rows
        row['ReactionSessionRound'] = ''
        row['ReactionSessionRoundHundredths'] = ''
        row['ReactionIntervalDurationMin'] = ''
        row['ReactionIntervalDurationMinHundredths'] = ''
        row['ReactionIntervalDurationMax'] = ''
        row['ReactionIntervalDurationMaxHundredths'] = ''
        row['RestBetweenIntervalsMin'] = ''
        row['RestBetweenIntervalsMinHundredths'] = ''
        row['RestBetweenIntervalsMax'] = ''
        row['RestBetweenIntervalsMaxHundredths'] = ''
        row['RestBetweenRoundsMin'] = ''
        row['RestBetweenRoundsMinHundredths'] = ''
        row['RestBetweenRoundsMax'] = ''
        row['RestBetweenRoundsMaxHundredths'] = ''
        row['ReactionMaxNumberOfCalls'] = ''
        row['CallDurationMinHundredths'] = ''
        row['CallDurationMax'] = ''
        row['CallDurationMaxHundredths'] = ''
        
        # Interval-specific data with power info from ERG
        if step['is_steady']:
            # Show just the average if it's essentially steady
            row['CallName'] = f"{step['name']} [{step['avg_power']}W]"
        else:
            # Show the ramp with average
            row['CallName'] = f"{step['name']} [{step['start_power']}-{step['end_power']}W, avg:{step['avg_power']}W]"
        
        row['CallColour'] = get_interval_color(step['avg_power'], ftp)
        row['CallDurationMin'] = seconds_to_hhmmss(step['duration'])
        row['HalfWayAlert'] = 'FALSE'
        
        rows.append(row)
    
    # Write CSV file WITHOUT BOM, matching the app export
    with open(output_file, 'w', newline='', encoding='ascii') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        for row in rows:
            writer.writerow(row)
        
        # Add trailing newline like in the app export
        csvfile.write('\n')
    
    print(f"Created PB Intervals CSV: {output_file}")
    print(f"Total intervals: {len(steps)}")
    total_duration = sum(step['duration'] for step in steps)
    print(f"Total duration: {seconds_to_hhmmss(total_duration)}")

def load_ftp_from_env():
    """Load FTP from .env file if it exists"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == 'FTP':
                            try:
                                return int(value.strip())
                            except ValueError:
                                pass
    return None

def main():
    parser = argparse.ArgumentParser(description='Convert Xert TCX + ERG workout to PB Intervals CSV')
    parser.add_argument('tcx_file', help='Input TCX file')
    parser.add_argument('erg_file', help='Input ERG file')
    parser.add_argument('-o', '--output', help='Output CSV file', default=None)
    parser.add_argument('-f', '--ftp', type=int, help='Override FTP value from .env file', default=None)
    
    args = parser.parse_args()
    
    # Get FTP from .env or command line
    ftp = args.ftp
    if ftp is None:
        ftp = load_ftp_from_env()
    
    if ftp is None:
        print("Error: FTP value is required. Either:", file=sys.stderr)
        print("  1. Create a .env file with FTP=YOUR_VALUE", file=sys.stderr)
        print("  2. Use the -f flag to specify FTP", file=sys.stderr)
        sys.exit(1)
    
    # Set output filename if not specified
    if args.output is None:
        args.output = args.tcx_file.replace('.tcx', '_pbintervals.csv')
    
    try:
        # Parse TCX file for structure
        workout_name, steps = parse_tcx_workout(args.tcx_file)
        
        # Parse ERG file for power data
        power_profile = parse_erg_file(args.erg_file)
        
        if not power_profile:
            print("Error: No power data found in ERG file", file=sys.stderr)
            sys.exit(1)
        
        # Create PB Intervals CSV
        create_pbintervals_csv(workout_name, steps, power_profile, args.output, ftp)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()