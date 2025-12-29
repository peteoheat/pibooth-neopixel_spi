#!/usr/bin/env python3
"""
neopixel_countdown_calibrate.py

Measures NeoPixel countdown timing and computes a suggested multiplier so:
    delay_per_pixel = (preview_delay / num_pixels) * multiplier

Outputs a JSONL log to /tmp/neopixel_countdown_log.jsonl and prints a recommended multiplier.
Optionally persists multiplier to ~/.config/neopixel_multiplier.json
"""

import time
import json
import argparse
from pathlib import Path

# Try to import your NeoPixel driver; adjust if your environment differs
try:
    import board
    import neopixel_spi
except Exception as e:
    raise SystemExit(f"Driver import failed: {e}\nRun this on the Pi where neopixel_spi and board are installed.")

# ------------------ CONFIGURATION (edit as needed) ------------------
SPI_OBJ = board.SPI()            # use board.SPI() as in your plugin
NUM_PIXELS = 24                  # actual number of pixels
BPP = 4                          # bytes per pixel (3 or 4)
BRIGHTNESS = 0.2
AUTO_WRITE = False               # True if pixel writes auto-show
PIXEL_ORDER = neopixel_spi.RGBW  # use neopixel_spi constant
BIT0 = 0b10000000

PREVIEW_DELAY = 5.0              # preview_delay from pibooth.cfg (seconds)
MEASURE_ALL_PIXELS = True        # if True, measure full countdown (NUM_PIXELS steps); else measure MEASURE_STEPS
MEASURE_STEPS = 16               # used if MEASURE_ALL_PIXELS is False
LOGFILE = Path("/tmp/neopixel_countdown_log.jsonl")
PERSIST_MULTIPLIER = True        # write computed multiplier to ~/.config/neopixel_multiplier.json
PERSIST_PATH = Path.home() / ".config" / "neopixel_multiplier.json"
# -------------------------------------------------------------------

def create_pixels(num_pixels, brightness):
    """Create a temporary NeoPixel_SPI instance for testing (match your plugin signature)."""
    return neopixel_spi.NeoPixel_SPI(SPI_OBJ, num_pixels, bpp=BPP,
                                    brightness=brightness, auto_write=AUTO_WRITE,
                                    pixel_order=PIXEL_ORDER, bit0=BIT0)

def measure_countdown(pixels, preview_delay, multiplier=1.0, steps=None, logfile=LOGFILE):
    """
    Run countdown once, log timestamps of each pixel update to logfile,
    and return list of timestamps for each step.
    """
    num = len(pixels)
    if steps is None:
        steps = num if MEASURE_ALL_PIXELS else min(MEASURE_STEPS, num)

    interval = (preview_delay / max(1.0, num)) * multiplier
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open("w") as f:
        # mark start
        f.write(json.dumps({"event": "start", "time": time.monotonic(), "num_pixels": num, "steps": steps}) + "\n")
        # set all pixels to red initially
        try:
            pixels.fill((255, 0, 0, 0))
            if not pixels.auto_write:
                pixels.show()
        except Exception:
            pass

        timestamps = []
        # For measurement we step 'steps' times from end->start as in your plugin
        for i in range(steps):
            idx = num - i - 1
            try:
                # set pixel off (or a distinct color) to record step
                pixels[idx] = (0, 0, 0, 255)
                if not pixels.auto_write:
                    pixels.show()
            except Exception:
                # if operations fail, still timestamp
                pass
            t = time.monotonic()
            timestamps.append(t)
            f.write(json.dumps({"step": i, "pixel_index": idx, "time": t}) + "\n")
            time.sleep(interval)

        f.write(json.dumps({"event": "end", "time": time.monotonic()}) + "\n")
    return timestamps

def analyze_timestamps(timestamps, preview_delay, num_pixels):
    """
    Compute observed average delta between consecutive step timestamps,
    expected per-pixel interval and suggested multiplier:
        expected_per_pixel = preview_delay / num_pixels
        suggested_multiplier = observed_avg_delta / expected_per_pixel
    Returns dict with analysis.
    """
    if len(timestamps) < 2:
        return {"error": "not enough timestamps", "count": len(timestamps)}
    deltas = [t2 - t1 for t1, t2 in zip(timestamps, timestamps[1:])]
    avg_delta = sum(deltas) / len(deltas)
    median_delta = sorted(deltas)[len(deltas)//2]
    expected_per_pixel = preview_delay / float(num_pixels)
    suggested_multiplier = avg_delta / expected_per_pixel if expected_per_pixel > 0 else None
    return {
        "observed_avg_delta": avg_delta,
        "observed_median_delta": median_delta,
        "expected_per_pixel": expected_per_pixel,
        "suggested_multiplier": suggested_multiplier,
        "steps_measured": len(timestamps),
    }

def persist_multiplier(multiplier, path=PERSIST_PATH):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"multiplier": float(multiplier), "timestamp": time.time()}
        path.write_text(json.dumps(data))
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Measure NeoPixel countdown and compute multiplier.")
    parser.add_argument("--preview-delay", type=float, default=PREVIEW_DELAY, help="preview_delay seconds")
    parser.add_argument("--pixels", type=int, default=NUM_PIXELS, help="number of pixels")
    parser.add_argument("--multiplier", type=float, default=1.0, help="initial multiplier used for measurement")
    parser.add_argument("--logfile", type=Path, default=LOGFILE, help="path to write timestamp log (jsonl)")
    parser.add_argument("--persist", action="store_true", default=PERSIST_MULTIPLIER, help="persist suggested multiplier to ~/.config")
    args = parser.parse_args()

    num_pixels = args.pixels
    preview_delay = args.preview_delay
    logfile = args.logfile

    print("Creating test NeoPixel instance...")
    pixels = create_pixels(num_pixels, BRIGHTNESS)

    print(f"Running measured countdown: preview_delay={preview_delay}s pixels={num_pixels} multiplier_used={args.multiplier}")
    timestamps = measure_countdown(pixels, preview_delay, multiplier=args.multiplier, steps=None, logfile=logfile)
    print(f"Timestamps logged to {logfile} ({len(timestamps)} steps)")

    analysis = analyze_timestamps(timestamps, preview_delay, num_pixels)
    print("\nAnalysis:")
    for k, v in analysis.items():
        print(f"  {k}: {v}")

    suggested = analysis.get("suggested_multiplier")
    if suggested is not None:
        print(f"\nSuggested multiplier to match preview_delay: {suggested:.4f}")
        if args.persist:
            ok = persist_multiplier(suggested)
            print(f"Persisted multiplier to {PERSIST_PATH}: {ok}")
    else:
        print("\nCould not compute suggested multiplier (check timestamps).")

if __name__ == "__main__":
    main()
