"""Constrained 2.5D contact world for a provenance-labelled course reconstruction.

Terrain is a collection of occurrence-specific painted strips. This is not a
rigid-body engine: no suspension, airborne landing, chassis roll or measured
CAGEBOT dynamics. Height, grade, layer occlusion and moving supports are explicit.
Controller code has no access to these objects.
"""
from dataclasses import dataclass
import math

G = 9.81


def clamp(x, low, high):
    return max(low, min(high, x))


@dataclass(frozen=True)
class Segment:
    index: int
    a: tuple
    b: tuple
    start: float
    length: float

    def project(self, x, y):
        dx, dy = self.b[0]-self.a[0], self.b[1]-self.a[1]
        t = clamp(((x-self.a[0])*dx+(y-self.a[1])*dy)/self.length**2, 0, 1)
        px, py = self.a[0]+t*dx, self.a[1]+t*dy
        return math.hypot(x-px, y-py), self.start+t*self.length, px, py, t


class Course:
    def __init__(self, spec):
        self.spec = spec
        a = self.assumptions = spec['assumptions']
        self.scale = a['metres_per_pixel']
        if not math.isfinite(self.scale) or self.scale <= 0:
            raise ValueError('metres_per_pixel must be positive')
        xy = [self.xy(p) for p in spec['points_px']]
        self.stations = [0.0]
        for p, q in zip(xy, xy[1:]):
            d = math.dist(p, q)
            if d <= 1e-9:
                raise ValueError('Duplicate course vertex')
            self.stations.append(self.stations[-1]+d)
        self.length = self.stations[-1]
        self.points = [(x,y,self.height(s)) for (x,y),s in zip(xy,self.stations)]
        self.segments = [Segment(i,p,q,self.stations[i],self.stations[i+1]-self.stations[i])
                         for i,(p,q) in enumerate(zip(self.points,self.points[1:]))]
        self.main_segments=list(self.segments)
        self.extra_paint = [[self.xy(p) for p in line] for line in spec.get('extra_paint_px',[])]
        for i,(p,q) in enumerate(self.extra_paint):
            self.segments.append(Segment(len(self.segments),(*p,0),(*q,0),-100-i,math.dist(p,q)))
        self.grid = {}
        self.cell = .25
        width = a['road_width_m']/2+.05
        for seg in self.segments:
            for ix in range(math.floor((min(seg.a[0],seg.b[0])-width)/self.cell),math.floor((max(seg.a[0],seg.b[0])+width)/self.cell)+1):
                for iy in range(math.floor((min(seg.a[1],seg.b[1])-width)/self.cell),math.floor((max(seg.a[1],seg.b[1])+width)/self.cell)+1):
                    self.grid.setdefault((ix,iy),[]).append(seg)
        self.v_zones = [self.xy(p) for p in spec.get('V_exceptions_px',[])]
        for i in range(spec['ground_from_vertex']+1,len(xy)-1):
            ax,ay=xy[i-1][0]-xy[i][0],xy[i-1][1]-xy[i][1]
            bx,by=xy[i+1][0]-xy[i][0],xy[i+1][1]-xy[i][1]
            inside=math.acos(clamp((ax*bx+ay*by)/(math.hypot(ax,ay)*math.hypot(bx,by)),-1,1))
            if inside<math.pi/3:self.v_zones.append(xy[i])
        self.start_s = spec['timing']['start_after_m']
        self.finish_s = self.length-spec['timing']['finish_before_end_m']
        self.gates = [self.start_s]
        self.gates += [s for s in self.stations[1:-1] if self.start_s+.05 < s < self.finish_s-.05]
        self.gates += [self.finish_s]
        self.lift_config = spec['mechanisms']['lift']
        self.seesaw_config = spec['mechanisms']['seesaw']
        self.lift_s = self.station_near(self.lift_config['near_px'],self.lift_config['occurrence_after_vertex'])
        self.seesaw_s = self.station_near(self.seesaw_config['near_px'])
        # Receiving-deck height depends on lift_s; refresh exported vertices and
        # grid references after its initialization as well as analytical queries.
        self.points=[(p[0],p[1],self.height(s)) for p,s in zip(self.points,self.stations)]
        extra=self.segments[len(self.main_segments):]
        self.main_segments=[Segment(i,p,q,self.stations[i],self.stations[i+1]-self.stations[i])
                            for i,(p,q) in enumerate(zip(self.points,self.points[1:]))]
        self.segments=self.main_segments+extra
        by_index={s.index:s for s in self.segments}
        self.grid={cell:[by_index[s.index] for s in segments] for cell,segments in self.grid.items()}

    def height(self,station):
        a=self.assumptions
        ground=self.stations[self.spec['ground_from_vertex']]
        z=a['deck_height_m']*clamp((ground-station)/self.spec['ground_ramp_m'],0,1)
        for occurrence in self.spec['raised_occurrences']:
            lo=self.stations[occurrence['start_vertex']];hi=self.stations[occurrence['end_vertex']]
            weight=min(clamp((station-lo)/occurrence['ramp_m'],0,1),clamp((hi-station)/occurrence['ramp_m'],0,1))
            z+=a['layer_separation_m']*weight
        # An explicit inferred receiving deck, not a teleport from the platform.
        if hasattr(self,'lift_s') and station>self.lift_s+self.lift_config['half_length_m']:
            lo=self.stations[self.lift_config['lower_landing_until_vertex']]
            hi=self.stations[self.lift_config['return_deck_at_vertex']]
            if station<hi:
                t=clamp((station-lo)/(hi-lo),0,1)
                z=self.lift_config['lower_height_m']+(z-self.lift_config['lower_height_m'])*t
        return z

    def xy(self, pixel):
        return pixel[0]*self.scale, (self.spec['source_map']['height_px']-pixel[1])*self.scale

    def station_near(self, pixel, after=0):
        x,y = self.xy(pixel)
        return min((s.project(x,y)[:2] for s in self.main_segments[after:]),key=lambda p:p[0])[1]

    def at(self, station):
        station = clamp(station,0,self.length)
        for s in self.main_segments:
            if station <= s.start+s.length+1e-9:
                t = (station-s.start)/s.length
                return (s.a[0]+t*(s.b[0]-s.a[0]),s.a[1]+t*(s.b[1]-s.a[1]),self.height(station)), math.atan2(s.b[1]-s.a[1],s.b[0]-s.a[0])
        raise ValueError('station out of range')

    def candidates(self, x, y):
        return self.grid.get((math.floor(x/self.cell),math.floor(y/self.cell)),[])

    def projections(self, x, y, mechanisms=None):
        for seg in self.candidates(x,y):
            d,s,px,py,t = seg.project(x,y)
            if d > self.assumptions['road_width_m']/2+.05:
                continue
            z=self.height(s) if s>=0 else seg.a[2]
            if s<0:dz=0
            elif hasattr(self,'lift_s') and 0<s-self.lift_s-self.lift_config['half_length_m']<.0001:
                dz=(self.height(s+.0001)-z)/.0001
            else:dz=(self.height(s+.0001)-self.height(s-.0001))/.0002
            gx=dz*(seg.b[0]-seg.a[0])/seg.length
            gy=dz*(seg.b[1]-seg.a[1])/seg.length
            kind='road' if s>=0 else 'branch'
            if mechanisms:
                if abs(s-self.lift_s) <= self.lift_config['half_length_m']:
                    z = mechanisms.lift_height
                    gx = gy = 0.0
                    kind='lift'
                if abs(s-self.seesaw_s) <= self.seesaw_config['half_length_m']*math.cos(mechanisms.theta):
                    # Station is horizontal distance; physical board length is
                    # fixed and its horizontal footprint changes with rotation.
                    z=mechanisms.pivot_height+(s-self.seesaw_s)*math.tan(mechanisms.theta)
                    gx=math.tan(mechanisms.theta)*(seg.b[0]-seg.a[0])/seg.length
                    gy=math.tan(mechanisms.theta)*(seg.b[1]-seg.a[1])/seg.length
                    kind='seesaw'
            yield dict(d=d,s=s,x=px,y=py,z=z,gx=gx,gy=gy,index=seg.index,kind=kind)

    def local_surfaces(self,x,y,mechanisms=None):
        """Merge consecutive strips locally before comparing separate decks.

        Clamped endpoint caps are part of the same continuous road. They cannot
        form a higher opaque plate over an adjacent segment's own guide.
        Nonadjacent crossing occurrences and mechanism boundaries stay separate.
        """
        groups=[]
        for p in sorted(self.projections(x,y,mechanisms),key=lambda p:p['index']):
            if p['d']>self.assumptions['road_width_m']/2:continue
            if (groups and p['kind'] in ('road','seesaw','lift') and p['kind']==groups[-1][-1]['kind']
                    and p['index']==groups[-1][-1]['index']+1):
                groups[-1].append(p)
            else:groups.append([p])
        return [min(group,key=lambda p:p['d']) for group in groups]

    def contact(self,x,y,z,mechanisms=None,max_step=.025):
        candidates = [p for p in self.local_surfaces(x,y,mechanisms)
                      if p['d'] <= self.assumptions['road_width_m']/2 and abs(p['z']-z)<=max_step]
        return min(candidates,key=lambda p:(p['d'],abs(p['z']-z))) if candidates else None

    def white(self,x,y,sensor_z,mechanisms):
        surfaces = [p for p in self.local_surfaces(x,y,mechanisms)
                    if p['d'] <= self.assumptions['road_width_m']/2 and -.002 <= sensor_z-p['z'] <= self.assumptions['sensor_range_m']]
        if not surfaces:
            return False
        # A ray sees the highest support below it, never a line through a deck.
        top = max(p['z'] for p in surfaces)
        visible = [p for p in surfaces if abs(p['z']-top)<.002]
        if any(p['d']<=self.assumptions['line_width_m']/2 for p in visible):
            return True
        if any(abs(p['s']-self.lift_s)<.018 for p in visible):
            return True
        if top < .01:
            for a,b in self.extra_paint:
                dx,dy=b[0]-a[0],b[1]-a[1]
                t=clamp(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy),0,1)
                if math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)<self.assumptions['line_width_m']/2:
                    return True
        return False


