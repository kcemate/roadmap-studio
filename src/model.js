/* Project validation, recovery, and edit-draft support. Financial definitions live in finance.js. */
const MAX_PROJECT_BYTES=10*1024*1024;
const MAX_DELETED_MARKERS=50000;
const BRAND_FONTS=['Arial','Calibri','Aptos','Helvetica','Georgia','Segoe UI','Verdana'];
const MAX_LOGO_CHARS=400*1024;
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
/* Typed percentages: validated like stored points, then read with the documented shorthand (0.5 = 50%). */
function checkedTypedPercent(raw,label){
  const s=String(raw??'').trim();if(!s)return'';
  checkedPercent(s.replace(/%$/,'').startsWith('.')?parsePercent(s):s,label);
  return parsePercent(s);
}
/* One date rule for input and loading: a valid calendar date between 1900 and 2200. Quarter labels resolve to the
   first day of the quarter for start dates and the last day for end dates. */
function checkedDate(value,label,fyStart,which='end'){
  if(value==null||value==='')return'';
  const d=parseAnyDate(value,which,fyStart);
  if(!d||d.getUTCFullYear()<1900||d.getUTCFullYear()>2200)throw new Error(`${label} needs a valid date between 1900 and 2200.`);
  return isoDate(d);
}
function boundedList(value,max,label,optional=false){
  if(optional&&value==null)return[];
  if(!Array.isArray(value)||value.length>max)throw new Error(`${label} must be a list of at most ${max} entries.`);
  return value;
}
function idRegistry(){ return{map:new Map(),used:new Set()}; }
function stableProjectId(raw,prefix,reg){
  if(typeof raw!=='string'||!raw.length||raw.length>1000)throw new Error('Every project record needs a valid identifier.');
  if(reg.map.has(raw))return reg.map.get(raw);
  let id=raw;
  if(!/^[A-Za-z][A-Za-z0-9_-]{0,79}$/.test(id)){
    let hash=2166136261;for(const ch of raw)hash=Math.imul(hash^ch.charCodeAt(0),16777619);
    id=prefix+'_'+(hash>>>0).toString(36);
  }
  let suffix=1;const base=id;
  while(reg.used.has(id))id=base+'_'+suffix++;
  reg.map.set(raw,id);reg.used.add(id);return id;
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
function sanitizeBrand(raw){
  if(!projectObject(raw))return{};
  const out={};
  if(typeof raw.accent==='string'&&/^#[0-9a-fA-F]{6}$/.test(raw.accent))out.accent=raw.accent.toUpperCase();
  if(BRAND_FONTS.includes(raw.font))out.font=raw.font;
  if(typeof raw.logo==='string'&&raw.logo.length<=MAX_LOGO_CHARS&&/^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/.test(raw.logo))out.logo=raw.logo;
  if(typeof raw.logoAspect==='number'&&Number.isFinite(raw.logoAspect)&&raw.logoAspect>.1&&raw.logoAspect<10)out.logoAspect=raw.logoAspect;
  return out;
}
function sanitizeExportPrefs(raw){
  const p=projectObject(raw)?raw:{};
  return{scope:p.scope==='current'?'current':'full',includeRegister:p.includeRegister===true,applyFilters:p.applyFilters===true,sinceReview:p.sinceReview!==false};
}
function sanitizeProject(raw,opts={}){
  if(!projectObject(raw))throw new Error('Choose a Roadmap Studio project file.');
  if(raw.v!=null&&![1,2,3].includes(raw.v))throw new Error('This project uses an unsupported version. Keep the original file and open it in the matching app.');
  if((opts.size??JSON.stringify(raw).length)>MAX_PROJECT_BYTES)throw new Error('Project exceeds the 10 MB import limit.');
  const maps={p:idRegistry(),w:idRegistry(),i:idRegistry()},fraction=raw.percentageUnit==='fraction';
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
      const milestone=it.milestone===true,start=checkedDate(it.start,'Start',fy,'start'),end=milestone?start:checkedDate(it.end,'End',fy,'end');
      if(start&&end&&end<start)throw new Error('End must be on or after Start.');
      const phases=boundedList(it.phases,100,'Realization phases',true).map(ph=>{
        if(!projectObject(ph))throw new Error('A realization phase is invalid.');
        const date=checkedDate(ph.date,'Phase',fy),pct=checkedPercent(ph.pct,'Phase percentage',fraction);
        if(!date||pct==='')throw new Error('Every realization phase needs a date and percentage.');
        return{date,pct};
      }).sort((a,b)=>a.date.localeCompare(b.date));
      for(let n=1;n<phases.length;n++)if(phases[n].date===phases[n-1].date||phases[n].pct<phases[n-1].pct)throw new Error('Realization phases need unique dates and increasing cumulative percentages.');
      // Unrecognized statuses load as Not Started and keep the original text so Review can flag them.
      const recognized=recognizeStatus(it.status),status=recognized||'Not Started';
      const importedStatus=recognized?(typeof it.importedStatus==='string'&&status==='Not Started'?projectText(it.importedStatus,60):''):projectText(it.status,60);
      const out={id,pillarId:maps.p.map.get(it.pillarId),wsId:maps.w.map.get(it.wsId),name:projectText(it.name)||'Untitled initiative',
        start,end,milestone,status,approval:normApproval(it.approval,status),owner:projectText(it.owner,120),
        valueType:normValueType(it.valueType),value:checkedMoney(it.value,'Value'),includeInTotals:it.includeInTotals!==false,
        realizedPct:checkedPercent(it.realizedPct,'Realized percentage',fraction),confidence:it.confidence==null||it.confidence===''?100:/^(high|med|medium|low)$/i.test(String(it.confidence))?parseConfidence(it.confidence):checkedPercent(it.confidence,'Confidence',fraction),phases,
        actualValue:checkedMoney(it.actualValue,'Actual value'),actualAsOf:checkedDate(it.actualAsOf,'Actuals as-of',fy),cost:checkedMoney(it.cost,'Implementation cost'),
        benefitKind:it.benefitKind==='recurring'?'recurring':'one-time',valueBasis:it.benefitKind==='recurring'&&it.valueBasis==='annual'?'annual':'lifetime',
        recognitionMethod:['completion','upfront'].includes(it.recognitionMethod)?it.recognitionMethod:'linear',
        creditedToId:projectText(it.creditedToId,1000),exclusionReason:projectText(it.exclusionReason,500),
        notes:projectText(it.notes,2000),nextStep:projectText(it.nextStep,240),decisionNeeded:projectText(it.decisionNeeded,500)};
      if(importedStatus)out.importedStatus=importedStatus;
      return out;
    });
    const collapsed={};if(projectObject(source.collapsedPillars))Object.entries(source.collapsedPillars).forEach(([id,v])=>{
      if(v===true&&maps.p.map.has(id))collapsed[maps.p.map.get(id)]=true;
      if(v===true&&id.startsWith('owner:')&&id.length<150)collapsed[id]=true;
    });
    const goal=checkedMoney(source.projectionTarget,'Portfolio goal'),stretch=checkedMoney(source.stretchGoal,'Stretch goal');
    return{structure,items,fyStart:fy,collapsedPillars:collapsed,projectionEnd:checkedDate(source.projectionEnd,'Projection end',fy)||null,
      projectionTarget:goal===''||goal<=0?'':goal,stretchGoal:stretch===''||stretch<=0?'':stretch,projectionShowRealized:source.projectionShowRealized!==false,
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
  // Exclusion links point within one plan. A link to an initiative that no longer exists is cleared, not fatal.
  [current,...scenarios.map(sc=>sc.payload),baseline,workingDraft].filter(Boolean).forEach(p=>{
    const ids=new Set(p.items.map(it=>it.id));
    p.items.forEach(it=>{
      if(!it.creditedToId)return;
      const mapped=maps.i.map.get(it.creditedToId);
      it.creditedToId=mapped&&mapped!==it.id&&ids.has(mapped)?mapped:'';
    });
  });
  const markerList=(list,reg,prefix,label)=>[...new Set(boundedList(list,MAX_DELETED_MARKERS,label,true).filter(id=>typeof id==='string'&&id.length&&id.length<=1000).map(id=>reg.map.get(id)||stableProjectId(id,prefix,reg)))];
  const deletedIds=markerList(raw.deletedIds,maps.i,'i','Deleted identifiers');
  const deletedStructureIds=[...new Set(boundedList(raw.deletedStructureIds,MAX_DELETED_MARKERS,'Deleted structure identifiers',true).filter(id=>typeof id==='string'&&id.length&&id.length<=1000).map(id=>maps.p.map.get(id)||maps.w.map.get(id)||(/^[A-Za-z][A-Za-z0-9_-]{0,79}$/.test(id)?id:null)).filter(Boolean))];
  const editDrafts={};if(projectObject(raw.editDrafts))Object.entries(raw.editDrafts).slice(0,5000).forEach(([rawId,fields])=>{
    const id=maps.i.map.get(rawId);if(!id||!projectObject(fields))return;
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
    if(maps.i.map.has(draft.id))drawerDraft={id:maps.i.map.get(draft.id),values:safePreference(draft.values),phases};
  }
  return{v:3,percentageUnit:'points',...current,fileName:projectText(raw.fileName,160)||DEFAULT_PROJECT_NAME,savedAt:Number(raw.savedAt)||0,
    projectId:/^[\w-]{1,80}$/.test(raw.projectId)?raw.projectId:crypto.randomUUID(),scenarios,baseline,workingDraft,deletedIds,deletedStructureIds,editDrafts,
    activeScenarioId:seenS.has(raw.activeScenarioId)?raw.activeScenarioId:null,showBaseline:raw.showBaseline!==false,
    drawerDraft,brand:sanitizeBrand(raw.brand),exportPrefs:sanitizeExportPrefs(raw.exportPrefs),
    roadmapGroup:raw.roadmapGroup==='owner'?'owner':'structure',tableDensity:raw.tableDensity==='compact'?'compact':'comfortable',colWidths:widths,
    filters:{q:projectText(f.q),status:STATUSES.includes(f.status)?f.status:'',owner:projectText(f.owner,120),pillarId:maps.p.map.get(f.pillarId)||'',valueType:VALUE_TYPES.includes(f.valueType)?f.valueType:''},
    workspace:safePreference(raw.workspace)||{}};
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
function clearInvalid(input){ input.removeAttribute('aria-invalid');input.setCustomValidity?.('');input.removeAttribute('title'); }
function validateNumericInput(input,percent=false){
  const raw=input.value.trim();if(!raw){clearInvalid(input);return true;}
  try{percent?checkedPercent(raw.replace(/%$/,'').startsWith('.')?parsePercent(raw):raw,'Percentage'):checkedMoney(raw,'Value');}
  catch(error){return invalidField(input,error.message);}
  clearInvalid(input);return true;
}
/* Deletion markers stop a stored scenario or the working plan from bringing deleted work back. Markers are only
   needed while some stored plan still contains the identifier, so they are pruned to that set. */
function storedPlanIds(){
  const items=new Set(),structure=new Set();
  [...S.scenarios.map(sc=>sc.payload),S.workingDraft].filter(Boolean).forEach(p=>{
    (p.items||[]).forEach(it=>items.add(it.id));
    (p.structure||[]).forEach(pl=>{structure.add(pl.id);(pl.workstreams||[]).forEach(w=>structure.add(w.id));});
  });
  return{items,structure};
}
function markDeleted(ids,structureIdsRemoved=[]){
  const stored=storedPlanIds();
  S.deletedIds=[...new Set([...S.deletedIds,...ids])].filter(id=>stored.items.has(id));
  S.deletedStructureIds=[...new Set([...S.deletedStructureIds,...structureIdsRemoved])].filter(id=>stored.structure.has(id));
  ids.forEach(id=>delete S.editDrafts[id]);
  const gone=new Set(ids);S.items.forEach(it=>{if(gone.has(it.creditedToId))it.creditedToId='';});
}
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

/* ---------- local recovery ----------
   Up to five copies within a 2 MB budget, newest first. A new copy never evicts every older copy: when the budget
   cannot hold it, older copies stay and the user is told. The primary autosave always takes priority. */
const RECOVERY_KEY='roadmapStudio.recovery.v1',RECOVERY_BUDGET=2*1024*1024,RECOVERY_MAX=5;
function localRecoveryProjects(){try{const list=JSON.parse(localStorage.getItem(RECOVERY_KEY)||'[]');return Array.isArray(list)?list.filter(v=>v&&typeof v.data==='string'):[];}catch{return[];}}
function recoveryName(data){ const m=/"fileName":"((?:[^"\\]|\\.){0,320})"/.exec(data.slice(0,4000)); try{return m?JSON.parse(`"${m[1]}"`):DEFAULT_PROJECT_NAME;}catch{return DEFAULT_PROJECT_NAME;} }
function backupCurrentProject(){
  S.lastRecoveryNotice='';
  let data;try{data=localStorage.getItem(LS_KEY);}catch{return;}
  if(!data)return;
  if(data.length>RECOVERY_BUDGET){S.lastRecoveryNotice=`No local recovery copy was kept: the previous project is ${megabytes(data.length)}, above the ${megabytes(RECOVERY_BUDGET)} recovery budget. Download project files to keep backups.`;return;}
  const versions=localRecoveryProjects();
  if(versions[0]?.data===data)return;
  const keep=[{name:recoveryName(data),date:Date.now(),data}];let size=data.length;
  for(const v of versions){if(keep.length>=RECOVERY_MAX)break;if(size+v.data.length>RECOVERY_BUDGET)continue;keep.push(v);size+=v.data.length;}
  while(keep.length){
    try{localStorage.setItem(RECOVERY_KEY,JSON.stringify(keep));return;}
    catch{ if(keep.length===1)break; keep.pop(); }
  }
  S.lastRecoveryNotice='No local recovery copy was kept: browser storage is full. Download project files to keep backups.';
}
function restoreRecovery(index){
  const version=localRecoveryProjects()[index];if(!version)return;
  if(!confirm(`Restore ${version.name}? The current saved project will be kept in recovery.`))return;
  try{const checked=sanitizeProject(JSON.parse(version.data));backupCurrentProject();deserializeInto(checked,{sanitized:true});enterStudio();autosave();showToast('Recovered project');}
  catch(error){showToast(error.message);}
}
