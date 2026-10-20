"""Compare independently evaluated theoretical layouts; no architecture inference."""
import argparse,json,math
from pathlib import Path

CORE=('memory','card_local','ttft','tpot')
REQUIRED=CORE+('transfer','host','layout_support')

def integer(v,name,zero=False):
    if type(v) is not int or v < (0 if zero else 1):raise ValueError(name+' must be an integer in range')
    return v

def resources(layout):
    wid=layout.get('id')
    if not isinstance(wid,str) or not wid.strip():raise ValueError('layout id required')
    work=integer(layout.get('workGroups'),'workGroups')
    spare=integer(layout.get('spareGroups'),'spareGroups',True)
    p=integer(layout.get('prefillCardsPerGroup'),'prefillCardsPerGroup')
    d=integer(layout.get('decodeCardsPerGroup'),'decodeCardsPerGroup')
    return {'workCards':work*(p+d),'spareCards':spare*(p+d),'totalCards':(work+spare)*(p+d)}

def summarize(layout,evaluation):
    cards=resources(layout)
    if not isinstance(evaluation,dict):raise ValueError('evaluation must be an object')
    checks=evaluation.get('checks',{})
    if not isinstance(checks,dict):raise ValueError('checks must be an object')
    failures=[];unknown=[];normalized={}
    for key in REQUIRED:
        item=checks.get(key,{'ok':None,'reason':'Not evaluated'})
        if not isinstance(item,dict):raise ValueError('check must be an object: '+key)
        value=item.get('ok')
        if value is not None and type(value) is not bool:raise ValueError('ok must be true, false or null: '+key)
        reason=item.get('reason','')
        if not isinstance(reason,str):raise ValueError('reason must be text')
        basis=item.get('basis','')
        if not isinstance(basis,str):raise ValueError('basis must be text')
        # A bare success flag cannot turn missing evidence into a supported constraint.
        if value is True and (not reason.strip() or not basis.strip()):
            value=None;reason='Success lacked explanation or source/explicit assumption'
        normalized[key]=dict(item,ok=value,reason=reason)
        if value is False:failures.append(key+': '+reason)
        if value is None:unknown.append(key+': '+reason)
    state='rejected' if failures else 'incomplete' if any(normalized[k]['ok'] is None for k in CORE) else 'conditional' if unknown else 'budget_candidate'
    return {'id':layout['id'],'layout':layout,'cards':cards,'state':state,'checks':normalized,'metrics':evaluation.get('metrics',{}),'reasons':failures+unknown}

def compare_layouts(layouts,evaluator):
    seen=set();results=[]
    if not layouts:raise ValueError('At least one layout required')
    # Prevalidate before calculating to avoid a partially evaluated malformed batch.
    for layout in layouts:
        resources(layout)
        if layout['id'] in seen:raise ValueError('Duplicate layout id')
        seen.add(layout['id'])
    for layout in layouts:results.append(summarize(layout,evaluator(layout)))
    minima={}
    for state in ['budget_candidate','conditional']:
        eligible=[x for x in results if x['state']==state]
        lowest=min((x['cards']['totalCards'] for x in eligible),default=None)
        minima[state]={'minimumTotalCardsWithinEvaluatedSet':lowest,'layoutIds':[x['id'] for x in eligible if x['cards']['totalCards']==lowest]}
    return {'scope':'evaluated layouts only, not global minimum or measured feasibility','results':results,'minimaByEvidenceState':minima,'recommendedLayoutId':None,'finalCards':None}

def reject_nonfinite(value):raise ValueError('Non-finite JSON value is invalid: '+value)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    rows=json.loads(Path(a.input).read_text(encoding='utf-8'),parse_constant=reject_nonfinite)
    if not isinstance(rows,list):raise ValueError('Input must be an array')
    evaluations={row['layout']['id']:row['evaluation'] for row in rows}
    result=compare_layouts([row['layout'] for row in rows],lambda layout:evaluations[layout['id']])
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(result['minimaByEvidenceState'],ensure_ascii=False))

if __name__=='__main__':main()