class Mechanisms:
    def __init__(self,course,lift_duration):
        self.course = course
        self.lift_duration = lift_duration
        self.lift_top = course.at(course.lift_s)[0][2]
        self.lift_height = self.lift_top
        self.lift_phase = 0  # 0 waiting for vehicle, 1 descending, 2 settled
        self.lift_elapsed = self.stop_elapsed = 0.0
        self.theta = math.radians(course.seesaw_config['limit_deg'])
        self.pivot_height=course.height(course.seesaw_s-course.seesaw_config['half_length_m']*math.cos(self.theta))+course.seesaw_config['half_length_m']*math.sin(self.theta)
        self.angular_velocity = 0.0

    def step(self,dt,station,wheel_speeds,contact=True):
        c=self.course
        cfg=c.lift_config
        on_lift=contact and abs(station-c.lift_s)<cfg['half_length_m']
        if self.lift_phase==0:
            stopped=max(abs(v) for v in wheel_speeds)<cfg['stop_speed_mps']
            self.stop_elapsed = self.stop_elapsed+dt if on_lift and stopped else 0.0
            if self.stop_elapsed>=cfg['stop_confirm_s']:
                self.lift_phase=1
        elif self.lift_phase==1:
            self.lift_elapsed=min(self.lift_duration,self.lift_elapsed+dt)
            t=self.lift_elapsed/self.lift_duration
            smooth=t*t*(3-2*t)
            self.lift_height=self.lift_top+(cfg['lower_height_m']-self.lift_top)*smooth
            if self.lift_elapsed>=self.lift_duration:
                self.lift_phase=2
        cfg=c.seesaw_config
        arm=station-c.seesaw_s
        torque=-cfg['damping_nms']*self.angular_velocity
        inertia=cfg['inertia_kgm2']
        if contact and abs(arm)<=cfg['half_length_m']*math.cos(self.theta):
            torque-=cfg['car_mass_kg']*G*arm
            inertia+=cfg['car_mass_kg']*(arm/math.cos(self.theta))**2
        self.angular_velocity+=torque/inertia*dt
        self.theta+=self.angular_velocity*dt
        limit=math.radians(cfg['limit_deg'])
        if abs(self.theta)>=limit:
            self.theta=clamp(self.theta,-limit,limit)
            if self.theta*self.angular_velocity>0:
                self.angular_velocity=0.0
        return on_lift


