/* ============ WORKSPACE: layouts, bulk edit, review, drilldown, paste ============ */
const WORKSPACE_COLUMNS=['name','pillar','ws','start','end','mile','status','approval','valueType','value','include','realized','confidence','owner'];
const WORKSPACE_BUILTIN_LAYOUTS=[
  {id:'all',name:'All columns',columns:WORKSPACE_COLUMNS},
  {id:'delivery',name:'Delivery review',columns:['name','pillar','ws','start','end','mile','status','approval','owner']},
  {id:'financial',name:'Financial review',columns:['name','pillar','approval','valueType','value','include','realized','confidence','owner']},
  {id:'planning',name:'Planning',columns:['name','pillar','ws','start','end','status','owner']}
];
const REVIEW_VIEWS=['exceptions','changes','compare','recovery'];
const workspaceSelection=new Set();
let workspaceReturnFocus=null,workspaceNormalized=null;

/* Saved preferences are normalized once per workspace object rather than on every render. */
function workspaceDefaults(){
  if(!S.workspace||typeof S.workspace!=='object')S.workspace={};
  const raw=S.workspace;
  if(workspaceNormalized===raw)return raw;
  if(!raw.sort||typeof raw.sort!=='object')raw.sort={key:'',dir:'asc'};
  if(!['asc','desc'].includes(raw.sort.dir))raw.sort.dir='asc';
  if(!WORKSPACE_COLUMNS.includes(raw.sort.key))raw.sort.key='';
  if(!Array.isArray(raw.layouts))raw.layouts=[];
  raw.layouts=raw.layouts.filter(layout=>layout&&typeof layout.name==='string'&&Array.isArray(layout.columns)).map(layout=>({
    id:textOf(layout.id)||`layout-${textOf(layout.name).toLowerCase().replace(/[^a-z0-9]+/g,'-')}`,
    name:textOf(layout.name).trim().slice(0,80),
    columns:layout.columns.filter(column=>WORKSPACE_COLUMNS.includes(column)),
    density:layout.density==='compact'?'compact':'comfortable',
    sort:layout.sort&&typeof layout.sort==='object'?{key:textOf(layout.sort.key),dir:layout.sort.dir==='desc'?'desc':'asc'}:{key:'',dir:'asc'}
  })).filter(layout=>layout.name&&layout.columns.length);
  if(!Array.isArray(raw.visibleColumns))raw.visibleColumns=[...WORKSPACE_COLUMNS];
  raw.visibleColumns=raw.visibleColumns.filter(column=>WORKSPACE_COLUMNS.includes(column));
  if(!raw.visibleColumns.length)raw.visibleColumns=[...WORKSPACE_COLUMNS];
  if(typeof raw.activeLayout!=='string')raw.activeLayout='all';
  if(!REVIEW_VIEWS.includes(raw.reviewView))raw.reviewView='exceptions';
  raw.reviewOpen=raw.reviewOpen===true;
  workspaceNormalized=raw;
  return raw;
}

function workspaceSortValue(item,key){
  if(key==='pillar')return pillarOf(item.pillarId)?.name||'';
  if(key==='ws')return wsOf(item.pillarId,item.wsId)?.name||'';
  if(key==='value')return itemValue(item);
  if(key==='realized')return realizedItemValue(item,reportingDate());
  if(key==='confidence')return parseConfidence(item.confidence);
  if(key==='approval')return approvalStatus(item);
  if(key==='valueType')return normValueType(item.valueType);
  if(key==='include')return isIncludedInTotals(item)?1:0;
  if(key==='mile')return item.milestone?1:0;
  if(key==='status')return STATUSES.indexOf(normStatus(item.status));
  if(key==='start'||key==='end'){
    const date=item[key] instanceof Date?item[key]:parseAnyDate(item[key],key,S.fyStart);
    return date&&Number.isFinite(date.getTime())?date.getTime():null;
  }
  return textOf(item[key]).trim();
}

function workspaceSortedItems(items){
  const sort=workspaceDefaults().sort;
  if(!sort.key)return items;
  const direction=sort.dir==='desc'?-1:1;
  return items.map((item,index)=>({item,index,value:workspaceSortValue(item,sort.key)})).sort((a,b)=>{
    const av=a.value,bv=b.value;
    if(av==null&&bv==null)return a.index-b.index;
    if(av==null)return 1;
    if(bv==null)return-1;
    let result=0;
    if(typeof av==='number'&&typeof bv==='number')result=av-bv;
    else result=String(av).localeCompare(String(bv),undefined,{numeric:true,sensitivity:'base'});
    return result?result*direction:a.index-b.index;
  }).map(row=>row.item);
}

function workspaceLayoutOptions(){
  const ws=workspaceDefaults(),layouts=[...WORKSPACE_BUILTIN_LAYOUTS,...ws.layouts];
  const custom=!layouts.some(layout=>layout.id===ws.activeLayout)?`<option value="custom" selected>Custom (unsaved)</option>`:'';
  return layouts.map(layout=>`<option value="${esc(layout.id)}" ${ws.activeLayout===layout.id?'selected':''}>${esc(layout.name)}</option>`).join('')+custom;
}

function workspaceColumnOptions(){
  return WORKSPACE_COLUMNS.map(column=>`<label><input type="checkbox" value="${column}" ${S.workspace.visibleColumns.includes(column)?'checked':''}>${esc(COLUMN_LABELS[column])}</label>`).join('');
}

function workspaceApplyLayout(id){
  const ws=workspaceDefaults();
  const layout=[...WORKSPACE_BUILTIN_LAYOUTS,...ws.layouts].find(entry=>entry.id===id);
  if(!layout)return;
  ws.activeLayout=layout.id;
  ws.visibleColumns=[...layout.columns];
  if(layout.density)S.tableDensity=layout.density;
  // Built-in layouts carry no sort, so choosing one returns the table to portfolio order.
  ws.sort=layout.sort?{...layout.sort}:{key:'',dir:'asc'};
  renderAll();
}

function workspaceSaveLayout(name){
  const ws=workspaceDefaults();
  const clean=textOf(name).trim().slice(0,80);
  if(!clean)return false;
  const existing=ws.layouts.find(layout=>layout.name.toLowerCase()===clean.toLowerCase());
  const layout={
    id:existing?.id||`layout-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,6)}`,
    name:clean,
    columns:[...ws.visibleColumns],
    density:S.tableDensity==='compact'?'compact':'comfortable',
    sort:{...ws.sort}
  };
  if(existing)Object.assign(existing,layout);else ws.layouts.push(layout);
  ws.activeLayout=layout.id;
  renderWorkspaceControls();
  scheduleSave();
  return true;
}

function visibleSelection(){ const visible=new Set(filteredItems().map(item=>item.id)); return S.items.filter(item=>workspaceSelection.has(item.id)&&visible.has(item.id)); }

