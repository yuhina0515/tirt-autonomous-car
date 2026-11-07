// Local planar stress bench. Actual layered core; no official-race qualification.
#include "layered/controller.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <random>
#include <vector>
struct P {double x,y;};
double dist(P a,P b){return std::hypot(a.x-b.x,a.y-b.y);}
double distanceTo(P p,const std::vector<P>& path){
 double best=1e9;for(size_t i=1;i<path.size();++i){P a=path[i-1],b=path[i];double dx=b.x-a.x,dy=b.y-a.y;
 double t=std::clamp(((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy),0.,1.);
 best=std::min(best,dist(p,{a.x+t*dx,a.y+t*dy}));}return best;
}
// Exact line-segment intersection with the oriented rectangular body footprint.
bool bodyLine(P p,double yaw,const std::vector<P>& path){
 double c=cos(yaw),s=sin(yaw);
 for(size_t i=1;i<path.size();++i){P ends[2];for(int j=0;j<2;j++){P q=path[i-1+j];double dx=q.x-p.x,dy=q.y-p.y;ends[j]={dx*c+dy*s,-dx*s+dy*c};}
 double lo=0,hi=1;bool ok=true;for(int axis=0;axis<2;axis++){double a=axis?ends[0].y:ends[0].x,b=axis?ends[1].y:ends[1].x,h=axis?.06:.09,d=b-a;
 if(fabs(d)<1e-12){if(fabs(a)>h)ok=false;}else{double t0=(-h-a)/d,t1=(h-a)/d;if(t0>t1)std::swap(t0,t1);lo=std::max(lo,t0);hi=std::min(hi,t1);}}
 if(ok&&lo<=hi)return true;}return false;
}
extern "C" __declspec(dllexport) void corner_trial(const double* coords,int count,uint64_t seed,double* result){
 std::vector<P> path;for(int i=0;i<count;i++)path.push_back({coords[2*i],coords[2*i+1]});
 std::mt19937_64 rng(seed);auto uniform=[&](double a,double b){return std::uniform_real_distribution<double>(a,b)(rng);};
 double track=uniform(.095,.135),ahead=uniform(.04,.085),spacing=uniform(.011,.018),vmax=uniform(.4,.85),dead=uniform(20,60);
 double tau=uniform(.04,.14),coast=uniform(.12,.35),accel=uniform(1.5,4.5),lg=uniform(.9,1.1),rg=uniform(.9,1.1),battery=uniform(.8,1),mu=uniform(.3,.8),noise=uniform(2,12);
 double heading=atan2(path[1].y-path[0].y,path[1].x-path[0].x),offset=uniform(-.015,.015),yawError=uniform(-.13962634,.13962634);
 P p={path[0].x-offset*sin(heading),path[0].y+offset*cos(heading)};heading+=yawError;
 std::normal_distribution<double> gaussian(0,noise);
 double vl=0,vr=0,maxError=0;int next=1,outcome=0,ms=0,firstWheel=-1,firstBody=-1; //0timeout1passed2fault3wrong_marker4missed_gate
 layered::Controller car;layered::Wheels cmd;uint16_t pending[5]={500,500,500,500,500};
 for(ms=0;ms<=15000;ms+=5){
  cmd=car.tick(ms,pending); //5ms sensor latency; first frame is background
  if(car.fault!=layered::Fault::None){outcome=2;break;}
  if(car.phase()==layered::Phase::Waiting||car.phase()==layered::Phase::Finished){outcome=3;break;}
  double c=cos(heading),s=sin(heading);
  for(int i=0;i<5;i++){double lateral=(2-i)*spacing;P sensor={p.x+ahead*c-lateral*s,p.y+ahead*s+lateral*c};int hits=0;
   P offsets[5]={{0,0},{.002,0},{-.002,0},{0,.002},{0,-.002}};
   for(P o:offsets)hits+=distanceTo({sensor.x+o.x,sensor.y+o.y},path)<=.01;
   pending[i]=uint16_t(std::clamp(std::round(500+(35-500)*hits/5.+gaussian(rng)),0.,1023.));}
  auto wheel=[&](double v,int pwm,double gain){double drive=std::max(0.,fabs(double(pwm))-dead)/(255-dead),target=std::copysign(vmax*drive*gain*battery,double(pwm));
   double limit=std::min(accel*battery,mu*9.81);return v+std::clamp((target-v)/(drive?tau:coast),-limit,limit)*.005;};
  vl=wheel(vl,cmd.left,lg);vr=wheel(vr,cmd.right,rg);double v=(vl+vr)/2,limit=mu*9.81/std::max(fabs(v),.02);
  P old=p;heading+=std::clamp((vr-vl)/track,-limit,limit)*.005;p.x+=v*cos(heading)*.005;p.y+=v*sin(heading)*.005;
  maxError=std::max(maxError,distanceTo(p,path));
  double wheelError=std::max(distanceTo({p.x-track/2*sin(heading),p.y+track/2*cos(heading)},path),distanceTo({p.x+track/2*sin(heading),p.y-track/2*cos(heading)},path));
  if(firstWheel<0&&wheelError+.0075>.095)firstWheel=ms;
  if(firstBody<0&&!bodyLine(p,heading,path))firstBody=ms;
  if(next<int(path.size())){
   P gate=path[next],a=path[next-1];double nx=gate.x-a.x,ny=gate.y-a.y,len=hypot(nx,ny);nx/=len;ny/=len;
   if(next+1<int(path.size())){P b=path[next+1];double dx=b.x-gate.x,dy=b.y-gate.y,l=hypot(dx,dy);nx+=dx/l;ny+=dy/l;double n=hypot(nx,ny);nx/=n;ny/=n;}
   double before=(old.x-gate.x)*nx+(old.y-gate.y)*ny,after=(p.x-gate.x)*nx+(p.y-gate.y)*ny;
   if(before<=0&&after>0){double t=-before/(after-before);P hit={old.x+t*(p.x-old.x),old.y+t*(p.y-old.y)};
    if(dist(hit,gate)>.095){outcome=4;break;}next++;}
  }
  if(next==int(path.size())){outcome=1;break;}
  if(maxError>.3){outcome=4;break;}
 }
 result[0]=outcome;result[1]=ms;result[2]=firstWheel;result[3]=firstBody;result[4]=maxError;result[5]=int(car.fault);result[6]=next-1;result[7]=path.size()-1;
}
