"""Create a dependency-free single INO for the practice candidate."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 source=ROOT/'firmware/race_two_marker';names=['motion_core.h','exit_motion.h','controller.h','race_two_marker.ino'];parts=[];hashes={}
 for name in names:
  f=source/name;hashes[name]=hashlib.sha256(f.read_bytes()).hexdigest();text=f.read_text(encoding='utf-8')
  text='\n'.join(line for line in text.splitlines() if line.strip() not in ['#pragma once','#include "motion_core.h"','#include "exit_motion.h"','#include "controller.h"'])
  parts.append('// BEGIN '+name+'\n'+text+'\n// END '+name)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text('// TIRT two-marker practice candidate. Hardware validation required.\n#include <Arduino.h>\n'+'\n'.join(parts)+'\n',encoding='utf-8')
 receipt=dict(source_hashes=hashes,ino_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),dependencies=[],uploaded=False)
 a.output.with_suffix('.manifest.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