function renderWorkspaceControls(){
  const ws=workspaceDefaults(),bar=$('workspaceTools');
  if(!bar)return;
  const visibleSelected=visibleSelection().length,hidden=workspaceSelection.size-visibleSelected;
  bar.querySelector('#wsLayout').innerHTML=workspaceLayoutOptions();
  const columnMenu=bar.querySelector('#wsColumnOptions');
  if(columnMenu&&!columnMenu.querySelector('input:focus'))columnMenu.innerHTML=workspaceColumnOptions();
  if($('wsAsOfDate')&&document.activeElement!==$('wsAsOfDate'))$('wsAsOfDate').value=isoDate(reportingDate());
  bar.querySelector('#wsSelectionCount').textContent=visibleSelected?`${visibleSelected} selected${hidden?` · ${hidden} hidden by filters (not edited)`:''}`:hidden?`${hidden} selected rows are hidden by filters`:'Select rows to edit';
  bar.querySelector('#wsBulkApply').disabled=!visibleSelected;
}

function workspaceBulkOptions(field){
  if(field==='status')return STATUSES;
  if(field==='approval')return APPROVAL_STATES;
  return [];
}

function configureBulkValue(){
  const field=$('wsBulkField')?.value||'status',select=$('wsBulkValue'),owner=$('wsBulkOwner');
  if(!select||!owner)return;
  const options=workspaceBulkOptions(field);
  select.hidden=field==='owner'; owner.hidden=field!=='owner';
  if(options.length)select.innerHTML=options.map(value=>`<option value="${esc(value)}">${esc(field==='approval'?approvalLabel(value):value)}</option>`).join('');
}

/* Bulk edits apply only to selected rows that are visible under the current filters. */
function applyWorkspaceBulk(){
  const field=$('wsBulkField')?.value,value=field==='owner'?$('wsBulkOwner')?.value.trim().slice(0,120):$('wsBulkValue')?.value;
  const targets=visibleSelection();
  if(!targets.length||!['owner','status','approval'].includes(field)||value==null)return;
  const previous=targets.map(item=>({id:item.id,value:item[field],importedStatus:item.importedStatus}));
  pushUndo();
  targets.forEach(item=>{ item[field]=field==='status'?normStatus(value):value; if(field==='status')delete item.importedStatus; });
  if(field==='owner')refreshOwners();
  workspaceSelection.clear();
  renderAll();
  // The toast's Undo reverses only this bulk field, keeping newer unrelated edits.
  showUndoToast(`${countLabel(targets.length,'initiative')} updated`,()=>{
    previous.forEach(entry=>{ const item=S.items.find(candidate=>candidate.id===entry.id); if(!item)return; item[field]=entry.value; if(entry.importedStatus)item.importedStatus=entry.importedStatus; });
    workspaceSelection.clear();
  });
}

function workspaceDate(value,which='end'){
  return value instanceof Date?value:parseAnyDate(value,which,S.fyStart);
}

/* ---------- Review: exceptions ---------- */
function workspaceExceptionGroups(){
  const asOf=reportingDate(),staleBefore=addDays(asOf,-90);
  const groups={
    missing:{title:'Missing inputs',hint:'Owner, dates, or financial value is missing, or dates are reversed.',items:[]},
    overdue:{title:'Overdue',hint:'End date passed before the reporting date.',items:[]},
    status:{title:'Needs a decision',hint:'Blocked, on hold, or an imported status that was not recognized.',items:[]},
    consistency:{title:'Inconsistent',hint:'Complete with nothing realized, Proposed with actuals, or actuals above plan.',items:[]},
    stale:{title:'Stale actuals',hint:'Recorded actuals have not been refreshed in 90 days.',items:[]},
    exclusion:{title:'Exclusion link',hint:'Excluded value needs a reason and a valid credited initiative.',items:[]}
  };
  S.items.forEach(item=>{
    const start=workspaceDate(item.start,'start'),end=item.milestone?start:workspaceDate(item.end,'end'),status=normStatus(item.status);
    const rawValue=parseMoney(item.value),value=itemValue(item);
    const missing=[],details=[];
    if(!textOf(item.owner).trim())missing.push('owner');
    if(!start)missing.push('start');
    if(!item.milestone&&!end)missing.push('end');
    if(rawValue==='')missing.push('value');
    if(missing.length)details.push(`Missing ${missing.join(', ')}`);
    const reversed=!!(start&&end&&end<start);
    if(reversed)details.push('End date precedes start date');
    if(item.benefitKind==='recurring'&&item.valueBasis==='annual'&&(!start||!end||reversed))details.push('Annual recurring value needs complete timing');
    if(details.length&&status!=='Cancelled')groups.missing.items.push({item,detail:details.join(' · ')});
    if(end&&!reversed&&end<asOf&&!['Complete','Cancelled'].includes(status))groups.overdue.items.push({item,detail:`Ended ${fmtDate(end)} · ${status}`});
    if(item.importedStatus)groups.status.items.push({item,detail:`Imported status “${item.importedStatus}” not recognized · loaded as ${status}`});
    else if(status==='Blocked'||status==='On Hold')groups.status.items.push({item,detail:`${status}${item.decisionNeeded?` · Decision: ${item.decisionNeeded}`:''}`});
    const realized=Math.max(0,realizedItemValue(item,asOf)),actual=parseMoney(item.actualValue);
    if(status==='Complete'&&value>0&&realized===0)groups.consistency.items.push({item,detail:'Complete, but nothing is realized'});
    if(approvalStatus(item)==='Proposed'&&actual!==''&&actual>0)groups.consistency.items.push({item,detail:`Proposed, but ${fmtMoneyShort(actual)} of actuals are recorded`});
    if(realized>value&&isIncludedInTotals(item))groups.consistency.items.push({item,detail:`Realized ${fmtMoneyShort(realized)} exceeds planned ${fmtMoneyShort(value)}`});
    const actualAsOf=workspaceDate(item.actualAsOf,'end');
    if(actual!==''&&(!actualAsOf||actualAsOf<staleBefore))groups.stale.items.push({item,detail:actualAsOf?`Actual as of ${fmtDate(actualAsOf)}`:'Actual has no as-of date'});
    if(item.includeInTotals===false){
      const target=S.items.find(candidate=>candidate.id===item.creditedToId),reason=textOf(item.exclusionReason).trim();
      if(!target||!reason||!isIncludedInTotals(target))groups.exclusion.items.push({item,detail:!reason&&!target?'Reason and credited initiative missing':!reason?'Reason missing':!target?'Credited initiative missing':'Credited initiative is also excluded'});
    }
  });
  return groups;
}
function exceptionCount(){ const ids=new Set();Object.values(workspaceExceptionGroups()).forEach(group=>group.items.forEach(row=>ids.add(row.item.id)));return ids.size; }

function exceptionRow(row,type){
  const value=itemValue(row.item);
  return `<button type="button" class="ws-review-row" data-exception-id="${esc(row.item.id)}">
    <span><b>${esc(row.item.name||'Untitled initiative')}</b><small>${esc(row.detail)}</small></span>
    <span>${esc(value?fmtMoneyShort(value):type==='missing'?'Needs input':'Review')}</span>
  </button>`;
}

function renderExceptions(){
  const groups=workspaceExceptionGroups();
  return `<div class="ws-exception-summary">${Object.entries(groups).map(([key,group])=>
    `<button type="button" data-jump-group="${key}"><b>${group.items.length}</b><span>${esc(group.title)}</span></button>`).join('')}</div>
    <div class="ws-review-groups">${Object.entries(groups).map(([key,group])=>`<section id="wsGroup-${key}" class="ws-review-group">
      <header><div><h4>${esc(group.title)}</h4><p>${esc(group.hint)}</p></div><span>${group.items.length}</span></header>
      ${group.items.length?group.items.map(row=>exceptionRow(row,key)).join(''):'<p class="ws-clear-state">No exceptions in this group.</p>'}
    </section>`).join('')}</div>`;
}

