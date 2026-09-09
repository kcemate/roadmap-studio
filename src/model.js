/* Project validation and shared financial definitions. */
const MAX_PROJECT_BYTES=10*1024*1024;
function projectText(value,max=240){
  return (typeof value==='string'||typeof value==='number'?String(value):'').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'').slice(0,max);
}
function projectObject(value){return !!value&&typeof value==='object'&&!Array.isArray(value);}
function checkedMoney(value,label){
  if(value==null||value==='')return'';
  const n=parseMoney(value);
  if(n===''||n<0||n>1e15)throw new Error(`${label} must be a non-negative dollar amount.`);
  return n;
}
function checkedPercent(value,label,fraction=false){
  if(value==null||value==='')return'';
  const str=String(value).trim(),n=Number(str.replace(/%$/,''));
  if(!/^(?:\d+(?:\.\d*)?|\.\d+)%?$/.test(str)||!Number.isFinite(n))throw new Error(`${label} must be between 0% and 100%.`);
  const points=fraction&&!str.endsWith('%')?n*100:n;
  if(points<0||points>100)throw new Error(`${label} must be between 0% and 100%.`);
  return points;
}
function checkedDate(value,label,fyStart){
  if(value==null||value==='')return'';
  const d=parseAnyDate(value,'end',fyStart);
  if(!d||d.getUTCFullYear()<1900||d.getUTCFullYear()>2200)throw new Error(`${label} needs a valid date between 1900 and 2200.`);
  return isoDate(d);
}
function boundedList(value,max,label,optional=false){
  if(optional&&value==null)return[];
  if(!Array.isArray(value)||value.length>max)throw new Error(`${label} must be a list of at most ${max} entries.`);
  return value;
}
function stableProjectId(raw,prefix,map){
  if(typeof raw!=='string'||!raw.length||raw.length>1000)throw new Error('Every project record needs a valid identifier.');
  if(map.has(raw))return map.get(raw);
  let id=raw;
  if(!/^[A-Za-z][A-Za-z0-9_-]{0,79}$/.test(id)){
    let hash=2166136261;for(const ch of raw)hash=Math.imul(hash^ch.charCodeAt(0),16777619);
    id=prefix+'_'+(hash>>>0).toString(36);
  }
  const used=new Set(map.values());let suffix=1,base=id;
  while(used.has(id))id=base+'_'+suffix++;
  map.set(raw,id);return id;
}
function safePreference(value,depth=0){
  if(depth>5)return null;
  if(typeof value==='string')return projectText(value,500);
  if(typeof value==='number')return Number.isFinite(value)?value:0;
  if(typeof value==='boolean'||value==null)return value;
  if(Array.isArray(value))return value.slice(0,100).map(v=>safePreference(v,depth+1));
  if(!projectObject(value))return null;
  const out={};Object.entries(value).slice(0,100).forEach(([k,v])=>{
    if(/^[A-Za-z][\w-]{0,80}$/.test(k)&&!['__proto__','constructor','prototype'].includes(k))out[k]=safePreference(v,depth+1);
  });return out;
}
function sanitizeProject(raw){
  if(!projectObject(raw))throw new Error('Choose a Roadmap Studio project file.');
  if(raw.v!=null&&![1,2,3].includes(raw.v))throw new Error('This project uses an unsupported version. Keep the original file and open it in the matching app.');
  if(JSON.stringify(raw).length>MAX_PROJECT_BYTES)throw new Error('Project exceeds the 10 MB import limit.');
  const maps={p:new Map(),w:new Map(),i:new Map()},fraction=raw.percentageUnit==='fraction';
  function plan(source){
    if(!projectObject(source))throw new Error('A saved plan is invalid.');
    const fy=source.fyStart==null?6:Number(source.fyStart);
    if(!Number.isInteger(fy)||fy<0||fy>11)throw new Error('Fiscal start month is invalid.');
    const seenP=new Set(),seenW=new Set(),seenI=new Set(),wsP=new Map();
    const structure=boundedList(source.structure,100,'Pillars').map(p=>{
      if(!projectObject(p)||seenP.has(p.id))throw new Error('Pillar identifiers must be unique.');seenP.add(p.id);
      const id=stableProjectId(p.id,'p',maps.p);
      const workstreams=boundedList(p.workstreams,200,'Workstreams').map(w=>{
        if(!projectObject(w)||seenW.has(w.id))throw new Error('Workstream identifiers must be unique.');seenW.add(w.id);
        const wid=stableProjectId(w.id,'w',maps.w);wsP.set(w.id,p.id);
        return{id:wid,name:projectText(w.name)||'Untitled workstream'};
      });return{id,name:projectText(p.name)||'Untitled pillar',workstreams};
    });
    const items=boundedList(source.items,5000,'Initiatives').map(it=>{
      if(!projectObject(it)||seenI.has(it.id))throw new Error('Initiative identifiers must be unique.');seenI.add(it.id);
      const id=stableProjectId(it.id,'i',maps.i);
      if(!seenP.has(it.pillarId)||wsP.get(it.wsId)!==it.pillarId)throw new Error('An initiative references a missing pillar or workstream.');
      const milestone=it.milestone===true,start=checkedDate(it.start,'Start',fy),end=milestone?start:checkedDate(it.end,'End',fy);
      if(start&&end&&end<start)throw new Error('End must be on or after Start.');
      const phases=boundedList(it.phases,100,'Realization phases',true).map(ph=>{
        if(!projectObject(ph))throw new Error('A realization phase is invalid.');
        const date=checkedDate(ph.date,'Phase',fy),pct=checkedPercent(ph.pct,'Phase percentage',fraction);
        if(!date||pct==='')throw new Error('Every realization phase needs a date and percentage.');
        return{date,pct};
      }).sort((a,b)=>a.date.localeCompare(b.date));
      for(let n=1;n<phases.length;n++)if(phases[n].date===phases[n-1].date||phases[n].pct<phases[n-1].pct)throw new Error('Realization phases need unique dates and increasing cumulative percentages.');
      return{id,pillarId:maps.p.get(it.pillarId),wsId:maps.w.get(it.wsId),name:projectText(it.name)||'Untitled initiative',
        start,end,milestone,status:normStatus(it.status),approval:normApproval(it.approval,it.status),owner:projectText(it.owner,120),
        valueType:normValueType(it.valueType),value:checkedMoney(it.value,'Value'),includeInTotals:it.includeInTotals!==false,
        realizedPct:checkedPercent(it.realizedPct,'Realized percentage',fraction),confidence:it.confidence==null||it.confidence===''?100:/^(high|med|medium|low)$/i.test(String(it.confidence))?parseConfidence(it.confidence):checkedPercent(it.confidence,'Confidence',fraction),phases,
        actualValue:checkedMoney(it.actualValue,'Actual value'),actualAsOf:checkedDate(it.actualAsOf,'Actuals as-of',fy),cost:checkedMoney(it.cost,'Implementation cost'),
        benefitKind:it.benefitKind==='recurring'?'recurring':'one-time',valueBasis:it.benefitKind==='recurring'&&it.valueBasis==='annual'?'annual':'lifetime',
        recognitionMethod:['completion','upfront'].includes(it.recognitionMethod)?it.recognitionMethod:'linear',
        creditedToId:projectText(it.creditedToId,1000),exclusionReason:projectText(it.exclusionReason,500)};
    });
    const collapsed={};if(projectObject(source.collapsedPillars))Object.entries(source.collapsedPillars).forEach(([id,v])=>{
      if(v===true&&maps.p.has(id))collapsed[maps.p.get(id)]=true;
      if(v===true&&id.startsWith('owner:')&&id.length<150)collapsed[id]=true;
    });
    return{structure,items,fyStart:fy,collapsedPillars:collapsed,projectionEnd:checkedDate(source.projectionEnd,'Projection end',fy)||null,
      projectionTarget:checkedMoney(source.projectionTarget,'Portfolio goal'),stretchGoal:checkedMoney(source.stretchGoal,'Stretch goal')||'',projectionShowRealized:source.projectionShowRealized!==false,
      weightConfidence:source.weightConfidence!==false,asOfDate:checkedDate(source.asOfDate,'Reporting date',fy)};
  }
  const current=plan(raw),seenS=new Set();
  const scenarios=boundedList(raw.scenarios,50,'Scenarios',true).map((sc,n)=>{
    if(!projectObject(sc)||!projectObject(sc.payload))throw new Error('A scenario is invalid.');
    const id=/^[A-Za-z][\w-]{0,79}$/.test(sc.id)?sc.id:'scenario_'+n;
    if(seenS.has(id))throw new Error('Scenario identifiers must be unique.');seenS.add(id);
    return{id,name:projectText(sc.name,100)||`Scenario ${n+1}`,savedAt:Number(sc.savedAt)||0,payload:plan(sc.payload)};
  });
  const baseline=raw.baseline?{...plan(raw.baseline),savedAt:Number(raw.baseline.savedAt)||0}:null;
  const workingDraft=raw.workingDraft?plan(raw.workingDraft):null;
  [current,...scenarios.map(sc=>sc.payload),baseline,workingDraft].filter(Boolean).forEach(p=>p.items.forEach(it=>{
    if(it.creditedToId){if(!maps.i.has(it.creditedToId))throw new Error('A credited initiative reference is missing.');it.creditedToId=maps.i.get(it.creditedToId);if(it.creditedToId===it.id)throw new Error('An initiative cannot credit itself.');}
  }));
  const deletedIds=boundedList(raw.deletedIds,5000,'Deleted identifiers',true).map(id=>maps.i.get(id)||stableProjectId(id,'i',maps.i));
  const editDrafts={};if(projectObject(raw.editDrafts))Object.entries(raw.editDrafts).slice(0,5000).forEach(([rawId,fields])=>{
    const id=maps.i.get(rawId);if(!id||!projectObject(fields))return;
    const clean={};['name','owner','start','end','value','realizedPct','actualValue','actualAsOf'].forEach(k=>{if(typeof fields[k]==='string')clean[k]=projectText(fields[k],500);});
    editDrafts[id]=clean;
  });
  const widths={...DEFAULT_COL_WIDTHS};Object.keys(widths).forEach(k=>{const n=Number(raw.colWidths?.[k]);if(Number.isFinite(n)&&n>=48&&n<=600)widths[k]=n;});
  const f=projectObject(raw.filters)?raw.filters:{};
  let drawerDraft=null;
  if(raw.drawerDraft!=null){
    const draft=raw.drawerDraft;
    if(!projectObject(draft)||!projectObject(draft.values))throw new Error('An unfinished initiative draft is invalid.');
    const phases=boundedList(draft.phases,100,'Draft realization phases',true).map(ph=>{
      if(!projectObject(ph))throw new Error('A draft realization phase is invalid.');
      return{date:projectText(ph.date,30),pct:projectText(ph.pct,100)};
    });
    if(maps.i.has(draft.id))drawerDraft={id:maps.i.get(draft.id),values:safePreference(draft.values),phases};
  }
  return{v:3,percentageUnit:'points',...current,fileName:projectText(raw.fileName,160)||'Roadmap',savedAt:Number(raw.savedAt)||0,
    projectId:/^[\w-]{1,80}$/.test(raw.projectId)?raw.projectId:crypto.randomUUID(),scenarios,baseline,workingDraft,deletedIds,editDrafts,
    activeScenarioId:seenS.has(raw.activeScenarioId)?raw.activeScenarioId:null,showBaseline:raw.showBaseline!==false,
    drawerDraft,
    roadmapGroup:raw.roadmapGroup==='owner'?'owner':'structure',tableDensity:raw.tableDensity==='compact'?'compact':'comfortable',colWidths:widths,
    filters:{q:projectText(f.q),status:STATUSES.includes(f.status)?f.status:'',owner:projectText(f.owner,120),pillarId:maps.p.get(f.pillarId)||'',valueType:VALUE_TYPES.includes(f.valueType)?f.valueType:''},
    workspace:safePreference(raw.workspace)||{}};
}
function portfolioFinancialTotals(items=S.items,date=reportingDate()){
  const out={Total:0,Savings:0,Avoidance:0,Approved:0,Proposed:0,Realized:0,RealizedSavings:0,RealizedAvoidance:0,Undated:0,Excluded:0,Count:0,Cost:0,Net:0};
  items.forEach(it=>{
    const value=itemValue(it);if(!isIncludedInTotals(it)){out.Excluded+=value;return;}
    const type=normValueType(it.valueType),actual=realizedItemValue(it,date);
    out.Total+=value;out[type]+=value;out[approvalStatus(it)]+=value;out.Realized+=actual;out['Realized'+type]+=actual;out.Count++;out.Cost+=parseMoney(it.cost)||0;out.Net+=netBenefit(it);
    const start=projectionDateOf(it,'start'),end=it.milestone?start:projectionDateOf(it,'end');
    if(!start||!end||end<start)out.Undated+=value;
  });return out;
}
function netBenefit(it){return itemValue(it)-(parseMoney(it.cost)||0);}
function initiativeYears(it){
  const start=projectionDateOf(it,'start'),end=it.milestone?start:projectionDateOf(it,'end');
  if(!start||!end||end<start)return 0;
  const stop=addDays(end,1);let cursor=start,years=0;
  while(cursor<stop){
    const year=cursor.getUTCFullYear()+1,month=start.getUTCMonth(),day=Math.min(start.getUTCDate(),utc(year,month+1,0).getUTCDate());
    const next=utc(year,month,day),slice=Math.min(stop,next)-cursor;
    years+=slice/(next-cursor);cursor=next;
  }return years;
}
function invalidField(input,message){
  input.setAttribute('aria-invalid','true');input.setCustomValidity?.(message);input.title=message;
  showToast(message);return false;
}
function validateNumericInput(input,percent=false){
  const raw=input.value.trim();if(!raw)return true;
  try{percent?checkedPercent(raw.replace(/%$/,'').startsWith('.')?parsePercent(raw):raw,'Percentage'):checkedMoney(raw,'Value');}
  catch(error){return invalidField(input,error.message);}
  input.removeAttribute('aria-invalid');input.setCustomValidity?.('');return true;
}
function markDeleted(ids){S.deletedIds=[...new Set([...S.deletedIds,...ids])];ids.forEach(id=>delete S.editDrafts[id]);S.items.forEach(it=>{if(ids.includes(it.creditedToId))it.creditedToId='';});}
function saveWorkingScenario(){
  const payload=clonePlanPayload(),sc=S.scenarios.find(s=>s.id===S.activeScenarioId);
  if(sc){sc.payload=payload;sc.savedAt=Date.now();}else S.workingDraft=payload;
}
function rememberDraft(id,field,value){
  if(!id||!field)return;
  S.editDrafts[id]=S.editDrafts[id]||{};S.editDrafts[id][field]=value;
  scheduleSave();
}
function clearDraft(id,field){if(!S.editDrafts[id])return;delete S.editDrafts[id][field];if(!Object.keys(S.editDrafts[id]).length)delete S.editDrafts[id];}
function labelDrawerFields(){
  $('drawerBody').querySelectorAll('.drawer-field').forEach(field=>{const control=field.querySelector('input,select,textarea'),label=field.querySelector('label');if(control?.id&&label)label.htmlFor=control.id;});
  $('dPhases').querySelectorAll('tr').forEach((tr,n)=>{tr.querySelector('[data-ph=date]')?.setAttribute('aria-label',`Phase ${n+1} date`);tr.querySelector('[data-ph=pct]')?.setAttribute('aria-label',`Phase ${n+1} cumulative percentage`);tr.querySelector('[data-phdel]')?.setAttribute('aria-label',`Delete phase ${n+1}`);});
}
function stashDrawerDraft(){
  if(!S.drawerId)return;S.drawerDirty=true;
  const values={};$('drawerBody').querySelectorAll('input[id],select[id],textarea[id]').forEach(el=>{values[el.id]=el.type==='checkbox'?el.checked:el.value;});
  const phases=[...$('dPhases').querySelectorAll('tr')].filter(tr=>tr.querySelector('[data-ph]')).map(tr=>({date:tr.querySelector('[data-ph=date]').value,pct:tr.querySelector('[data-ph=pct]').value}));
  S.drawerDraft={id:S.drawerId,values,phases};scheduleSave();
}
document.addEventListener('keydown',event=>{
  if(event.key!=='Tab'||!S.drawerId)return;
  const controls=[...$('itemDrawer').querySelectorAll('button,input,select,textarea,[tabindex="0"]')].filter(el=>!el.disabled&&el.getClientRects().length);
  if(!controls.length)return;const first=controls[0],last=controls.at(-1),active=document.activeElement;
  if(event.shiftKey&&(active===first||!$('itemDrawer').contains(active))){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&(active===last||!$('itemDrawer').contains(active))){event.preventDefault();first.focus();}
});
function localRecoveryProjects(){try{return JSON.parse(localStorage.getItem('roadmapStudio.recovery.v1')||'[]');}catch{return[];}}
function backupCurrentProject(){
  try{const data=localStorage.getItem(LS_KEY);if(!data||data.length>2*1024*1024)return;
    const state=JSON.parse(data),versions=localRecoveryProjects();
    if(versions[0]?.data===data)return;
    versions.unshift({name:state.fileName||'Roadmap',date:Date.now(),data});
    while(versions.length>5||JSON.stringify(versions).length>2*1024*1024)versions.pop();
    localStorage.setItem('roadmapStudio.recovery.v1',JSON.stringify(versions));
  }catch{/* Primary autosave and recovery download remain authoritative. */}
}
function restoreRecovery(index){
  const version=localRecoveryProjects()[index];if(!version)return;
  if(!confirm(`Restore ${version.name}? The current saved project will be kept in recovery.`))return;
  try{const checked=sanitizeProject(JSON.parse(version.data));backupCurrentProject();deserializeInto(checked);enterStudio();autosave();showToast('Recovered project');}
  catch(error){showToast(error.message);}
}
