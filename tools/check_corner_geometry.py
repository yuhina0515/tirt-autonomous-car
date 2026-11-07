"""Cross-check accelerated nearest-distance and rectangular-body geometry."""
import ctypes,json,math,random,shutil,sys
from pathlib import Path
from sim_native import compile_bridge
from simulation_model import nearest

base=Path(sys.argv[1]).resolve();out=base/'geometry-check';out.mkdir(exist_ok=False)
shutil.copytree(base/'host/layered',out/'layered');shutil.copy2(base/'host/bridge.cpp',out/'bench.cpp')
(out/'bridge.cpp').write_text('''#include "bench.cpp"
extern "C" __declspec(dllexport) double distance_check(double x,double y,const double* coords,int n){std::vector<P> p;for(int i=0;i<n;i++)p.push_back({coords[2*i],coords[2*i+1]});return distanceTo({x,y},p);}
extern "C" __declspec(dllexport) int body_check(double x,double y,double yaw,const double* coords,int n){std::vector<P> p;for(int i=0;i<n;i++)p.push_back({coords[2*i],coords[2*i+1]});return bodyLine({x,y},yaw,p);}
''')
lib=ctypes.CDLL(str(compile_bridge(out)));d=lib.distance_check;d.argtypes=[ctypes.c_double,ctypes.c_double,ctypes.POINTER(ctypes.c_double),ctypes.c_int];d.restype=ctypes.c_double
b=lib.body_check;b.argtypes=[ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.POINTER(ctypes.c_double),ctypes.c_int];b.restype=ctypes.c_int
rng=random.Random(20261106)
for _ in range(500):
    path=[[rng.uniform(-2,2),rng.uniform(-2,2)] for _ in range(8)];coords=(ctypes.c_double*16)(*[v for p in path for v in p]);x,y=rng.uniform(-2,2),rng.uniform(-2,2)
    assert abs(d(x,y,coords,8)-nearest(x,y,path)[0])<1e-12
fixtures=[([[-1,0],[1,0]],0,1),([[-1,.07],[1,.07]],0,0),([[-1,.06],[1,.06]],0,1),([[.08,-1],[.08,1]],0,1),([[.1,-1],[.1,1]],0,0),([[.08,-1],[.08,1]],math.pi/2,0),([[0,0],[.01,.01]],1,1)]
for path,yaw,expected in fixtures:
    coords=(ctypes.c_double*4)(*[v for p in path for v in p]);assert b(0,0,yaw,coords,2)==expected
receipt=dict(distance_cases_vs_existing_python_model=500,body_analytic_cases=len(fixtures),passed=True)
(base/'geometry-check.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
