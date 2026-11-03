"""Run the actual vendor-exported sketch in a desktop DLL, without hardware I/O.

Windows/MSVC host compilation is not Arduino compilation. Vendor LED and Serial
are no-ops; real millis, ADC and GPIO boundaries are replaced explicitly.
"""
import ctypes
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STATE = ['sensorF', 'turnFault', 'lapDone', 'liftState', 'turnActive',
         'gapActive', 'cornerWideRecovery', 'turnDirection', 'turnCaptureSide',
         'outerProbeActive', 'splitActive', 'straightPwm', 'firstFaultLine', 'firstFaultF']
DIAGNOSTICS = ['linePosition','lineConfidence','wideEvents','missionPhase','uncertaintyMs','markerArmed',
               'eventSerial','eventCode','missionCandidates','missionStep','missionAmbiguous']


def build(source, directory):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    text = Path(source).read_text(encoding='utf-8')
    if 'TIRT_NATIVE_ADAPTER' in text:
        return build_handwritten(source, directory)
    digest = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    # Observer-only instrumentation: preserve the first fault's original source
    # line and F before later ADC samples obscure the triggering observation.
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if line.strip()=='turnFault = 1;':
            lines[i]=line.replace('turnFault = 1;',
                'if(!firstFaultLine){firstFaultLine=%d;firstFaultF=sensorF;} turnFault = 1;' % (i+1))
    (directory / 'sketch.inc').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (directory / 'moto_NeoPixel.h').write_text('''#pragma once
#define NEO_GRB 0
#define NEO_KHZ800 0
struct moto_NeoPixel {
 moto_NeoPixel(int,int,int){} void begin(){} void show(){}
 int Color(int,int,int){return 0;} void setPixelColor(int,int){}
};
''', encoding='utf-8')
    variables = set(re.findall(r'^(?:int|unsigned long)\s+(\w+)\s*;', text, re.M))
    prototypes = '\n'.join(re.findall(r'^void\s+\w+\([^\n]*\)(?=\s*\{)', text, re.M))
    prototypes = prototypes.replace('\n', ';\n') + ';'
    parameter_cases = '\n'.join(
        'if(!strcmp(name,"%s")){%s=value;return 1;}' % (n, n)
        for n in sorted(variables))
    state_cases = '\n'.join('case %d:return %s;' % (i, n if n in variables or n.startswith('firstFault') else '0')
                            for i, n in enumerate(STATE))
    bridge = r'''
#include <string>
#include <cstdlib>
#include <cstring>
#include <cstdint>
class String:public std::string {
public: using std::string::string;
 String(int n):std::string(std::to_string(n)){}
 String(const std::string &s):std::string(s){}
 String operator+(const String &s)const{return String(std::string(*this)+std::string(s));}
};
const int LOW=0,HIGH=1,INPUT=0,OUTPUT=1,A1=15,A2=16,A3=17,A4=18,A5=19;
static uint32_t nowMs=0;
static int firstFaultLine=0,firstFaultF=0;
static int adc[20]={},pwm[20]={},digital[20]={};
unsigned long millis(){return nowMs;}
void delay(unsigned long ms){nowMs+=ms;}
void pinMode(int,int){}
int digitalRead(int){return 0;}
int analogRead(int pin){return adc[pin];}
void digitalWrite(int pin,int value){digital[pin]=value;}
void analogWrite(int pin,int value){pwm[pin]=value;}
struct SerialStub{void begin(int){} template<class T>void print(T){} template<class T>void println(T){};} Serial;
@PROTOTYPES@
#include "sketch.inc"
extern "C" __declspec(dllexport) void reset_sim(){
 nowMs=0;firstFaultLine=firstFaultF=0;memset(pwm,0,sizeof(pwm));memset(digital,0,sizeof(digital));
 for(int i=0;i<20;++i)adc[i]=500;
 setup();nowMs=0;
}
extern "C" __declspec(dllexport) void step_sim(uint32_t ms,int a5,int a4,int a3,int a2,int a1){
 nowMs=ms;adc[A5]=a5;adc[A4]=a4;adc[A3]=a3;adc[A2]=a2;adc[A1]=a1;loop();
}
extern "C" __declspec(dllexport) int get_state(int field){switch(field){@STATE@}return 0;}
extern "C" __declspec(dllexport) int left_command(){return digital[7]==LOW?pwm[5]:-pwm[5];}
extern "C" __declspec(dllexport) int right_command(){return digital[4]==HIGH?pwm[6]:-pwm[6];}
extern "C" __declspec(dllexport) int set_parameter(const char*name,int value){@PARAMETERS@return 0;}
'''.replace('@PROTOTYPES@', prototypes).replace('@STATE@', state_cases).replace('@PARAMETERS@', parameter_cases)
    (directory / 'bridge.cpp').write_text(bridge, encoding='utf-8')
    return compile_bridge(directory), digest


