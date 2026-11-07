"""Explicitly transport a validated profile across uniform CRLF/LF only.

Raw frozen manifests/teacher receipts remain unchanged. No world value, policy,
model/source identity, trace or validation result is rewritten by this tool.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def digest(data):return hashlib.sha256(data).hexdigest()


def normalized(data):
    count=data.count(b'\r\n')
    if data.count(b'\r')!=count or count and data.count(b'\n')!=count:
        raise ValueError('only uniform CRLF or LF is accepted')
    return data.replace(b'\r\n',b'\n'),'CRLF' if count else 'LF'


def policy_identity(profile):
    data={k:v for k,v in profile.items() if k not in ('course_sha256','course_text_transfers')}
    return digest(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8'))


def transfer(profile,old_course,new_course):
    old=Path(old_course).read_bytes();new=Path(new_course).read_bytes()
    if profile.get('course_sha256')!=digest(old):raise ValueError('profile does not bind the old raw course')
    a,old_style=normalized(old);b,new_style=normalized(new)
    if a!=b:raise ValueError('course differs beyond line endings')
    if digest(old)==digest(new):raise ValueError('no course text transfer is necessary')
    if json.loads(old.decode('utf-8'))!=json.loads(new.decode('utf-8')):raise ValueError('parsed course changed')
    result=copy.deepcopy(profile);result['course_sha256']=digest(new)
    history=result.setdefault('course_text_transfers',[])
    if not isinstance(history,list):raise ValueError('invalid transfer history')
    history.append(dict(old_raw_sha256=digest(old),new_raw_sha256=digest(new),utf8_lf_sha256=digest(a),
        old_newlines=old_style,new_newlines=new_style,policy_payload_sha256=policy_identity(profile),
        method='uniform CRLF/LF only; all normalized UTF8 bytes and parsed JSON identical; raw teacher/manifests retained',
        tool_sha256=digest(Path(__file__).read_bytes())))
    if policy_identity(result)!=policy_identity(profile):raise ValueError('profile policy changed')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',required=True,type=Path);p.add_argument('--old-course',required=True,type=Path)
    p.add_argument('--new-course',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();result=transfer(json.loads(args.profile.read_text(encoding='utf-8')),args.old_course,args.new_course)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result['course_text_transfers'][-1]))


if __name__=='__main__':main()
