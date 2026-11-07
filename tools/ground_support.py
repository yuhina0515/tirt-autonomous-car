"""Explicit, bounded ground backing; physical support is not road legality.

An optional colored-map backing is a declared hypothesis, not a measured floor.
The original road geometry, reflectance paint and V exception are unchanged.
"""
import math
from course_world import Course as RoadCourse,geometry as road_geometry


class GroundCourse(RoadCourse):
    def __init__(self,spec):
        super().__init__(spec);self.backings=[]
        for backing in spec.get('ground_backings',[]):
            if (not isinstance(backing,dict) or type(backing.get('height_m')) not in (int,float) or backing['height_m']!=0):
                raise ValueError('ground backing requires explicit zero height')
            bounds=backing.get('bounds_px')
            if (not isinstance(bounds,list) or len(bounds)!=4 or
                any(type(v) not in (int,float) or not math.isfinite(v) for v in bounds)):
                raise ValueError('ground backing needs finite rectangular pixel bounds')
            x0,y0,x1,y1=bounds
            if not (0<=x0<x1<=spec['source_map']['width_px'] and 0<=y0<y1<=spec['source_map']['height_px']):
                raise ValueError('ground backing lies outside the source map')
            a=self.xy((x0,y0));b=self.xy((x1,y1))
            self.backings.append((a[0],b[1],b[0],a[1]))

    def road_contact(self,*args,**kwargs):
        return super().contact(*args,**kwargs)

    def contact(self,x,y,z,mechanisms=None,max_step=.025):
        road=self.road_contact(x,y,z,mechanisms,max_step)
        if road is not None:return road
        if abs(z)>max_step:return None
        if any(x0<=x<=x1 and y0<=y<=y1 for x0,y0,x1,y1 in self.backings):
            return dict(d=0,s=-1000,x=x,y=y,z=0,gx=0,gy=0,index=-1,kind='ground_backing')
        return None


class RoadLegalityView:
    """Keep the original tire predicate querying painted-road support only."""
    def __init__(self,course):self.course=course
    def __getattr__(self,name):return getattr(self.course,name)
    def contact(self,*args,**kwargs):return self.course.road_contact(*args,**kwargs)


def geometry(course,mechanisms,pose,plant):
    return road_geometry(RoadLegalityView(course),mechanisms,pose,plant)
