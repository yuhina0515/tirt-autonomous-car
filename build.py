"""Build editable CAGEBOT XML and Arduino from one explicit control program."""
import argparse
import hashlib
import json
from pathlib import Path
from blockly_codegen import *

ROOT=Path(__file__).resolve().parent
HEADER=['millis','tick','dt','rawA5','rawA4','rawA3','rawA2','rawA1',
        'mask','state','reason','position','accepted_position','contrast',
        'left_pwm','right_pwm','rejected','timing_faults']
# States: WAIT=0 ACQUIRE=1 TRACK=2 UNCERTAIN=3 STOP=4 FAULT=5 CAPTURE=6.
# Reasons: OK=0 LOST=1 WIDE=2 SPLIT=3 JUMP=4 UNARMED=5 TIMING=6
#          MANUAL_STOP=7 CONFIRM=8 ACQUIRE_TIMEOUT=9 RUN_LIMIT=10 LOW_CONTRAST=11
#          DEPART=12 FINISH=13 SEARCH=14 GAP=15 CROSSING=16.

def validate(c):
    for n in ('calibration_measured','drive_enabled','lap_enabled'):
        if type(c[n]) is not bool:raise ValueError(n+' must be boolean')
    if c['drive_enabled'] and not c['calibration_measured']:
        raise ValueError('Drive enable requires measured calibration')
    for name in ('line_adc_A5_to_A1','background_adc_A5_to_A1'):
        if len(c[name])!=5 or any(type(v) is not int or not 0<=v<=1023 for v in c[name]):
            raise ValueError(name+' needs five integer ADC endpoints')
    if any(abs(a-b)<100 for a,b in zip(c['line_adc_A5_to_A1'],c['background_adc_A5_to_A1'])):
        raise ValueError('Endpoint span must be >=100 ADC per sensor')
    bounds={'period_ms':(5,20),'log_period_ms':(40,1000),'max_tick_gap_ms':(30,100),
            'on_strength':(1,1000),'off_strength':(0,999),'weight_floor':(0,999),
            'min_contrast':(1,1000),'valid_confirm_ms':(10,200),'candidate_band':(1,1000),
            'max_jump':(1,2000),'uncertain_stop_ms':(40,500),'acquire_timeout_ms':(200,5000),
            'max_run_ms':(1000,300000),'base_pwm':(1,255),'curve_pwm':(1,255),
            'uncertain_pwm':(1,255),'min_pwm':(1,254),'max_pwm':(2,255),
            'kp':(0,150),'kd':(0,10),'slew_pwm_per_tick':(1,50),
            'search_timeout_ms':(100,1500),'gap_timeout_ms':(40,500),
            'wide_timeout_ms':(100,1000),'search_edge':(300,1000),
            'search_pwm':(25,100),'departure_pwm':(25,100),
            'departure_confirm_ms':(100,2000),'min_lap_ms':(1000,240000),
            'finish_confirm_ms':(50,900)}
    for n,(lo,hi) in bounds.items():
        if type(c[n]) is not int or not lo<=c[n]<=hi:raise ValueError('Invalid '+n)
    if not c['weight_floor']<c['off_strength']<c['on_strength']:raise ValueError('Invalid hysteresis/floor')
    if not c['min_pwm']<c['uncertain_pwm']<=c['curve_pwm']<=c['base_pwm']<=c['max_pwm']:
        raise ValueError('PWM bounds leave insufficient steering authority')
    if not c['period_ms']<=c['valid_confirm_ms']<c['uncertain_stop_ms']:
        raise ValueError('Confirmation must fit uncertainty deadline')
    if c['max_tick_gap_ms']<2*c['period_ms']:raise ValueError('Timing gap too small')
    if not c['valid_confirm_ms']<min(c['search_timeout_ms'],c['gap_timeout_ms']):
        raise ValueError('Recovery must allow line confirmation')
    if not c['valid_confirm_ms']<c['finish_confirm_ms']<c['wide_timeout_ms']:
        raise ValueError('Finish confirmation must fit wide deadline')
    if not c['departure_confirm_ms']<c['min_lap_ms']<c['max_run_ms']:
        raise ValueError('Lap timing must fit run limit')
    if max(c['search_pwm'],c['departure_pwm'])>c['max_pwm']:
        raise ValueError('Recovery/departure PWM exceeds cap')

