# Bug Analysis: False Ramps in CSV Output

## Problem Summary
The converted CSV file shows false "ramps" (e.g., `[388-166W]`) when all intervals should be steady power according to the ZWO file (all `<SteadyState>` elements).

## Root Causes

### 1. Timing Misalignment
The ERG file has transitions that occur slightly before TCX interval boundaries:
- **TCX says**: Interval 2 ends at `659s`
- **ERG shows**: Transition happens at `658.8s`
- **Difference**: `0.2s` mismatch

### 2. Interpolation Bug
When `get_power_at_time()` looks for power at `659s`:
1. No exact match found (closest is `658.8s`)
2. The ERG has duplicate timestamps at transition points:
   ```
   658.8s: 387.8W  (before transition)
   658.8s: 166.0W  (after transition)
   910.2s: 166.0W
   ```
3. The interpolation loop skips the first `658.8s` entry and interpolates between:
   - `(658.8s, 166.0W)` ← wrong value (post-transition)
   - `(910.2s, 166.0W)`
4. Result: Gets `166W` instead of `388W`

### 3. Example Walkthrough

**Expected (from ZWO):**
- Step 2: 59s @ 388W (steady)
- Step 3: 251s @ 166W (steady)
- Step 4: 59s @ 388W (steady)

**Actual CSV output:**
- `Interval [388-166W]` ← FALSE RAMP
- `Interval [166W]` ✓
- `Interval [166-388W]` ← FALSE RAMP

## Solution

Modify `get_power_at_time()` to:
1. Use a tolerance window (±2 seconds) when looking for "exact" matches
2. When near a transition, select the appropriate value based on `use_end_value`
3. Avoid interpolating across transitions by finding the nearest stable power value

## Test Case
Using `XMB Workout CL8 - Xert` files:
- All 7 high-power intervals should show as `[388W]` (steady)
- All rest intervals should show as steady values
- NO ramps should appear in the output
