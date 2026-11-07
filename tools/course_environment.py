"""Select an explicit world extension; empty backing keeps legacy physics."""
from course_world import Course as RoadCourse,geometry as road_geometry
from ground_support import GroundCourse,geometry as backing_geometry


def model_features(spec):
    backings=spec.get('ground_backings',[])
    if not isinstance(backings,list):raise ValueError('ground_backings must be a list')
    return ['ground_backing'] if backings else []


def Course(spec):
    return GroundCourse(spec) if model_features(spec) else RoadCourse(spec)


def geometry(course,mechanisms,pose,plant):
    return backing_geometry(course,mechanisms,pose,plant) if isinstance(course,GroundCourse) else road_geometry(course,mechanisms,pose,plant)