@dataclass
class Pose:
    x: float
    y: float
    z: float
    yaw: float
    pitch: float = 0.0
    vl: float = 0.0
    vr: float = 0.0


def gravity_along(contact,yaw):
    slope=contact['gx']*math.cos(yaw)+contact['gy']*math.sin(yaw)
    return math.atan(slope)


def advance(pose,command,plant,contact,dt):
    grade=gravity_along(contact,pose.yaw)
    normal=G/math.sqrt(1+contact['gx']**2+contact['gy']**2)
    values=[];tractions=[]
    for v,pwm,gain in zip((pose.vl,pose.vr),command,(plant.left_gain,plant.right_gain)):
        duty=max(0,abs(pwm)-plant.dead_pwm)/(255-plant.dead_pwm)
        target=math.copysign(plant.max_wheel_mps*duty*gain*plant.battery_factor,pwm)
        tau=plant.motor_tau_s if duty else plant.coast_tau_s
        limit=min(plant.max_accel_mps2*plant.battery_factor,plant.friction_mu*normal*plant.drive_normal_fraction)
        traction=clamp((target-v)/tau,-limit,limit)
        tractions.append(traction)
        acceleration=traction-G*math.sin(grade)
        values.append(v+acceleration*dt)
    pose.vl,pose.vr=values
    speed=sum(values)/2
    yaw_rate=(pose.vr-pose.vl)/plant.track_m
    budget=plant.friction_mu*normal*plant.drive_normal_fraction
    longitudinal=sum(tractions)/2
    lateral=math.sqrt(max(0,budget**2-longitudinal**2))
    # Longitudinal motor/braking force and centripetal force share traction.
    # Near zero center speed a pivot needs no centripetal acceleration; rotational
    # inertia and individual tire slips remain outside this constrained model.
    yaw_limit=lateral/max(abs(speed),.02)
    yaw_rate=clamp(yaw_rate,-yaw_limit,yaw_limit)
    yaw_mid=pose.yaw+yaw_rate*dt/2
    pose.x+=speed*math.cos(grade)*math.cos(yaw_mid)*dt
    pose.y+=speed*math.cos(grade)*math.sin(yaw_mid)*dt
    pose.yaw+=yaw_rate*dt
    pose.pitch=grade


