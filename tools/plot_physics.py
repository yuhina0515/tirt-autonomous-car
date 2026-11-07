"""Plot saved simulation traces. Requires matplotlib; never connects to a car."""
import argparse
import csv
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('results',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--python-libs',type=Path,help='Optional local matplotlib package directory')
    p.add_argument('--candidate-label',default='Gentle acceleration (trial)')
    args=p.parse_args()
    if args.python_libs:sys.path.insert(0,str(args.python_libs.resolve()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data=json.loads(args.results.read_text())
    folder=args.results.parent
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    colors=['#2563eb','#e67700']
    names=['simplified','generated_candidate']
    labels=['Simplified baseline',args.candidate_label]
    ax=axes[0,0]
    outcomes=['reached','fault','false_marker','escaped','timeout']
    shades=['#15803d','#dc2626','#a855f7','#e67700','#94a3b8']
    for i,name in enumerate(names):
        rows=[r for r in data['results'] if r['model']==name]
        left=0
        for outcome,color in zip(outcomes,shades):
            count=sum(r['outcome']==outcome for r in rows)
            ax.barh(i,count,left=left,color=color,label=outcome if i==0 else None)
            if count>4:ax.text(left+count/2,i,str(count),ha='center',va='center',color='white',fontsize=9)
            left+=count
    ax.set_yticks([0,1],labels);ax.set_xlabel('Synthetic cases (not probability)')
    ax.set_title('Different-seed batch, shared nominal case')
    ax.set_ylim(-.6,2.0)
    ax.legend(fontsize=7,ncol=3,loc='upper left')
    for name,label,color in zip(names,labels,colors):
        file=folder/(name+'-unchanged-wide_v60_left-0.csv')
        rows=list(csv.DictReader(file.open()))
        axes[0,1].plot([float(r['x']) for r in rows],[float(r['y']) for r in rows],color=color,label=label)
        straight=list(csv.DictReader((folder/(name+'-unchanged-straight-0.csv')).open()))
        t=[int(r['ms'])/1000 for r in straight]
        axes[1,0].plot(t,[float(r['left']) for r in straight],color=color,label=label)
        axes[1,1].plot(t,[(float(r['vl'])+float(r['vr']))/2 for r in straight],color=color,label=label)
    axes[0,1].plot([0,1.2,.75],[0,0,.779],color='#444',ls='--',lw=1,label='Synthetic guide line')
    axes[0,1].set(xlabel='x (m)',ylabel='y (m)',title='Nominal V-corner with synthetic white patch')
    axes[0,1].axis('equal');axes[0,1].legend(fontsize=7)
    axes[1,0].set(xlabel='Time (s)',ylabel='Left PWM command',title='Straight acceleration command')
    axes[1,1].set(xlabel='Time (s)',ylabel='Assumed chassis speed (m/s)',title='Motor lag and battery model response')
    for ax in axes.flat:ax.grid(alpha=.15)
    fig.suptitle('Assumed-plant simulation — no measured car calibration',fontsize=13,y=.985)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output,dpi=160,bbox_inches='tight',pad_inches=.18)
    print(args.output)


if __name__=='__main__':main()