/* ---------- Review: since last review (baseline to current) ---------- */
function planItemDates(raw,fyStart){ const start=raw.start?parseAnyDate(raw.start,'start',fyStart):null; return{start,end:raw.milestone?start:(raw.end?parseAnyDate(raw.end,'end',fyStart):null)}; }
function sinceReviewData(){
  if(!S.baseline)return null;
  const base=new Map((S.baseline.items||[]).map(it=>[it.id,it])),now=new Map(S.items.map(it=>[it.id,it])),fy=S.baseline.fyStart??S.fyStart;
  const added=[],dropped=[],valueMoved=[],slipped=[],statusChanged=[];
  S.items.forEach(it=>{
    const before=base.get(it.id);
    if(!before){added.push({item:it,value:isIncludedInTotals(it)?itemValue(it):0});return;}
    const was=isIncludedInTotals(before)?itemValue(before):0,is=isIncludedInTotals(it)?itemValue(it):0;
    if(Math.abs(is-was)>=.005)valueMoved.push({item:it,before:was,after:is,delta:is-was});
    const b=planItemDates(before,fy),a=itemDates(it);
    if(b.end&&a.end&&a.end>b.end)slipped.push({item:it,before:b.end,after:a.end,days:Math.round((a.end-b.end)/MS_DAY)});
    else if(b.end&&!a.end)slipped.push({item:it,before:b.end,after:null,days:null});
    if(normStatus(before.status)!==normStatus(it.status))statusChanged.push({item:it,before:normStatus(before.status),after:normStatus(it.status)});
  });
  base.forEach((before,id)=>{ if(!now.has(id))dropped.push({item:before,value:isIncludedInTotals(before)?itemValue(before):0}); });
  const baseTotals=portfolioTotals(S.baseline.items||[]),nowTotals=portfolioTotals();
  valueMoved.sort((x,y)=>Math.abs(y.delta)-Math.abs(x.delta));slipped.sort((x,y)=>(y.days??1e9)-(x.days??1e9));
  return{savedAt:S.baseline.savedAt,added,dropped,valueMoved,slipped,statusChanged,before:baseTotals.Total,after:nowTotals.Total,delta:nowTotals.Total-baseTotals.Total};
}
function renderSinceReview(){
  const d=sinceReviewData();
  if(!d)return'<div class="ws-review-empty"><b>No baseline yet</b><span>Freeze a baseline after each review. This view then shows what was added, dropped, revalued, rescheduled, or changed status since.</span></div>';
  const list=(title,rows,detail)=>`<section class="ws-review-group"><header><div><h4>${esc(title)}</h4></div><span>${rows.length}</span></header>${rows.length?rows.map(row=>`<button type="button" class="ws-review-row" ${S.items.some(i=>i.id===row.item.id)?`data-exception-id="${esc(row.item.id)}"`:'disabled'}><span><b>${esc(row.item.name||'Untitled initiative')}</b><small>${esc(detail(row))}</small></span></button>`).join(''):'<p class="ws-clear-state">None.</p>'}</section>`;
  return`<div class="ws-compare-summary"><div><span>Baseline (${esc(new Date(d.savedAt||0).toLocaleDateString('en-US',{dateStyle:'medium'}))})</span><b>${esc(fmtMoneyShort(d.before))}</b></div><div><span>Now</span><b>${esc(fmtMoneyShort(d.after))}</b></div><div><span>Change in identified value</span><b>${d.delta>=0?'+':''}${esc(fmtMoneyShort(d.delta))}</b></div></div>
    <div class="ws-review-groups">${list('Added',d.added,r=>`${fmtMoneyShort(r.value)} identified`)}${list('Dropped',d.dropped,r=>`${fmtMoneyShort(r.value)} removed`)}${list('Value moved',d.valueMoved,r=>`${fmtMoneyShort(r.before)} → ${fmtMoneyShort(r.after)} (${r.delta>=0?'+':''}${fmtMoneyShort(r.delta)})`)}${list('Dates slipped',d.slipped,r=>r.after?`End ${fmtDate(r.before)} → ${fmtDate(r.after)} (+${r.days} days)`:`End ${fmtDate(r.before)} → not set`)}${list('Status changed',d.statusChanged,r=>`${r.before} → ${r.after}`)}</div>`;
}

/* ---------- Review: scenario comparison ---------- */
function scenarioRecord(id){
  if(id==='current')return{name:`Current: ${exportScenarioName()}`,payload:{items:S.items,projectionTarget:S.projectionTarget}};
  return S.scenarios.find(scenario=>scenario.id===id)||null;
}
function scenarioDateText(value,which){
  const date=workspaceDate(value,which);
  return date?fmtDate(date):'Undated';
}
function renderComparison(){
  const scenarios=S.scenarios;
  if(!scenarios.length)return'<div class="ws-review-empty"><b>No saved scenarios</b><span>Save scenarios to compare value, timing, approval, and goal gap.</span></div>';
  const ws=workspaceDefaults(),ids=['current',...scenarios.map(scenario=>scenario.id)];
  if(!ids.includes(ws.compareA))ws.compareA=scenarios[0]?.id||'current';
  if(!ids.includes(ws.compareB)||ws.compareB===ws.compareA)ws.compareB=ws.compareA==='current'?scenarios[0].id:'current';
  const optionHtml=selected=>ids.map(id=>{ const scenario=scenarioRecord(id); return`<option value="${esc(id)}" ${id===selected?'selected':''}>${esc(scenario?.name||id)}</option>`; }).join('');
  const a=scenarioRecord(ws.compareA),b=scenarioRecord(ws.compareB);
  const aItems=new Map((a?.payload?.items||[]).map(item=>[item.id,item])),bItems=new Map((b?.payload?.items||[]).map(item=>[item.id,item]));
  const idsUnion=[...new Set([...aItems.keys(),...bItems.keys()])];
  // Row values and summary totals use the same lifetime, included-only definition.
  const rowValue=item=>item&&isIncludedInTotals(item)?itemValue(item):0;
  const aTotal=portfolioTotals([...aItems.values()]).Total,bTotal=portfolioTotals([...bItems.values()]).Total;
  const goalOf=payload=>{const g=parseMoney(payload?.projectionTarget);return g!==''&&g>0?g:'';};
  const aGoal=goalOf(a?.payload),bGoal=goalOf(b?.payload);
  const delta=bTotal-aTotal,goalDelta=(bGoal||0)-(aGoal||0);
  const goalChange=aGoal===''&&bGoal===''?'No goal set':`${goalDelta>=0?'+':''}${fmtMoneyShort(goalDelta)}`;
  const goalNote=aGoal===''&&bGoal===''?'':`<small>${esc(aGoal===''?'No goal':fmtMoneyShort(aGoal))} → ${esc(bGoal===''?'No goal':fmtMoneyShort(bGoal))}</small>`;
  const goalGap=bGoal===''?'No goal set':bGoal>bTotal?`${fmtMoneyShort(bGoal-bTotal)} short`:`${fmtMoneyShort(bTotal-bGoal)} above`;
  const rows=idsUnion.map(id=>{
    const left=aItems.get(id),right=bItems.get(id),name=right?.name||left?.name||S.items.find(item=>item.id===id)?.name||'Untitled initiative';
    const leftValue=rowValue(left),rightValue=rowValue(right),diff=rightValue-leftValue;
    return`<tr><th scope="row">${esc(name)}</th><td>${esc(left?fmtMoneyShort(leftValue):'—')}</td><td>${esc(right?fmtMoneyShort(rightValue):'—')}</td><td class="ws-delta ${diff<0?'down':''}">${diff>=0?'+':''}${esc(fmtMoneyShort(diff))}</td>
      <td><small>Start ${esc(scenarioDateText(left?.start,'start'))} &rarr; ${esc(scenarioDateText(right?.start,'start'))}<br>End ${esc(scenarioDateText(left?.end,'end'))} &rarr; ${esc(scenarioDateText(right?.end,'end'))}</small></td>
      <td>${esc(left?approvalLabel(approvalStatus(left)):'—')} &rarr; ${esc(right?approvalLabel(approvalStatus(right)):'—')}</td></tr>`;
  }).join('');
  return `<div class="ws-compare-controls"><label>From<select id="wsCompareA">${optionHtml(ws.compareA)}</select></label><span aria-hidden="true">&rarr;</span><label>To<select id="wsCompareB">${optionHtml(ws.compareB)}</select></label></div>
    <div class="ws-compare-summary"><div><span>Portfolio change</span><b>${delta>=0?'+':''}${esc(fmtMoneyShort(delta))}</b></div><div><span>Goal change</span><b>${esc(goalChange)}</b>${goalNote}</div><div><span>Goal gap (To)</span><b>${esc(goalGap)}</b></div></div>
    <div class="ws-compare-table-wrap"><table class="ws-compare-table"><thead><tr><th>Initiative</th><th>From</th><th>To</th><th>Value delta</th><th>Timing</th><th>Approval</th></tr></thead><tbody>${rows||'<tr><td colspan="6">No initiatives in either scenario.</td></tr>'}</tbody></table></div>`;
}

