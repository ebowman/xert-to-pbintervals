# Xert to PB Intervals Converter

**For XERT users without smart trainers who want structured workouts on Peloton or any indoor bike**

Convert Xert Online cycling workouts to PB Intervals app format - the solution for programming your phone to guide you through XERT workouts without an ERG/smart trainer or Zwift.

## Why This Exists

You're an XERT user who wants to:
- Do structured XERT workouts on a Peloton, spin bike, or basic indoor trainer
- Have your phone guide you through intervals without a smart trainer
- Avoid the cost and complexity of ERG trainers and Zwift setups
- Use the workout programming you already have in XERT

**Solution**: Export your XERT workout → Convert with this tool → Import to PB Intervals app (paid iOS app, not affiliated) → Follow along on any bike!

## Quick Start

1. Create a `.env` file with your FTP:
```bash
echo "FTP=304" > .env
```

2. Export your workout from Xert Online in **both TCX and ERG formats**

3. Run the converter:
```bash
python3 tcx_erg_to_pbintervals.py "workout.tcx" "workout.erg" -o output.csv
```

4. Import the CSV into [PB Intervals](https://apps.apple.com/app/pb-intervals/id1582351337) app on your iPhone (paid app with CSV import feature)

## Requirements

- Python 3.6+
- No external dependencies (uses only Python standard library)
- PB Intervals app (paid iOS app with CSV import capability)
- XERT Online account to export workouts

## Usage

```bash
python3 tcx_erg_to_pbintervals.py TCX_FILE ERG_FILE [options]

Arguments:
  TCX_FILE    The .tcx file exported from Xert Online
  ERG_FILE    The .erg file exported from Xert Online
  
Options:
  -o OUTPUT   Output CSV filename (default: workout_pbintervals.csv)
  -f FTP      Override FTP from .env file (optional)
```

### FTP Configuration

The script requires your FTP (Functional Threshold Power) to determine power zone colors. You can provide it in two ways:

1. **Recommended: Create a `.env` file** (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env and set your FTP value
```

2. **Or override with -f flag**:
```bash
python3 tcx_erg_to_pbintervals.py "workout.tcx" "workout.erg" -f 304
```

The `-f` flag always takes precedence over the `.env` file value.

### Examples

```bash
# Using FTP from .env file
python3 tcx_erg_to_pbintervals.py "VIRTUAL - Ellis.tcx" "VIRTUAL - Ellis.erg" -o ellis.csv

# Override FTP for this workout
python3 tcx_erg_to_pbintervals.py "VIRTUAL - Ellis.tcx" "VIRTUAL - Ellis.erg" -o ellis.csv -f 320
```

## Automated Workflow (macOS)

For macOS users, `workflow.py` provides a streamlined workflow:

1. Export your workout from XERT Online (both .tcx and .erg files) to ~/Downloads
2. Run the workflow script:
```bash
python3 workflow.py
```

The script will:
- Automatically find the most recent matching TCX/ERG pair in ~/Downloads
- Convert them to PB Intervals format
- Open the macOS Share sheet for easy AirDrop to your iPhone
- Copy the file path to clipboard

This eliminates the need to manually specify filenames and makes it easy to quickly convert and transfer workouts to your phone.

## How It Works

The converter combines data from two Xert export formats:

- **TCX file**: Provides interval names and durations
- **ERG file**: Provides accurate power targets throughout the workout

For each interval, the script:
1. Extracts the power at the start and end from the ERG data
2. If power changes <10%, shows a single value (e.g., `[323W]`)
3. If power changes >10%, shows the ramp (e.g., `[82-205W, avg:144W]`)
4. Colors intervals based on power zones relative to your FTP

## Power Zone Colors

- 🔵 Blue: Recovery (<56% FTP)
- 🟢 Green: Endurance (56-76% FTP)
- 🟡 Yellow: Tempo (76-90% FTP)
- 🟠 Orange: Threshold (90-105% FTP)
- 🔴 Red-orange: VO2 Max (105-120% FTP)
- 🔴 Red: Neuromuscular (>120% FTP)

## Development Journey

### The Challenge

Xert Online exports workouts in multiple formats, but none directly compatible with PB Intervals. We needed to:
1. Understand PB Intervals' CSV format requirements
2. Extract meaningful power data from Xert exports
3. Handle the complexity of ramps vs steady-state intervals

### What We Learned

1. **TCX vs ERG vs ZWO formats**:
   - TCX has interval structure but simplified power zones
   - ERG has precise power profiles but no interval names
   - ZWO has power as % of FTP but lacks interval names
   - Solution: Combine TCX structure with ERG power data

2. **The ERG timing challenge**:
   - ERG files have instant power transitions at time boundaries
   - Duplicate timestamps mark transitions (e.g., two entries at 13:00)
   - We handle this by taking power BEFORE transitions for interval ends and AFTER for starts

3. **PB Intervals CSV requirements**:
   - Exactly 28 columns (not 30 as PDF suggested)
   - No UTF-8 BOM, ASCII encoding
   - Unix line endings with trailing newline
   - First row contains both timer settings AND first interval

4. **Power representation**:
   - Users need to know target power for Peloton workouts
   - Ramps show start→end with average for reference
   - Steady intervals (±10%) show single value for clarity
   - No name-based heuristics - data drives everything

### Design Decisions

- **No heuristics**: We don't guess based on interval names like "Warmup"
- **10% threshold**: Changes under 10% are treated as steady-state
- **Always show data**: Every interval shows its actual power progression
- **Keep it simple**: Single Python file, no dependencies

## Troubleshooting

**"File not found" error**: Make sure both TCX and ERG files are in the current directory or provide full paths.

**Wrong power values**: Ensure you're using the ERG file from the same export as the TCX file.

**Import crashes PB Intervals**: The app requires a specific workflow:
1. Open PB Intervals
2. Create a new workout
3. Choose "Import from CSV"
4. Select your file

## Keywords / Search Terms

For those searching: XERT to Peloton, XERT workout on indoor bike, XERT without smart trainer, XERT without ERG, cycling workout programming without Zwift, structured cycling workouts on spin bike, XERT to CSV, PB Intervals import, indoor cycling workout apps, Peloton alternative workouts, power-based training without smart trainer, FTP-based interval training on basic bike.

## License

MIT

## Author

Created with assistance from Claude to solve a specific workout import challenge for XERT users without smart trainers.