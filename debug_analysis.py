#!/usr/bin/env python3
"""Debug script to analyze the timing and power mismatches"""

import xml.etree.ElementTree as ET

# Parse ZWO
zwo_file = "/Users/ebowman/Downloads/XMB Workout CL8 - Xert.zwo"
tree = ET.parse(zwo_file)
root = tree.getroot()

print("=" * 80)
print("ZWO FILE ANALYSIS (Source of Truth)")
print("=" * 80)
print(f"FTP: {root.find('ftpOverride').text}W")
print()

current_time = 0
for i, interval in enumerate(root.findall('.//workout/*'), 1):
    duration = int(interval.get('Duration'))
    power = float(interval.get('Power'))
    power_watts = power * 271  # FTP from ZWO
    interval_type = interval.tag

    print(f"Step {i}: {interval_type}")
    print(f"  Duration: {duration}s ({duration//60}:{duration%60:02d})")
    print(f"  Power: {power:.4f} ({power*100:.2f}% FTP) = {power_watts:.1f}W")
    print(f"  Time range: {current_time}s - {current_time + duration}s")
    print()

    current_time += duration

print()
print("=" * 80)
print("ERG FILE ANALYSIS")
print("=" * 80)

erg_file = "/Users/ebowman/Downloads/XMB Workout CL8 - Xert.erg"
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
                    power_profile.append((minutes * 60, watts))
                except ValueError:
                    continue

print("Power changes in ERG file:")
for i, (time_sec, watts) in enumerate(power_profile):
    print(f"  {time_sec:7.1f}s ({time_sec/60:6.2f}min): {watts:6.1f}W")

print()
print("=" * 80)
print("TCX FILE ANALYSIS")
print("=" * 80)

tcx_file = "/Users/ebowman/Downloads/XMB Workout CL8 - Xert.tcx"
tree = ET.parse(tcx_file)
root = tree.getroot()

ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
      'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

steps = []
for step in root.findall('.//tcx:Workout/tcx:Step', ns):
    name_elem = step.find('tcx:Name', ns)
    name = name_elem.text if name_elem is not None else "Interval"

    duration_elem = step.find('.//tcx:Seconds', ns)
    duration = int(duration_elem.text) if duration_elem is not None else 60

    steps.append((name, duration))

print("Steps from TCX:")
current_time = 0
for i, (name, duration) in enumerate(steps, 1):
    print(f"Step {i}: {name}")
    print(f"  Duration: {duration}s")
    print(f"  Time range: {current_time}s - {current_time + duration}s")
    current_time += duration
    print()

print()
print("=" * 80)
print("TIMING COMPARISON: ZWO vs ERG")
print("=" * 80)

# Rebuild intervals from ZWO
zwo_intervals = []
current_time = 0
for interval in root.findall('.//workout/*'):
    duration = int(interval.get('Duration'))
    power = float(interval.get('Power'))
    power_watts = power * 271
    zwo_intervals.append({
        'start': current_time,
        'end': current_time + duration,
        'duration': duration,
        'power': power_watts
    })
    current_time += duration

# Compare with ERG transitions
print("\nExpected vs Actual transitions:")
print(f"{'ZWO Time':<15} {'ZWO Power':<15} {'ERG Time':<15} {'ERG Power':<15} {'Delta'}")
print("-" * 80)

erg_idx = 0
for i, interval in enumerate(zwo_intervals):
    # Find ERG transition closest to ZWO end time
    closest_erg = min(power_profile, key=lambda x: abs(x[0] - interval['end']))
    delta = closest_erg[0] - interval['end']

    print(f"{interval['end']:7.1f}s      {interval['power']:6.1f}W      "
          f"{closest_erg[0]:7.1f}s      {closest_erg[1]:6.1f}W      {delta:+6.1f}s")

print()
print("=" * 80)
print("ISSUE DIAGNOSIS")
print("=" * 80)
print("""
1. ZWO file shows ALL intervals as SteadyState (no ramps)
2. ERG file timings are slightly off from TCX timings (0.2-1s differences)
3. When the converter looks up power at TCX interval boundaries, it's interpolating
   between ERG points that don't align perfectly
4. This creates false "ramps" where there should be steady power

SOLUTION:
- Use a tolerance when looking up power values (e.g., ±2 seconds)
- Find the nearest ERG transition instead of interpolating
- Or better: parse the ZWO file directly since it has the correct structure
""")