function renderRecovery(){
  const versions=localRecoveryProjects();
  if(!versions.length)return'<div class="ws-review-empty"><b>No recovery versions</b><span>Roadmap Studio keeps bounded local versions before project replacement and recovery.</span></div>';
  return `<div class="ws-recovery-list">${versions.map((version,index)=>{
    const date=new Date(Number(version.date)||0),dateText=Number.isFinite(date.getTime())?date.toLocaleString('en-US',{dateStyle:'medium',timeStyle:'short'}):'Date unavailable';
    return`<div class="ws-recovery-row"><span><b>${esc(version.name||DEFAULT_PROJECT_NAME)}</b><small>${esc(dateText)} · ${esc(megabytes(version.data.length))} · Stored only in this browser</small></span><button type="button" class="btn" data-recovery-index="${index}">Restore</button></div>`;
  }).join('')}</div>`;
}

function renderWorkspaceReview(){
  const ws=workspaceDefaults(),review=$('workspaceReview'),body=$('workspaceReviewBody');
  if(!review||!body)return;
  review.hidden=!ws.reviewOpen;
  $('gridBody').hidden=ws.reviewOpen;
  // While Review is open, the grid's filters and bulk tools are hidden with the grid they act on.
  $('gridToolbar').classList.toggle('review-open',ws.reviewOpen);
  $('workspaceTools').hidden=ws.reviewOpen;
  $('wsReviewToggle').classList.toggle('on',ws.reviewOpen);
  $('wsReviewToggle').setAttribute('aria-expanded',String(ws.reviewOpen));
  review.querySelectorAll('[data-review-view]').forEach(button=>{
    const active=button.dataset.reviewView===ws.reviewView;
    button.classList.toggle('on',active); button.setAttribute('aria-selected',String(active)); button.tabIndex=active?0:-1;
  });
  if(!ws.reviewOpen){body.innerHTML='';return;}
  body.innerHTML=ws.reviewView==='compare'?renderComparison():ws.reviewView==='recovery'?renderRecovery():ws.reviewView==='changes'?renderSinceReview():renderExceptions();
  body.querySelectorAll('[data-exception-id]').forEach(button=>button.onclick=()=>openDrawer(button.dataset.exceptionId));
  body.querySelectorAll('[data-jump-group]').forEach(button=>button.onclick=()=>document.getElementById(`wsGroup-${button.dataset.jumpGroup}`)?.scrollIntoView({block:'nearest',behavior:'smooth'}));
  ['wsCompareA','wsCompareB'].forEach(id=>{ const select=$(id); if(select)select.onchange=()=>{ ws[id==='wsCompareA'?'compareA':'compareB']=select.value; renderWorkspaceReview(); scheduleSave(); }; });
  body.querySelectorAll('[data-recovery-index]').forEach(button=>button.onclick=()=>restoreRecovery(Number(button.dataset.recoveryIndex)));
}

/* ---------- financial drilldown ---------- */
function financialTargetSpec(target){
  const id=target.id||'',weighted=S.weightConfidence!==false;
  const map={
    execTotal:{title:'Total portfolio',metric:'planned'},rollupTotal:{title:'Total portfolio',metric:'planned'},stackCombinedTotal:{title:'Savings + Avoidance',metric:'planned'},
    projCombined:{title:'Projected Savings + Avoidance',metric:'projected',weighted},
    execApproved:{title:'Active value',metric:'planned',approval:'Approved'},rollupApproved:{title:'Active value',metric:'planned',approval:'Approved'},
    execProposed:{title:'Proposed value',metric:'planned',approval:'Proposed'},rollupProposed:{title:'Proposed value',metric:'planned',approval:'Proposed'},
    execRealized:{title:'Realized',metric:'actual'},rollupRealized:{title:'Realized',metric:'actual'},
    projSavings:{title:'Projected Savings',metric:'projected',type:'Savings',weighted},savingsTotal:{title:'Savings',metric:'planned',type:'Savings'},stackSavingsTotal:{title:'Savings',metric:'planned',type:'Savings'},
    projAvoidance:{title:'Projected Avoidance',metric:'projected',type:'Avoidance',weighted},avoidanceTotal:{title:'Avoidance',metric:'planned',type:'Avoidance'},
    projExpected:{title:weighted?'Projected, unweighted':'Projected, confidence-weighted',metric:'projected',weighted:!weighted},projAnnualized:{title:'Annual run-rate of recurring benefits',metric:'annualized',weighted},
    realizedSavingsTotal:{title:'Realized Savings',metric:'actual',type:'Savings'},realizedAvoidanceTotal:{title:'Realized Avoidance',metric:'actual',type:'Avoidance'}
  };
  if(map[id])return map[id];
  if(target.matches('.stack-segment'))return{title:'Pillar contribution',metric:'planned',pillarId:target.dataset.pillar,type:target.dataset.series==='savings'?'Savings':null};
  if(target.matches('.rollup-bar'))return{title:'Pillar contribution',metric:'planned',pillarId:target.dataset.pillar,approval:target.dataset.approval};
  if(target.matches('.exec-segment'))return{title:'Portfolio contribution',metric:target.dataset.stage==='realized'?'actual':'planned',approval:target.dataset.stage==='approved'?'Approved':target.dataset.stage==='proposed'?'Proposed':null,type:target.dataset.type};
  if(target.matches('#projectionHoverCombined,#projectionHoverSavings,#projectionHoverRealized'))return id.includes('Realized')?{title:'Realized at the projection end',metric:'actual'}:{title:'Projection at the selected end date',metric:'projected',weighted,type:id.includes('Savings')?'Savings':null};
  return null;
}

