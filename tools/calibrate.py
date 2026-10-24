"""Propose per-sensor endpoints from explicitly labelled stationary captures."""
import argparse
import json
from pathlib import Path
import statistics
from analyze import load

def endpoints(line_path,background_path,config):
    line,*_=load(line_path);background,*_=load(background_path)
    line=[r for r in line if r['label']=='LINE'];background=[r for r in background if r['label']=='BACKGROUND']
    for samples in (line,background):
        if len(samples)<30:raise ValueError('At least 30 correctly labelled records per surface required')
        if any(r['state']!=6 or r['left_pwm'] or r['right_pwm'] for r in samples):
            raise ValueError('Calibration must use the motor-off capture profile')
    a=[];b=[];evidence=[]
    for k in ('rawA5','rawA4','rawA3','rawA2','rawA1'):
        x=sorted(r[k] for r in line);y=sorted(r[k] for r in background)
        medx=int(statistics.median(x));medy=int(statistics.median(y))
        # Require non-overlapping central 80% ranges, not only distinct means.
        xr=[x[len(x)//10],x[(len(x)*9)//10]];yr=[y[len(y)//10],y[(len(y)*9)//10]]
        if abs(medx-medy)<100 or not (xr[1]<yr[0] or yr[1]<xr[0]):
            raise ValueError(k+': low contrast or overlapping ranges; repeat physical measurement')
        a.append(medx);b.append(medy);evidence.append({'sensor':k,'line_p10_p90':xr,'background_p10_p90':yr})
    result=dict(config);result.update({'status':'MEASURED_ENDPOINTS_REVIEW_BEFORE_ARMING','calibration_measured':True,
        'drive_enabled':False,'line_adc_A5_to_A1':a,'background_adc_A5_to_A1':b})
    return result,{'line_records':len(line),'background_records':len(background),'ranges':evidence,
                   'note':'Review sensor placement, polarity and track surfaces; drive remains disabled.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--line',type=Path,required=True);p.add_argument('--background',type=Path,required=True)
    p.add_argument('--config',type=Path,default=Path(__file__).resolve().parents[1]/'config.json');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit('Refuse to overwrite measured configuration; choose a new output')
    result,evidence=endpoints(a.line,a.background,json.loads(a.config.read_text(encoding='utf-8-sig')))
    a.out.write_text(json.dumps(result,indent=2)+'\n');a.out.with_suffix('.evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
