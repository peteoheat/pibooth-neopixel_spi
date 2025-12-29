__version__ = "3.2.1"

import time
import threading
import math
import random
import colorsys
import json
from pathlib import Path

import pibooth
import board
import neopixel_spi
from pibooth.utils import LOGGER

# --- Defaults ---
DEFAULT_PIXELS = 24
DEFAULT_BRIGHTNESS = 0.2
DEFAULT_BPP = 4
DEFAULT_BIT0 = 0b10000000
DEFAULT_ORDER = neopixel_spi.RGBW
DEFAULT_AUTO_WRITE = False
DEFAULT_ATTRACT_SPEED = 0.02
DEFAULT_PREVIEW_DELAY = 5.0
DEFAULT_PREVIEW_COUNTDOWN = True
DEFAULT_FLASH_COLOR = "255,255,255,0"
DEFAULT_ATTRACT_SEQUENCE = "rainbow||6"
DEFAULT_ATTRACT_DEFAULT_DURATION = 6.0

# Calibration defaults
DEFAULT_NEOPIXEL_MULTIPLIER = 1.75
DEFAULT_AUTO_CALIBRATE = True
DEFAULT_CALIBRATE_STEPS = 8
DEFAULT_MULTIPLIER_MIN = 0.5
DEFAULT_MULTIPLIER_MAX = 4.0

# Persistence path (same path used by the calibration script)
PERSIST_PATH = Path.home() / ".config" / "neopixel_multiplier.json"

# --- Module state ---
_pixels = None
_attract_thread = None
_attract_stop = threading.Event()
_attract_lock = threading.RLock()

# --- Parsing helpers for combined sequence field ---
def _parse_color_field(s):
    s = (s or "").strip()
    if not s:
        return None
    parts = [p.strip() for p in s.split(",") if p.strip()]
    try:
        vals = tuple(int(p) for p in parts)
        if len(vals) == 3:
            return (vals[0], vals[1], vals[2], 0)
        elif len(vals) >= 4:
            return (vals[0], vals[1], vals[2], vals[3])
    except Exception:
        return None
    return None

def _parse_attract_sequence(raw):
    seq = []
    if not raw:
        return seq
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        fields = [f.strip() for f in part.split("|")]
        while len(fields) < 3:
            fields.append("")
        name = fields[0]
        if not name:
            continue
        color = _parse_color_field(fields[1])
        duration = None
        try:
            if fields[2]:
                duration = float(fields[2])
        except Exception:
            duration = None
        seq.append((name, color, duration))
    return seq

def _parse_color(s, fallback=(255, 255, 255, 0)):
    if not s:
        return fallback
    parts = [p.strip() for p in s.split(",") if p.strip()]
    try:
        vals = tuple(int(p) for p in parts)
        if len(vals) == 3:
            return (vals[0], vals[1], vals[2], 0)
        elif len(vals) >= 4:
            return (vals[0], vals[1], vals[2], vals[3])
    except Exception:
        pass
    return fallback

# --- Basic wheel color ---
def wheel(pos, order=DEFAULT_ORDER):
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if order in (neopixel_spi.RGB, neopixel_spi.GRB) else (r, g, b, 0)