def sense(course,mechanisms,pose,plant,rng):
    values=[]
    a=course.assumptions
    for i in range(5):
        lateral=(2-i)*plant.sensor_spacing_m
        sx=pose.x+plant.sensor_ahead_m*math.cos(pose.pitch)*math.cos(pose.yaw)-lateral*math.sin(pose.yaw)
        sy=pose.y+plant.sensor_ahead_m*math.cos(pose.pitch)*math.sin(pose.yaw)+lateral*math.cos(pose.yaw)
        sz=pose.z+plant.sensor_ahead_m*math.sin(pose.pitch)+a['sensor_height_m']
        r=plant.sensor_radius_m
        hits=sum(course.white(sx+dx,sy+dy,sz,mechanisms) for dx,dy in ((0,0),(r,0),(-r,0),(0,r),(0,-r)))
        value=plant.background_adc+(plant.line_adc-plant.background_adc)*hits/5
        values.append(round(clamp(value+rng.gauss(0,plant.adc_noise),0,1023)))
    return values


def chassis_pitch(course,mechanisms,pose):
    """Assumed front caster plus drive-axle support; no suspension dynamics."""
    ahead=course.assumptions['caster_ahead_m']
    x=pose.x+ahead*math.cos(pose.yaw);y=pose.y+ahead*math.sin(pose.yaw)
    front=course.contact(x,y,pose.z,mechanisms,max_step=.08)
    if front:
        return math.atan2(front['z']-pose.z,ahead)
    drive=course.contact(pose.x,pose.y,pose.z,mechanisms)
    return gravity_along(drive,pose.yaw) if drive else pose.pitch