def program(c,profile):
    validate(c);variables={};funcs={}
    def var(n,v=0,t='long'):variables[n]=(t,v)
    capture=profile=='capture'
    settings={'driveMode':int(not capture),'configReady':int(c['drive_enabled'] and c['calibration_measured']),
        'periodMs':20 if capture else c['period_ms'],'logPeriodMs':20 if capture else c['log_period_ms'],
        'maxTickGapMs':c['max_tick_gap_ms'],'onLevel':c['on_strength'],'offLevel':c['off_strength'],
        'weightFloor':c['weight_floor'],'minContrast':c['min_contrast'],
        'validConfirmMs':c['valid_confirm_ms'],'candidateBand':c['candidate_band'],
        'maxJump':c['max_jump'],'uncertainStopMs':c['uncertain_stop_ms'],
        'acquireTimeoutMs':c['acquire_timeout_ms'],'maxRunMs':c['max_run_ms'],
        'basePwm':c['base_pwm'],'curvePwm':c['curve_pwm'],'uncertainPwm':c['uncertain_pwm'],
        'minPwm':c['min_pwm'],'maxPwm':c['max_pwm'],'kp':c['kp'],'kd':c['kd'],'slewPwm':c['slew_pwm_per_tick'],
        'lapEnabled':int(c['lap_enabled']),'searchTimeoutMs':c['search_timeout_ms'],
        'gapTimeoutMs':c['gap_timeout_ms'],'wideTimeoutMs':c['wide_timeout_ms'],
        'searchEdge':c['search_edge'],'searchPwm':c['search_pwm'],'departurePwm':c['departure_pwm'],
        'departureConfirmMs':c['departure_confirm_ms'],'minLapMs':c['min_lap_ms'],
        'finishConfirmMs':c['finish_confirm_ms']}
    for n,v in settings.items():var(n,v,'unsigned long' if n.endswith('Ms') else 'long')
    for n in ('nowMs','lastTickMs','dtMs','logAtMs','runAtMs','buttonAtMs','candidateAtMs','uncertainAtMs','elapsedMs','tick','rejected','timingFaults',
              'recoveryBudgetMs','lineAtMs','wideAtMs'):
        var(n,0,'unsigned long')
    for n in ('controlState','reason','maskF','activeCount','contrast','maxStrength','minStrength',
              'weighted','totalW','candidatePos','lastPosition','pendingPos','candidatePending',
              'difference','absDifference','validCandidate','candidateAccepted','hasPosition',
              'derivative','slope','tickDt','correction','lastCorrection','magnitude','targetBase','limitPwm',
              'leftTarget','rightTarget','leftPwm','rightPwm','buttonLow','buttonPrevious',
              'buttonReleased','buttonEvent','historyReady','wasTracking',
              'recoveryKind','departed','linePending','widePending'):
        var(n,6 if n=='controlState' and capture else 0)
    for i,(a,b) in enumerate(zip(c['line_adc_A5_to_A1'],c['background_adc_A5_to_A1'])):
        for n,v in ((f'line{i}',a),(f'background{i}',b),(f'raw{i}',0),(f'norm{i}',0),
                    (f'smooth{i}',0),(f'on{i}',0),(f'weight{i}',0)):var(n,v)
    sensors=[setv('maskF',0),setv('activeCount',0),setv('maxStrength',0),setv('minStrength',1000),setv('weighted',0),setv('totalW',0)]
    for i,pin in enumerate(('A5','A4','A3','A2','A1')):
        n=f'norm{i}';s=f'smooth{i}';on=f'on{i}';w=f'weight{i}'
        sensors += [setv(f'raw{i}',('analog',pin)),setv(n,div(mul(sub(f'raw{i}',f'background{i}'),1000),sub(f'line{i}',f'background{i}'))),
            cond(lt(n,0),[setv(n,0)]),cond(gt(n,1000),[setv(n,1000)]),
            cond(eq('historyReady',0),[setv(s,n)],[setv(s,div(add(s,mul(n,3)),4))])]
        if i in (1,2,3):
            sensors += [cases([(ge(s,'onLevel'),[setv(on,1)]),(le(s,'offLevel'),[setv(on,0)])]),
                setv('maskF',add('maskF',mul(on,16>>i))),setv('activeCount',add('activeCount',on)),
                cond(gt(s,'maxStrength'),[setv('maxStrength',s)]),cond(lt(s,'minStrength'),[setv('minStrength',s)]),
                setv(w,0),cond(eq(on,1),[setv(w,sub(s,'weightFloor'))]),
                cond(lt(w,0),[setv(w,0)]),setv('totalW',add('totalW',w)),
                setv('weighted',add('weighted',mul(w,(i-2)*1000)))]
        else:sensors += [setv(on,0),setv(w,0)]
    sensors += [setv('historyReady',1),setv('contrast',sub('maxStrength','minStrength'))]
    funcs['read_sensors']=sensors
    funcs['button_update']=[setv('buttonEvent',0),setv('buttonLow',eq(('digital','12'),0)),
        cond(ne('buttonLow','buttonPrevious'),[setv('buttonAtMs','nowMs'),setv('buttonPrevious','buttonLow')]),
        setv('elapsedMs',sub('nowMs','buttonAtMs')),
        cond(both(eq('buttonLow',0),ge('elapsedMs',25)),[setv('buttonReleased',1)]),
        cond(both(both(eq('buttonLow',1),eq('buttonReleased',1)),ge('elapsedMs',25)),[setv('buttonReleased',0),setv('buttonEvent',1)])]
    funcs['start_run']=[setv('controlState',1),setv('reason',8),setv('runAtMs','nowMs'),
        setv('departed',0),setv('linePending',0),setv('widePending',0),setv('recoveryKind',0),
        setv('candidatePending',0),setv('hasPosition',0),setv('historyReady',0),
        setv('lastPosition',0),setv('lastCorrection',0),setv('derivative',0),
        setv('leftPwm',0),setv('rightPwm',0)]
    funcs['classify']=[setv('validCandidate',0),setv('candidateAccepted',0),
        cases([(eq('activeCount',0),[setv('reason',1)]),(eq('activeCount',3),[setv('reason',2)]),
               (both(eq('on1',1),both(eq('on2',0),eq('on3',1))),[setv('reason',3)]),
               (lt('contrast','minContrast'),[setv('reason',11)])],
              [setv('validCandidate',1),setv('reason',0),setv('candidatePos',div('weighted','totalW'))])]
    # Freeze one recovery budget/direction on entry. Blips or reason changes never extend it.
    funcs['check_candidate']=[call('classify'),cond(eq('validCandidate',1),[
        setv('difference',sub('candidatePos','lastPosition')),setv('absDifference','difference'),
        cond(lt('absDifference',0),[setv('absDifference',sub(0,'absDifference'))]),
        cond(both(eq('controlState',2),le('absDifference','maxJump')),[setv('candidateAccepted',1),setv('candidatePending',0)],[
            setv('difference',sub('candidatePos','pendingPos')),setv('absDifference','difference'),
            cond(lt('absDifference',0),[setv('absDifference',sub(0,'absDifference'))]),
            cond(either(eq('candidatePending',0),gt('absDifference','candidateBand')),
                 [setv('candidatePending',1),setv('candidateAtMs','nowMs'),setv('pendingPos','candidatePos')]),
            setv('elapsedMs',sub('nowMs','candidateAtMs')),
            cond(ge('elapsedMs','validConfirmMs'),[setv('candidateAccepted',1)],
                 [setv('reason',8),cond(eq('controlState',2),[setv('reason',4)])])])
    ],[setv('candidatePending',0)])]
    steering=[setv('slope',0),setv('tickDt','dtMs'),
        cond(both(eq('hasPosition',1),eq('wasTracking',1)),[
            setv('slope',div(mul(sub('candidatePos','lastPosition'),1000),'tickDt'))],
            [setv('derivative',0)]),
        cond(gt('slope',200000),[setv('slope',200000)]),cond(lt('slope',-200000),[setv('slope',-200000)]),
        setv('derivative',div(add(mul('derivative',3),'slope'),4)),
        setv('correction',div(add(mul('kp','candidatePos'),mul('kd','derivative')),1000)),
        setv('magnitude','candidatePos'),cond(lt('magnitude',0),[setv('magnitude',sub(0,'magnitude'))]),
        setv('targetBase',sub('basePwm',div(mul(sub('basePwm','curvePwm'),'magnitude'),1000))),
        setv('limitPwm',sub('targetBase','minPwm')),
        cond(gt('correction','limitPwm'),[setv('correction','limitPwm')]),
        cond(lt('correction',sub(0,'limitPwm')),[setv('correction',sub(0,'limitPwm'))]),
        setv('leftTarget',add('targetBase','correction')),setv('rightTarget',sub('targetBase','correction')),
        setv('lastCorrection','correction'),setv('lastPosition','candidatePos'),setv('hasPosition',1),
        setv('controlState',2),setv('reason',0),setv('candidatePending',0)]
    funcs['steer']=steering
    funcs['hold_course']=[setv('limitPwm',sub('uncertainPwm','minPwm')),setv('correction','lastCorrection'),
        cond(gt('correction','limitPwm'),[setv('correction','limitPwm')]),
        cond(lt('correction',sub(0,'limitPwm')),[setv('correction',sub(0,'limitPwm'))]),
        setv('leftTarget',add('uncertainPwm','correction')),setv('rightTarget',sub('uncertainPwm','correction'))]
    funcs['begin_recovery']=[setv('controlState',3),setv('uncertainAtMs','nowMs'),setv('derivative',0),
        setv('recoveryKind',0),setv('recoveryBudgetMs','uncertainStopMs'),
        cases([(eq('activeCount',0),[
            setv('recoveryKind',1),setv('recoveryBudgetMs','gapTimeoutMs'),
            cases([(le('lastPosition',sub(0,'searchEdge')),[setv('recoveryKind',2),setv('recoveryBudgetMs','searchTimeoutMs')]),
                   (ge('lastPosition','searchEdge'),[setv('recoveryKind',3),setv('recoveryBudgetMs','searchTimeoutMs')])])]),
               (eq('activeCount',3),[setv('recoveryKind',4),setv('recoveryBudgetMs','wideTimeoutMs')])])]
    funcs['recover']=[call('hold_course'),
        cases([(eq('activeCount',0),[
            cases([(eq('recoveryKind',2),[setv('leftTarget',0),setv('rightTarget','searchPwm'),setv('reason',14)]),
                   (eq('recoveryKind',3),[setv('rightTarget',0),setv('leftTarget','searchPwm'),setv('reason',14)]),
                   (eq('recoveryKind',1),[setv('leftTarget','uncertainPwm'),setv('rightTarget','uncertainPwm'),setv('reason',15)])])]),
               (both(eq('activeCount',3),eq('recoveryKind',4)),[
                   setv('leftTarget','uncertainPwm'),setv('rightTarget','uncertainPwm'),setv('reason',16)])])]
    fault=lambda reason:[setv('controlState',5),setv('reason',reason),setv('leftTarget',0),setv('rightTarget',0)]
    normal=[setv('wasTracking',eq('controlState',2)),call('check_candidate'),
        cond(eq('candidateAccepted',1),[call('steer')],[setv('rejected',add('rejected',1)),
            cond(eq('controlState',2),[call('begin_recovery')]),
            cond(eq('controlState',3),[call('recover')]),
            cond(both(both(eq('controlState',1),eq('lapEnabled',1)),eq('activeCount',3)),[
                setv('leftTarget','departurePwm'),setv('rightTarget','departurePwm'),setv('reason',12)])])]
    funcs['lap_update']=[
        cond(both(eq('controlState',2),eq('candidateAccepted',1)),[
            cond(eq('linePending',0),[setv('linePending',1),setv('lineAtMs','nowMs')]),
            setv('elapsedMs',sub('nowMs','lineAtMs')),
            cond(ge('elapsedMs','departureConfirmMs'),[setv('departed',1)])],[setv('linePending',0)]),
        cond(both(both(eq('lapEnabled',1),eq('departed',1)),
                  both(both(eq('controlState',3),eq('recoveryKind',4)),eq('activeCount',3))),[
            setv('elapsedMs',sub('nowMs','runAtMs')),
            cond(ge('elapsedMs','minLapMs'),[
                cond(eq('widePending',0),[setv('widePending',1),setv('wideAtMs','nowMs')]),
                setv('elapsedMs',sub('nowMs','wideAtMs')),
                cond(ge('elapsedMs','finishConfirmMs'),[
                    setv('controlState',4),setv('reason',13),setv('leftTarget',0),setv('rightTarget',0)])],
                [setv('widePending',0)])],[setv('widePending',0)])]
    funcs['run_control']=[setv('elapsedMs',sub('nowMs','runAtMs')),
        cases([(ge('elapsedMs','maxRunMs'),[setv('controlState',4),setv('reason',10)]),
               (both(eq('controlState',1),ge('elapsedMs','acquireTimeoutMs')),fault(9))],[
            setv('elapsedMs',sub('nowMs','uncertainAtMs')),
            cond(both(eq('controlState',3),ge('elapsedMs','recoveryBudgetMs')),fault(1),normal+[call('lap_update')])])]
    motors=[]
    for side in ('left','right'):
        t=side+'Target';p=side+'Pwm'
        motors += [cond(gt(t,'maxPwm'),[setv(t,'maxPwm')]),cond(lt(t,0),[setv(t,0)]),
            cases([(le(t,0),[setv(p,0)]),(gt(t,p),[
                setv(p,add(p,'slewPwm')),cond(lt(p,'minPwm'),[setv(p,'minPwm')]),cond(gt(p,t),[setv(p,t)])])],[setv(p,t)])]
    motors += [('digitalwrite','7',0),('digitalwrite','4',1),('pwm','5','leftPwm'),('pwm','6','rightPwm')]
    funcs['write_motors']=motors
    fields=['nowMs','tick','dtMs']+[f'raw{i}' for i in range(5)]+['maskF','controlState','reason',
        'candidatePos','lastPosition','contrast','leftPwm','rightPwm','rejected','timingFaults']
    record=[setv('logAtMs','nowMs')]
    for i,f in enumerate(fields):
        record.append(('print',f,i==len(fields)-1))
        if i<len(fields)-1:record.append(('print',('text',','),False))
    funcs['telemetry']=[setv('elapsedMs',sub('nowMs','logAtMs')),cond(ge('elapsedMs','logPeriodMs'),record)]
    setup=[('serial',115200)]+[('declare',n,t,v) for n,(t,v) in variables.items()]+[
        ('pwm','5',0),('pwm','6',0),('digitalwrite','7',0),('digitalwrite','4',1),
        setv('nowMs',('millis',)),setv('lastTickMs','nowMs'),setv('buttonAtMs','nowMs')]
    active=[setv('controlState',6)]
    if not capture:
        active=[call('button_update'),
            cases([(eq('configReady',0),[setv('controlState',0),setv('reason',5)]),
                   (eq('buttonEvent',1),[
                       cond(both(ge('controlState',1),le('controlState',3)),
                            [setv('controlState',4),setv('reason',7)],[call('start_run')])])]),
            cond(both(ge('controlState',1),le('controlState',3)),[
                cond(gt('dtMs','maxTickGapMs'),[setv('timingFaults',add('timingFaults',1))]+fault(6),[call('run_control')])])]
    loop=[setv('nowMs',('millis',)),setv('dtMs',sub('nowMs','lastTickMs')),
        cond(ge('dtMs','periodMs'),[setv('lastTickMs','nowMs'),setv('tick',add('tick',1)),
            setv('leftTarget',0),setv('rightTarget',0),call('read_sensors')]+active+[
            call('write_motors'),call('telemetry')])]
    return variables,funcs,setup,loop