function drilldownMatches(item,spec){
  if(spec.type&&normValueType(item.valueType)!==spec.type)return false;
  if(spec.approval&&approvalStatus(item)!==spec.approval)return false;
  if(spec.pillarId&&item.pillarId!==spec.pillarId)return false;
  return true;
}

function drilldownValue(item,spec){
  if(spec.metric==='actual')return Math.max(0,realizedItemValue(item,reportingDate()));
  if(spec.metric==='expected')return itemValue(item)*parseConfidence(item.confidence)/100;
  if(spec.metric==='annualized')return annualizedValue(item)*(spec.weighted?parseConfidence(item.confidence)/100:1);
  if(spec.metric==='projected'){const fin=projectionFinancialItems([item],{weightConfidence:!!spec.weighted})[0];return fin?projectedValueAt(fin,selectedProjectionEnd()):0;}
  return itemValue(item);
}

function drilldownFormula(item,spec){
  if(spec.metric==='actual')return parseMoney(item.actualValue)!==''?'Recorded actual at its as-of date':'Fallback realized percentage or phase schedule';
  if(spec.metric==='expected')return'Lifetime planned value multiplied by confidence';
  if(spec.metric==='annualized')return`Recurring benefit normalized to a 365-day run rate${spec.weighted?', multiplied by confidence':''}`;
  const basis=item.valueBasis==='annual'?'annual input converted to initiative duration':'lifetime planned value';
  const recognition={linear:'recognized evenly across the date range',completion:'recognized at completion',upfront:'recognized at start'}[item.recognitionMethod]||'planned value';
  if(spec.metric==='projected')return`${basis}; ${recognition}; counted through ${fmtDate(selectedProjectionEnd())}${spec.weighted?'; multiplied by confidence':''}`;
  return`${basis}; ${recognition}`;
}

function drilldownRow(item,population,spec,showCosts=false){
  const value=drilldownValue(item,spec),pillar=pillarOf(item.pillarId)?.name||'Unassigned pillar';
  const cost=Math.max(0,parseMoney(item.cost)||0),net=netBenefit(item);
  return `<tr data-population="${population}"><th scope="row"><button type="button" data-drill-item="${esc(item.id)}">${esc(item.name||'Untitled initiative')}</button><small>${esc(pillar)} · ${esc(approvalLabel(approvalStatus(item)))}${exclusionLabel(item)?` · ${esc(exclusionLabel(item))}`:''}</small></th><td>${esc(fmtMoneyShort(value))}</td>${showCosts?`<td>${esc(fmtMoneyShort(cost))}</td><td>${esc(fmtMoneyShort(net))}</td>`:''}<td>${esc(drilldownFormula(item,spec))}</td></tr>`;
}

function openWorkspaceDrilldown(spec,trigger){
  const dialog=$('workspaceDrilldown'); if(!dialog||!spec)return;
  workspaceReturnFocus=trigger||document.activeElement;
  const matched=S.items.filter(item=>drilldownMatches(item,spec));
  const included=matched.filter(isIncludedInTotals),excluded=matched.filter(item=>!isIncludedInTotals(item));
  const undated=included.filter(isUndated);
  const showCosts=matched.some(item=>(parseMoney(item.cost)||0)>0);
  const reconciled=portfolioTotals(matched,reportingDate());
  const total=spec.metric==='planned'?(spec.type?reconciled[spec.type]:spec.approval?reconciled[spec.approval]:reconciled.Total):spec.metric==='actual'?(spec.type?reconciled['Realized'+spec.type]:reconciled.Realized):included.reduce((sum,item)=>sum+drilldownValue(item,spec),0),asOf=reportingDate();
  $('workspaceDrilldownTitle').textContent=spec.title;
  $('workspaceDrilldownBody').innerHTML=`<div class="ws-drill-summary"><div><span>Included total</span><b>${esc(fmtMoneyShort(total))}</b></div><p>As of ${esc(fmtDate(asOf))}</p></div>
    <p class="ws-formula"><b>Formula</b> Planned values use lifetime economics. Realized values are recorded actuals where entered, otherwise the realization schedule, and are never confidence-weighted. Excluded and Cancelled rows never enter the headline total.${spec.metric==='projected'?' Projected values count planned recognition through the selected projection end date; undated work cannot be projected.':''}${showCosts?' Net benefit equals lifetime planned value minus implementation cost.':''}</p>
    ${[['included','Included',included],['excluded','Excluded',excluded],['undated','Undated',undated]].map(([key,label,items])=>`<section class="ws-drill-group"><header><h4>${label}</h4><span>${items.length}</span></header>${items.length?`<table><thead><tr><th>Initiative</th><th>Value</th>${showCosts?'<th>Implementation cost</th><th>Net benefit</th>':''}<th>Calculation</th></tr></thead><tbody>${items.map(item=>drilldownRow(item,key,spec,showCosts)).join('')}</tbody></table>`:'<p>No initiatives in this population.</p>'}</section>`).join('')}`;
  dialog.querySelectorAll('[data-drill-item]').forEach(button=>button.onclick=()=>{ closeWorkspaceDrilldown(); openDrawer(button.dataset.drillItem); });
  if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');
  $('workspaceDrilldownClose').focus();
}

function closeWorkspaceDrilldown(){
  const dialog=$('workspaceDrilldown'); if(!dialog)return;
  if(typeof dialog.close==='function'&&dialog.open)dialog.close();else dialog.removeAttribute('open');
  if(workspaceReturnFocus?.isConnected)workspaceReturnFocus.focus();
  workspaceReturnFocus=null;
}

const DRILL_SELECTORS={
  exec:['#execTotal','#execApproved','#execProposed','#execRealized','.exec-segment'],
  rollup:['#rollupTotal','#rollupApproved','#rollupProposed','#rollupRealized','.rollup-bar'],
  proj:['#projSavings','#projAvoidance','#projCombined','#projExpected','#projAnnualized','#projectionHoverCombined','#projectionHoverSavings','#projectionHoverRealized'],
  stack:['#stackSavingsTotal','#stackCombinedTotal','.stack-segment'],
  road:['#savingsTotal','#avoidanceTotal','#realizedSavingsTotal','#realizedAvoidanceTotal']
};
function enhanceFinancialTargets(){
  const selectors=DRILL_SELECTORS[S.tab];if(!selectors)return;
  document.querySelectorAll(selectors.join(',')).forEach(target=>{
    const spec=financialTargetSpec(target); if(!spec)return;
    target.classList.add('ws-drill-target'); target.setAttribute('role','button'); target.setAttribute('tabindex','0'); target.setAttribute('aria-label',`Inspect ${spec.title.toLowerCase()} contributors`);
    if(target._workspaceDrillBound)return;
    target._workspaceDrillBound=true;
    const open=event=>{ if(event.type==='keydown'&&!['Enter',' '].includes(event.key))return; if(event.type==='keydown')event.preventDefault(); openWorkspaceDrilldown(financialTargetSpec(target),target); };
    target.addEventListener('click',open); target.addEventListener('keydown',open);
  });
}