def compile_bridge(directory):
    env = os.environ.copy()
    if not shutil.which('cl'):
        candidates = sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Auxiliary/Build/vcvars64.bat'))
        if not candidates:
            raise RuntimeError('MSVC cl or Visual Studio Community vcvars64.bat is required')
        result = subprocess.run('cmd /d /s /c ""%s" >nul && set"' % candidates[-1],
                                capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if '=' in line and not line.startswith('='):
                k, v = line.split('=', 1)
                env[k.upper()] = v
    dll = directory / 'controller.dll'
    compiler = shutil.which('cl', path=env.get('PATH'))
    result = subprocess.run([compiler, '/nologo', '/LD', '/EHsc', '/O2', '/std:c++17',
                             '/I' + str(directory), 'bridge.cpp', '/link', '/OUT:' + str(dll)],
                            cwd=str(directory), env=env, capture_output=True, text=True)
    (directory / 'compile.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return dll


def build_handwritten(source, directory):
    """Compile the real native adapter and its core, with host-only hardware mocks."""
    source = Path(source).resolve()
    core = source.with_name('controller.h')
    digest = hashlib.sha256(source.read_bytes()+b'\0controller.h\0'+core.read_bytes()).hexdigest()
    shutil.copyfile(core, directory/'controller.h')
    shutil.copyfile(source, directory/'sketch.inc')
    (directory/'Arduino.h').write_text(r'''#pragma once
#include <cstdint>
const int LOW=0,HIGH=1,INPUT=0,OUTPUT=1,A1=15,A2=16,A3=17,A4=18,A5=19;
#define F(s) s
extern uint32_t nowMs;
extern int adc[20],pwm[20],digital[20];
inline uint32_t millis(){return nowMs;}
inline void delay(uint32_t ms){nowMs+=ms;}
inline void pinMode(int,int){}
inline int digitalRead(int){return 0;}
inline int analogRead(int pin){return adc[pin];}
inline void digitalWrite(int pin,int value){digital[pin]=value;}
inline void analogWrite(int pin,int value){pwm[pin]=value;}
struct SerialStub { void begin(int){} template<class T>void print(T){} template<class T>void println(T){} };
extern SerialStub Serial;
''',encoding='utf-8')
    (directory/'Adafruit_NeoPixel.h').write_text('''#pragma once
#define NEO_GRB 0
#define NEO_KHZ800 0
struct Adafruit_NeoPixel {
 Adafruit_NeoPixel(int,int,int){} void begin(){} void show(){}
 int Color(int,int,int){return 0;} void setPixelColor(int,int){}
};
''',encoding='utf-8')
    mapping = ['s.f','s.fault!=tirt::Fault::None','s.lapDone','int(s.lift)',
               's.motion==tirt::Motion::Search','s.motion==tirt::Motion::Gap',
               's.recovery','s.direction','s.captureSide','s.probe','s.splitActive',
               's.straightPwm','0','faultF']
    cases=''.join('case %d:return %s;'%(i,value) for i,value in enumerate(mapping))
    diagnostics=''
    if 'TIRT_CONTINUOUS_CANDIDATE' in core.read_text(encoding='utf-8'):
        expressions=['s.position','s.confidence','s.events','s.missionPhase','s.uncertainMs','s.markerArmed']
        if 'TIRT_MISSION_PREFIX' in core.read_text(encoding='utf-8'):
            expressions+=['s.eventSerial','s.eventCode','s.missionCandidates','s.missionStep','s.missionAmbiguous']
        diagnostic_cases=''.join('case %d:return %s;'%(i,v) for i,v in enumerate(expressions))
        diagnostics='extern "C" __declspec(dllexport) int get_diagnostic(int field){const auto &s=controller.state();switch(field){'+diagnostic_cases+'}return 0;}\nextern "C" __declspec(dllexport) int diagnostic_count(){return '+str(len(expressions))+';}'
    (directory/'bridge.cpp').write_text(r'''
#include "Arduino.h"
#include <cstring>
uint32_t nowMs=0;
int adc[20]={},pwm[20]={},digital[20]={},faultF=0;
bool observedFault=false;
SerialStub Serial;
#include "controller.h"
void statusLed(bool);
void writeWheels(tirt::Wheels);
#include "sketch.inc"
extern "C" __declspec(dllexport) void reset_sim(){
 nowMs=0;faultF=0;observedFault=false;memset(pwm,0,sizeof(pwm));memset(digital,0,sizeof(digital));
 for(int i=0;i<20;++i)adc[i]=500;
 setup();nowMs=0;
}
extern "C" __declspec(dllexport) void step_sim(uint32_t ms,int a5,int a4,int a3,int a2,int a1){
 nowMs=ms;adc[A5]=a5;adc[A4]=a4;adc[A3]=a3;adc[A2]=a2;adc[A1]=a1;loop();
 if(!observedFault && controller.state().fault!=tirt::Fault::None){observedFault=true;faultF=controller.state().f;}
}
extern "C" __declspec(dllexport) int get_state(int field){const auto &s=controller.state();switch(field){@CASES@}return 0;}
extern "C" __declspec(dllexport) int left_command(){return digital[7]==LOW?pwm[5]:-pwm[5];}
extern "C" __declspec(dllexport) int right_command(){return digital[4]==HIGH?pwm[6]:-pwm[6];}
extern "C" __declspec(dllexport) int set_parameter(const char*,int){return 0;}
extern "C" __declspec(dllexport) int fault_reason(){return int(controller.state().fault);}
@DIAGNOSTICS@
'''.replace('@CASES@',cases).replace('@DIAGNOSTICS@',diagnostics),encoding='utf-8')
    return compile_bridge(directory), digest


class Controller:
    def __init__(self, dll):
        self.lib = ctypes.CDLL(str(dll))
        self.lib.step_sim.argtypes = [ctypes.c_uint32] + [ctypes.c_int] * 5
        self.lib.set_parameter.argtypes = [ctypes.c_char_p, ctypes.c_int]

    def reset(self, parameters=None):
        self.lib.reset_sim()
        for name, value in (parameters or {}).items():
            if not self.lib.set_parameter(name.encode(), value):
                raise ValueError('Unknown sketch parameter: ' + name)

    def step(self, ms, adc):
        self.lib.step_sim(ms, *adc)
        return (self.lib.left_command(), self.lib.right_command())

    def state(self):
        return {name: self.lib.get_state(i) for i, name in enumerate(STATE)}

    def diagnostics(self):
        if not hasattr(self.lib,'get_diagnostic'):return {}
        count=self.lib.diagnostic_count() if hasattr(self.lib,'diagnostic_count') else 6
        return {name:self.lib.get_diagnostic(i) for i,name in enumerate(DIAGNOSTICS[:count])}