def build(config,out,profile):
    c=json.loads(Path(config).read_text(encoding='utf-8-sig'));parts=program(c,profile)
    xml=Exporter().xml(*parts);ino=xml_to_ino(xml)
    out=Path(out);out.mkdir(parents=True,exist_ok=True);stem=out.name
    (out/(stem+'.xml')).write_text(xml,encoding='utf-8',newline='\n')
    (out/(stem+'.ino')).write_text(ino,encoding='utf-8',newline='\n')
    report={'profile':profile,'drive_armed':bool(not profile=='capture' and parts[0]['configReady'][1]),
        'physical_acceptance':False,'telemetry_header':HEADER,
        'config_sha256':hashlib.sha256(Path(config).read_bytes()).hexdigest(),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'codegen_sha256':hashlib.sha256((ROOT/'blockly_codegen.py').read_bytes()).hexdigest(),
        'xml_sha256':hashlib.sha256(xml.encode()).hexdigest(),'ino_sha256':hashlib.sha256(ino.encode()).hexdigest()}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=ROOT/'config.json')
    p.add_argument('--profile',choices=['capture','track'],default='track');p.add_argument('--out',type=Path,default=ROOT/'firmware/practice_controller')
    p.add_argument('--from-xml',type=Path);a=p.parse_args()
    if a.from_xml:
        a.out.mkdir(parents=True,exist_ok=True)
        (a.out/(a.out.name+'.ino')).write_text(xml_to_ino(a.from_xml.read_text(encoding='utf-8-sig')),encoding='utf-8',newline='\n')
    else:print(json.dumps(build(a.config,a.out,a.profile),indent=2))