function enhanceGrid(){
  workspaceDefaults();
  const table=$('initGrid');
  renderWorkspaceControls();
  if(!table)return;
  const headers=[...table.querySelectorAll('thead th')],rows=[...table.querySelectorAll('tbody tr[data-id]')];
  const hiddenIndexes=[];
  headers.forEach((header,index)=>{
    const key=header.dataset.col;
    if(!key)return;
    if(!header.querySelector('.ws-sort')){
      const label=[...header.childNodes].filter(node=>node.nodeType===Node.TEXT_NODE).map(node=>node.textContent).join('').trim();
      [...header.childNodes].filter(node=>node.nodeType===Node.TEXT_NODE).forEach(node=>node.remove());
      const button=document.createElement('button'); button.type='button'; button.className='ws-sort'; button.innerHTML=`<span>${esc(label)}</span><i aria-hidden="true"></i>`;
      button.onclick=()=>{ const sort=S.workspace.sort; sort.dir=sort.key===key&&sort.dir==='asc'?'desc':'asc'; sort.key=key; S.workspace.activeLayout='custom'; renderAll(); };
      header.insertBefore(button,header.firstChild);
    }
    const active=S.workspace.sort.key===key;
    header.setAttribute('aria-sort',active?(S.workspace.sort.dir==='desc'?'descending':'ascending'):'none');
    header.querySelector('.ws-sort').classList.toggle('on',active);
    const visible=S.workspace.visibleColumns.includes(key);
    header.hidden=!visible;
    if(!visible)hiddenIndexes.push(index);
  });
  const selectHead=headers[0];
  if(selectHead&&!$('wsSelectAll')){
    selectHead.innerHTML='<input type="checkbox" id="wsSelectAll" aria-label="Select all filtered initiatives">';
    $('wsSelectAll').onchange=()=>{
      table.querySelectorAll('tbody tr[data-id]').forEach(row=>$('wsSelectAll').checked?workspaceSelection.add(row.dataset.id):workspaceSelection.delete(row.dataset.id));
      enhanceGrid();
    };
  }
  let selectedVisible=0;
  rows.forEach(row=>{
    hiddenIndexes.forEach(index=>{if(row.children[index])row.children[index].hidden=true;});
    const cell=row.children[0];
    if(!cell.querySelector('[data-ws-select]')){
      const number=cell.textContent.trim();
      cell.innerHTML=`<div class="ws-row-selector"><input type="checkbox" data-ws-select aria-label="Select ${esc(row.querySelector('[data-f=name]')?.value||'initiative')}"><span>${esc(number)}</span></div>`;
      cell.querySelector('[data-ws-select]').onchange=event=>{ event.target.checked?workspaceSelection.add(row.dataset.id):workspaceSelection.delete(row.dataset.id); enhanceGrid(); };
    }
    const checked=workspaceSelection.has(row.dataset.id);
    cell.querySelector('[data-ws-select]').checked=checked;if(checked)selectedVisible++;
  });
  if($('wsSelectAll')){
    $('wsSelectAll').checked=!!rows.length&&selectedVisible===rows.length;
    $('wsSelectAll').indeterminate=selectedVisible>0&&selectedVisible<rows.length;
  }
}

function enhanceDrawer(){
  const drawer=$('itemDrawer'); if(!drawer||drawer.getAttribute('aria-hidden')==='true')return;
  drawer.setAttribute('aria-modal','true'); drawer.setAttribute('aria-labelledby','drawerTitle');
  drawer.querySelectorAll('.drawer-field').forEach((field,index)=>{
    const label=field.querySelector('label'),control=field.querySelector('input,select,textarea');
    if(!label||!control)return;
    if(!control.id)control.id=`workspaceDrawerField${index}`;
    label.htmlFor=control.id;
  });
}

/* The Initiatives tab badge counts initiatives with at least one Review exception. */
function renderReviewBadge(){
  const count=S.view==='studio'?exceptionCount():0,tab=$('segData');
  if(count)tab.dataset.badge=String(count);else delete tab.dataset.badge;
  $('reviewBadgeText').textContent=count?`${countLabel(count,'initiative')} need review`:'';
  $('wsReviewToggle')?.setAttribute('aria-label',count?`Review (${countLabel(count,'initiative')} with exceptions)`:'Review');
}

function refreshWorkspace(){
  const ws=workspaceDefaults();
  [...workspaceSelection].forEach(id=>{ if(!S.items.some(item=>item.id===id))workspaceSelection.delete(id); });
  if(S.tab==='data'){renderWorkspaceReview();}
  enhanceFinancialTargets();
  renderReviewBadge();
  return ws;
}

/* ---------- paste rows from a spreadsheet (clipboard only; no file import) ---------- */
const PASTE_HEADERS={name:['initiative','name','initiative name','title'],pillar:['pillar'],ws:['workstream','work stream','stream'],start:['start','start date'],end:['end','end date','finish'],
  status:['status'],approval:['approval','active/proposed','stage'],valueType:['type','value type','savings / avoidance','savings/avoidance'],value:['value','$ value','amount','dollar value'],
  owner:['owner'],confidence:['confidence','conf','conf.'],realizedPct:['% realized','realized %','realized'],nextStep:['next step'],decisionNeeded:['decision needed','decision'],notes:['notes','note','comments']};
