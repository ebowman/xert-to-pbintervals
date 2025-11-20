#!/usr/bin/env python3
"""Verify that the fixed CSV matches the ZWO file structure"""

import xml.etree.ElementTree as ET
import csv

# Parse ZWO to get expected intervals
zwo_file = "/Users/ebowman/Downloads/XMB Workout CL8 - Xert.zwo"
tree = ET.parse(zwo_file)
root = tree.getroot()
ftp = int(root.find('ftpOverride').text)

zwo_intervals = []
for i, interval in enumerate(root.findall('.//workout/*'), 1):
    duration = int(interval.get('Duration'))
    power = float(interval.get('Power'))
    power_watts = int(round(power * ftp))
    interval_type = interval.tag

    zwo_intervals.append({
        'step': i,
        'type': interval_type,
        'duration': duration,
        'power': power_watts,
        'power_pct': power * 100
    })

# Parse the FIXED CSV
csv_file = "/Users/ebowman/Downloads/XMB Workout CL8 - Xert-FIXED.csv"
csv_intervals = []

with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['CallDurationMin']:
            # Extract power from CallName (e.g., "Interval [388W]")
            call_name = row['CallName']
            # Extract wattage between brackets
            if '[' in call_name and 'W]' in call_name:
                power_str = call_name[call_name.index('[')+1:call_name.index('W]')]
                # Check if it's a ramp (contains '-')
                if '-' in power_str:
                    is_ramp = True
                    power = power_str
                else:
                    is_ramp = False
                    power = int(power_str)

                # Parse duration HH:MM:SS
                time_parts = row['CallDurationMin'].split(':')
                duration = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])

                csv_intervals.append({
                    'name': call_name,
                    'power': power,
                    'duration': duration,
                    'is_ramp': is_ramp
                })

# Compare
print("=" * 100)
print("VERIFICATION: ZWO vs FIXED CSV")
print("=" * 100)
print()

print(f"{'Step':<6} {'ZWO Power':<15} {'ZWO Duration':<15} {'CSV Power':<15} {'CSV Duration':<15} {'Match'}")
print("-" * 100)

all_match = True
for i, (zwo, csv_int) in enumerate(zip(zwo_intervals, csv_intervals), 1):
    zwo_dur = f"{zwo['duration']//60}:{zwo['duration']%60:02d}"
    csv_dur = f"{csv_int['duration']//60}:{csv_int['duration']%60:02d}"

    # Check if powers match (within ±2W tolerance for rounding)
    if csv_int['is_ramp']:
        power_match = "❌ RAMP!"
        all_match = False
    elif abs(csv_int['power'] - zwo['power']) <= 2:
        power_match = "✓"
    else:
        power_match = f"❌ ({csv_int['power']} vs {zwo['power']})"
        all_match = False

    # Check duration match
    if zwo['duration'] == csv_int['duration']:
        duration_match = "✓"
    else:
        duration_match = f"❌ ({csv_dur} vs {zwo_dur})"
        all_match = False

    match_str = power_match if power_match == "✓" and duration_match == "✓" else f"{power_match} {duration_match}"

    print(f"{i:<6} {zwo['power']:>5}W ({zwo['power_pct']:>5.1f}%)  {zwo_dur:<15} "
          f"{str(csv_int['power']):>7}W      {csv_dur:<15} {match_str}")

print()
print("=" * 100)
if all_match:
    print("✅ SUCCESS! All intervals match between ZWO and CSV")
    print("   - No false ramps detected")
    print("   - All power values match")
    print("   - All durations match")
else:
    print("❌ ISSUES FOUND - See differences above")

print("=" * 100)
