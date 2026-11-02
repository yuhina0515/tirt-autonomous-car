"""Stateless assumed vehicle/track/sensor model; no controller, I/O or pass criteria."""
from dataclasses import dataclass, asdict
import math
import random

@dataclass
class Plant:
    # All values are assumptions, not measured CAGEBOT specifications.
    track_m: float = 0.115
    sensor_ahead_m: float = 0.060
    sensor_spacing_m: float = 0.014
    sensor_radius_m: float = 0.002
    line_width_m: float = 0.020
    road_width_m: float = 0.200
    max_wheel_mps: float = 0.65
    dead_pwm: float = 40
    motor_tau_s: float = 0.080
    coast_tau_s: float = 0.240
    max_accel_mps2: float = 2.5
    left_gain: float = 1.0
    right_gain: float = 0.97
    battery_factor: float = 1.0
    friction_mu: float = 0.55
    sample_ms: int = 5
    latency_ms: int = 5
    adc_noise: float = 4
    line_adc: float = 35
    background_adc: float = 500
    grade_deg: float = 0

    def __post_init__(self):
        for name,value in asdict(self).items():
            if not math.isfinite(value):raise ValueError(name+' must be finite')
        for name in ['track_m','sensor_ahead_m','sensor_spacing_m','sensor_radius_m',
                     'line_width_m','road_width_m','max_wheel_mps','motor_tau_s',
                     'coast_tau_s','max_accel_mps2','left_gain','right_gain','battery_factor','friction_mu']:
            if getattr(self,name)<=0:raise ValueError(name+' must be positive')
        if not 0<=self.dead_pwm<255:raise ValueError('dead_pwm must be in [0,255)')
        if not isinstance(self.sample_ms,int) or self.sample_ms<1:raise ValueError('sample_ms must be a positive integer')
        if not isinstance(self.latency_ms,int) or self.latency_ms<0:raise ValueError('latency_ms must be a nonnegative integer')
        if self.adc_noise<0:raise ValueError('adc_noise must be nonnegative')


def nearest(x, y, points):
    best = (float('inf'), 0.0, 0.0)
    accumulated = 0.0
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        t = max(0, min(1, ((x-ax)*dx + (y-ay)*dy) / length**2))
        d = math.hypot(x-ax-t*dx, y-ay-t*dy)
        if d < best[0]:
            best = d, accumulated + t*length, math.atan2(dy, dx)
        accumulated += length
    return best


def angle(a):
    return (a + math.pi) % (2*math.pi) - math.pi


def scenario(name):
    if name == 'straight':
        return [(0, 0), (2.1, 0)], 0, 0.0
    side = -1 if name.endswith('_right') else 1
    deg = 120 if 'v60' in name else 90 if '90' in name else 60
    rad = math.radians(deg) * side
    return [(0, 0), (1.2, 0), (1.2 + math.cos(rad)*0.9, math.sin(rad)*0.9)], rad, .045 if 'wide' in name else 0


def read_adc(x, y, heading, p, path, patch, rng, features=None):
    result = []
    for i in range(5):  # A5,A4,A3,A2,A1: left to right
        lateral = (2-i)*p.sensor_spacing_m
        sx = x + p.sensor_ahead_m*math.cos(heading) - lateral*math.sin(heading)
        sy = y + p.sensor_ahead_m*math.sin(heading) + lateral*math.cos(heading)
        # Area-like footprint averaging. Intermediate readings are intentionally
        # retained; ADC thresholding is performed by the original controller.
        hits = 0
        samples = [(0,0), (p.sensor_radius_m,0), (-p.sensor_radius_m,0),
                   (0,p.sensor_radius_m), (0,-p.sensor_radius_m)]
        for ox, oy in samples:
            d, _, _ = nearest(sx+ox, sy+oy, path)
            on = d <= p.line_width_m/2
            if patch and math.hypot(sx+ox-1.2, sy+oy) < patch:
                on = True
            for feature in features or []:
                if feature['x0'] <= sx+ox <= feature['x1'] and feature['y0'] <= sy+oy <= feature['y1']:
                    on = feature['on']
            hits += on
        adc = p.background_adc + (p.line_adc-p.background_adc)*hits/len(samples)
        result.append(round(max(0, min(1023, adc+rng.gauss(0,p.adc_noise)))))
    return result


def wheel(v, pwm, gain, p, dt):
    # Dead zone, battery and asymmetric gain map PWM to unloaded target speed.
    drive = max(0, abs(pwm)-p.dead_pwm)/(255-p.dead_pwm)
    target = math.copysign(p.max_wheel_mps*drive*gain*p.battery_factor, pwm)
    tau = p.motor_tau_s if drive else p.coast_tau_s
    accel = (target-v)/tau
    limit = min(p.max_accel_mps2*p.battery_factor, p.friction_mu*9.81)
    accel = max(-limit, min(limit, accel)) - 9.81*math.sin(math.radians(p.grade_deg))
    return v + accel*dt