const PASTE_DEFAULT_ORDER=['name','pillar','ws','start','end','value','valueType','owner'];
function parsePastedRows(text){
  const lines=String(text||'').replace(/\r\n?/g,'\n').split('\n').filter(line=>line.trim());
  if(!lines.length)return{rows:[],errors:['Paste rows copied from a spreadsheet (tab-separated cells).'],columns:[]};
  if(!lines.some(line=>line.includes('\t'))&&lines.length>1&&lines[0].includes(','))return{rows:[],errors:['These rows are comma-separated. Copy the cells from a spreadsheet instead; cells arrive tab-separated.'],columns:[]};
  const cells=lines.map(line=>line.split('\t').map(cell=>cell.trim().replace(/^"(.*)"$/,'$1')));
  const lookup=new Map();Object.entries(PASTE_HEADERS).forEach(([key,names])=>names.forEach(name=>lookup.set(name,key)));
  const headerKeys=cells[0].map(cell=>lookup.get(cell.toLowerCase())||null);
  const hasHeader=headerKeys.filter(Boolean).length>=2;
  const columns=hasHeader?headerKeys:PASTE_DEFAULT_ORDER.slice(0,cells[0].length);
  const body=hasHeader?cells.slice(1):cells,rows=[],errors=[];
  if(!columns.includes('name'))return{rows:[],errors:['Include an Initiative (or Name) column.'],columns};
  body.forEach((row,index)=>{
    const line=index+(hasHeader?2:1),get=key=>{const i=columns.indexOf(key);return i>=0?(row[i]??'').trim():'';};
    try{
      const name=projectText(get('name'),240).trim();if(!name)throw new Error('Initiative name is empty.');
      const start=checkedDate(get('start'),'Start',S.fyStart,'start'),end=checkedDate(get('end'),'End',S.fyStart,'end');
      if(start&&end&&end<start)throw new Error('End must be on or after Start.');
      const statusText=get('status'),status=statusText?recognizeStatus(statusText):'Not Started';
      const rawPct=get('realizedPct');
      const out={name,pillar:projectText(get('pillar'),240).trim(),ws:projectText(get('ws'),240).trim(),start,end,
        status:status||'Not Started',importedStatus:statusText&&!status?projectText(statusText,60):'',
        approval:get('approval')?normApproval(get('approval'),status||'Not Started'):normApproval('',status||'Not Started'),
        valueType:normValueType(get('valueType')),value:checkedMoney(get('value').replace(/\s/g,''),'Value'),owner:projectText(get('owner'),120).trim(),
        confidence:get('confidence')?(/^(high|med|medium|low)$/i.test(get('confidence'))?parseConfidence(get('confidence')):checkedTypedPercent(get('confidence').replace(/\s/g,''),'Confidence')):100,
        realizedPct:checkedTypedPercent(rawPct,'% Realized'),
        nextStep:projectText(get('nextStep'),240),decisionNeeded:projectText(get('decisionNeeded'),500),notes:projectText(get('notes'),2000)};
      rows.push(out);
    }catch(error){errors.push(`Row ${line}: ${error.message}`);}
  });
  return{rows,errors,columns,hasHeader};
}
function pastePlan(parsed){
  const target=pillarOf(S.filters.pillarId)||S.structure[0];
  const newPillars=new Map(),newWorkstreams=new Map();
  const findPillar=name=>name?S.structure.find(p=>p.name.toLowerCase()===name.toLowerCase()):target;
  parsed.rows.forEach(row=>{
    const p=findPillar(row.pillar);
    if(!p&&row.pillar)newPillars.set(row.pillar.toLowerCase(),row.pillar);
    const wsName=row.ws;
    if(wsName&&!(p&&p.workstreams.some(w=>w.name.toLowerCase()===wsName.toLowerCase())))newWorkstreams.set(`${(row.pillar||target?.name||'').toLowerCase()}\u0000${wsName.toLowerCase()}`,wsName);
  });
  return{newPillars:[...newPillars.values()],newWorkstreams:[...newWorkstreams.values()],target};
}
function applyPastedRows(parsed){
  if(!parsed.rows.length)return 0;
  if(S.items.length+parsed.rows.length>MAX_INITIATIVES){showToast(`A project can hold at most ${MAX_INITIATIVES} initiatives.`);return 0;}
  const plan=pastePlan(parsed);
  if(S.structure.length+plan.newPillars.length>MAX_PILLARS){showToast(`A project can hold at most ${MAX_PILLARS} pillars.`);return 0;}
  if(!plan.target&&!parsed.rows.every(row=>row.pillar)){showToast('Add a pillar before pasting rows without a Pillar column.');return 0;}
  pushUndo();
  const pillarFor=name=>{
    if(!name)return plan.target;
    let p=S.structure.find(x=>x.name.toLowerCase()===name.toLowerCase());
    if(!p){p={id:uid('p'),name,workstreams:[]};S.structure.push(p);}
    return p;
  };
  const wsFor=(p,name)=>{
    if(!name){if(!p.workstreams.length)p.workstreams.push({id:uid('w'),name:'New workstream'});return p.workstreams[0];}
    let w=p.workstreams.find(x=>x.name.toLowerCase()===name.toLowerCase());
    if(!w&&p.workstreams.length<MAX_WORKSTREAMS){w={id:uid('w'),name};p.workstreams.push(w);}
    return w||p.workstreams[0];
  };
  parsed.rows.forEach(row=>{
    const p=pillarFor(row.pillar),w=wsFor(p,row.ws);
    const item={id:uid('i'),pillarId:p.id,wsId:w.id,name:row.name,start:row.start?parseAnyDate(row.start,'start',S.fyStart):null,end:row.end?parseAnyDate(row.end,'end',S.fyStart):null,
      milestone:false,status:row.status,approval:row.approval,owner:row.owner,valueType:row.valueType,value:row.value,includeInTotals:true,realizedPct:row.realizedPct,confidence:row.confidence,phases:[],
      benefitKind:'one-time',valueBasis:'lifetime',recognitionMethod:'linear',nextStep:row.nextStep,decisionNeeded:row.decisionNeeded,notes:row.notes};
    if(row.importedStatus)item.importedStatus=row.importedStatus;
    S.items.push(item);
  });
  refreshOwners();renderAll();
  return parsed.rows.length;
}
function openPasteRows(){
  const dialog=$('pasteDialog');if(!dialog)return;
  $('pasteText').value='';$('pastePreview').innerHTML='<p>Copy cells from Excel, Numbers, or Google Sheets and paste them here. A header row (Initiative, Pillar, Workstream, Start, End, Value, Type, Owner, Status…) maps columns by name; without one, columns are read in that order.</p>';
  $('pasteApply').disabled=true;
  workspaceReturnFocus=document.activeElement;
  dialog.showModal();$('pasteText').focus();
}
function previewPastedRows(){
  const parsed=parsePastedRows($('pasteText').value),plan=pastePlan(parsed);
  const created=[plan.newPillars.length?`Creates ${countLabel(plan.newPillars.length,'pillar')}: ${plan.newPillars.join(', ')}`:'',plan.newWorkstreams.length?`Creates ${countLabel(plan.newWorkstreams.length,'workstream')}: ${plan.newWorkstreams.join(', ')}`:''].filter(Boolean);
  const value=parsed.rows.reduce((sum,row)=>sum+(row.value||0),0);
  $('pastePreview').innerHTML=`<p><b>${countLabel(parsed.rows.length,'initiative')} ready</b>${parsed.rows.length?` · ${esc(fmtMoneyShort(value))} entered value`:''}${parsed.hasHeader?' · columns matched by header':''}</p>${created.map(line=>`<p>${esc(line)}</p>`).join('')}${parsed.errors.length?`<ul class="paste-errors">${parsed.errors.slice(0,12).map(e=>`<li>${esc(e)}</li>`).join('')}${parsed.errors.length>12?`<li>${parsed.errors.length-12} more rows skipped</li>`:''}</ul>`:''}`;
  $('pasteApply').disabled=!parsed.rows.length;
  $('pasteApply').textContent=parsed.rows.length?`Add ${countLabel(parsed.rows.length,'initiative')}`:'Add initiatives';
  return parsed;
}

