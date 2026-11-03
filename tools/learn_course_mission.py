"""Learn model-specific mission words from verified training observations only.

Station labels the lift offline. The compiled core receives ADC/time and literal
event words, never coordinates. Conservative source binding requires retraining
after any core/adapter edit, including edits confined to motor control.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

from course_world import Course
from course_referee import verify_sensor_trace,audit_trace
from simulation_model import Plant
from sim_native import ROOT, Controller, build

TOKENS={1:'W',2:'L',3:'R',4:'LIFT'}
MODELS=('tools/course_world.py','tools/simulation_model.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha(path):
    """Text identity portable across LF/CRLF; frozen manifests retain raw bytes."""
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def feature_identity(source):
    """Bind all event semantics conservatively; exclude only learned literals."""
    source=Path(source)
    text=source.with_name('controller.h').read_text(encoding='utf-8')
    text,n=re.subn(r'missionWordCount = \d+', 'missionWordCount = PROFILE',text)
    if n!=1:raise ValueError('mission count anchor changed')
    text,n=re.subn(r'// MISSION_TABLE_BEGIN.*?// MISSION_TABLE_END','// MISSION_TABLE',text,flags=re.S)
    if n!=1:raise ValueError('mission table anchors changed')
    if 'TIRT_JUNCTION_PREFIX' in text:
        text,n=re.subn(r'junctionWordCount = \d+', 'junctionWordCount = PROFILE',text)
        if n!=1:raise ValueError('junction count anchor changed')
        text,n=re.subn(r'// JUNCTION_TABLE_BEGIN.*?// JUNCTION_TABLE_END','// JUNCTION_TABLE',text,flags=re.S)
        if n!=1:raise ValueError('junction table anchors changed')
    return hashlib.sha256(source.read_bytes()+b'\0'+text.encode()).hexdigest()


def observable_events(rows):
    """Read actual-core events, after replay proves their ADC/time derivation."""
    previous=0;events=[]
    for row in rows:
        serial=int(row['eventSerial'])
        if serial==previous:continue
        if serial!=previous+1 or not int(row['ticked']):raise ValueError('invalid event serial')
        code=int(row['eventCode'])
        if code not in (1,2,3):raise ValueError('invalid observed token')
        events.append((code,row));previous=serial
    return events


def lift_observation(row,course,gate_events):
    """Teacher label from audited physical pose and ordered crossings only.

    Never consume the CSV station annotation: overlapping occurrences make it
    ambiguous, and changing an annotation must not change the training target.
    Unprofiled training observes the platform at its original upper landing.
    """
    point,yaw=course.at(course.lift_s)
    dx,dy=float(row['x'])-point[0],float(row['y'])-point[1]
    along=dx*math.cos(yaw)+dy*math.sin(yaw)
    across=-dx*math.sin(yaw)+dy*math.cos(yaw)
    required=sum(s<course.lift_s-course.lift_config['half_length_m'] for s in course.gates)
    crossed=sum(e['ms']<=int(row['ms']) for e in gate_events)
    return (crossed>=required and abs(along)<course.lift_config['half_length_m'] and
        abs(across)<course.assumptions['road_width_m']/2 and abs(float(row['z'])-point[2])<.03)


def stage_profile(source,directory,profile_path,course_hash):
    source=Path(source);directory=Path(directory)
    profile=json.loads(Path(profile_path).read_text(encoding='utf-8'))
    if profile['course_sha256']!=course_hash:raise ValueError('mission belongs to a different course hypothesis')
    if feature_identity(source)!=profile['feature_sha256']:raise ValueError('mission core/event semantics changed; retraining required')
    if set(profile['sensor_model_sha256'])!=set(MODELS):raise ValueError('incomplete mission model identity')
    model_hash=canonical_sha if profile.get('model_hash_encoding')=='utf8_lf' else sha
    for name,digest in profile['sensor_model_sha256'].items():
        if model_hash(ROOT/name)!=digest:raise ValueError('mission sensor/world model changed: '+name)
    words=profile['words'];mapping={v:k for k,v in TOKENS.items()}
    if not 1<=len(words)<=4:raise ValueError('one to four explicit mission hypotheses required')
    if any(not 1<=len(w)<=30 or w[-1]!='LIFT' or any(t not in mapping or t=='LIFT' and i!=len(w)-1 for i,t in enumerate(w)) for w in words):
        raise ValueError('invalid mission event word')
    header=source.with_name('controller.h').read_text(encoding='utf-8')
    if 'TIRT_MISSION_PREFIX' not in header:raise ValueError('experimental event-prefix core required')
    if header.count('missionWordCount = 0')!=1:raise ValueError('source must be an unprofiled core')
    header=header.replace('missionWordCount = 0','missionWordCount = '+str(len(words)))
    cases=[]
    for i,word in enumerate(words):
        values=','.join(str(mapping[t]) for t in word)
        cases.append('case %d:{static const uint8_t word[]={%s};return at<sizeof(word)?word[at]:0;}'%(i,values))
    begin=header.index('// MISSION_TABLE_BEGIN')+len('// MISSION_TABLE_BEGIN')
    end=header.index('// MISSION_TABLE_END',begin)
    header=header[:begin]+'\n        switch(hypothesis){'+''.join(cases)+'}return 0;\n        '+header[end:]
    junctions=profile.get('junctions',[])
    if not isinstance(junctions,list) or len(junctions)>4:raise ValueError('invalid junction hypotheses')
    if 'TIRT_JUNCTION_PREFIX' in header and header.count('junctionWordCount = 0')!=1:
        raise ValueError('source must have an unprofiled junction table')
    if junctions:
        if 'TIRT_JUNCTION_PREFIX' not in header:raise ValueError('source does not support junction context')
        header=header.replace('junctionWordCount = 0','junctionWordCount = '+str(len(junctions)))
        cases=[]
        for i,j in enumerate(junctions):
            if (not isinstance(j,dict) or set(j)!=set(('word','turn')) or j['turn'] not in ('L','R') or
                not isinstance(j['word'],list) or not 1<=len(j['word'])<=30 or j['word'][-1]!='W' or
                any(t not in ('L','R','W') for t in j['word'])):raise ValueError('invalid junction word/action')
            values=','.join(str(mapping[t]) for t in [j['turn']]+j['word'])
            cases.append('case %d:{static const uint8_t word[]={%s};return at<sizeof(word)?word[at]:0;}'%(i,values))
        begin=header.index('// JUNCTION_TABLE_BEGIN')+len('// JUNCTION_TABLE_BEGIN')
        end=header.index('// JUNCTION_TABLE_END',begin)
        header=header[:begin]+'\n        switch(hypothesis){'+''.join(cases)+'}return 0;\n        '+header[end:]
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'controller.h').write_text(header,encoding='utf-8')
    shutil.copy2(source,directory/source.name)
    return directory/source.name


def learn(directories,source=None,progress=None):
    words=set();provenance=[];rejected=[];course_hash=models=feature=None
    replacement=None;replacement_hash=None
    if source is not None:
        source=Path(source)
        if source.with_name('controller.h').read_text().count('missionWordCount = 0')!=1:
            raise ValueError('replacement must be an unprofiled observation core')
        replacement_feature=feature_identity(source)
        replacement_dir=ROOT/'build-output/control-recovery/prefix-revalidation'/replacement_feature
        dll,replacement_hash=build(source,replacement_dir/'host');replacement=Controller(dll)
    for folder in map(Path,directories):
        results=json.loads((folder/'results.json').read_text(encoding='utf-8'))
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        if sha(folder/'manifest.json')!=results['manifest_sha256']:raise ValueError('manifest changed')
        if results['source_sha256']!=manifest['source_hash']:raise ValueError('result source identity changed')
        digest=sha(folder/'course.json')
        if digest!=manifest['course_sha256']:raise ValueError('frozen course changed')
        if results['course_sha256']!=digest:raise ValueError('result course identity changed')
        if course_hash is not None and course_hash!=digest:raise ValueError('mixed course hypotheses')
        course_hash=digest
        frozen_models={n:canonical_sha(folder/'model'/n) for n in MODELS}
        for name,value in manifest['model_files'].items():
            if sha(folder/'model'/name)!=value:raise ValueError('frozen model changed: '+name)
        if models is not None and models!=frozen_models:raise ValueError('mixed training world/sensor models')
        if any(canonical_sha(ROOT/n)!=v for n,v in frozen_models.items()):raise ValueError('training model differs from current model')
        models=frozen_models
        source=folder/'host'/'sketch.inc'
        if source.with_name('controller.h').read_text().count('missionWordCount = 0')!=1:
            raise ValueError('training requires an unprofiled observation core')
        identity=feature_identity(source)
        if feature is not None and feature!=identity:raise ValueError('mixed training core/event identities')
        feature=identity
        dll,source_hash=build(source,folder/'learning-audit-host')
        if source_hash!=manifest['source_hash']:raise ValueError('frozen source changed')
        controller=Controller(dll)
        spec=json.loads((folder/'course.json').read_text(encoding='utf-8'));course=Course(spec)
        trials=manifest['trials']
        if [r['seed'] for r in results['attempts']]!=manifest['expected_seeds'] or len(trials)!=len(results['attempts']):
            raise ValueError('incomplete training batch')
        for trial,attempt in zip(trials,results['attempts']):
            if progress:progress('Auditing physical trace and sensor/core replay: seed='+str(attempt['seed']))
            if attempt['seed'] not in spec['timing']['seeds']:raise ValueError('held-out seeds cannot be used for training')
            if (trial['seed']!=attempt['seed'] or trial['plant']!=attempt['plant'] or
                trial['lift_duration_s']!=attempt['lift_duration_s'] or attempt['source_hash']!=source_hash or
                attempt['course_hash']!=digest or attempt['manifest_sha256']!=results['manifest_sha256']):
                raise ValueError('training trial differs from manifest')
            name=attempt['trace_file']
            if name!='seed-'+str(trial['seed'])+'.csv':raise ValueError('unexpected trace filename')
            path=folder/name;trace_hash=sha(path)
            if trace_hash!=attempt['trace_sha256']:raise ValueError('trace changed')
            physical=audit_trace(path,spec,Plant(**trial['plant']),trial['lift_duration_s'],trace_hash)
            verify_sensor_trace(path,controller,spec,Plant(**trial['plant']),trial['seed'],trial['lift_duration_s'])
            with path.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
            word=[];target=None
            for code,row in observable_events(rows):
                if code==1 and lift_observation(row,course,physical['gate_events']):
                    word.append('LIFT');target=row;break
                word.append(TOKENS[code])
            if target is None:
                rejected.append(dict(seed=attempt['seed'],trace_sha256=trace_hash,reason='model_lift_not_observed'));continue
            if replacement is not None:
                # Reuse a trajectory only if the revised actual core produces
                # identical commands, states and events through its audited
                # teacher target under regenerated physical ADC/time. Changes
                # after that prefix still require new full-course trials.
                prefix=replacement_dir/(trace_hash+'-prefix.csv')
                with prefix.open('w',newline='',encoding='utf-8') as f:
                    writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader()
                    writer.writerows(r for r in rows if int(r['ms'])<=int(target['ms']))
                verify_sensor_trace(prefix,replacement,spec,Plant(**trial['plant']),trial['seed'],trial['lift_duration_s'])
            words.add(tuple(word));provenance.append(dict(seed=attempt['seed'],source_sha256=source_hash,
                manifest_sha256=results['manifest_sha256'],trace_sha256=trace_hash,word=word,
                prefix_end_ms=int(target['ms']),revalidated_source_sha256=replacement_hash))
            if progress:progress('Verified training prefix: seed='+str(attempt['seed'])+' end_ms='+str(target['ms']))
    if not words:raise ValueError('no lift-labelled training prefix')
    if len(words)>4 or any(len(w)>30 for w in words):raise ValueError('observed mission exceeds fixed onboard capacity')
    return dict(status='hypothesis_specific_experiment_not_officially_verified',course_sha256=course_hash,
        feature_sha256=replacement_feature if replacement is not None else feature,
        feature_binding='entire core and adapter except learned literals; changes require fresh training or identical physical ADC/core/state/command replay through every audited training target',
        model_hash_encoding='utf8_lf',sensor_model_sha256=models,
        words=[list(w) for w in sorted(words)],training=provenance,rejected_training=rejected,
        note='Offline observer labels lift. Actual-core event diagnostics are verified from regenerated seeded ADC/time. Firmware receives literal words and ADC/time only.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('directories',nargs='+',type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--source',type=Path,help='Revalidate identical actual-core behavior through every training prefix before rebinding')
    args=p.parse_args();payload=learn(args.directories,args.source,
        progress=lambda message:print(message,file=sys.stderr,flush=True))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps({'words':payload['words'],'training_prefixes':len(payload['training']),'rejected':len(payload['rejected_training'])},indent=2))


if __name__=='__main__':main()
