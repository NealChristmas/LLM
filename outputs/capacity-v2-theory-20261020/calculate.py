"""Pure theory adapter: reads only explicit config, structure and assumptions."""
import json,math,hashlib,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HELPER=ROOT/'tools'
sys.path.insert(0,str(HELPER))
import theory_math as tm
GIB=2**30

def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def calculate(request,model,config,a):
    tc=config['text_config'];n=tm.planned_concurrency(request['concurrency'],request['growthPercent'])
    assert request['scope']=='fixed_reference_layout_only' and request['load']=='balanced_burst_fcfs'
    assert request['prefixHitPercent']==0 and request['kvQuant']=='INT8_hypothetical'
    assert request['inputTokens']+request['outputTokens']<=tc['max_position_embeddings']
    groups=model['sourceCheckpointGroups']
    # Recover W8 expert data from packed FP4 logical counts; retain other native data precision.
    experts=sum(groups[k]['logicalTensorElements'] for k in ['main_routed_experts','draft_routed_experts'])
    dense=sum(groups[k]['nativePayloadBytes']-groups[k]['quantMetadataBytes'] for k in ['main_other','draft_other'])
    vision=groups['vision_and_aligner']['nativePayloadBytes']
    host=groups['engram_tables']['logicalTensorElements']*a['weightFactor']/GIB
    owners=tc['kv_source_layer_ids'];ratios=[tc['compress_ratios'][i] for i in owners]
    assert owners==[2,8,14,20] and all(x>0 for x in ratios)
    positions=sum(1/x for x in ratios)
    latent=tc['head_dim']+a['latentScaleBytesPerRow'];index=tc['index_head_dim']+a['indexScaleBytesPerRow']
    per_token=positions*(latent+index)
    fixed=(tc['num_hidden_layers']+tc['num_nextn_predict_layers'])*tc['sliding_window']*latent
    logical=per_token*(request['inputTokens']+request['outputTokens'])+fixed
    cache_budget=logical*a['cacheFactor']
    pin=tm.linear_work_top(request['inputTokens'],model['activeParameters']['prefill'])
    dout=tm.linear_work_top(1,model['activeParameters']['decode'])
    scenarios=[]
    for scene in a['scenarios']:
        phase={}
        for label in ['prefill','decode']:
            layout=a[label]
            assert layout['instances']*layout['cardsPerInstance']==layout['cards']
            assert layout['expertShards']==layout['cards']*a['chipsPerCard']
            busy=math.ceil(n/layout['instances'])
            chip_weight=(experts/layout['expertShards']+dense/layout['tensorParallel']*a['denseReplicationFactor']+vision)*a['weightFactor']/GIB
            chip_cache=busy*cache_budget/GIB
            chip_runtime=a['runtimeGiBPerCard']/a['chipsPerCard']
            chip_total=chip_weight+chip_cache+chip_runtime
            chip_capacity=a['nominalGBPerCard']*1e9/a['chipsPerCard']/GIB
            phase[label]={'physicalCards':layout['cards'],'inferenceInstances':layout['instances'],'busyRequestsPerInstance':busy,'effectiveTopsPerInstance':tm.effective_tops(layout['cardsPerInstance'],a['int8PeakTopsPerCard'],scene[label+'Efficiency']),'cardWeightGiB':chip_weight*a['chipsPerCard'],'cardCacheGiB':chip_cache*a['chipsPerCard'],'cardRuntimeGiB':a['runtimeGiBPerCard'],'cardTotalGiB':chip_total*a['chipsPerCard'],'cardCapacityGiB':chip_capacity*a['chipsPerCard'],'cardLocalCapacityWithinAssumption':chip_total<=chip_capacity,'memoryMapping':'uniform chip partition budget; not validated residency or allocation peak'}
        ttft=tm.burst_mean_ttft_ms(n,a['prefill']['instances'],pin,phase['prefill']['effectiveTopsPerInstance'],a['inputFixedMs'])
        tpot=phase['decode']['busyRequestsPerInstance']*dout*a['draftWorkFactor']/phase['decode']['effectiveTopsPerInstance']*1000+a['decodeFixedMs']
        ok=all(v['cardLocalCapacityWithinAssumption'] for v in phase.values()) and ttft<=request['ttftMs'] and tpot<=request['tpotMs']
        scenarios.append({'assumption':scene,'phase':phase,'meanTtftBudgetMs':ttft,'busyDecodeStepBudgetMs':tpot,'withinModeledConstraints':ok})
    center=next(s for s in scenarios if s['assumption']['name']=='中心预算假设')
    card_count=a['prefill']['cards']+a['decode']['cards']
    totals=tm.card_totals(1,card_count,request['spareGroups']) if center['withinModeledConstraints'] else None
    return {'method':'DeepSeek-V4.1 model-specific W8 + hypothetical INT8 cache theory/2.0','evaluationScope':'one fixed reference layout, not a global minimum search','plannedConcurrency':n,'inputWorkTopPerRequest':pin,'decodeWorkTopPerToken':dout,'meanPrefillCompletionOrder':tm.mean_fcfs_order(n,a['prefill']['instances']),'targetDataGroups':{'expertW8Bytes':experts,'denseRetainedBytes':dense,'visionRetainedBytes':vision},'cache':{'ownerLayers':owners,'compressionRatios':ratios,'positionMultiplier':positions,'hypotheticalGlobalBytesPerToken':per_token,'hypotheticalFixedSlidingBytes':fixed,'logicalBytesPerRequest':logical,'budgetBytesPerRequest':cache_budget,'implementationVerified':False},'hostEngramBudgetGiBPerNode':host,'scenarios':scenarios,'central':center,'budgetCards':totals,'unmodeledConditions':a['unverified'],'deploymentFeasibilityVerified':False,'measuredSloVerified':False,'globalMinimumCards':None,'finalCards':None}

def main():
    start=time.perf_counter();request,model,config,a=read('request.json'),read('model-input.json'),read('config.json'),read('assumptions.json')
    assert sha(ROOT/'config.json')==model['identity']['configSha256']
    r=calculate(request,model,config,a)
    r.update({'request':request,'identity':model['identity'],'assumptions':a,'inputHashes':{n:sha(ROOT/n) for n in ['request.json','model-input.json','config.json','assumptions.json']},'algorithmSha256':sha(Path(__file__)),'helperSha256':sha(HELPER/'theory_math.py'),'execution':{'performanceBaselineFilesRead':0,'networkRequests':0,'elapsedSeconds':time.perf_counter()-start}})
    (ROOT/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'physicalCards':r['budgetCards'],'ttftMs':r['central']['meanTtftBudgetMs'],'tpotApproxMs':r['central']['busyDecodeStepBudgetMs'],'baselineRead':0}))
if __name__=='__main__':main()