def geometry(course,mechanisms,pose,plant):
    """Independent body-line and full tire-footprint coverage at this pose."""
    a=course.assumptions
    visible=[p for p in course.projections(pose.x,pose.y,mechanisms) if abs(p['z']-pose.z)<.025]
    body=False
    for p in visible:
        dx,dy=p['x']-pose.x,p['y']-pose.y
        forward=dx*math.cos(pose.yaw)+dy*math.sin(pose.yaw)
        lateral=-dx*math.sin(pose.yaw)+dy*math.cos(pose.yaw)
        body |= abs(forward)<=a['body_length_m']/2 and abs(lateral)<=a['body_width_m']/2
    v_exception=any(math.hypot(pose.x-x,pose.y-y)<.12 and pose.z<.025 for x,y in course.v_zones)
    wheels=True
    for side in (-1,1):
        for front in (-.012,.012):
            for edge in (-a['wheel_width_m']/2,a['wheel_width_m']/2):
                lateral=side*plant.track_m/2+edge
                x=pose.x+front*math.cos(pose.yaw)-lateral*math.sin(pose.yaw)
                y=pose.y+front*math.sin(pose.yaw)+lateral*math.cos(pose.yaw)
                wheels &= course.contact(x,y,pose.z,mechanisms,max_step=.03) is not None
    station=min(visible,key=lambda p:p['d'])['s'] if visible else -1000
    ceiling=any(.02 < p['z']-pose.z < a['body_height_m'] and abs(p['s']-station)>a['body_length_m']*2
                for p in course.projections(pose.x,pose.y,mechanisms) if p['d']<a['body_width_m']/2)
    return dict(body_line=bool(body),wheel_road=bool(wheels or v_exception),ceiling_collision=ceiling)


def crossed_gate(course,station,previous,current):
    point,yaw=course.at(station)
    nx,ny=math.cos(yaw),math.sin(yaw)
    before=(previous.x-point[0])*nx+(previous.y-point[1])*ny
    after=(current.x-point[0])*nx+(current.y-point[1])*ny
    if not before<=0<after:
        return False
    t=-before/(after-before)
    x=previous.x+t*(current.x-previous.x)
    y=previous.y+t*(current.y-previous.y)
    z=previous.z+t*(current.z-previous.z)
    lateral=abs(-(x-point[0])*ny+(y-point[1])*nx)
    return lateral<course.assumptions['road_width_m']/2 and abs(z-point[2])<.03


def forward_travel(course,previous,current,mechanisms,tolerance_m=1e-6):
    dx,dy=current.x-previous.x,current.y-previous.y
    if math.hypot(dx,dy)<=tolerance_m:return True
    # At a corner the body can straddle the incoming and outgoing guide. Either
    # adjacent directed tangent is valid; unrelated layers remain excluded.
    x,y=(current.x+previous.x)/2,(current.y+previous.y)/2
    z=(current.z+previous.z)/2
    nearby=[p for p in course.projections(x,y,mechanisms) if p['s']>=0 and p['d']<course.assumptions['body_width_m']/2 and abs(p['z']-z)<.03]
    if not nearby:return False
    closest=min(nearby,key=lambda p:p['d'])
    for p in nearby:
        if abs(p['index']-closest['index'])>1:continue
        seg=course.main_segments[p['index']]
        if (dx*(seg.b[0]-seg.a[0])+dy*(seg.b[1]-seg.a[1]))/seg.length>=-tolerance_m:return True
    return False


def inspect_geometry(course,step=.025):
    """Draft-model feasibility diagnostics, never a source-verification stamp."""
    m=Mechanisms(course,27)
    conflicts=[]
    for i in range(math.ceil(course.length/step)+1):
        s=min(course.length,i*step)
        if abs(s-course.lift_s)<course.lift_config['half_length_m']+.05 or abs(s-course.seesaw_s)<course.seesaw_config['half_length_m']+.05:
            continue
        point,yaw=course.at(s)
        # This check concerns the hypothetical deck clearance, not vehicle tuning.
        from simulation_model import Plant
        if geometry(course,m,Pose(*point,yaw),Plant())['ceiling_collision']:
            conflicts.append(round(s,5))
    limit=math.radians(course.seesaw_config['limit_deg'])
    entry=course.seesaw_s-course.seesaw_config['half_length_m']*math.cos(limit)
    exit=course.seesaw_s+course.seesaw_config['half_length_m']*math.cos(limit)
    lift_exit=course.lift_s+course.lift_config['half_length_m']+.000001
    return dict(route_length_assumed_m=course.length,route_vertices=len(course.points),ordered_gates=len(course.gates),
                sampled_ceiling_conflicts_m=conflicts,clearance_sample_step_m=step,
                seesaw_initial_entry_gap_m=m.pivot_height-course.seesaw_config['half_length_m']*math.sin(limit)-course.height(entry),
                seesaw_final_exit_gap_m=m.pivot_height-course.seesaw_config['half_length_m']*math.sin(limit)-course.height(exit),
                lift_settled_exit_gap_m=course.height(lift_exit)-course.lift_config['lower_height_m'],
                official_geometry_verified=False)