# --- Patterns implementations ---
def pattern_rainbow(step_delay, order=DEFAULT_ORDER):
    num = len(_pixels)
    for j in range(256):
        if _attract_stop.is_set():
            return
        for i in range(num):
            pixel_index = (i * 256 // num) + j
            _pixels[i] = wheel(pixel_index & 255, order)
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_color_wipe(step_delay, color=(255, 0, 0, 0)):
    num = len(_pixels)
    for i in range(num):
        if _attract_stop.is_set():
            return
        _pixels[i] = color
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_theater_chase(step_delay, color=(127, 127, 127, 0), iterations=10):
    num = len(_pixels)
    for it in range(iterations):
        if _attract_stop.is_set():
            return
        for q in range(3):
            for i in range(0, num, 3):
                _pixels[(i + q) % num] = color
            if not _pixels.auto_write:
                _pixels.show()
            time.sleep(step_delay)
            for i in range(0, num, 3):
                _pixels[(i + q) % num] = (0, 0, 0, 0)

def pattern_pulse(step_delay, color=(0, 0, 255, 0), steps=40):
    num = len(_pixels)
    for s in range(steps):
        if _attract_stop.is_set():
            return
        t = (1 + math.sin((s / float(steps)) * 2 * math.pi)) / 2
        rgb = tuple(min(255, int(c * t)) for c in color[:3])
        col = (rgb[0], rgb[1], rgb[2], color[3] if len(color) == 4 else 0)
        for i in range(num):
            _pixels[i] = col
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_comet(step_delay, color=(255, 255, 255, 0), tail=8):
    num = len(_pixels)
    for pos in range(num + tail):
        if _attract_stop.is_set():
            return
        for i in range(num):
            distance = pos - i
            if 0 <= distance < tail:
                brightness = max(0.0, 1 - (distance / float(tail)))
                col = tuple(min(255, int(c * brightness)) for c in color[:3]) + ((color[3],) if len(color) == 4 else (0,))
                _pixels[i] = col
            else:
                _pixels[i] = (0, 0, 0, 0)
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_sparkle(step_delay, color=(255, 255, 255, 0), chance=0.05, duration=1.0):
    num = len(_pixels)
    rounds = max(1, int(duration / max(0.001, step_delay)))
    for _ in range(rounds):
        if _attract_stop.is_set():
            return
        for i in range(num):
            if random.random() < chance:
                _pixels[i] = color
            else:
                _pixels[i] = (0, 0, 0, 0)
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_gradient(step_delay, color=(0, 128, 255, 0)):
    num = len(_pixels)
    for shift in range(0, 360, max(1, int(6 * max(0.001, step_delay)))):
        if _attract_stop.is_set():
            return
        for i in range(num):
            h = ((i / float(max(1, num))) * 0.6 + (shift / 360.0)) % 1.0
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(h, 0.8, 0.7)]
            _pixels[i] = (r, g, b, color[3] if len(color) == 4 else 0)
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_chase_multi(step_delay, colors=((255, 0, 0, 0), (0, 255, 0, 0), (0, 0, 255, 0)), spacing=2, reps=4):
    num = len(_pixels)
    palette = list(colors)
    pos = 0
    total = num * reps
    for _ in range(total):
        if _attract_stop.is_set():
            return
        for i in range(num):
            if ((i + pos) // spacing) % len(palette) == 0:
                _pixels[i] = palette[(i // spacing) % len(palette)]
            else:
                _pixels[i] = (0, 0, 0, 0)
        if not _pixels.auto_write:
            _pixels.show()
        pos = (pos + 1) % num
        time.sleep(step_delay)

def pattern_fire(step_delay, cooling=0.95, sparking=0.05):
    num = len(_pixels)
    heat = [0.0] * num
    while not _attract_stop.is_set():
        for i in range(num):
            heat[i] = max(0.0, heat[i] * cooling - random.random() * 0.02)
        if random.random() < sparking:
            idx = random.randint(0, num - 1)
            heat[idx] = min(1.0, heat[idx] + random.uniform(0.4, 0.9))
        for i in range(num):
            t = heat[i]
            if t <= 0:
                col = (0, 0, 0, 0)
            else:
                h = 0.02 + (0.02 * t)
                r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(h, min(1, t), min(1, 0.6 + t * 0.4))]
                col = (r, g, b, 0)
            _pixels[i] = col
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

def pattern_ocean(step_delay):
    num = len(_pixels)
    for shift in range(360):
        if _attract_stop.is_set():
            return
        for i in range(num):
            h = (0.55 + 0.05 * math.sin((i / float(max(1, num))) * 2 * math.pi + shift / 20.0)) % 1.0
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(h, 0.8, 0.6)]
            _pixels[i] = (r, g, b, 0)
        if not _pixels.auto_write:
            _pixels.show()
        time.sleep(step_delay)

# --- Attract orchestration using sequence entries ---
def _attract_loop(sequence, step_delay, default_duration=DEFAULT_ATTRACT_DEFAULT_DURATION):
    LOGGER.debug("neopixel: attract loop starting sequence=%s", sequence)
    mapping = {
        "rainbow": lambda c: pattern_rainbow(step_delay),
        "color_wipe": lambda c: pattern_color_wipe(step_delay, c or (255, 0, 0, 0)),
        "theater_chase": lambda c: pattern_theater_chase(step_delay, c or (127, 127, 127, 0), iterations=8),
        "pulse": lambda c: pattern_pulse(step_delay, c or (0, 0, 255, 0), steps=30),
        "comet": lambda c: pattern_comet(step_delay, c or (255, 255, 255, 0), tail=8),
        "sparkle": lambda c: pattern_sparkle(step_delay, c or (255, 255, 255, 0), chance=0.06, duration=1.5),
        "gradient": lambda c: pattern_gradient(step_delay, c or (0, 128, 255, 0)),
        "chase_multi": lambda c: pattern_chase_multi(step_delay, colors=(c or (255, 0, 0, 0), (0, 255, 0, 0), (0, 0, 255, 0)), spacing=2, reps=4),
        "fire": lambda c: pattern_fire(step_delay, cooling=0.96, sparking=0.04),
        "ocean": lambda c: pattern_ocean(step_delay),
    }

    idx = 0
    try:
        while not _attract_stop.is_set():
            if not sequence:
                mapping["rainbow"](None)
                time.sleep(default_duration)
                continue
            name, color, duration = sequence[idx % len(sequence)]
            fn = mapping.get(name)
            if fn is None:
                LOGGER.warning("neopixel: unknown pattern '%s', using rainbow", name)
                fn = mapping["rainbow"]
            dwell = duration if (duration is not None) else default_duration
            start = time.monotonic()
            try:
                while not _attract_stop.is_set() and (time.monotonic() - start) < dwell:
                    fn(color)
                    if (time.monotonic() - start) < dwell:
                        time.sleep(0.01)
            except Exception:
                LOGGER.exception("neopixel: pattern '%s' raised", name)
            idx += 1
    finally:
        LOGGER.debug("neopixel: attract loop exiting")

def _start_attract_from_sequence(seq, step_delay, default_duration=DEFAULT_ATTRACT_DEFAULT_DURATION):
    global _attract_thread
    with _attract_lock:
        if _attract_thread and _attract_thread.is_alive():
            return
        _attract_stop.clear()
        _attract_thread = threading.Thread(target=_attract_loop, args=(seq, step_delay, default_duration), daemon=True)
        _attract_thread.start()
        LOGGER.debug("neopixel: attract started with sequence length=%s", len(seq))

def _stop_attract(timeout=1.0):
    global _attract_thread
    with _attract_lock:
        if not _attract_thread:
            return
        _attract_stop.set()
        if _attract_thread.is_alive():
            _attract_thread.join(timeout=timeout)
        _attract_thread = None
        if _pixels is not None:
            try:
                _pixels.fill((0, 0, 0, 0))
                if not _pixels.auto_write:
                    _pixels.show()
            except Exception:
                LOGGER.exception("neopixel: failed to clear pixels on stop")

# --- Calibration helpers ---
def _measure_write_time(pixels, steps=DEFAULT_CALIBRATE_STEPS):
    try:
        num = len(pixels)
    except Exception:
        return 0.0
    saved = []
    try:
        for i in range(min(4, num)):
            try:
                saved.append(pixels[i])
            except Exception:
                saved.append(None)
    except Exception:
        saved = []

    start = time.monotonic()
    try:
        for s in range(max(1, steps)):
            for i in range(min(4, num)):
                try:
                    pixels[i] = (0, 0, 0, 0) if (s % 2 == 0) else (8, 8, 8, 0)
                except Exception:
                    pass
            if not pixels.auto_write:
                try:
                    pixels.show()
                except Exception:
                    pass
    finally:
        elapsed = time.monotonic() - start
        try:
            for i, v in enumerate(saved):
                if v is not None:
                    pixels[i] = v
            if not pixels.auto_write:
                pixels.show()
        except Exception:
            pass

    return elapsed / max(1, steps)

def _compute_multiplier_from_measurement(pixels, preview_delay, steps=DEFAULT_CALIBRATE_STEPS,
                                         min_mult=DEFAULT_MULTIPLIER_MIN, max_mult=DEFAULT_MULTIPLIER_MAX):
    try:
        num = len(pixels)
        if preview_delay <= 0 or num <= 0:
            return DEFAULT_NEOPIXEL_MULTIPLIER
    except Exception:
        return DEFAULT_NEOPIXEL_MULTIPLIER

    per_step = _measure_write_time(pixels, steps=steps)
    if per_step <= 0:
        return DEFAULT_NEOPIXEL_MULTIPLIER
    multiplier = (per_step * num) / max(1e-6, preview_delay)
    multiplier = max(min_mult, min(max_mult, multiplier))
    return multiplier

# --- Load persisted multiplier if present and valid ---
def _load_persisted_multiplier(path=PERSIST_PATH, min_mult=DEFAULT_MULTIPLIER_MIN, max_mult=DEFAULT_MULTIPLIER_MAX):
    try:
        if not path.exists():
            return None
        raw = path.read_text()
        data = json.loads(raw)
        mult = float(data.get("multiplier"))
        if not (min_mult <= mult <= max_mult):
            LOGGER.warning("neopixel: persisted multiplier %.3f out of bounds (%.3f..%.3f); ignoring", mult, min_mult, max_mult)
            return None
        LOGGER.info("neopixel: loaded persisted multiplier %.4f from %s", mult, str(path))
        return mult
    except Exception:
        LOGGER.exception("neopixel: failed to load persisted multiplier")
        return None

# --- Countdown --- 
def countdown(seconds, pixels, multiplier):
    try:
        num_pixels = len(pixels)
    except Exception:
        LOGGER.exception("neopixel: countdown failed to get pixel count")
        return

    raw = float(seconds) / max(1, num_pixels)
    delay = raw * max(0.0001, float(multiplier))
    try:
        pixels.fill((255, 0, 0, 0))
        if not pixels.auto_write:
            pixels.show()
        for i in range(num_pixels):
            pixels[num_pixels - i - 1] = (0, 0, 0, 255)
            if not pixels.auto_write:
                pixels.show()
            time.sleep(delay)
    except Exception:
        LOGGER.exception("neopixel: countdown error")

# --- pibooth.cfg registration ---
@pibooth.hookimpl
def pibooth_configure(cfg):
    cfg.add_option("NEOPIXEL", "pixels", DEFAULT_PIXELS, "Number of NeoPixels")
    cfg.add_option("NEOPIXEL", "brightness", DEFAULT_BRIGHTNESS, "Brightness 0.0-1.0")
    cfg.add_option("NEOPIXEL", "bpp", DEFAULT_BPP, "Bytes per pixel (3=RGB,4=RGBW)")
    cfg.add_option("NEOPIXEL", "bit0", DEFAULT_BIT0, "Bit0 timing value for SPI")
    cfg.add_option("NEOPIXEL", "pixel_order", "RGBW", "Pixel order name from neopixel_spi (RGB, GRB, RGBW, ...)")
    cfg.add_option("NEOPIXEL", "auto_write", DEFAULT_AUTO_WRITE, "Auto write on set (True/False)")
    cfg.add_option("NEOPIXEL", "attract_sequence", DEFAULT_ATTRACT_SEQUENCE, "Sequence: pattern|R,G,B[,W]|seconds;pattern2|...;...")
    cfg.add_option("NEOPIXEL", "attract_speed", DEFAULT_ATTRACT_SPEED, "Base attract pattern step delay (seconds)")
    cfg.add_option("NEOPIXEL", "attract_default_duration", DEFAULT_ATTRACT_DEFAULT_DURATION, "Default duration (s) for sequence entries that omit a duration")
    cfg.add_option("NEOPIXEL", "preview_delay", DEFAULT_PREVIEW_DELAY, "How long the preview state lasts (seconds)")
    cfg.add_option("NEOPIXEL", "preview_countdown", DEFAULT_PREVIEW_COUNTDOWN, "Show a countdown during preview (True/False)")
    cfg.add_option("NEOPIXEL", "flash_color", DEFAULT_FLASH_COLOR, "Flash color as CSV R,G,B[,W]")

    # Calibration options
    cfg.add_option("NEOPIXEL", "neopixel_multiplier", DEFAULT_NEOPIXEL_MULTIPLIER, "Manual multiplier to tune pixel countdown timing")
    cfg.add_option("NEOPIXEL", "neopixel_auto_calibrate", DEFAULT_AUTO_CALIBRATE, "Auto-calibrate multiplier at startup (True/False)")
    cfg.add_option("NEOPIXEL", "neopixel_calibrate_steps", DEFAULT_CALIBRATE_STEPS, "Number of cycles for calibration measurement")
    cfg.add_option("NEOPIXEL", "neopixel_multiplier_min", DEFAULT_MULTIPLIER_MIN, "Minimum allowed multiplier")
    cfg.add_option("NEOPIXEL", "neopixel_multiplier_max", DEFAULT_MULTIPLIER_MAX, "Maximum allowed multiplier")

# --- Startup: initialize hardware, calibrate multiplier (optional), and start attract --- 
@pibooth.hookimpl
def pibooth_startup(cfg, app):
    global _pixels
    try:
        px = int(cfg.get("NEOPIXEL", "pixels", fallback=DEFAULT_PIXELS))
        brightness = float(cfg.get("NEOPIXEL", "brightness", fallback=DEFAULT_BRIGHTNESS))
        bpp = int(cfg.get("NEOPIXEL", "bpp", fallback=DEFAULT_BPP))
        bit0 = int(cfg.get("NEOPIXEL", "bit0", fallback=DEFAULT_BIT0))
        po_raw = cfg.get("NEOPIXEL", "pixel_order", fallback="RGBW").strip()
        try:
            pixel_order = getattr(neopixel_spi, po_raw)
        except Exception:
            pixel_order = DEFAULT_ORDER
        auto_write = cfg.get("NEOPIXEL", "auto_write", fallback=str(DEFAULT_AUTO_WRITE)).lower() in ("1", "true", "yes")
        attract_sequence_raw = cfg.get("NEOPIXEL", "attract_sequence", fallback=DEFAULT_ATTRACT_SEQUENCE)
        attract_speed = float(cfg.get("NEOPIXEL", "attract_speed", fallback=DEFAULT_ATTRACT_SPEED))
        attract_default_duration = float(cfg.get("NEOPIXEL", "attract_default_duration", fallback=DEFAULT_ATTRACT_DEFAULT_DURATION))
        preview_delay = float(cfg.get("NEOPIXEL", "preview_delay", fallback=DEFAULT_PREVIEW_DELAY))
        preview_countdown = cfg.get("NEOPIXEL", "preview_countdown", fallback=str(DEFAULT_PREVIEW_COUNTDOWN)).lower() in ("1", "true", "yes")
        flash_color = _parse_color(cfg.get("NEOPIXEL", "flash_color", fallback=DEFAULT_FLASH_COLOR))

        # calibration settings
        cfg_multiplier = float(cfg.get("NEOPIXEL", "neopixel_multiplier", fallback=DEFAULT_NEOPIXEL_MULTIPLIER))
        auto_calibrate = cfg.get("NEOPIXEL", "neopixel_auto_calibrate", fallback=str(DEFAULT_AUTO_CALIBRATE)).lower() in ("1", "true", "yes")
        calibrate_steps = int(cfg.get("NEOPIXEL", "neopixel_calibrate_steps", fallback=DEFAULT_CALIBRATE_STEPS))
        mult_min = float(cfg.get("NEOPIXEL", "neopixel_multiplier_min", fallback=DEFAULT_MULTIPLIER_MIN))
        mult_max = float(cfg.get("NEOPIXEL", "neopixel_multiplier_max", fallback=DEFAULT_MULTIPLIER_MAX))
    except Exception:
        LOGGER.exception("neopixel: config parse error; using defaults")
        px = DEFAULT_PIXELS
        brightness = DEFAULT_BRIGHTNESS
        bpp = DEFAULT_BPP
        bit0 = DEFAULT_BIT0
        pixel_order = DEFAULT_ORDER
        auto_write = DEFAULT_AUTO_WRITE
        attract_sequence_raw = DEFAULT_ATTRACT_SEQUENCE
        attract_speed = DEFAULT_ATTRACT_SPEED
        attract_default_duration = DEFAULT_ATTRACT_DEFAULT_DURATION
        preview_delay = DEFAULT_PREVIEW_DELAY
        preview_countdown = DEFAULT_PREVIEW_COUNTDOWN
        flash_color = _parse_color(DEFAULT_FLASH_COLOR)
        cfg_multiplier = DEFAULT_NEOPIXEL_MULTIPLIER
        auto_calibrate = DEFAULT_AUTO_CALIBRATE
        calibrate_steps = DEFAULT_CALIBRATE_STEPS
        mult_min = DEFAULT_MULTIPLIER_MIN
        mult_max = DEFAULT_MULTIPLIER_MAX

    LOGGER.info("neopixel: initializing NeoPixel_SPI n=%s brightness=%.2f", px, brightness)
    try:
        spi = board.SPI()
        _pixels = neopixel_spi.NeoPixel_SPI(spi, px, bpp=bpp, brightness=brightness,
                                           auto_write=auto_write, pixel_order=pixel_order, bit0=bit0)
        app.pixels = _pixels

        seq = _parse_attract_sequence(attract_sequence_raw)

        # load persisted multiplier if present
        persisted = _load_persisted_multiplier(PERSIST_PATH, min_mult=mult_min, max_mult=mult_max)

        # compute multiplier: prefer persisted, else auto-calibrate if enabled, else cfg_multiplier
        computed_multiplier = cfg_multiplier
        if persisted is not None:
            computed_multiplier = persisted
        else:
            if auto_calibrate:
                try:
                    measured_mult = _compute_multiplier_from_measurement(_pixels, preview_delay,
                                                                         steps=max(1, calibrate_steps),
                                                                         min_mult=mult_min, max_mult=mult_max)
                    if measured_mult is not None:
                        computed_multiplier = measured_mult
                        LOGGER.info("neopixel: auto-calibrated multiplier=%.3f", computed_multiplier)
                except Exception:
                    LOGGER.exception("neopixel: auto-calibration failed; using configured multiplier")
                    computed_multiplier = cfg_multiplier

        app._neopixel_cfg = {
            "attract_sequence": seq,
            "attract_speed": attract_speed,
            "attract_default_duration": attract_default_duration,
            "preview_delay": preview_delay,
            "preview_countdown": preview_countdown,
            "flash_color": flash_color,
            "neopixel_multiplier": computed_multiplier,
        }

        _start_attract_from_sequence(seq, attract_speed, default_duration=attract_default_duration)
    except Exception:
        LOGGER.exception("neopixel: failed to initialize NeoPixel_SPI")

# --- State hooks --- 
@pibooth.hookimpl
def state_wait_enter(app):
    LOGGER.debug("neopixel: state_wait_enter")
    cfg = getattr(app, "_neopixel_cfg", {})
    seq = cfg.get("attract_sequence", [])
    speed = cfg.get("attract_speed", DEFAULT_ATTRACT_SPEED)
    default_duration = cfg.get("attract_default_duration", DEFAULT_ATTRACT_DEFAULT_DURATION)
    _start_attract_from_sequence(seq, speed, default_duration=default_duration)

def state_wait_do(app):
    pass

@pibooth.hookimpl
def state_wait_exit(app):
    LOGGER.debug("neopixel: state_wait_exit")
    _stop_attract()

@pibooth.hookimpl
def state_choose_enter(app):
    LOGGER.debug("neopixel: state_choose_enter")
    try:
        app.pixels.fill((255, 0, 0, 0))
        if not app.pixels.auto_write:
            app.pixels.show()
    except Exception:
        LOGGER.exception("neopixel: state_choose_enter failed")

@pibooth.hookimpl
def state_preview_enter(app):
    LOGGER.debug("neopixel: state_preview_enter")
    try:
        app.pixels.fill((0, 255, 0, 0))
        if not app.pixels.auto_write:
            app.pixels.show()

        cfg = getattr(app, "_neopixel_cfg", {})
        preview_delay = cfg.get("preview_delay", DEFAULT_PREVIEW_DELAY)
        preview_countdown = cfg.get("preview_countdown", DEFAULT_PREVIEW_COUNTDOWN)
        multiplier = cfg.get("neopixel_multiplier", DEFAULT_NEOPIXEL_MULTIPLIER)

        if preview_countdown:
            proc = threading.Thread(target=countdown, args=(preview_delay, app.pixels, multiplier), daemon=True)
            proc.start()
            app.neopixels_proc = proc
    except Exception:
        LOGGER.exception("neopixel: state_preview_enter failed")

@pibooth.hookimpl
def state_preview_exit(app):
    LOGGER.debug("neopixel: state_preview_exit")
    try:
        cfg = getattr(app, "_neopixel_cfg", {})
        flash_color = cfg.get("flash_color", _parse_color(DEFAULT_FLASH_COLOR))
        try:
            app.pixels.fill(flash_color)
            if not app.pixels.auto_write:
                app.pixels.show()
            time.sleep(0.12)
        finally:
            app.pixels.fill((255, 255, 255, 255))
            if not app.pixels.auto_write:
                app.pixels.show()
    except Exception:
        LOGGER.exception("neopixel: state_preview_exit failed")

@pibooth.hookimpl
def state_capture_exit(app):
    LOGGER.debug("neopixel: state_capture_exit")
    try:
        app.pixels.fill((0, 0, 0, 0))
        if not app.pixels.auto_write:
            app.pixels.show()
    except Exception:
        LOGGER.exception("neopixel: state_capture_exit failed")

@pibooth.hookimpl
def pibooth_cleanup(app):
    LOGGER.debug("neopixel: pibooth_cleanup")
    _stop_attract()
    try:
        if _pixels is not None:
            _pixels.fill((0, 0, 0, 0))
            if not _pixels.auto_write:
                _pixels.show()
    except Exception:
        LOGGER.exception("neopixel: cleanup failed")
