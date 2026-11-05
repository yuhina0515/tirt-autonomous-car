"""Catalogue every directed segment of the frozen hypothesis, without tuning it."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from course_environment import Course

PHASES = [(0,18,'Start and central approach'),(18,33,'Raised crossing 1'),
          (33,75,'Central and left serpentine'),(75,95,'Raised crossing 2'),
          (95,105,'Left circular approach'),(105,119,'Raised crossing 3 and seesaw'),
          (119,142,'Upper-right loops'),(142,165,'Raised crossing 4 and lift'),
          (165,191,'Post-lift return'),(191,210,'TAIWAN sharp turns and finish')]


def intersection(a,b,c,d):
    u=(b[0]-a[0],b[1]-a[1]);v=(d[0]-c[0],d[1]-c[1]);w=(c[0]-a[0],c[1]-a[1])
    cross=lambda x,y:x[0]*y[1]-x[1]*y[0]
    det=cross(u,v)
    if abs(det)<1e-10:
        return None # collinear repetitions are catalogued separately
    t=cross(w,v)/det;q=cross(w,u)/det
    return (t,q) if 0<=t<=1 and 0<=q<=1 else None


def catalogue(spec):
    route_id=hashlib.sha256(json.dumps(spec['points_px'],separators=(',',':')).encode()).hexdigest()
    if route_id!='3aaab9f25fbfc354edba736d9d783cb05593e1cae8e69224b53c2331fbaa76e6':
        raise ValueError('Phase ranges are bound to the reviewed directed reconstruction')
    c=Course(spec);rows=[]
    for seg in c.main_segments:
        i=seg.index; phase=next(n for a,b,n in PHASES if a<=i<b)
        heading=math.atan2(seg.b[1]-seg.a[1],seg.b[0]-seg.a[0]);turn=0
        if i:
            old=c.main_segments[i-1];h=math.atan2(old.b[1]-old.a[1],old.b[0]-old.a[0])
            turn=math.degrees(math.atan2(math.sin(heading-h),math.cos(heading-h)))
        tags=[];strategies=[]
        if abs(turn)>=120:tags.append('acute_V');strategies.append('slow approach; ordered chosen-side capture; no early opposite-branch exit')
        elif abs(turn)>=60:tags.append('sharp_turn');strategies.append('reduce translation before bounded turn and confirmed return')
        elif abs(turn)>=10:tags.append('curve');strategies.append('continuous position PD; lower speed with increasing error')
        else:tags.append('straight');strategies.append('centered PD with bounded PWM and acceleration')
        zs=[c.height(seg.start+seg.length*k/20) for k in range(21)]
        if max(zs)-min(zs)>.005:tags.append('grade_transition');strategies.append('same observed-line control; traction/height remain physical constraints')
        if any(a['start_vertex']<=i<a['end_vertex'] for a in spec['raised_occurrences']):tags.append('raised_occurrence')
        overlaps=[]
        for other in c.main_segments:
            if abs(other.index-i)<=2:continue
            hit=intersection(seg.a,seg.b,other.a,other.b)
            if hit:
                s1=seg.start+hit[0]*seg.length;s2=other.start+hit[1]*other.length
                dz=abs(c.height(s1)-c.height(s2))
                overlaps.append(dict(segment=other.index,kind='separate_layer' if dz>.03 else 'same_layer_crossing'))
            elif min(other.project(*seg.a[:2])[0],other.project(*seg.b[:2])[0])<.001:
                overlaps.append(dict(segment=other.index,kind='shared_or_endpoint_geometry'))
        if overlaps:tags.append('overlap');strategies.append('world resolves height; firmware must use observable context for any branch')
        paints=[]
        for j,(a,b) in enumerate(c.extra_paint):
            if intersection(seg.a,seg.b,a,b) or min(seg.project(*a)[0],seg.project(*b)[0])<.02:paints.append(j)
        if paints:tags.append('extra_paint');strategies.append('bounded ambiguity; broad/split alone cannot identify mission')
        for label,station,cfg in [('seesaw',c.seesaw_s,c.seesaw_config),('lift',c.lift_s,c.lift_config)]:
            if seg.start<=station+cfg['half_length_m'] and seg.start+seg.length>=station-cfg['half_length_m']:
                tags.append(label)
                strategies.append('PD through load change; no measured rollback/tipping feedback' if label=='seesaw' else 'bound observed prefix; stop31s; narrow exit100ms within1500ms')
        if i==198:tags.append('contextual_right');strategies.append('bound post-lift R L W L R L R L W selects R at terminal W only')
        if i==0:tags.append('start');strategies.append('physical start crossing starts referee clock')
        if seg.start<=c.finish_s<seg.start+seg.length:tags.append('finish');strategies.append('physical referee finish crossing; reference has no onboard finish stop')
        rows.append(dict(segment=i,vertices=[i,i+1],phase=phase,from_px=spec['points_px'][i],to_px=spec['points_px'][i+1],
            model_start_m=round(seg.start,4),model_end_m=round(seg.start+seg.length,4),turn_deg=round(turn,2),
            tags=tags,strategies=strategies,overlaps=overlaps,extra_paint=paints))
    return dict(status='inferred_route_analysis_not_official_layout',vertices=len(c.points),segments=len(rows),gates=len(c.gates),
        model_length_m=c.length,phases=[dict(start=a,end=b,name=n) for a,b,n in PHASES],segments_analysis=rows,
        known_unmodelled=['arbitrary competition lettering','explicit dashed/gap intervals (not encoded in this route)',
                         'on-site mechanism placement variants','complete rigid-body/tipping/contact','measured tire slip/torque',
                         'actual shortcut action (disabled; full A apex followed)','verified F meaning and official exits',
                         'onboard physical finish crossing detection'],ambiguities=spec['ambiguities'],
        counts=dict(Counter(tag for row in rows for tag in row['tags'])))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--course',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=catalogue(json.loads(a.course.read_text(encoding='utf-8')))
    report['course_sha256']=hashlib.sha256(a.course.read_bytes()).hexdigest()
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'scenarios.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['# Complete directed scenario catalogue','',
        'All lengths, directions, layers and task placements below belong to the inferred model, not surveyed official geometry. Segment IDs are zero-based. Strategies are analysis annotations; firmware does not receive segment IDs or coordinates.','',
        '| Segment / vertices | Phase | Model m | Turn deg | Situations | Response / limitation |','|---|---|---|---|---|---|']
    for r in report['segments_analysis']:
        lines.append(f"| {r['segment']} / {r['vertices'][0]}->{r['vertices'][1]} | {r['phase']} | {r['model_start_m']}..{r['model_end_m']} | {r['turn_deg']} | {', '.join(r['tags'])} | {'; '.join(r['strategies'])} |")
    lines+=['','## Unmodelled / unresolved']+['- '+s for s in report['known_unmodelled']+report['ambiguities']]
    (a.output/'SCENARIOS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Independent static scientific route plot, not an edited official image.
    import fitz
    colors=['#2563eb','#dc2626','#16a34a','#9333ea','#ea580c','#0891b2','#be185d','#4f46e5','#65a30d','#a16207']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="1300" viewBox="0 0 1240 1300">',
           '<rect width="1240" height="1300" fill="white"/>',
           '<text x="40" y="40" font-size="24">Directed course hypothesis: 210 segments / 10 phases</text>',
           '<text x="40" y="72" font-size="18">Not verified official geometry; numbers mark phase starts.</text>']
    points=report['segments_analysis']
    for n,phase in enumerate(report['phases']):
        xy=[points[phase['start']]['from_px']]+[r['to_px'] for r in points[phase['start']:phase['end']]]
        coords=' '.join(str(x)+','+str(y) for x,y in xy)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{colors[n]}" stroke-width="4"/>')
        x,y=xy[0];parts.append(f'<circle cx="{x}" cy="{y}" r="15" fill="white" stroke="{colors[n]}"/>')
        parts.append(f'<text x="{x-7}" y="{y+6}" font-size="18">{n+1}</text>')
        parts.append(f'<text x="40" y="{1090+n*18}" fill="{colors[n]}" font-size="15">{n+1}: {phase["start"]}..{phase["end"]} {phase["name"]}</text>')
    spec=json.loads(a.course.read_text(encoding='utf-8'))
    markers=[(points[0]['from_px'],'START'),(spec['mechanisms']['seesaw']['near_px'],'SEESAW'),
             (spec['mechanisms']['lift']['near_px'],'LIFT'),(points[198]['from_px'],'CONTEXT R'),(points[209]['from_px'],'FINISH')]
    for (x,y),label in markers:
        parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="black"/><text x="{x+18}" y="{y-18}" font-size="18">{label}</text>')
    parts.append('</svg>');svg=''.join(parts).encode()
    (a.output/'route-phases.svg').write_bytes(svg)
    doc=fitz.open(stream=svg,filetype='svg');doc.get_page_pixmap(0).save(a.output/'route-phases.png')
    print(json.dumps({k:report[k] for k in ('vertices','segments','gates','model_length_m','counts')},indent=2))


if __name__=='__main__':main()
