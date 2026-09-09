/* ============ WORKSPACE AUDIT TOOLS ============ */
const WORKSPACE_COLUMNS=['name','pillar','ws','start','end','mile','status','approval','valueType','value','include','realized','confidence','owner'];
const WORKSPACE_BUILTIN_LAYOUTS=[
  {id:'all',name:'All columns',columns:WORKSPACE_COLUMNS},
  {id:'delivery',name:'Delivery review',columns:['name','pillar','ws','start','end','mile','status','approval','owner']},
  {id:'financial',name:'Financial review',columns:['name','pillar','approval','valueType','value','include','realized','confidence','owner']},
  {id:'planning',name:'Planning',columns:['name','pillar','ws','start','end','status','owner']}
];
const workspaceSelection=new Set();
let workspaceReturnFocus=null;

function workspaceDefaults(){
  const raw=S.workspace&&typeof S.workspace==='object'?S.workspace:{};
  S.workspace=raw;
  if(!raw.sort||typeof raw.sort!=='object')raw.sort={key:'',dir:'asc'};
  if(!['asc','desc'].includes(raw.sort.dir))raw.sort.dir='asc';
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
  if(!['exceptions','compare','recovery'].includes(raw.reviewView))raw.reviewView='exceptions';
  raw.reviewOpen=raw.reviewOpen===true;
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
  if(key==='start'||key==='end'){
    const date=item[key] instanceof Date?item[key]:parseAnyDate(item[key],key,S.fyStart);
    return date&&Number.isFinite(date.getTime())?date.getTime():null;
  }
  return textOf(item[key]).trim();
}