function initWorkspace(){
  workspaceDefaults();
  if($('workspaceTools'))return refreshWorkspace();
  const fy=$('fySelect');
  if(fy&&!document.querySelector('label[for="fySelect"]')){
    const label=document.createElement('label'); label.className='ws-fy-label'; label.htmlFor='fySelect'; label.textContent='Fiscal year';
    fy.insertAdjacentElement('beforebegin',label);
  }
  const toolbar=$('gridToolbar'),gridBody=$('gridBody');
  const review=document.createElement('button'); review.type='button'; review.id='wsReviewToggle'; review.className='btn btn-quiet ws-review-toggle'; review.setAttribute('aria-expanded','false'); review.textContent='Review';
  toolbar.appendChild(review);
  const tools=document.createElement('div'); tools.id='workspaceTools'; tools.className='workspace-tools'; tools.setAttribute('aria-label','Initiative workspace tools');
  tools.innerHTML=`<div class="ws-layout-tools"><label>Layout<select id="wsLayout">${workspaceLayoutOptions()}</select></label><details class="ws-columns" id="wsColumns"><summary>Columns</summary><div id="wsColumnOptions">${workspaceColumnOptions()}</div></details><button type="button" class="btn btn-quiet" id="wsSaveLayout">Save layout</button><label class="ws-asof">As of<input type="date" min="1900-01-01" max="2200-12-31" id="wsAsOfDate" value="${esc(isoDate(reportingDate()))}"></label><span id="workspaceVersion" class="ws-version">v${esc(APP_VERSION)}</span></div>
    <div class="ws-bulk-tools"><span id="wsSelectionCount">Select rows to edit</span><label class="sr-only" for="wsBulkField">Bulk field</label><select id="wsBulkField"><option value="status">Status</option><option value="approval">Approval</option><option value="owner">Owner</option></select><label class="sr-only" for="wsBulkValue">Bulk value</label><select id="wsBulkValue"></select><label class="sr-only" for="wsBulkOwner">Owner name</label><input id="wsBulkOwner" list="ownerList" placeholder="Owner" maxlength="120" hidden><button type="button" class="btn" id="wsBulkApply" disabled>Apply</button></div>`;
  toolbar.insertAdjacentElement('afterend',tools);
  review.onclick=()=>{ S.workspace.reviewOpen=!S.workspace.reviewOpen; renderWorkspaceReview(); if(!S.workspace.reviewOpen)renderGrid(); scheduleSave(); };
  $('wsLayout').onchange=()=>{ if($('wsLayout').value!=='custom')workspaceApplyLayout($('wsLayout').value); };
  $('wsSaveLayout').onclick=()=>{ const name=prompt('Layout name'); if(name)workspaceSaveLayout(name); };
  $('wsColumnOptions').addEventListener('change',event=>{
    const input=event.target.closest('input');if(!input)return;
    const checked=[...$('wsColumnOptions').querySelectorAll('input:checked')].map(control=>control.value);
    if(!checked.includes('name')){ input.checked=true; return; }
    S.workspace.visibleColumns=checked; S.workspace.activeLayout='custom'; renderGrid(); scheduleSave();
  });
  // The Columns menu closes on Escape or a click outside it.
  document.addEventListener('click',event=>{const menu=$('wsColumns');if(menu?.open&&!menu.contains(event.target))menu.open=false;});
  document.addEventListener('keydown',event=>{const menu=$('wsColumns');if(event.key==='Escape'&&menu?.open){menu.open=false;menu.querySelector('summary').focus();}});
  $('wsAsOfDate').onchange=()=>{ const input=$('wsAsOfDate');let value;
    try{value=checkedDate(input.value,'Reporting date',S.fyStart);}catch(error){input.value=isoDate(reportingDate());return invalidField(input,error.message);}
    clearInvalid(input);if(value===S.asOfDate)return; pushUndo(); S.asOfDate=value; renderAll(); };
  $('wsBulkField').onchange=configureBulkValue; $('wsBulkApply').onclick=applyWorkspaceBulk; configureBulkValue();

  const section=document.createElement('section'); section.id='workspaceReview'; section.className='workspace-review'; section.hidden=true; section.setAttribute('aria-label','Portfolio review');
  section.innerHTML=`<div class="ws-review-head"><h3>Portfolio review</h3><div class="ws-review-tabs" role="tablist" aria-label="Review views"><button type="button" role="tab" id="wsTab-exceptions" data-review-view="exceptions">Exceptions</button><button type="button" role="tab" id="wsTab-changes" data-review-view="changes">Since last review</button><button type="button" role="tab" id="wsTab-compare" data-review-view="compare">Compare</button><button type="button" role="tab" id="wsTab-recovery" data-review-view="recovery">Recovery</button></div></div><div id="workspaceReviewBody" role="tabpanel"></div>`;
  gridBody.insertAdjacentElement('beforebegin',section);
  const tabs=[...section.querySelectorAll('[data-review-view]')];
  tabs.forEach((button,index)=>{
    button.onclick=()=>{ S.workspace.reviewView=button.dataset.reviewView; renderWorkspaceReview(); scheduleSave(); };
    button.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;
      event.preventDefault();tabs[next].click();tabs[next].focus();});
  });

  const dialog=document.createElement('dialog'); dialog.id='workspaceDrilldown'; dialog.className='workspace-dialog'; dialog.setAttribute('aria-modal','true'); dialog.setAttribute('aria-labelledby','workspaceDrilldownTitle');
  dialog.innerHTML=`<div class="ws-dialog-head"><h3 id="workspaceDrilldownTitle">Financial contributors</h3><button type="button" class="icon-btn" id="workspaceDrilldownClose" aria-label="Close financial drilldown">&times;</button></div><div class="ws-dialog-body" id="workspaceDrilldownBody"></div>`;
  document.body.appendChild(dialog);
  $('workspaceDrilldownClose').onclick=closeWorkspaceDrilldown;
  dialog.addEventListener('click',event=>{ if(event.target===dialog)closeWorkspaceDrilldown(); });
  dialog.addEventListener('close',()=>{ if(workspaceReturnFocus?.isConnected)workspaceReturnFocus.focus(); workspaceReturnFocus=null; });

  const paste=document.createElement('dialog'); paste.id='pasteDialog'; paste.className='workspace-dialog'; paste.setAttribute('aria-modal','true'); paste.setAttribute('aria-labelledby','pasteTitle');
  paste.innerHTML=`<div class="ws-dialog-head"><h3 id="pasteTitle">Paste rows from a spreadsheet</h3><button type="button" class="icon-btn" id="pasteClose" aria-label="Close paste rows">&times;</button></div><div class="ws-dialog-body"><label class="sr-only" for="pasteText">Pasted rows</label><textarea id="pasteText" rows="8" spellcheck="false" placeholder="Paste copied cells here"></textarea><div id="pastePreview" class="paste-preview" aria-live="polite"></div><div class="paste-actions"><button type="button" class="btn" id="pasteCancel">Cancel</button><button type="button" class="btn btn-primary" id="pasteApply" disabled>Add initiatives</button></div></div>`;
  document.body.appendChild(paste);
  const closePaste=()=>{paste.close();};
  $('pasteClose').onclick=closePaste;$('pasteCancel').onclick=closePaste;
  paste.addEventListener('close',()=>{ if(workspaceReturnFocus?.isConnected)workspaceReturnFocus.focus(); workspaceReturnFocus=null; });
  $('pasteText').addEventListener('input',previewPastedRows);
  $('pasteApply').onclick=()=>{const parsed=parsePastedRows($('pasteText').value),added=applyPastedRows(parsed);if(added){closePaste();showUndoToast(`${countLabel(added,'initiative')} added${parsed.errors.length?` · ${parsed.errors.length} rows skipped`:''}`);}};

  return refreshWorkspace();
}