function workspaceSortedItems(items){
  const sort=workspaceDefaults().sort;
  if(!sort.key||!WORKSPACE_COLUMNS.includes(sort.key))return items;
  const direction=sort.dir==='desc'?-1:1;
  return items.map((item,index)=>({item,index})).sort((a,b)=>{
    const av=workspaceSortValue(a.item,sort.key),bv=workspaceSortValue(b.item,sort.key);
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
  const ws=workspaceDefaults();
  return [...WORKSPACE_BUILTIN_LAYOUTS,...ws.layouts].map(layout=>
    `<option value="${esc(layout.id)}" ${ws.activeLayout===layout.id?'selected':''}>${esc(layout.name)}</option>`).join('');
}

function workspaceColumnOptions(){
  const labels={name:'Initiative',pillar:'Pillar',ws:'Workstream',start:'Start',end:'End',mile:'Milestone',status:'Status',approval:'Approval',valueType:'Value type',value:'Value',include:'In totals',realized:'Realized',confidence:'Confidence',owner:'Owner'};
  return WORKSPACE_COLUMNS.map(column=>`<label><input type="checkbox" value="${column}" ${S.workspace.visibleColumns.includes(column)?'checked':''}>${esc(labels[column])}</label>`).join('');
}

function workspaceApplyLayout(id){
  const ws=workspaceDefaults();
  const layout=[...WORKSPACE_BUILTIN_LAYOUTS,...ws.layouts].find(entry=>entry.id===id);
  if(!layout)return;
  ws.activeLayout=layout.id;
  ws.visibleColumns=[...layout.columns];
  if(layout.density)S.tableDensity=layout.density;
  if(layout.sort)ws.sort={...layout.sort};
  renderAll();
  scheduleSave();
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

function renderWorkspaceControls(){
  const ws=workspaceDefaults(),bar=$('workspaceTools');
  if(!bar)return;
  const selected=workspaceSelection.size;
  bar.querySelector('#wsLayout').innerHTML=workspaceLayoutOptions();
  bar.querySelector('#wsLayout').value=[...bar.querySelector('#wsLayout').options].some(option=>option.value===ws.activeLayout)?ws.activeLayout:'all';
  const columnMenu=bar.querySelector('#wsColumnOptions');
  if(columnMenu&&!columnMenu.querySelector('input:focus'))columnMenu.innerHTML=workspaceColumnOptions();
  columnMenu?.querySelectorAll('input').forEach(input=>input.onchange=()=>{
    const checked=[...columnMenu.querySelectorAll('input:checked')].map(control=>control.value);
    if(!checked.includes('name')){ input.checked=true; return; }
    ws.visibleColumns=checked; ws.activeLayout='custom'; enhanceGrid(); scheduleSave();
  });
  if($('wsAsOfDate')&&document.activeElement!==$('wsAsOfDate'))$('wsAsOfDate').value=isoDate(reportingDate());
  bar.querySelector('#wsSelectionCount').textContent=selected?`${selected} selected`:'Select rows to edit';
  bar.querySelector('#wsBulkApply').disabled=!selected;
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

function applyWorkspaceBulk(){
  const field=$('wsBulkField')?.value,value=field==='owner'?$('wsBulkOwner')?.value.trim():$('wsBulkValue')?.value;
  const targets=S.items.filter(item=>workspaceSelection.has(item.id));
  if(!targets.length||!['owner','status','approval'].includes(field)||value==null)return;
  const previous=targets.map(item=>({id:item.id,value:item[field]}));
  pushUndo();
  targets.forEach(item=>{ item[field]=value; });
  if(field==='owner'&&typeof refreshOwners==='function')refreshOwners();
  workspaceSelection.clear();
  renderAll();
  if(typeof showUndoToast==='function')showUndoToast(`${targets.length} ${targets.length===1?'initiative':'initiatives'} updated`,()=>{
    previous.forEach(entry=>{ const item=S.items.find(candidate=>candidate.id===entry.id); if(item)item[field]=entry.value; });
    workspaceSelection.clear();
  });
}

function workspaceDate(value,which='end'){
  return value instanceof Date?value:parseAnyDate(value,which,S.fyStart);
}

function workspaceExceptionGroups(){
  const asOf=reportingDate(),staleBefore=addDays(asOf,-90);
  const groups={
    missing:{title:'Missing inputs',hint:'Owner, dates, or financial value is missing.',items:[]},
    overdue:{title:'Overdue',hint:'End date passed before the reporting date.',items:[]},
    stale:{title:'Stale actuals',hint:'Recorded actuals have not been refreshed in 90 days.',items:[]},
    exclusion:{title:'Exclusion link',hint:'Excluded value needs a reason and a valid credited initiative.',items:[]}
  };
  S.items.forEach(item=>{
    const start=workspaceDate(item.start,'start'),end=item.milestone?start:workspaceDate(item.end,'end');
    const rawValue=parseMoney(item.value);
    const missing=[],details=[];
    if(!textOf(item.owner).trim())missing.push('owner');
    if(!start)missing.push('start');
    if(!item.milestone&&!end)missing.push('end');
    if(rawValue==='')missing.push('value');
    if(missing.length)details.push(`Missing ${missing.join(', ')}`);
    const reversed=!!(start&&end&&end<start);
    if(reversed)details.push('End date precedes start date');
    if(item.benefitKind==='recurring'&&item.valueBasis==='annual'&&(!start||!end||reversed))details.push('Annual recurring value needs complete timing');
    if(details.length)groups.missing.items.push({item,detail:details.join(' · ')});
    if(end&&!reversed&&end<asOf&&normStatus(item.status)!=='Complete')groups.overdue.items.push({item,detail:`Ended ${fmtDate(end)} · ${item.status}`});
    const actual=parseMoney(item.actualValue),actualAsOf=workspaceDate(item.actualAsOf,'end');
    if(actual!==''&&(!actualAsOf||actualAsOf<staleBefore))groups.stale.items.push({item,detail:actualAsOf?`Actual as of ${fmtDate(actualAsOf)}`:'Actual has no as-of date'});
    if(!isIncludedInTotals(item)){
      const target=S.items.find(candidate=>candidate.id===item.creditedToId),reason=textOf(item.exclusionReason).trim();
      if(!target||!reason||!isIncludedInTotals(target))groups.exclusion.items.push({item,detail:!reason&&!target?'Reason and credited initiative missing':!reason?'Reason missing':!target?'Credited initiative missing':'Credited initiative is also excluded'});
    }
  });
  return groups;
}

function exceptionRow(row,type){
  const value=itemValue(row.item);
  return `<button type="button" class="ws-review-row" data-exception-id="${esc(row.item.id)}">
    <span><b>${esc(row.item.name||'Untitled initiative')}</b><small>${esc(row.detail)}</small></span>
    <span>${esc(value?fmtMoneyShort(value,true):type==='missing'?'Needs input':'Review')}</span>
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

function scenarioRecord(id){
  if(id==='current')return{name:'Current plan',payload:{items:S.items,projectionTarget:S.projectionTarget}};
  return(S.scenarios||[]).find(scenario=>scenario.id===id)||null;
}

function scenarioDateText(value,which){
  const date=workspaceDate(value,which);
  return date?fmtDate(date):'Undated';
}

function renderComparison(){
  const scenarios=S.scenarios||[];
  if(!scenarios.length)return'<div class="ws-review-empty"><b>No saved scenarios</b><span>Save scenarios to compare value, timing, approval, and goal gap.</span></div>';
  const ws=workspaceDefaults(),ids=['current',...scenarios.map(scenario=>scenario.id)];
  if(!ids.includes(ws.compareA))ws.compareA=scenarios[0]?.id||'current';
  if(!ids.includes(ws.compareB)||ws.compareB===ws.compareA)ws.compareB=scenarios[1]?.id||'current';
  const optionHtml=selected=>ids.map(id=>{ const scenario=scenarioRecord(id); return`<option value="${esc(id)}" ${id===selected?'selected':''}>${esc(scenario?.name||id)}</option>`; }).join('');
  const a=scenarioRecord(ws.compareA),b=scenarioRecord(ws.compareB);
  const aItems=new Map((a?.payload?.items||[]).map(item=>[item.id,item])),bItems=new Map((b?.payload?.items||[]).map(item=>[item.id,item]));
  const idsUnion=[...new Set([...aItems.keys(),...bItems.keys()])];
  const sum=items=>typeof portfolioFinancialTotals==='function'?portfolioFinancialTotals([...items.values()]).Total:[...items.values()].reduce((total,item)=>total+Math.max(0,parseMoney(item.value)||0),0);
  const aTotal=sum(aItems),bTotal=sum(bItems),aGoal=Math.max(0,parseMoney(a?.payload?.projectionTarget)||0),bGoal=Math.max(0,parseMoney(b?.payload?.projectionTarget)||0);
  const delta=bTotal-aTotal,goalDelta=bGoal-aGoal;
  const rows=idsUnion.map(id=>{
    const left=aItems.get(id),right=bItems.get(id),name=right?.name||left?.name||S.items.find(item=>item.id===id)?.name||'Untitled initiative';
    const leftValue=Math.max(0,parseMoney(left?.value)||0),rightValue=Math.max(0,parseMoney(right?.value)||0);
    return`<tr><th scope="row">${esc(name)}</th><td>${esc(fmtMoneyShort(leftValue,true))}</td><td>${esc(fmtMoneyShort(rightValue,true))}</td><td class="ws-delta ${rightValue-leftValue<0?'down':''}">${rightValue-leftValue>=0?'+':''}${esc(fmtMoneyShort(rightValue-leftValue,true))}</td>
      <td><small>Start ${esc(scenarioDateText(left?.start,'start'))} &rarr; ${esc(scenarioDateText(right?.start,'start'))}<br>End ${esc(scenarioDateText(left?.end,'end'))} &rarr; ${esc(scenarioDateText(right?.end,'end'))}</small></td>
      <td>${esc(approvalLabel(left?.approval))} &rarr; ${esc(approvalLabel(right?.approval))}</td></tr>`;
  }).join('');
  return `<div class="ws-compare-controls"><label>From<select id="wsCompareA">${optionHtml(ws.compareA)}</select></label><span aria-hidden="true">&rarr;</span><label>To<select id="wsCompareB">${optionHtml(ws.compareB)}</select></label></div>
    <div class="ws-compare-summary"><div><span>Portfolio change</span><b>${delta>=0?'+':''}${esc(fmtMoneyShort(delta,true))}</b></div><div><span>Goal change</span><b>${goalDelta>=0?'+':''}${esc(fmtMoneyShort(goalDelta,true))}</b></div><div><span>Goal gap</span><b>${esc(fmtMoneyShort(bTotal-bGoal,true))}</b></div></div>
    <div class="ws-compare-table-wrap"><table class="ws-compare-table"><thead><tr><th>Initiative</th><th>From</th><th>To</th><th>Value delta</th><th>Timing</th><th>Approval</th></tr></thead><tbody>${rows||'<tr><td colspan="6">No initiatives in either scenario.</td></tr>'}</tbody></table></div>`;
}

function renderRecovery(){
  const versions=typeof localRecoveryProjects==='function'?localRecoveryProjects():[];
  if(!versions.length)return'<div class="ws-review-empty"><b>No recovery versions</b><span>Roadmap Studio keeps bounded local versions before project replacement and recovery.</span></div>';
  return `<div class="ws-recovery-list">${versions.map((version,index)=>{
    const date=new Date(Number(version.date)||0),dateText=Number.isFinite(date.getTime())?date.toLocaleString('en-US',{dateStyle:'medium',timeStyle:'short'}):'Date unavailable';
    return`<div class="ws-recovery-row"><span><b>${esc(version.name||'Roadmap')}</b><small>${esc(dateText)} · Stored only in this browser</small></span><button type="button" class="btn" data-recovery-index="${index}">Restore</button></div>`;
  }).join('')}</div>`;
}

function renderWorkspaceReview(){
  const ws=workspaceDefaults(),review=$('workspaceReview'),body=$('workspaceReviewBody');
  if(!review||!body)return;
  review.hidden=!ws.reviewOpen;
  if($('gridBody'))$('gridBody').hidden=ws.reviewOpen;
  $('wsReviewToggle')?.classList.toggle('on',ws.reviewOpen);
  $('wsReviewToggle')?.setAttribute('aria-expanded',String(ws.reviewOpen));
  review.querySelectorAll('[data-review-view]').forEach(button=>{
    const active=button.dataset.reviewView===ws.reviewView;
    button.classList.toggle('on',active); button.setAttribute('aria-selected',String(active));
  });
  body.innerHTML=ws.reviewView==='compare'?renderComparison():ws.reviewView==='recovery'?renderRecovery():renderExceptions();
  body.querySelectorAll('[data-exception-id]').forEach(button=>button.onclick=()=>openDrawer(button.dataset.exceptionId));
  body.querySelectorAll('[data-jump-group]').forEach(button=>button.onclick=()=>document.getElementById(`wsGroup-${button.dataset.jumpGroup}`)?.scrollIntoView({block:'nearest',behavior:'smooth'}));
  ['wsCompareA','wsCompareB'].forEach(id=>{ const select=$(id); if(select)select.onchange=()=>{ ws[id==='wsCompareA'?'compareA':'compareB']=select.value; renderWorkspaceReview(); scheduleSave(); }; });
  body.querySelectorAll('[data-recovery-index]').forEach(button=>button.onclick=()=>{ if(typeof restoreRecovery==='function')restoreRecovery(Number(button.dataset.recoveryIndex)); });
}

function financialTargetSpec(target){
  const id=target.id||'';
  const map={
    execTotal:{title:'Total portfolio',metric:'planned'},rollupTotal:{title:'Total portfolio',metric:'planned'},projCombined:{title:'Projected total impact',metric:'planned'},projectionHeadline:{title:'Projected total impact',metric:'planned'},stackCombinedTotal:{title:'Total impact',metric:'planned'},
    execApproved:{title:'Active value',metric:'planned',approval:'Approved'},rollupApproved:{title:'Active value',metric:'planned',approval:'Approved'},
    execProposed:{title:'Proposed value',metric:'planned',approval:'Proposed'},rollupProposed:{title:'Proposed value',metric:'planned',approval:'Proposed'},
    execRealized:{title:'Recorded actuals',metric:'actual'},rollupRealized:{title:'Recorded actuals',metric:'actual'},
    projSavings:{title:'Projected savings',metric:'planned',type:'Savings'},savingsTotal:{title:'Savings',metric:'planned',type:'Savings'},stackSavingsTotal:{title:'Savings',metric:'planned',type:'Savings'},
    projAvoidance:{title:'Projected avoidance',metric:'planned',type:'Avoidance'},avoidanceTotal:{title:'Avoidance',metric:'planned',type:'Avoidance'},
    projExpected:{title:'Confidence-weighted value',metric:'expected'},projAnnualized:{title:'Annualized recurring value',metric:'annualized'},
    realizedSavingsTotal:{title:'Recorded savings actuals',metric:'actual',type:'Savings'},realizedAvoidanceTotal:{title:'Recorded avoidance actuals',metric:'actual',type:'Avoidance'}
  };
  if(map[id])return map[id];
  if(target.matches('.stack-segment'))return{title:'Pillar contribution',metric:'planned',pillarId:target.dataset.pillar,type:target.dataset.series==='Savings'?'Savings':null};
  if(target.matches('.rollup-bar'))return{title:'Pillar contribution',metric:'planned',pillarId:target.dataset.pillar,approval:target.dataset.approval};
  if(target.matches('.exec-segment'))return{title:'Portfolio contribution',metric:target.dataset.stage==='realized'?'actual':'planned',approval:target.dataset.stage==='approved'?'Approved':target.dataset.stage==='proposed'?'Proposed':null,type:target.dataset.type};
  if(target.matches('#projectionHoverCombined,#projectionHoverSavings,#projectionHoverRealized'))return{title:'Projection at reporting point',metric:id.includes('Realized')?'actual':'planned',type:id.includes('Savings')?'Savings':null};
  return null;
}

function drilldownMatches(item,spec){
  if(spec.type&&normValueType(item.valueType)!==spec.type)return false;
  if(spec.approval&&approvalStatus(item)!==spec.approval)return false;
  if(spec.pillarId&&item.pillarId!==spec.pillarId)return false;
  return true;
}

function drilldownValue(item,metric){
  if(metric==='actual')return realizedItemValue(item,reportingDate());
  if(metric==='expected')return itemValue(item)*parseConfidence(item.confidence)/100;
  if(metric==='annualized')return typeof annualizedValue==='function'?annualizedValue(item):itemValue(item);
  return itemValue(item);
}

function drilldownFormula(item,spec){
  if(spec.metric==='actual')return parseMoney(item.actualValue)!==''?'Recorded actual at its as-of date':'Fallback realized percentage or phase schedule';
  if(spec.metric==='expected')return'Lifetime planned value multiplied by confidence';
  if(spec.metric==='annualized')return'Recurring benefit normalized to a 365-day run rate';
  const basis=item.valueBasis==='annual'?'annual input converted to initiative duration':'lifetime planned value';
  const recognition={linear:'recognized evenly across the date range',completion:'recognized at completion',upfront:'recognized at start'}[item.recognitionMethod]||'planned value';
  return`${basis}; ${recognition}`;
}

function drilldownRow(item,population,spec,showCosts=false){
  const value=drilldownValue(item,spec.metric),pillar=pillarOf(item.pillarId)?.name||'Unassigned pillar';
  const cost=Math.max(0,parseMoney(item.cost)||0),net=typeof netBenefit==='function'?netBenefit(item):itemValue(item)-cost;
  return `<tr data-population="${population}"><th scope="row"><button type="button" data-drill-item="${esc(item.id)}">${esc(item.name||'Untitled initiative')}</button><small>${esc(pillar)} · ${esc(approvalLabel(approvalStatus(item)))}</small></th><td>${esc(fmtMoneyShort(value,true))}</td>${showCosts?`<td>${esc(fmtMoneyShort(cost,true))}</td><td>${esc(fmtMoneyShort(net,true))}</td>`:''}<td>${esc(drilldownFormula(item,spec))}</td></tr>`;
}

function openWorkspaceDrilldown(spec,trigger){
  const dialog=$('workspaceDrilldown'); if(!dialog||!spec)return;
  workspaceReturnFocus=trigger||document.activeElement;
  const matched=S.items.filter(item=>drilldownMatches(item,spec));
  const included=matched.filter(isIncludedInTotals),excluded=matched.filter(item=>!isIncludedInTotals(item));
  const undated=included.filter(item=>!workspaceDate(item.start,'start')||(!item.milestone&&!workspaceDate(item.end,'end')));
  const showCosts=matched.some(item=>(parseMoney(item.cost)||0)>0);
  const reconciled=typeof portfolioFinancialTotals==='function'?portfolioFinancialTotals(matched,reportingDate()):null;
  const total=spec.metric==='planned'&&reconciled?(spec.type?reconciled[spec.type]:spec.approval?reconciled[spec.approval]:reconciled.Total):included.reduce((sum,item)=>sum+drilldownValue(item,spec.metric),0),asOf=reportingDate();
  $('workspaceDrilldownTitle').textContent=spec.title;
  $('workspaceDrilldownBody').innerHTML=`<div class="ws-drill-summary"><div><span>Included total</span><b>${esc(fmtMoneyShort(total,true))}</b></div><p>As of ${esc(fmtDate(asOf))}</p></div>
    <p class="ws-formula"><b>Formula</b> Planned values use lifetime economics. Recorded actuals remain independent of confidence. Excluded rows never enter the headline total.${showCosts?' Net benefit equals lifetime planned value minus implementation cost.':''}</p>
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

function enhanceFinancialTargets(){
  const selectors=['#execTotal','#execApproved','#execProposed','#execRealized','#rollupTotal','#rollupApproved','#rollupProposed','#rollupRealized','#projectionHeadline','#projSavings','#projAvoidance','#projCombined','#projExpected','#projAnnualized','#stackSavingsTotal','#stackCombinedTotal','#savingsTotal','#avoidanceTotal','#realizedSavingsTotal','#realizedAvoidanceTotal','.stack-segment','.rollup-bar','.exec-segment','#projectionHoverCombined','#projectionHoverSavings','#projectionHoverRealized'];
  document.querySelectorAll(selectors.join(',')).forEach(target=>{
    const spec=financialTargetSpec(target); if(!spec)return;
    target.classList.add('ws-drill-target'); target.setAttribute('role','button'); target.setAttribute('tabindex','0'); target.setAttribute('aria-label',`Inspect ${spec.title.toLowerCase()} contributors`);
    if(target._workspaceDrillBound)return;
    target._workspaceDrillBound=true;
    const open=event=>{ if(event.type==='keydown'&&!['Enter',' '].includes(event.key))return; if(event.type==='keydown')event.preventDefault(); openWorkspaceDrilldown(financialTargetSpec(target),target); };
    target.addEventListener('click',open); target.addEventListener('keydown',open);
  });
  document.querySelectorAll('svg').forEach(svg=>{ if(svg.querySelector('[tabindex="0"]'))svg.setAttribute('role','group'); });
}

function enhanceGrid(){
  workspaceDefaults();
  const table=$('initGrid');
  renderWorkspaceControls();
  if(!table)return;
  const headers=[...table.querySelectorAll('thead th')];
  headers.forEach((header,index)=>{
    const key=header.dataset.col;
    if(key){
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
      table.querySelectorAll('tbody tr').forEach(row=>{ if(row.children[index])row.children[index].hidden=!visible; });
    }
  });
  const selectHead=headers[0];
  if(selectHead&&!$('wsSelectAll')){
    selectHead.innerHTML='<input type="checkbox" id="wsSelectAll" aria-label="Select all filtered initiatives">';
    $('wsSelectAll').onchange=()=>{
      table.querySelectorAll('tbody tr[data-id]').forEach(row=>$('wsSelectAll').checked?workspaceSelection.add(row.dataset.id):workspaceSelection.delete(row.dataset.id));
      enhanceGrid(); renderWorkspaceControls();
    };
  }
  table.querySelectorAll('tbody tr[data-id]').forEach(row=>{
    const cell=row.children[0];
    if(!cell.querySelector('[data-ws-select]')){
      const number=cell.textContent.trim();
      cell.innerHTML=`<div class="ws-row-selector"><input type="checkbox" data-ws-select aria-label="Select ${esc(row.querySelector('[data-f=name]')?.value||'initiative')}"><span>${esc(number)}</span></div>`;
      cell.querySelector('[data-ws-select]').onchange=event=>{ event.target.checked?workspaceSelection.add(row.dataset.id):workspaceSelection.delete(row.dataset.id); enhanceGrid(); renderWorkspaceControls(); };
    }
    cell.querySelector('[data-ws-select]').checked=workspaceSelection.has(row.dataset.id);
  });
  const visibleRows=[...table.querySelectorAll('tbody tr[data-id]')],selectedVisible=visibleRows.filter(row=>workspaceSelection.has(row.dataset.id)).length;
  if($('wsSelectAll')){
    $('wsSelectAll').checked=!!visibleRows.length&&selectedVisible===visibleRows.length;
    $('wsSelectAll').indeterminate=selectedVisible>0&&selectedVisible<visibleRows.length;
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

function refreshWorkspace(){
  const ws=workspaceDefaults();
  [...workspaceSelection].forEach(id=>{ if(!S.items.some(item=>item.id===id))workspaceSelection.delete(id); });
  renderWorkspaceControls();
  renderWorkspaceReview();
  enhanceGrid();
  enhanceDrawer();
  enhanceFinancialTargets();
  if($('workspaceVersion'))$('workspaceVersion').textContent=`v${typeof APP_VERSION==='undefined'?'':APP_VERSION}`;
  return ws;
}

function initWorkspace(){
  workspaceDefaults();
  if($('workspaceTools'))return refreshWorkspace();
  const fySelect=$('fySelect');
  if(fySelect&&!document.querySelector('label[for="fySelect"]')){
    const label=document.createElement('label'); label.className='ws-fy-label'; label.htmlFor='fySelect'; label.textContent='Fiscal year';
    fySelect.insertAdjacentElement('beforebegin',label);
  }
  const toolbar=$('gridToolbar'),gridBody=$('gridBody');
  if(toolbar){
    const review=document.createElement('button'); review.type='button'; review.id='wsReviewToggle'; review.className='btn btn-quiet ws-review-toggle'; review.setAttribute('aria-expanded','false'); review.textContent='Review';
    toolbar.appendChild(review);
    const tools=document.createElement('div'); tools.id='workspaceTools'; tools.className='workspace-tools'; tools.setAttribute('aria-label','Initiative workspace tools');
    tools.innerHTML=`<div class="ws-layout-tools"><label>Layout<select id="wsLayout">${workspaceLayoutOptions()}</select></label><details class="ws-columns"><summary>Columns</summary><div id="wsColumnOptions">${workspaceColumnOptions()}</div></details><button type="button" class="btn btn-quiet" id="wsSaveLayout">Save layout</button><label class="ws-asof">As of<input type="date" id="wsAsOfDate" value="${esc(isoDate(reportingDate()))}"></label><span id="workspaceVersion" class="ws-version">v${esc(typeof APP_VERSION==='undefined'?'':APP_VERSION)}</span></div>
      <div class="ws-bulk-tools"><span id="wsSelectionCount">Select rows to edit</span><label class="sr-only" for="wsBulkField">Bulk field</label><select id="wsBulkField"><option value="status">Status</option><option value="approval">Approval</option><option value="owner">Owner</option></select><label class="sr-only" for="wsBulkValue">Bulk value</label><select id="wsBulkValue"></select><label class="sr-only" for="wsBulkOwner">Owner name</label><input id="wsBulkOwner" list="ownerList" placeholder="Owner" hidden><button type="button" class="btn" id="wsBulkApply" disabled>Apply</button></div>`;
    toolbar.insertAdjacentElement('afterend',tools);
    review.onclick=()=>{ S.workspace.reviewOpen=!S.workspace.reviewOpen; renderWorkspaceReview(); scheduleSave(); };
    $('wsLayout').onchange=()=>workspaceApplyLayout($('wsLayout').value);
    $('wsSaveLayout').onclick=()=>{ const name=prompt('Layout name'); if(name)workspaceSaveLayout(name); };
    $('wsAsOfDate').onchange=()=>{ const value=$('wsAsOfDate').value; if(value===S.asOfDate)return; pushUndo(); S.asOfDate=value; renderAll(); scheduleSave(); };
    $('wsBulkField').onchange=configureBulkValue; $('wsBulkApply').onclick=applyWorkspaceBulk; configureBulkValue();
  }
  if(gridBody){
    const review=document.createElement('section'); review.id='workspaceReview'; review.className='workspace-review'; review.hidden=true; review.setAttribute('aria-label','Portfolio review');
    review.innerHTML=`<div class="ws-review-head"><h3>Portfolio review</h3><div class="ws-review-tabs" role="tablist"><button type="button" role="tab" data-review-view="exceptions">Exceptions</button><button type="button" role="tab" data-review-view="compare">Compare</button><button type="button" role="tab" data-review-view="recovery">Recovery</button></div></div><div id="workspaceReviewBody"></div>`;
    gridBody.insertAdjacentElement('beforebegin',review);
    review.querySelectorAll('[data-review-view]').forEach(button=>button.onclick=()=>{ S.workspace.reviewView=button.dataset.reviewView; renderWorkspaceReview(); scheduleSave(); });
  }
  if(!$('workspaceDrilldown')){
    const dialog=document.createElement('dialog'); dialog.id='workspaceDrilldown'; dialog.className='workspace-dialog'; dialog.setAttribute('aria-modal','true'); dialog.setAttribute('aria-labelledby','workspaceDrilldownTitle');
    dialog.innerHTML=`<div class="ws-dialog-head"><h3 id="workspaceDrilldownTitle">Financial contributors</h3><button type="button" class="icon-btn" id="workspaceDrilldownClose" aria-label="Close financial drilldown">&times;</button></div><div class="ws-dialog-body" id="workspaceDrilldownBody"></div>`;
    document.body.appendChild(dialog);
    $('workspaceDrilldownClose').onclick=closeWorkspaceDrilldown;
    dialog.addEventListener('click',event=>{ if(event.target===dialog)closeWorkspaceDrilldown(); });
    dialog.addEventListener('close',()=>{ if(workspaceReturnFocus?.isConnected)workspaceReturnFocus.focus(); workspaceReturnFocus=null; });
  }
  if(!$('workspaceLive')){
    const live=document.createElement('div'); live.id='workspaceLive'; live.className='sr-only'; live.setAttribute('aria-live','polite'); document.body.appendChild(live);
  }
  if(gridBody&&typeof MutationObserver!=='undefined'){
    const observer=new MutationObserver(()=>queueMicrotask(enhanceGrid));
    observer.observe(gridBody,{childList:true,subtree:false});
  }
  return refreshWorkspace();
}
