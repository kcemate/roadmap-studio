/* ============ EXPORTS: PNG, PowerPoint, presentation ============
   The PowerPoint deck is built on two slide masters (title and content) with a title placeholder, a footer, and a
   slide number. One palette and one type scale apply to every slide: title 28 pt, body 14 pt, caption 10 pt. */
const PPT_W=13.333, PPT_H=7.5;
const PPT_TYPE={title:28,body:14,caption:10,metric:24,hero:44};
const PPT_COLOR={ink:'1D1D1F',muted:'5D6168',grey1:'C9CDD4',grey2:'EEF0F3',hair:'E5E7EB',white:'FFFFFF',
  savings:'188038',savingsDark:'0E5A27',savingsLight:'A8D5B5',avoidance:'2563EB',avoidanceDark:'1E3A8A',avoidanceLight:'A9C1F5',
  risk:'B45309',riskLight:'FDF1E4'};
const PPT_STAGE_COLORS={realized:{Savings:PPT_COLOR.savingsDark,Avoidance:PPT_COLOR.avoidanceDark},approved:{Savings:PPT_COLOR.savings,Avoidance:PPT_COLOR.avoidance},proposed:{Savings:PPT_COLOR.savingsLight,Avoidance:PPT_COLOR.avoidanceLight}};
const PPT_STATUS_PILL=STATUS_PILL;
let PPT_EXPORT_CONTEXT=null,PPT_SLIDES=[];

function pptFont(){ return S.brand?.font||'Arial'; }
function pptAccent(){ return (S.brand?.accent||'#1D1D1F').slice(1).toUpperCase(); }
function exportReportingDate(){ const value=reportingDate(); return value instanceof Date&&!isNaN(value)?value:todayUtc(); }
function exportScenarioName(){
  const active=S.scenarios.find(s=>s.id===S.activeScenarioId);
  return active?.name||WORKING_PLAN_NAME;
}
/* One file-naming rule: "<project> — <view> — <as-of date>.<ext>"; project files keep "<project>.roadmap.json". */
function exportFileName(kind,ext){
  const base=String(S.fileName||DEFAULT_PROJECT_NAME).replace(/[\\/:*?"<>|\u0000-\u001f]+/g,' ').replace(/\s+/g,' ').trim().slice(0,120)||DEFAULT_PROJECT_NAME;
  return kind==='project'?`${base}.${ext}`:`${base} — ${kind} — ${isoDate(exportReportingDate())}.${ext}`;
}
function exportGroupingLabel(){ return S.roadmapGroup==='owner'?'Owner':'Structure'; }
function exportPrefs(){ S.exportPrefs=sanitizeExportPrefs(S.exportPrefs); return S.exportPrefs; }
function exportScopeValue(override){
  if(override==='current'||override==='full')return override;
  const control=$('pptScope');
  return control?.value==='current'||S.exportScope==='current'?'current':'full';
}
const REPORT_TABS=['exec','rollup','proj','stack','road','register'];
function exportViewLabel(tab=S.tab){
  return LABELS[REPORT_TABS.includes(tab)?(tab==='proj'?'projection':tab==='stack'?'contribution':tab):'road'];
}
function filterSummary(){
  const f=S.filters,parts=[];
  if(f.pillarId)parts.push(`Pillar: ${pillarOf(f.pillarId)?.name||'—'}`);
  if(f.owner)parts.push(`Owner: ${f.owner}`);
  if(f.status)parts.push(`Status: ${f.status}`);
  if(f.valueType)parts.push(f.valueType);
  if(f.q)parts.push(`Search: “${f.q}”`);
  return parts.join(' · ');
}
function exportFiltered(){ return exportPrefs().applyFilters&&filtersActive(); }
function buildExportContext(scope){
  const filtered=exportFiltered();
  return{
    scope,
    scopeLabel:scope==='current'?`Current view: ${exportViewLabel()}`:'Full deck',
    project:S.fileName||DEFAULT_PROJECT_NAME,
    scenario:exportScenarioName(),
    asOf:exportReportingDate(),
    baseline:S.baseline&&S.showBaseline!==false?'Baseline comparison on':S.baseline?'Baseline comparison off':'No baseline',
    weighting:S.weightConfidence===false?'Unweighted':'Confidence-weighted',
    grouping:exportGroupingLabel(),
    filterLabel:filtered?`Filtered · ${filterSummary()}`:'',
    version:APP_VERSION
  };
}
function exportContext(){ return PPT_EXPORT_CONTEXT||buildExportContext(exportScopeValue()); }

/* ---------- export options (remembered per project) ---------- */
function ensureExportScopeControl(){
  if($('pptScope')||!$('pptBtn'))return;
  const select=document.createElement('select');
  select.id='pptScope'; select.className='fy-select'; select.setAttribute('aria-label','PowerPoint export scope');
  select.title='Choose whether PowerPoint exports this view or the full deck';
  select.innerHTML='<option value="full">Full deck</option><option value="current">Current view</option>';
  select.onchange=()=>{S.exportScope=select.value;exportPrefs().scope=select.value;scheduleSave();};
  $('pptBtn').before(select);
  const options=document.createElement('details');options.id='deckOptions';options.className='deck-options';
  options.innerHTML=`<summary aria-label="Deck options">Options</summary><div class="deck-options-panel">
    <label><input type="checkbox" id="exportApplyFilters"> Use Initiatives filters <small id="exportFilterSummary"></small></label>
    <label><input type="checkbox" id="exportIncludeRegister"> Include register appendix</label>
    <label><input type="checkbox" id="exportSinceReview"> Include “Since last review” when a baseline exists</label>
    <hr><b>Brand</b>
    <label>Accent <input type="color" id="brandAccent" value="#1d1d1f"></label>
    <label>Font <select id="brandFont">${BRAND_FONTS.map(f=>`<option>${f}</option>`).join('')}</select></label>
    <label>Logo <input type="file" id="brandLogo" accept="image/png,image/jpeg"></label>
    <button type="button" class="btn btn-quiet" id="brandLogoClear">Remove logo</button>
    <small>The logo is embedded in the project file and the deck; it never leaves this device otherwise.</small></div>`;
  select.before(options);
  document.addEventListener('click',event=>{if(options.open&&!options.contains(event.target))options.open=false;});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&options.open){options.open=false;options.querySelector('summary').focus();}});
  const bind=(id,key)=>{$(id).onchange=()=>{exportPrefs()[key]=$(id).checked;if(id==='exportIncludeRegister')$('registerAppendix').checked=$(id).checked;scheduleSave();};};
  bind('exportApplyFilters','applyFilters');bind('exportIncludeRegister','includeRegister');bind('exportSinceReview','sinceReview');
  $('registerAppendix').onchange=()=>{exportPrefs().includeRegister=$('registerAppendix').checked;$('exportIncludeRegister').checked=$('registerAppendix').checked;scheduleSave();};
  $('brandAccent').onchange=()=>{pushUndo();S.brand={...S.brand,accent:$('brandAccent').value.toUpperCase()};scheduleSave();};
  $('brandFont').onchange=()=>{pushUndo();S.brand={...S.brand,font:$('brandFont').value};scheduleSave();};
  $('brandLogo').onchange=event=>{
    const file=event.target.files[0];event.target.value='';if(!file)return;
    if(!/^image\/(png|jpeg)$/.test(file.type)||file.size>MAX_LOGO_CHARS*.74)return showToast('Choose a PNG or JPEG logo under 290 KB.');
    const reader=new FileReader();reader.onload=()=>{const img=new Image();img.onload=()=>{pushUndo();S.brand={...S.brand,logo:reader.result,logoAspect:Math.min(9,Math.max(.2,img.naturalWidth/img.naturalHeight||1))};scheduleSave();showToast('Logo added to deck masters');};img.onerror=()=>showToast('That image could not be read.');img.src=reader.result;};
    reader.readAsDataURL(file);
  };
  $('brandLogoClear').onclick=()=>{if(!S.brand.logo)return;pushUndo();const {logo,logoAspect,...rest}=S.brand;S.brand=rest;scheduleSave();};
}
function syncExportControls(){
  const prefs=exportPrefs();
  if($('pptScope')&&document.activeElement!==$('pptScope')){$('pptScope').value=S.exportScope||prefs.scope;$('pptScope').title=`Full deck, or the current view only (${exportViewLabel()}${['struct','data'].includes(S.tab)?': editing tabs export the Roadmap':''})`;}
  if(!$('exportApplyFilters'))return;
  $('exportApplyFilters').checked=prefs.applyFilters;$('exportIncludeRegister').checked=prefs.includeRegister;$('exportSinceReview').checked=prefs.sinceReview;
  $('registerAppendix').checked=prefs.includeRegister;
  $('exportFilterSummary').textContent=filtersActive()?`(${filteredItems().length} of ${S.items.length}: ${filterSummary()})`:'(no filters set)';
  $('brandAccent').value=(S.brand.accent||'#1D1D1F').toLowerCase();$('brandFont').value=pptFont();$('brandLogoClear').hidden=!S.brand.logo;
}
ensureExportScopeControl();

/* ---------- Roadmap PNG ---------- */
const PNG_MAX_SIDE=16000,PNG_MAX_AREA=120e6;
function exportRoadmapPng(){
  renderTimeline();
  const el=$('tlSvg'); if(!el){showToast('Add a pillar before exporting the roadmap.');return;}
  const xml=new XMLSerializer().serializeToString(el), img=new Image(), c=buildExportContext('current');
  const w=el.width.baseVal.value,header=92,h=el.height.baseVal.value+header;
  const s=Math.max(.1,Math.min(2,PNG_MAX_SIDE/w,PNG_MAX_SIDE/h,Math.sqrt(PNG_MAX_AREA/(w*h))));
  img.onerror=()=>showToast('The roadmap image could not be drawn.');
  img.onload=()=>{ const canvas=document.createElement('canvas');
    canvas.width=Math.floor(w*s); canvas.height=Math.floor(h*s); const x=canvas.getContext('2d');
    if(!x){showToast('This roadmap is too large for a PNG in this browser. Use PowerPoint instead.');return;}
    x.scale(s,s); x.fillStyle='#fbfbfd'; x.fillRect(0,0,w,header); x.fillStyle='#1d1d1f'; x.font='600 20px sans-serif';
    x.fillText(c.project,20,31); x.font='12px sans-serif'; x.fillStyle='#6e6e73';
    x.fillText(`${c.scenario}  ·  As of ${fmtDate(c.asOf)}  ·  Grouping: ${c.grouping}${s<2?`  ·  Scaled to ${Math.round(s*50)}% to fit image limits`:''}`,20,57);
    x.fillText(`Roadmap  ·  Roadmap Studio ${c.version}`,20,77); x.drawImage(img,0,header,w,h-header);
    canvas.toBlob(b=>{if(!b){showToast('This roadmap is too large for a PNG in this browser. Use PowerPoint instead.');return;}dl(b,exportFileName('Roadmap','png'));},'image/png'); };
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(xml);
}
$('pngBtn').onclick=exportRoadmapPng;

/* ---------- text and shape helpers ---------- */
function pptTextWidthIn(value,fontPt,bold=false){ return measureTextPx(value,fontPt*96/72,bold?700:400,pptFont())/96; }
function pptBoundText(value,widthIn,fontPt,bold=false){const text=String(value||''),limit=Math.max(0,widthIn)*.97;if(pptTextWidthIn(text,fontPt,bold)<=limit)return text;let lo=0,hi=text.length;while(lo<hi){const mid=Math.ceil((lo+hi)/2),candidate=`${text.slice(0,mid).trimEnd()}…`;if(pptTextWidthIn(candidate,fontPt,bold)<=limit)lo=mid;else hi=mid-1;}return `${text.slice(0,lo).trimEnd()}…`;}
function pptWrapText(value,width,font=PPT_TYPE.body,maxLines=2,bold=false){
  const words=String(value||'').split(/\s+/).filter(Boolean),lines=[];let line='';
  while(words.length){const word=words.shift(),next=line?`${line} ${word}`:word;
    if(pptTextWidthIn(next,font,bold)<=width*.96){line=next;continue;}
    if(line){lines.push(line);line='';words.unshift(word);}else{lines.push(pptBoundText(word,width,font,bold));}
    if(lines.length===maxLines-1&&words.length){lines.push(pptBoundText(words.join(' '),width,font,bold));return lines.join('\n');}
  }
  if(line)lines.push(line);return lines.slice(0,maxLines).join('\n');
}
function pptText(slide,text,x,y,w,h,font=PPT_TYPE.body,extra={}){
  slide.addText(String(text),{x,y,w,h,fontFace:pptFont(),fontSize:font,color:PPT_COLOR.ink,margin:0,breakLine:false,wrap:false,valign:'mid',...extra});
}
function addPptSafeLine(slide,x1,y1,x2,y2,color,width=1,opts={}){
  const dx=x2-x1, dy=y2-y1;
  const shape={x:Math.min(x1,x2),y:Math.min(y1,y2),w:Math.abs(dx),h:Math.abs(dy),line:{color,width,transparency:opts.transparency||0}};
  if(opts.objectName)shape.objectName=opts.objectName;
  if(opts.dashType)shape.line.dashType=opts.dashType;
  if(shape.w>0&&shape.h>0&&dx*dy<0)shape.flipV=true;
  slide.addShape('line',shape);
}
function pptBalancedPages(items,max=2){
  const pages=Math.max(1,Math.ceil(items.length/max)),size=Math.floor(items.length/pages),extra=items.length%pages,out=[];let offset=0;
  for(let i=0;i<pages;i++){const count=size+(i<extra?1:0);out.push(items.slice(offset,offset+count));offset+=count;}return out;
}
/* Slide notes are collected per slide and written once, one paragraph per line, so sections never run together. */
function pptNote(slide,text){ (slide.__rsNotes||(slide.__rsNotes=[])).push(String(text)); }
function pptFlushNotes(slides){ slides.forEach(slide=>{ if(slide.__rsNotes?.length)slide.addNotes(slide.__rsNotes.join('\n\n')); }); }
function pptItemNotes(slide,items){
  if(!items.length)return;
  pptNote(slide,items.map(it=>`${it.name}\n${normValueType(it.valueType)} ${fmtMoney(itemValue(it))||'$0'}; ${exclusionLabel(it)||'Included'}; ${approvalLabel(approvalStatus(it))}; ${normStatus(it.status)}; Owner: ${it.owner||'Unassigned'}\n${it.milestone?`Milestone ${it.start?fmtDate(it.start):'unscheduled'}`:fmtDateRange(it.start,it.end)}; Realized ${fmtMoney(Math.max(0,realizedItemValue(it,exportReportingDate())))||'$0'}${it.nextStep?`\nNext step: ${it.nextStep}`:''}${it.decisionNeeded?`\nDecision needed: ${it.decisionNeeded}`:''}${it.notes?`\nNotes: ${it.notes}`:''}`).join('\n\n'));
}
function pptAddFullNameNotes(slide,entries){const names=[...new Set(entries.filter(Boolean).map(String))];if(names.length)pptNote(slide,`Full names\n${names.join('\n')}`);}
function pptFinancialTotals(items){ return portfolioTotals(items); }
function pptFiscalBands(axis,X){ const bands=[]; let fy=fqOf(axis.quarters[0],S.fyStart).fy, start=axis.quarters[0];
  axis.quarters.forEach((q,i)=>{ const qFy=fqOf(q,S.fyStart).fy; if(qFy!==fy){ bands.push({fy,start,end:q}); fy=qFy; start=q; }
    if(i===axis.quarters.length-1)bands.push({fy,start,end:axis.end}); });
  return bands.map(b=>({...b,x:X(b.start),w:X(b.end)-X(b.start)})); }
function pptPillarAxis(items){ const dated=items.filter(i=>i.start), asOf=exportReportingDate();
  let min=asOf.getTime(),max=asOf.getTime();dated.forEach(i=>{const s=i.start.getTime(),e=(i.end||i.start).getTime();if(s<min)min=s;if(e>max)max=e;});
  const start=dated.length?quarterStart(new Date(min),S.fyStart):fyStartOf(asOf,S.fyStart);
  let end=dated.length?nextQuarter(quarterStart(new Date(max),S.fyStart)):nextQuarter(start);
  const quarters=[];for(let q=start;q<end||quarters.length<4;q=nextQuarter(q))quarters.push(q);
  end=nextQuarter(quarters[quarters.length-1]);return{start,end,quarters,todayU:asOf}; }
function pptMoneyFormat(step,max){
  const [unit,suffix]=max>=1e9?[1e9,'B']:max>=1e6?[1e6,'M']:max>=1e3?[1e3,'K']:[1,''];
  const scaled=step/unit,decimals=Number.isInteger(Math.round(scaled*1e6)/1e6)?0:Number.isInteger(Math.round(scaled*10*1e6)/1e6)?1:2;
  const commas=unit===1e9?',,,':unit===1e6?',,':unit===1e3?',':'';
  return`$#,##0${decimals?'.'+'0'.repeat(decimals):''}${commas}${suffix?`"${suffix}"`:''}`;
}

/* ---------- masters ---------- */
function definePptMasters(pptx,c){
  const font=pptFont(),accent=pptAccent(),logo=S.brand?.logo,aspect=S.brand?.logoAspect||1,logoH=.42,logoW=Math.min(2.2,logoH*aspect);
  const footer=[c.project,c.scenario,`As of ${fmtDate(c.asOf)}`,c.filterLabel].filter(Boolean).join('  ·  ');
  const titleW=(logo?PPT_W-1.0-logoW-.3:PPT_W-1.0)-.22;
  const logoObjects=logo?[{image:{data:logo,x:PPT_W-.5-logoW,y:.32,w:logoW,h:logoH}}]:[];
  pptx.defineSlideMaster({title:'RS_CONTENT',background:{color:'FFFFFF'},margin:[.5,.5,.5,.5],
    objects:[{rect:{x:.5,y:.36,w:.07,h:.52,fill:{color:accent},line:{color:accent}}},...logoObjects,
      {line:{x:.5,y:6.98,w:PPT_W-1,h:0,line:{color:PPT_COLOR.hair,width:.75}}},
      {text:{text:pptBoundText(footer,10.9,PPT_TYPE.caption),options:{x:.5,y:7.04,w:11.1,h:.26,fontFace:font,fontSize:PPT_TYPE.caption,color:PPT_COLOR.muted,valign:'middle',margin:0}}},
      {placeholder:{options:{name:'slide-title',type:'title',x:.72,y:.27,w:titleW,h:.95,fontFace:font,fontSize:PPT_TYPE.title,bold:true,color:PPT_COLOR.ink,valign:'top',margin:0,align:'left'},text:''}}],
    slideNumber:{x:12.33,y:7.04,w:.5,h:.26,fontFace:font,fontSize:PPT_TYPE.caption,color:PPT_COLOR.muted,align:'right'}});
  pptx.defineSlideMaster({title:'RS_TITLE',background:{color:'FFFFFF'},margin:[.5,.5,.5,.5],
    objects:[{rect:{x:0,y:0,w:.32,h:PPT_H,fill:{color:accent},line:{color:accent}}},...(logo?[{image:{data:logo,x:1.1,y:.9,w:Math.min(3,.7*aspect),h:.7}}]:[]),
]});
}
function pptSlide(pptx,master='RS_CONTENT'){ const slide=pptx.addSlide({masterName:master}); PPT_SLIDES.push(slide); return slide; }
// Titles are action titles generated from the data; they wrap to two lines rather than shrink.
function pptTitle(slide,text){ slide.addText(pptWrapText(text,PPT_W-1.5,PPT_TYPE.title,2,true),{placeholder:'slide-title',objectName:'slide-title',fontFace:pptFont(),fontSize:PPT_TYPE.title,bold:true,color:PPT_COLOR.ink}); }
function addPptContext(slide,section,pageLabel='',overrides={}){
  const c={...exportContext(),...overrides};
  if(pageLabel)pptText(slide,pageLabel,9.3,6.68,3.53,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted,align:'right',objectName:'page-label'});
  if(c.weighted)pptText(slide,c.weighting,.5,6.68,4,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted,objectName:'weighting-label'});
  pptNote(slide,[c.project,section,[c.scenario,c.scopeLabel,pageLabel].filter(Boolean).join('  ·  '),`As of ${fmtDate(c.asOf)}`,c.baseline,c.weighted?c.weighting:'Values are not confidence-weighted',`Grouping: ${c.grouping}`,c.filterLabel,`Roadmap Studio ${c.version}`].filter(Boolean).join('\n'));
}
function pptLegend(slide,entries,y=6.68,x=.5){
  let cx=x;entries.forEach(([color,label,kind])=>{
    if(kind==='line')addPptSafeLine(slide,cx,y+.12,cx+.3,y+.12,color,1.5,{dashType:'dash'});
    else slide.addShape('rect',{x:cx,y:y+.05,w:.16,h:.14,fill:{color},line:{color}});
    const w=pptTextWidthIn(label,PPT_TYPE.caption)+.1;pptText(slide,label,cx+(kind==='line'?.36:.22),y,w,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted});cx+=w+(kind==='line'?.62:.48);
  });
}

/* ---------- action titles (data-driven, with guards) ---------- */
function summaryTitle(t,gs){
  if(!t.Total)return gs.set?`No opportunity identified yet toward the ${fmtMoneyShort(gs.goal)} goal`:'No opportunity identified yet';
  if(!gs.set)return`${fmtMoneyShort(t.Total)} identified opportunity across ${countLabel(t.FinancialCount,'initiative')}; ${fmtMoneyShort(t.Realized)} realized`;
  if(t.Approved>=gs.goal)return`Active work alone covers the ${fmtMoneyShort(gs.goal)} goal (${fmtPct(gs.activePct)}); ${fmtMoneyShort(t.Total)} identified opportunity`;
  if(t.Total>=gs.goal)return`Active work covers ${fmtPct(gs.activePct)} of the ${fmtMoneyShort(gs.goal)} goal; ${fmtMoneyShort(gs.proposedNeeded)} of the opportunity depends on Proposed`;
  return goalHeadline(gs);
}

/* ---------- 1. title slide ---------- */
function addPptTitleSlide(pptx){
  const c=exportContext(),slide=pptSlide(pptx,'RS_TITLE');
  pptText(slide,pptWrapText(c.project,11.2,40,2,true),1.1,2.35,11.2,1.6,40,{bold:true,wrap:true,valign:'bottom',objectName:'deck-title'});
  pptText(slide,pptBoundText(`${c.scenario}  ·  As of ${fmtDate(c.asOf)}`,11.2,18),1.1,4.15,11.2,.4,18,{color:PPT_COLOR.muted,objectName:'deck-subtitle'});
  if(c.filterLabel)pptText(slide,pptBoundText(c.filterLabel,11.2,PPT_TYPE.body),1.1,4.62,11.2,.3,PPT_TYPE.body,{color:PPT_COLOR.muted});
  pptText(slide,`Prepared with Roadmap Studio ${c.version}`,1.1,6.7,8,.3,PPT_TYPE.caption,{color:PPT_COLOR.muted});
  pptNote(slide,[c.project,c.scenario,`As of ${fmtDate(c.asOf)}`,c.baseline,c.filterLabel,`Roadmap Studio ${c.version}`].filter(Boolean).join('\n'));
}

/* ---------- 2. one-page summary (approved composition: two centered blocks above one continuous bar) ---------- */
/* The tracker key, shared with the web Executive Summary: one two-tone swatch per stage. */
const EXEC_LEGEND=[['realized','Realized'],['approved','Active remaining'],['proposed','Proposed remaining']];
function pptExecLegend(slide,x,y){
  let cx=x;EXEC_LEGEND.forEach(([stage,label])=>{
    ['Savings','Avoidance'].forEach((type,i)=>{const color=EXEC_COLORS[stage][type].slice(1).toUpperCase();slide.addShape('rect',{x:cx+i*.17,y:y+.06,w:.15,h:.13,fill:{color},line:{color}});});
    pptText(slide,label,cx+.42,y,2.1,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted});cx+=pptTextWidthIn(label,PPT_TYPE.caption)+.85;});
  pptText(slide,'Green = Savings · Blue = Avoidance',cx,y,3.5,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted});
}
function addPptExecutiveSummarySlide(pptx){
  const slide=pptSlide(pptx), data=executiveSummaryData(), t=data.totals, total=t.Total, gs=goalStatus(t), goal=gs.goal, stretchGoal=gs.stretch;
  const white='FFFFFF';
  addPptContext(slide,'Executive Summary');
  pptTitle(slide,summaryTitle(t,gs));
  const blockY=1.45, blockH=stretchGoal?1.74:1.62, blockW=5.0;
  const addGoalBlock=(x,fill,label,main,note,labelColor,kind,value)=>{
    slide.addShape('roundRect',{x,y:blockY,w:blockW,h:blockH,rectRadius:.08,fill:{color:fill},line:{color:fill},objectName:`summary-block:${kind}`});
    slide.addText(label,{x:x+.28,y:blockY+.19,w:blockW-.56,h:.28,fontFace:pptFont(),fontSize:16,bold:true,color:labelColor,align:'center',margin:0});
    slide.addText(main,{x:x+.28,y:blockY+.55,w:blockW-.56,h:.5,fontFace:pptFont(),fontSize:PPT_TYPE.hero,bold:true,color:white,align:'center',margin:0,objectName:`summary-metric:${kind}`});
    slide.addText(note,{x:x+.28,y:blockY+(stretchGoal?1.07:1.2),w:blockW-.56,h:.25,fontFace:pptFont(),fontSize:stretchGoal?14:16,color:'F2F2F7',align:'center',margin:0});
    if(stretchGoal)pptText(slide,`${fmtGoalProgress(value,stretchGoal)} of stretch goal`,x+.28,blockY+1.36,blockW-.56,.22,14,{color:labelColor,align:'center',objectName:`executive-stretch-${kind}`});
  };
  addGoalBlock(1.25,PPT_COLOR.ink,'IDENTIFIED OPPORTUNITY',gs.set?fmtGoalProgress(total,goal):fmtMoneyShort(total),gs.set?`${fmtMoneyShort(total)} identified toward the goal`:'Identified · no goal set','D1D1D6','identified',total);
  addGoalBlock(7.08,PPT_COLOR.savingsDark,'REALIZED',gs.set?fmtGoalProgress(t.Realized,goal):fmtMoneyShort(t.Realized),gs.set?`${fmtMoneyShort(t.Realized)} realized to date`:'Realized to date','DDF4E5','realized',t.Realized);

  const barX=.76, barY=3.88, barW=11.82, barH=.64, axisMax=executiveMeasurementMax(total,goal,stretchGoal);
  const X=value=>barX+Math.max(0,Math.min(1,value/axisMax))*barW;
  // Same six-segment bar as the web tracker: Realized, Active remaining, Proposed remaining, each split Savings/Avoidance.
  slide.addShape('roundRect',{x:barX,y:barY,w:barW,h:barH,rectRadius:.08,fill:{color:PPT_COLOR.grey2},line:{color:PPT_COLOR.grey2},objectName:'executive-bar-track'});
  let cursor=0;const segments=[];
  data.segments.forEach(seg=>{const start=X(cursor),end=X(cursor+seg.value);cursor+=seg.value;if(end-start>.001)segments.push({start,end,seg,color:EXEC_COLORS[seg.stage][seg.type].slice(1).toUpperCase(),name:`executive-segment:${seg.stage}:${seg.type}`});});
  const radius=.32;
  segments.forEach((s,index)=>{
    const width=Math.max(.01,s.end-s.start),first=index===0,last=index===segments.length-1&&Math.abs(s.end-(barX+barW))<.001,name=s.name;
    if(first||last){
      slide.addShape('roundRect',{x:s.start,y:barY,w:width,h:barH,rectRadius:.08,fill:{color:s.color},line:{color:s.color},objectName:name});
      if(first&&s.end<barX+barW)slide.addShape('rect',{x:Math.max(s.start,s.end-radius),y:barY,w:Math.min(radius,width),h:barH,fill:{color:s.color},line:{color:s.color,transparency:100}});
      if(last&&s.start>barX)slide.addShape('rect',{x:s.start,y:barY,w:Math.min(radius,width),h:barH,fill:{color:s.color},line:{color:s.color,transparency:100}});
    }else slide.addShape('rect',{x:s.start,y:barY,w:width,h:barH,fill:{color:s.color},line:{color:s.color,transparency:100},objectName:name});
  });
  const markerPositions=[...(gs.set?[X(goal)]:[]),...(stretchGoal?[X(stretchGoal)]:[])];
  // A label is placed only in the widest gap between goal markers inside its span, and only when it fits there.
  const placeLabel=(label,start,end,size,y,h,opts,avoidMarkers=true)=>{
    const edges=[start,...(avoidMarkers?markerPositions:[]).filter(x=>x>start&&x<end).sort((a,b)=>a-b),end],spaces=edges.slice(1).map((r,i)=>({start:edges[i],width:r-edges[i]})),room=spaces.sort((a,b)=>b.width-a.width)[0];
    if(end-start>.001&&room.width>=pptTextWidthIn(label,size,true)+.16)pptText(slide,label,room.start+.08,y,room.width-.16,h,size,{bold:true,align:'center',...opts});
  };
  segments.forEach(s=>placeLabel(`${s.seg.type} ${fmtMoneyShort(s.seg.value)}`,s.start,s.end,12,barY+.18,.28,{color:s.seg.stage==='proposed'?PPT_COLOR.ink:white,objectName:`executive-segment-label:${s.seg.stage}:${s.seg.type}`}));
  let stageCursor=0;
  ['realized','approved','proposed'].forEach(stage=>{
    const value=t.buckets[stage].Savings+t.buckets[stage].Avoidance,start=X(stageCursor),end=X(stageCursor+value);stageCursor+=value;
    if(value)placeLabel(`${EXEC_STAGE_NAMES[stage]} · ${fmtMoneyShort(value)}`,start,end,14,3.46,.28,{color:PPT_COLOR.muted,objectName:`executive-stage-label:${stage}`},false); // above the bar, clear of the markers
  });
  pptExecLegend(slide,.78,6.64);
  const targets=[];
  if(gs.set)targets.push({kind:'goal',value:goal,x:X(goal),color:PPT_COLOR.ink,label:'GOAL'});
  if(stretchGoal)targets.push({kind:'stretch',value:stretchGoal,x:X(stretchGoal),color:PPT_COLOR.muted,label:'STRETCH GOAL'});
  targets.forEach(target=>{
    target.amount=fmtGoalMoney(target.value);
    target.w=Math.max(pptTextWidthIn(target.amount,16,true),pptTextWidthIn(target.label,14,true))+.16;
    target.labelX=Math.max(barX,Math.min(target.x-target.w,barX+barW-target.w));
  });
  if(targets.length>1&&targets[0].labelX+targets[0].w+.2>targets[1].labelX){
    targets[0].labelX=Math.max(barX,targets[1].labelX-targets[0].w-.2);
    targets[1].labelX=Math.max(targets[1].labelX,targets[0].labelX+targets[0].w+.2);
  }
  targets.forEach(target=>{
    addPptSafeLine(slide,target.x,barY-.1,target.x,barY+barH+.06,target.color,1.7,{objectName:`executive-${target.kind}-marker`,...(target.kind==='stretch'?{dashType:'dash'}:{})});
    const anchor=Math.max(target.labelX+.04,Math.min(target.x,target.labelX+target.w-.04));
    addPptSafeLine(slide,target.x,barY+barH+.06,anchor,4.62,target.color,.75);
    pptText(slide,target.amount,target.labelX,4.66,target.w,.27,16,{bold:true,color:target.color,align:'right',objectName:`executive-${target.kind}-amount`});
    pptText(slide,target.label,target.labelX,4.97,target.w,.24,14,{bold:true,color:target.color,align:'right',objectName:`executive-${target.kind}-label`});
  });
  const axisY=5.3;
  addPptSafeLine(slide,barX,axisY,barX+barW,axisY,PPT_COLOR.hair,.75,{objectName:'executive-axis'});
  for(let i=0;i<=4;i++){
    const value=axisMax*i/4,x=X(value),label=fmtGoalMoney(value),w=pptTextWidthIn(label,14)+.12;
    const labelX=Math.max(barX,Math.min(x-w/2,barX+barW-w));
    addPptSafeLine(slide,x,axisY-.05,x,axisY,PPT_COLOR.muted,.75,{objectName:`executive-axis-tick:${i}`});
    pptText(slide,label,labelX,axisY+.08,w,.24,14,{color:PPT_COLOR.muted,align:i===0?'left':i===4?'right':'center',objectName:`executive-axis-label:${i}`});
  }
  pptText(slide,`Savings ${fmtMoneyShort(t.Savings)}`,.78,5.82,4.0,.38,PPT_TYPE.metric,{bold:true,color:PPT_COLOR.savings});
  pptText(slide,`${fmtMoneyShort(t.RealizedSavings)} realized savings`,.78,6.24,4.0,.3,PPT_TYPE.body,{color:PPT_COLOR.savingsDark});
  pptText(slide,`Avoidance ${fmtMoneyShort(t.Avoidance)}`,5.05,5.82,4.3,.38,PPT_TYPE.metric,{bold:true,color:PPT_COLOR.avoidance});
  pptText(slide,`${fmtMoneyShort(t.RealizedAvoidance)} realized avoidance`,5.05,6.24,4.3,.3,PPT_TYPE.body,{color:PPT_COLOR.avoidanceDark});
  pptText(slide,goalGapText(gs),9.5,5.82,3.08,.38,PPT_TYPE.metric,{bold:true,align:'right',objectName:'summary-gap'});
  if(t.RealizedBeyondPlan>0)pptText(slide,`${fmtMoneyShort(t.RealizedBeyondPlan)} of actuals exceed plan and are not added to identified value`,9.0,6.24,3.58,.3,PPT_TYPE.caption,{color:PPT_COLOR.muted,align:'right',wrap:true});
  pptNote(slide,`Goal: ${gs.set?fmtMoney(goal):'No goal set'}.${stretchGoal?` Stretch goal entered independently: ${fmtMoney(stretchGoal)}. Stretch percentages use this amount, with no automatic multiplier.`:''} Identified value is lifetime planned Savings plus Avoidance for included initiatives (Active and Proposed), unweighted; this is the one goal basis used on every slide. The dollar scale matches the Executive Summary web tracker, from $0 to ${fmtGoalMoney(axisMax)}; the scale endpoint is not an additional goal.`);
  pptNote(slide,`Realized: ${fmtMoney(t.Realized)} (recorded actual dollars where entered, otherwise realization percentages or dated phases; never confidence-weighted). The bar matches the web tracker: each planned dollar appears once, as Realized, Active remaining, or Proposed remaining, each split Savings/Avoidance; realized value is capped at each initiative's plan${t.RealizedBeyondPlan>0?`; ${fmtMoney(t.RealizedBeyondPlan)} of actuals exceed plan`:''}.`);
}

/* ---------- 3. bridge to goal (native, editable waterfall) ---------- */
function addPptBridgeSlide(pptx){
  const slide=pptSlide(pptx),t=portfolioTotals(),gs=goalStatus(t);
  addPptContext(slide,'Bridge to goal');
  const realized=t.buckets.realized.Savings+t.buckets.realized.Avoidance,active=t.buckets.approved.Savings+t.buckets.approved.Avoidance,proposed=t.buckets.proposed.Savings+t.buckets.proposed.Avoidance;
  pptTitle(slide,!t.Total?'No value identified yet':gs.set?(gs.gap>0?`${fmtMoneyShort(active+proposed)} still to deliver and ${fmtMoneyShort(gs.gap)} not yet identified for the ${fmtMoneyShort(gs.goal)} goal`:`Identified value reaches ${fmtMoneyShort(t.Total)}, ${fmtMoneyShort(-gs.gap)} beyond the ${fmtMoneyShort(gs.goal)} goal; ${fmtMoneyShort(active+proposed)} still to deliver`):`${fmtMoneyShort(active+proposed)} of identified value still to deliver`);
  const labels=['Realized within plan','Active remaining','Proposed remaining','Identified'],base=[0,realized,realized+active,0],value=[realized,active,proposed,t.Total];
  if(gs.set&&gs.gap>0){labels.push('Gap to goal','Goal');base.push(t.Total,0);value.push(gs.gap,gs.goal);}
  else if(gs.set){labels.push('Goal');base.push(0);value.push(gs.goal);}
  const colors=[PPT_COLOR.savingsDark,PPT_COLOR.savings,PPT_COLOR.savingsLight,PPT_COLOR.ink,...(gs.set&&gs.gap>0?[PPT_COLOR.grey1]:[]),PPT_COLOR.muted];
  const axis=niceAxis(Math.max(t.Total,gs.goal||0)*1.08);
  const series=[{name:'Base',labels,values:base},...labels.map((label,i)=>({name:label,labels,values:labels.map((_,j)=>j===i?value[i]:0)}))];
  slide.addChart(pptx.ChartType.bar,series,{x:.5,y:1.45,w:8.4,h:4.95,barDir:'col',barGrouping:'stacked',barGapWidthPct:55,
    chartColors:['FFFFFF',...colors.slice(0,labels.length)],chartColorsOpacity:100,showLegend:false,showValue:false,
    valAxisMinVal:0,valAxisMaxVal:axis.max,valAxisMajorUnit:axis.step,valAxisLabelFormatCode:pptMoneyFormat(axis.step,axis.max),valAxisLabelFontSize:PPT_TYPE.caption,valAxisLabelColor:PPT_COLOR.muted,
    catAxisLabelFontSize:PPT_TYPE.caption,catAxisLabelColor:PPT_COLOR.ink,catAxisLineShow:false,valAxisLineShow:false,
    valGridLine:{color:PPT_COLOR.hair,size:.5},catGridLine:{style:'none'},fontFace:pptFont(),objectName:'bridge-chart',altText:'Bridge from realized value to the portfolio goal'});
  const rows=[['Realized within plan',realized,PPT_COLOR.savingsDark],['Active remaining',active,PPT_COLOR.savings],['Proposed remaining',proposed,PPT_COLOR.savingsLight],['Identified',t.Total,PPT_COLOR.ink]];
  if(gs.set)rows.push([gs.gap>0?'Gap to goal':'Above goal',Math.abs(gs.gap),gs.gap>0?PPT_COLOR.grey1:PPT_COLOR.savings],['Goal',gs.goal,PPT_COLOR.muted]);
  let y=1.7;rows.forEach(([label,amount,color])=>{slide.addShape('rect',{x:9.35,y:y+.08,w:.16,h:.16,fill:{color},line:{color:PPT_COLOR.grey1,width:.5}});
    pptText(slide,label,9.62,y,2.0,.32,PPT_TYPE.body,{color:PPT_COLOR.ink});pptText(slide,fmtMoneyShort(amount),11.4,y,1.43,.32,PPT_TYPE.body,{bold:true,align:'right',objectName:`bridge-value:${label}`});y+=.5;});
  if(t.RealizedBeyondPlan>0){pptText(slide,`Realized to date is ${fmtMoneyShort(t.Realized)}: ${fmtMoneyShort(t.RealizedBeyondPlan)} of actuals exceed plan and are not added to identified value.`,9.35,y+.05,3.48,.6,PPT_TYPE.caption,{color:PPT_COLOR.muted,wrap:true,valign:'top'});y+=.7;}
  if(!gs.set)pptText(slide,'No goal set: enter a portfolio goal to show the gap.',9.35,y+.1,3.5,.5,PPT_TYPE.caption,{color:PPT_COLOR.muted,wrap:true,valign:'top'});
  pptNote(slide,`Bridge on the headline basis: identified planned value (Active + Proposed, lifetime, unweighted). Realized ${fmtMoney(realized)} is capped at each initiative's plan; Active remaining ${fmtMoney(active)}; Proposed remaining ${fmtMoney(proposed)}; Identified ${fmtMoney(t.Total)}.${gs.set?` Goal ${fmtMoney(gs.goal)}; ${gs.gap>0?`gap ${fmtMoney(gs.gap)}`:`above goal by ${fmtMoney(-gs.gap)}`}.`:' No goal set.'} The chart is a native stacked column chart with a transparent base series, so values stay editable.`);
}

/* ---------- 4. timing: when each pillar's Active and Proposed work runs (no dollars on the time axis) ---------- */
function addPptPortfolioRollupSlide(pptx){
  const data=portfolioRollupData(),pages=pptBalancedPages(data.groups||[],5),timeX=4.2,timeW=8.6,bodyY=2.0,groupH=.86;
  const span=data.axisEnd-data.axisStart,X=d=>timeX+Math.max(0,Math.min(1,(d-data.axisStart)/span))*timeW;
  const undated=data.items.filter(row=>!row.start);
  pages.forEach((groups,pageIndex)=>{
    const slide=pptSlide(pptx);addPptContext(slide,'Portfolio Rollup',pages.length>1?`Timing ${pageIndex+1}/${pages.length}`:'');
    pptTitle(slide,pageIndex?'Portfolio Rollup (continued)':!data.items.length?'Portfolio Rollup: no initiatives to schedule':`Portfolio Rollup: work runs ${data.minYear}–${data.maxYear}${undated.length?`; ${undated.length} undated (${fmtMoneyShort(undated.reduce((s,r)=>s+r.value,0))})`:''}`);
    if(!data.items.length){pptText(slide,'No included initiatives',.6,2.2,11,.5,PPT_TYPE.body,{color:PPT_COLOR.muted});return;}
    const bottom=bodyY+Math.max(1,groups.length)*groupH;
    data.years.forEach((year,i)=>{const x=X(year),nx=X(utc(year.getUTCFullYear()+1,year.getUTCMonth(),1));
      if(i%2)slide.addShape('rect',{x,y:1.62,w:nx-x,h:bottom-1.62,fill:{color:'F7F8FA'},line:{transparency:100}});
      addPptSafeLine(slide,x,1.62,x,bottom,PPT_COLOR.hair,.6);
      if(nx-x>.5)pptText(slide,data.fyName(year),x,1.64,nx-x,.26,PPT_TYPE.caption,{bold:true,align:'center',color:PPT_COLOR.muted});});
    const asOfX=X(exportReportingDate());addPptSafeLine(slide,asOfX,1.9,asOfX,bottom,PPT_COLOR.muted,.9,{dashType:'dash',objectName:'rollup-asof'});
    pptText(slide,`As of ${fmtDate(exportReportingDate())}`,Math.min(asOfX+.05,timeX+timeW-1.6),bottom+.04,1.6,.22,PPT_TYPE.caption,{color:PPT_COLOR.muted});
    groups.forEach((group,i)=>{
      const y=bodyY+i*groupH;addPptSafeLine(slide,.5,y,12.83,y,PPT_COLOR.hair,.6);
      pptText(slide,pptBoundText(group.p.name,3.55,PPT_TYPE.body,true),.5,y+.06,3.6,.3,PPT_TYPE.body,{bold:true,objectName:`rollup-pillar:${group.p.id}`});
      APPROVAL_STATES.forEach((approval,ai)=>{
        const b=group.summary[approval],ly=y+.38+ai*.22;
        pptText(slide,`${approvalLabel(approval)} · ${b.count}${b.undatedCount?` (${b.undatedCount} undated)`:''}`,.5,ly-.02,3.6,.22,PPT_TYPE.caption,{color:PPT_COLOR.muted});
        if(!b.start)return;
        const sx=X(b.start),ex=X(addDays(b.end,1)),bw=Math.max(.04,ex-sx),color=approval==='Approved'?PPT_COLOR.ink:PPT_COLOR.grey1;
        slide.addShape('roundRect',{x:sx,y:ly+.01,w:bw,h:.16,rectRadius:.04,fill:{color},line:{color},objectName:`rollup-bar:${group.p.id}:${approval}`});
        const label=`${b.scheduledCount} ${approvalLabel(approval).toLowerCase()} · ${fmtDate(b.start)} – ${fmtDate(b.end)}`;
        if(pptTextWidthIn(label,PPT_TYPE.caption)+.2<timeX+timeW-ex)pptText(slide,label,ex+.08,ly-.03,timeX+timeW-ex-.08,.22,PPT_TYPE.caption,{color:PPT_COLOR.muted});
      });
    });
    pptLegend(slide,[[PPT_COLOR.ink,'Active'],[PPT_COLOR.grey1,'Proposed'],[PPT_COLOR.muted,'As of','line']],6.68,4.2);
    pptAddFullNameNotes(slide,groups.map(g=>g.p.name));
    pptNote(slide,`${countLabel(data.items.length,'included initiative')}; ${data.excludedCount} excluded.\nActive value: ${fmtMoney(data.totals.Approved)}\nProposed value: ${fmtMoney(data.totals.Proposed)}\nRealized: ${fmtMoney(data.totals.Realized)}\nBars span the earliest start to the latest end of scheduled initiatives in each pillar and stage; undated initiatives are counted beside each stage. Dollar values are on the Pillar Contribution slide, not on the time axis.`);
  });
}

/* ---------- 5. projection (native, editable line chart with round ticks) ---------- */
function projectionChartSeries(end){
  const data=projectionPoints(end),baseline=S.showBaseline!==false?baselineProjectionPoints(end):null;
  if(!data.items.length)return{data,baseline,labels:[],series:[]};
  const months=[];let cursor=utc(data.axis.start.getUTCFullYear(),data.axis.start.getUTCMonth()+1,0);
  const monthly=(end-data.axis.start)/MS_DAY<=5.5*366;
  while(cursor<end){months.push(cursor);cursor=monthly?utc(cursor.getUTCFullYear(),cursor.getUTCMonth()+2,0):utc(cursor.getUTCFullYear(),cursor.getUTCMonth()+4,0);}
  months.push(end);
  const series=projectionSeries(data.items,months),labels=months.map(d=>`${d.toLocaleDateString('en-US',{month:'short',timeZone:'UTC'})} ${String(d.getUTCFullYear()).slice(2)}`);
  const out=[{name:'Savings + Avoidance',labels,values:months.map((_,i)=>series.Savings[i]+series.Avoidance[i]),color:PPT_COLOR.avoidance,width:2.75},
    {name:'Savings only',labels,values:series.Savings.slice(),color:PPT_COLOR.savings,width:2.25}];
  if(S.projectionShowRealized!==false)out.push({name:'Realized to date',labels,values:series.Realized.slice(),color:'70757D',width:1.5,dash:true});
  if(baseline?.items?.length){const b=projectionSeries(baseline.items,months);out.push({name:'Baseline',labels,values:months.map((_,i)=>b.Savings[i]+b.Avoidance[i]),color:'905C43',width:1.5,dash:true});}
  return{data,baseline,labels,series:out,months};
}
function addPptProjectionSlide(pptx){
  const slide=pptSlide(pptx),end=selectedProjectionEnd(),chart=projectionChartSeries(end),data=chart.data,totals=projectionTotalsAt(data.items,end),gs=goalStatus(),run=data.run;
  addPptContext(slide,'Projection','',{weighted:true});
  const weighted=S.weightConfidence!==false?' (confidence-weighted)':'';
  pptTitle(slide,!data.items.length?'Projection: no dated financial initiatives':`${fmtMoneyShort(totals.Combined)} projected by ${fmtDate(end)}${weighted}${gs.set?`, ${fmtGoalProgress(totals.Combined,gs.goal)} of the ${fmtMoneyShort(gs.goal)} goal`:''}`);
  pptNote(slide,`Projection through ${fmtDate(end)}${weighted}\nSavings ${fmtMoney(totals.Savings)}\nAvoidance ${fmtMoney(totals.Avoidance)}\nRealized ${fmtMoney(totals.Realized)}\nExpected (planned × confidence, all dated work) ${fmtMoney(run.expected)}\nAnnualized recurring run-rate ${fmtMoney(run.annualized)}\n${chart.baseline?.points?.length?`Baseline ${fmtMoney(chart.baseline.points.at(-1).Combined)}; change ${fmtMoney(totals.Combined-chart.baseline.points.at(-1).Combined)}`:'No baseline'}\nGoal comparisons use identified value on the summary; this slide reports the projection as a share of the goal. Undated work cannot be projected. Actuals are never confidence-weighted.`);
  if(!data.items.length){pptText(slide,'Add dates and values to initiatives to project value over time.',.6,2.2,11,.5,PPT_TYPE.body,{color:PPT_COLOR.muted});return;}
  let dataMax=0;chart.series.forEach(s=>s.values.forEach(v=>{if(v>dataMax)dataMax=v;}));
  const showGoal=gs.set&&gs.goal<=Math.max(dataMax,1)*1.8;
  const axis=niceAxis(Math.max(dataMax,showGoal?gs.goal:0)*1.04);
  const series=[...chart.series];if(showGoal)series.push({name:'Goal',labels:chart.labels,values:chart.labels.map(()=>gs.goal),color:PPT_COLOR.ink,width:1.25,dash:true});
  const solid=series.filter(s=>!s.dash),dashed=series.filter(s=>s.dash);
  const common={valAxisMinVal:0,valAxisMaxVal:axis.max,valAxisMajorUnit:axis.step,valAxisLabelFormatCode:pptMoneyFormat(axis.step,axis.max),valAxisLabelFontSize:PPT_TYPE.caption,valAxisLabelColor:PPT_COLOR.muted,
    catAxisLabelFontSize:PPT_TYPE.caption,catAxisLabelColor:PPT_COLOR.muted,catAxisLabelFrequency:Math.max(1,Math.ceil(chart.labels.length/10)),valGridLine:{color:PPT_COLOR.hair,size:.5},catGridLine:{style:'none'},
    showLegend:false,lineDataSymbol:'none',fontFace:pptFont()};
  const group=(list,dash)=>({type:pptx.ChartType.line,data:list.map(s=>({name:s.name,labels:s.labels,values:s.values})),options:{chartColors:list.map(s=>s.color),lineSize:dash?1.5:2.5,...(dash?{lineDash:'dash'}:{})}});
  const groups=[group(solid,false),...(dashed.length?[group(dashed,true)]:[])];
  slide.addChart(groups,{x:.5,y:1.45,w:9.2,h:4.95,...common,objectName:'projection-chart',altText:'Projected Savings and Avoidance over time'});
  let y=1.75;series.forEach(s=>{
    addPptSafeLine(slide,9.95,y+.14,10.3,y+.14,s.color,s.dash?1.5:2.5,{dashType:s.dash?'dash':undefined});
    pptText(slide,s.name,10.4,y,2.4,.28,PPT_TYPE.body,{color:s.color==='70757D'?PPT_COLOR.muted:s.color,objectName:`projection-label:${s.name}`});
    pptText(slide,fmtMoneyShort(s.values.at(-1)),10.4,y+.28,2.4,.3,PPT_TYPE.metric-4,{bold:true,color:s.color==='70757D'?PPT_COLOR.muted:s.color,objectName:`projection-value:${s.name}`});y+=.72;});
  if(gs.set&&!showGoal)pptText(slide,`Goal ${fmtMoneyShort(gs.goal)} is above this scale`,9.95,y,2.85,.3,PPT_TYPE.caption,{color:PPT_COLOR.muted});
  pptText(slide,`Avoidance adds ${fmtMoneyShort(totals.Avoidance)} · as of ${fmtDate(exportReportingDate())}`,5.5,6.68,7.3,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted,align:'right'});
}

/* ---------- 6. pillar contribution (native, editable stacked bars + separate dollar and share columns) ---------- */
function contributionTitle(rows,total){
  const live=rows.filter(r=>r.Combined>0);if(!live.length)return'Pillar Contribution: no financial values';
  const top=[...live].sort((a,b)=>b.Combined-a.Combined)[0],share=top.Combined/total*100;
  if(live.length===1)return`All identified value sits in ${top.p.name}`;
  if(share>=1.5*100/live.length)return`${top.p.name} carries ${fmtPct(share)} of identified value`;
  return`Value is spread across ${live.length} pillars; the largest, ${top.p.name}, holds ${fmtPct(share)}`;
}
function addPptStackedSlide(pptx){
  const rows=stackedPillarRows().filter(r=>r.Combined>0||r.Realized>0),total=rows.reduce((s,r)=>s+r.Combined,0),pages=pptBalancedPages(rows,10);
  pages.forEach((page,pageIndex)=>{
    const slide=pptSlide(pptx);addPptContext(slide,'Pillar Contribution',pages.length>1?`Pillars ${pageIndex+1}/${pages.length}`:'');
    pptTitle(slide,pageIndex?'Pillar Contribution (continued)':contributionTitle(rows,total));
    pptNote(slide,'Pillar Contribution\nBars show each pillar\'s identified value split into Realized, Active remaining, and Proposed remaining (the same basis as the summary). Dollar values and percentage shares are separate columns. Pillars keep structure order on every slide.');
    if(!page.length){pptText(slide,'Add Savings or Avoidance values to see pillar contribution.',.6,2.2,11,.5,PPT_TYPE.body,{color:PPT_COLOR.muted});return;}
    const names=page.map(r=>pptBoundText(r.p.name,2.5,PPT_TYPE.caption));
    const stage=(key)=>page.map(r=>r.totals.buckets[key].Savings+r.totals.buckets[key].Avoidance);
    const h=Math.min(4.95,.45*page.length+.6),axis=niceAxis(Math.max(...page.map(r=>r.Combined),1)*1.04);
    slide.addChart(pptx.ChartType.bar,[{name:'Realized',labels:names,values:stage('realized')},{name:'Active remaining',labels:names,values:stage('approved')},{name:'Proposed remaining',labels:names,values:stage('proposed')}],
      {x:.5,y:1.45,w:6.3,h,barDir:'bar',barGrouping:'stacked',barGapWidthPct:45,catAxisOrientation:'maxMin',chartColors:[PPT_COLOR.savingsDark,PPT_COLOR.savings,PPT_COLOR.savingsLight],
        valAxisMinVal:0,valAxisMaxVal:axis.max,valAxisMajorUnit:axis.step,valAxisLabelFormatCode:pptMoneyFormat(axis.step,axis.max),valAxisLabelFontSize:PPT_TYPE.caption,valAxisLabelColor:PPT_COLOR.muted,
        catAxisLabelFontSize:PPT_TYPE.caption,catAxisLabelColor:PPT_COLOR.ink,valGridLine:{color:PPT_COLOR.hair,size:.5},catGridLine:{style:'none'},showLegend:false,fontFace:pptFont(),objectName:'contribution-chart',altText:'Identified value by pillar'});
    pptLegend(slide,[[PPT_COLOR.savingsDark,'Realized'],[PPT_COLOR.savings,'Active remaining'],[PPT_COLOR.savingsLight,'Proposed remaining']],Math.min(6.68,1.5+h),.6);
    // Savings-only and Savings + Avoidance shares are separate columns, each summing to 100% (as on the web view).
    const savingsTotal=rows.reduce((s,r)=>s+r.Savings,0),col={name:7.0,s:8.95,sp:9.95,c:10.85,cp:12.0},headY=1.5,rowH=Math.min(.45,4.6/page.length);
    pptText(slide,'Pillar',col.name,headY,1.8,.26,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted});
    [[col.s,.95,'Savings $'],[col.sp,.8,'Share'],[col.c,1.05,'Total $'],[col.cp,.83,'Share']].forEach(([x,w,label])=>pptText(slide,label,x,headY,w,.26,PPT_TYPE.caption,{bold:true,align:'right',color:PPT_COLOR.muted}));
    addPptSafeLine(slide,col.name,headY+.32,12.83,headY+.32,PPT_COLOR.hair,.6);
    page.forEach((row,i)=>{const y=headY+.4+i*rowH;
      pptText(slide,pptBoundText(row.p.name,1.85,PPT_TYPE.body,true),col.name,y,1.88,.3,PPT_TYPE.body,{bold:true,objectName:`contribution-pillar:${row.p.id}`});
      pptText(slide,fmtMoneyShort(row.Savings),col.s,y,.95,.3,PPT_TYPE.body,{align:'right',objectName:`contribution-dollar:savings:${row.p.id}`});
      pptText(slide,fmtPct(savingsTotal?row.Savings/savingsTotal*100:0),col.sp,y,.8,.3,PPT_TYPE.body,{align:'right',color:PPT_COLOR.muted,objectName:`contribution-share:savings:${row.p.id}`});
      pptText(slide,fmtMoneyShort(row.Combined),col.c,y,1.05,.3,PPT_TYPE.body,{align:'right',bold:true,objectName:`contribution-dollar:combined:${row.p.id}`});
      pptText(slide,fmtPct(total?row.Combined/total*100:0),col.cp,y,.83,.3,PPT_TYPE.body,{align:'right',objectName:`contribution-share:combined:${row.p.id}`});
      addPptSafeLine(slide,col.name,y+rowH-.04,12.83,y+rowH-.04,PPT_COLOR.hair,.4);});
    pptAddFullNameNotes(slide,page.map(r=>r.p.name));
  });
}

/* ---------- 7. pillar roadmap pages: up to ten rows, workstream headers, value column, realized fill ---------- */
const ROADMAP_ROWS_PER_PAGE=10;
function pptRoadmapGroups(items=S.items){
  if(S.roadmapGroup!=='owner')return S.structure.map(p=>({p,items:items.filter(it=>it.pillarId===p.id),kind:'Pillar'}));
  const owners=[...new Set(items.map(it=>it.owner||'Unassigned'))].sort((a,b)=>a==='Unassigned'?1:b==='Unassigned'?-1:a.localeCompare(b));
  return owners.map((owner,index)=>{const id=`ppt-owner-${index}`,list=items.filter(it=>(it.owner||'Unassigned')===owner).map(it=>({...it,wsId:id}));
    return{p:{id:`owner:${owner}`,name:owner,workstreams:[{id,name:countLabel(list.length,'initiative')}]},items:list,kind:'Owner'};});
}
function pptRoadmapRows(p,items){
  const order=new Map((p.workstreams||[]).map((w,i)=>[w.id,i])),rows=[];
  const sorted=[...items].sort((a,b)=>(order.get(a.wsId)??1e9)-(order.get(b.wsId)??1e9)||(a.start||Infinity)-(b.start||Infinity));
  let current=null;
  sorted.forEach(it=>{
    if(it.wsId!==current){current=it.wsId;const ws=(p.workstreams||[]).find(w=>w.id===it.wsId);
      const wsItems=sorted.filter(x=>x.wsId===it.wsId),t=portfolioTotals(wsItems);rows.push({kind:'ws',name:ws?.name||'Unassigned',wsId:it.wsId,value:t.Total});}
    rows.push({kind:'item',it});
  });
  return rows;
}
function pptPaginateRoadmap(rows){
  const pages=[];let page=[],lastHeader=null;
  rows.forEach(row=>{
    if(row.kind==='ws')lastHeader=row;
    if(page.length>=ROADMAP_ROWS_PER_PAGE||(row.kind==='ws'&&page.length>=ROADMAP_ROWS_PER_PAGE-1)){pages.push(page);page=[];if(row.kind==='item'&&lastHeader)page.push({...lastHeader,continued:true});}
    page.push(row);
  });
  if(page.length||!pages.length)pages.push(page);
  return pages;
}
function pillarPageTitle(p,t,items,kind){
  const risk=items.filter(it=>isRiskStatus(it.status)).length;
  if(!items.length)return`${p.name}: no initiatives yet`;
  if(!t.Total)return`${p.name}: ${countLabel(items.length,'initiative')}, no value entered`;
  return`${p.name}: ${fmtMoneyShort(t.Total)} identified, ${fmtMoneyShort(t.Realized)} realized${risk?`; ${risk} at risk or blocked`:''}`;
}
function addPptStatusPill(slide,status,x,y,objectName){
  const [fill,ink]=PPT_STATUS_PILL[status]||PPT_STATUS_PILL['Not Started'],w=pptTextWidthIn(status,PPT_TYPE.caption,true)+.2;
  slide.addShape('roundRect',{x,y,w,h:.22,rectRadius:.11,fill:{color:fill},line:{color:fill},objectName});
  pptText(slide,status,x,y,w,.22,PPT_TYPE.caption,{bold:true,color:ink,align:'center'});
  return w;
}
function addPptPillarSlide(pptx,p,idx,total,options={}){
  const allItems=options.items||S.items.filter(i=>i.pillarId===p.id),totals=portfolioTotals(allItems),axis=options.axis||pptPillarAxis(allItems);
  const pages=pptPaginateRoadmap(pptRoadmapRows(p,allItems)),nameX=.5,nameW=3.55,timeX=5.25,timeW=6.15,valueX=11.5,valueW=1.33,bodyY=1.95,rowH=.43;
  const X=d=>timeX+Math.max(0,Math.min(1,(d-axis.start)/(axis.end-axis.start)))*timeW;
  pages.forEach((rows,pageIndex)=>{
    const slide=pptSlide(pptx);addPptContext(slide,'Roadmap',`${options.kind||'Pillar'} ${idx+1}/${total}${pages.length>1?` · Page ${pageIndex+1}/${pages.length}`:''}`);
    pptTitle(slide,pageIndex?`${p.name} (continued)`:pillarPageTitle(p,totals,allItems,options.kind));
    const bottom=bodyY+Math.max(1,rows.length)*rowH;
    pptText(slide,'Initiative',nameX,1.62,2,.24,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted});
    pptText(slide,'Value',valueX,1.62,valueW,.24,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted,align:'right'});
    pptFiscalBands(axis,X).forEach((band,i)=>{
      if(i%2)slide.addShape('rect',{x:band.x,y:1.4,w:band.w,h:bottom-1.4,fill:{color:'F7F8FA'},line:{transparency:100}});
      if(band.w>.5)pptText(slide,fyLabel(band.fy),band.x,1.4,band.w,.22,PPT_TYPE.caption,{bold:true,align:'center',color:PPT_COLOR.muted});
    });
    axis.quarters.forEach(q=>{const x=X(q),w=X(nextQuarter(q))-x;addPptSafeLine(slide,x,1.62,x,bottom,PPT_COLOR.hair,.5);
      if(w>.32)pptText(slide,`Q${fqOf(q,S.fyStart).q}`,x,1.63,w,.22,PPT_TYPE.caption,{color:PPT_COLOR.muted,align:'center'});});
    const asOfX=X(axis.todayU);addPptSafeLine(slide,asOfX,1.88,asOfX,bottom,PPT_COLOR.muted,.9,{dashType:'dash',objectName:'roadmap-asof'});
    const asOfLabel=`As of ${fmtDate(axis.todayU)}`,asOfW=pptTextWidthIn(asOfLabel,PPT_TYPE.caption)+.1;
    pptText(slide,asOfLabel,Math.max(timeX,Math.min(asOfX-asOfW/2,timeX+timeW-asOfW)),bottom+.03,asOfW,.22,PPT_TYPE.caption,{color:PPT_COLOR.muted,align:'center',objectName:'roadmap-asof-label'});
    if(!rows.length)pptText(slide,'No initiatives in this pillar',nameX,bodyY+.05,8,.3,PPT_TYPE.body,{color:PPT_COLOR.muted});
    rows.forEach((row,rowIndex)=>{
      const y=bodyY+rowIndex*rowH;
      if(row.kind==='ws'){
        slide.addShape('rect',{x:nameX,y:y+.04,w:12.33,h:rowH-.08,fill:{color:PPT_COLOR.grey2},line:{transparency:100}});
        pptText(slide,pptBoundText(`${row.name}${row.continued?' (continued)':''}`.toUpperCase(),timeX-nameX-.2,PPT_TYPE.caption,true),nameX+.1,y,timeX-nameX-.2,rowH,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted,charSpacing:.5,objectName:`workstream-header:${row.wsId}`});
        if(!row.continued)pptText(slide,fmtMoneyShort(row.value),valueX,y,valueW,rowH,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted,align:'right'});
        return;
      }
      const it=row.it,status=normStatus(it.status),type=normValueType(it.valueType),value=itemValue(it),realized=Math.max(0,realizedItemValue(it,exportReportingDate()));
      const pillW=pptTextWidthIn(status,PPT_TYPE.caption,true)+.2,nameRoom=timeX-nameX-pillW-.25;
      const name=pptBoundText(it.name||'Untitled initiative',nameRoom,PPT_TYPE.body,true);
      pptText(slide,name,nameX,y,nameRoom,rowH,PPT_TYPE.body,{bold:true,objectName:`initiative-label:${it.id}`,color:status==='Cancelled'?PPT_COLOR.muted:PPT_COLOR.ink});
      addPptStatusPill(slide,status,timeX-pillW-.12,y+(rowH-.22)/2,`initiative-status:${it.id}`);
      pptText(slide,isIncludedInTotals(it)?fmtMoneyShort(value):`(${fmtMoneyShort(value)})`,valueX,y,valueW,rowH,PPT_TYPE.body,{align:'right',color:isIncludedInTotals(it)?PPT_COLOR.ink:PPT_COLOR.muted,objectName:`initiative-value:${it.id}`});
      addPptSafeLine(slide,nameX,y+rowH,12.83,y+rowH,PPT_COLOR.hair,.4);
      if(!it.start){pptText(slide,'Undated',timeX+.08,y,1.4,rowH,PPT_TYPE.caption,{italic:true,color:PPT_COLOR.muted,objectName:`initiative-undated:${it.id}`});return;}
      // Same marks as the web roadmap: type colour for planned value, darker shade for the realized share.
      const [base,dark]=type==='Avoidance'?[PPT_COLOR.avoidance,PPT_COLOR.avoidanceDark]:[PPT_COLOR.savings,PPT_COLOR.savingsDark];
      const by=y+(rowH-.2)/2;
      if(it.milestone){slide.addShape('diamond',{x:X(it.start)-.1,y:by-.01,w:.2,h:.22,fill:{color:dark},line:{color:dark},objectName:`initiative-bar:${it.id}`});return;}
      const sx=X(it.start),ex=X(addDays(it.end||it.start,1)),bw=Math.max(.04,ex-sx),ratio=value?Math.min(1,realized/value):0;
      slide.addShape('roundRect',{x:sx,y:by,w:bw,h:.2,rectRadius:.05,fill:{color:base},line:{color:isRiskStatus(status)?PPT_COLOR.risk:base,width:isRiskStatus(status)?1.25:.5},objectName:`initiative-bar:${it.id}`});
      if(ratio>0)slide.addShape('roundRect',{x:sx,y:by,w:Math.max(.04,bw*ratio),h:.2,rectRadius:.05,fill:{color:dark},line:{color:dark,width:.5},objectName:`initiative-realized:${it.id}`});
    });
    pptLegend(slide,[[PPT_COLOR.savings,'Savings planned'],[PPT_COLOR.savingsDark,'Savings realized'],[PPT_COLOR.avoidance,'Avoidance planned'],[PPT_COLOR.avoidanceDark,'Avoidance realized'],[PPT_COLOR.risk,'Amber outline = at risk or blocked'],['EEF0F3','Pill = status']]);
    const items=rows.filter(r=>r.kind==='item').map(r=>r.it);
    pptAddFullNameNotes(slide,[p.name,...rows.filter(r=>r.kind==='ws').map(r=>r.name)]);pptItemNotes(slide,items);
  });
}
function addPptRoadmapSlides(pptx){const groups=pptRoadmapGroups(),axis=pptPillarAxis(S.items);groups.forEach((group,index)=>addPptPillarSlide(pptx,group.p,index,groups.length,{...group,axis}));}

/* ---------- since last review (from the baseline) ---------- */
function addPptSinceReviewSlide(pptx){
  const d=sinceReviewData();if(!d)return;
  const slide=pptSlide(pptx);addPptContext(slide,'Since last review');
  const when=new Date(d.savedAt||0).toLocaleDateString('en-US',{dateStyle:'medium'});
  pptTitle(slide,`Since ${when}: identified value ${d.delta>=0?'+':''}${fmtMoneyShort(d.delta)}; ${d.added.length} added, ${d.dropped.length} dropped, ${d.slipped.length} slipped`);
  const cols=[['Added',d.added,r=>fmtMoneyShort(r.value)],['Dropped',d.dropped,r=>fmtMoneyShort(r.value)],['Value moved',d.valueMoved,r=>`${r.delta>=0?'+':''}${fmtMoneyShort(r.delta)}`],['Dates slipped',d.slipped,r=>r.days!=null?`+${r.days} days`:'end cleared']];
  cols.forEach(([title,rows,detail],i)=>{
    const x=.5+i*3.13,w=2.95;
    pptText(slide,`${title} (${rows.length})`,x,1.5,w,.3,PPT_TYPE.body,{bold:true});
    addPptSafeLine(slide,x,1.86,x+w,1.86,PPT_COLOR.hair,.6);
    rows.slice(0,8).forEach((row,j)=>{const y=1.95+j*.55;
      pptText(slide,pptWrapText(row.item.name||'Untitled initiative',w-.9,PPT_TYPE.body,2),x,y,w-.9,.5,PPT_TYPE.body,{wrap:true,valign:'top'});
      pptText(slide,detail(row),x+w-.88,y,.88,.25,PPT_TYPE.caption,{align:'right',color:PPT_COLOR.muted,valign:'top'});});
    if(rows.length>8)pptText(slide,`+${rows.length-8} more in notes`,x,1.95+8*.55,w,.26,PPT_TYPE.caption,{color:PPT_COLOR.muted});
    if(!rows.length)pptText(slide,'None',x,1.95,w,.3,PPT_TYPE.body,{color:PPT_COLOR.muted});
  });
  pptNote(slide,[`Compared with the baseline frozen ${when}. Identified value ${fmtMoney(d.before)} → ${fmtMoney(d.after)}.`,...cols.map(([title,rows,detail])=>`${title}: ${rows.length?rows.map(r=>`${r.item.name} (${detail(r)})`).join('; '):'none'}`),`Status changed: ${d.statusChanged.length?d.statusChanged.map(r=>`${r.item.name} ${r.before} → ${r.after}`).join('; '):'none'}`].join('\n'));
}

/* ---------- decisions needed ---------- */
function decisionRows(){ return S.items.filter(it=>it.decisionNeeded||normStatus(it.status)==='Blocked').map(it=>({it,decision:it.decisionNeeded||'Blocked: no decision recorded'})); }
function addPptDecisionsSlide(pptx){
  const rows=decisionRows();if(!rows.length)return;
  pptBalancedPages(rows,8).forEach((page,pageIndex,pages)=>{
    const slide=pptSlide(pptx);addPptContext(slide,'Decisions needed',pages.length>1?`Page ${pageIndex+1}/${pages.length}`:'');
    const value=rows.reduce((s,r)=>s+(isIncludedInTotals(r.it)?itemValue(r.it):0),0);
    pptTitle(slide,pageIndex?'Decisions needed (continued)':`${countLabel(rows.length,'decision')} needed, affecting ${fmtMoneyShort(value)} of identified value`);
    [['Initiative',.5,3.6],['Decision needed',4.2,5.6],['Owner',9.9,1.6],['Value',11.5,1.33]].forEach(([label,x,w])=>pptText(slide,label,x,1.5,w,.24,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted,align:label==='Value'?'right':'left'}));
    addPptSafeLine(slide,.5,1.8,12.83,1.8,PPT_COLOR.hair,.6);
    page.forEach((row,i)=>{const y=1.88+i*.6,it=row.it;
      pptText(slide,pptWrapText(it.name||'Untitled initiative',3.5,PPT_TYPE.body,2,true),.5,y,3.6,.55,PPT_TYPE.body,{bold:true,wrap:true,valign:'top',objectName:`decision-initiative:${it.id}`});
      pptText(slide,pptWrapText(row.decision,5.5,PPT_TYPE.body,2),4.2,y,5.6,.55,PPT_TYPE.body,{wrap:true,valign:'top'});
      pptText(slide,pptBoundText(it.owner||'Unassigned',1.55,PPT_TYPE.body),9.9,y,1.6,.3,PPT_TYPE.body,{valign:'top'});
      pptText(slide,fmtMoneyShort(itemValue(it)),11.5,y,1.33,.3,PPT_TYPE.body,{align:'right',valign:'top'});
      addPptSafeLine(slide,.5,y+.58,12.83,y+.58,PPT_COLOR.hair,.4);});
    pptItemNotes(slide,page.map(r=>r.it));
  });
}

/* ---------- deck assembly ---------- */
function addCurrentPptView(pptx){
  if(S.tab==='register')addPptInitiativeRegister(pptx);
  else if(S.tab==='exec')addPptExecutiveSummarySlide(pptx);
  else if(S.tab==='rollup')addPptPortfolioRollupSlide(pptx);
  else if(S.tab==='proj')addPptProjectionSlide(pptx);
  else if(S.tab==='stack')addPptStackedSlide(pptx);
  else addPptRoadmapSlides(pptx);
}
function addFullDeck(pptx){
  addPptTitleSlide(pptx);addPptExecutiveSummarySlide(pptx);addPptBridgeSlide(pptx);addPptPortfolioRollupSlide(pptx);
  addPptProjectionSlide(pptx);addPptStackedSlide(pptx);addPptRoadmapSlides(pptx);
  if(exportPrefs().sinceReview)addPptSinceReviewSlide(pptx);
  addPptDecisionsSlide(pptx);
  if(exportPrefs().includeRegister)addPptInitiativeRegister(pptx);
}
/* Filtered exports run every slide on the filtered initiatives (and the filtered pillar). Goal comparisons are
   suppressed because a portfolio goal does not apply to a subset. State is restored afterwards. */
function withExportScope(run){
  if(!exportFiltered())return run();
  const saved={items:S.items,structure:S.structure,goal:S.projectionTarget,stretch:S.stretchGoal},keep=new Set(filteredItems().map(it=>it.id));
  S.items=S.items.filter(it=>keep.has(it.id));
  if(S.filters.pillarId)S.structure=S.structure.filter(p=>p.id===S.filters.pillarId);
  S.projectionTarget='';S.stretchGoal='';
  try{return run();}finally{S.items=saved.items;S.structure=saved.structure;S.projectionTarget=saved.goal;S.stretchGoal=saved.stretch;}
}
/* Two corrections to the written package, applied before download; the vendored library itself is unmodified.
   1. PptxGenJS 4.0.1 writes embedded chart workbooks whose table range ends with a stray apostrophe
      (ref="A1:C4'"). Keynote then drops every chart and strict readers may repair the file.
   2. Title placeholders get the stable shape name "slide-title" (PptxGenJS ignores objectName on placeholders).
   3. [Content_Types].xml declares one slideMaster part per slide although only one master is written; overrides
      for parts that do not exist are removed (the 1.6.4-1.6.7 known packaging limitation). */
async function repairChartWorkbooks(buffer){
  const zip=await JSZip.loadAsync(buffer);
  const types=await zip.file('[Content_Types].xml').async('string');
  const cleaned=types.replace(/<Override\s+PartName="\/([^"]+)"[^>]*\/>/g,(tag,part)=>zip.file(part)?tag:'');
  if(cleaned!==types)zip.file('[Content_Types].xml',cleaned);
  for(const name of Object.keys(zip.files).filter(n=>/^ppt\/slides\/slide\d+\.xml$/.test(n))){
    const xml=await zip.file(name).async('string');
    const named=xml.replace(/(<p:cNvPr id="\d+" name=")[^"]*("><\/p:cNvPr><p:cNvSpPr\/><p:nvPr><p:ph\s+idx="\d+"\s+type="title")/g,'$1slide-title$2');
    if(named!==xml)zip.file(name,named);
  }
  const books=Object.keys(zip.files).filter(name=>/^ppt\/embeddings\/[^/]+\.xlsx$/.test(name));
  for(const name of books){
    const book=await JSZip.loadAsync(await zip.file(name).async('arraybuffer'));
    for(const table of Object.keys(book.files).filter(n=>/^xl\/tables\/table\d+\.xml$/.test(n))){
      const xml=await book.file(table).async('string'),fixed=xml.replace(/ref="([A-Z]+\d+:[A-Z]+\d+)'"/g,'ref="$1"');
      if(fixed!==xml)book.file(table,fixed);
    }
    zip.file(name,await book.generateAsync({type:'arraybuffer',compression:'DEFLATE'}));
  }
  return zip.generateAsync({type:'blob',compression:'DEFLATE',mimeType:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
}
let PPTX_LOADING=null;
function loadPptxRuntime(){
  if(typeof PptxGenJS==='function')return Promise.resolve();
  if(PPTX_LOADING)return PPTX_LOADING;
  const src=$('pptRuntime')?.content.querySelector('script')?.getAttribute('src')||'vendor/pptxgen.bundle.js';
  PPTX_LOADING=new Promise((resolve,reject)=>{
    const script=document.createElement('script');script.src=src;
    script.onload=()=>typeof PptxGenJS==='function'?resolve():reject(new Error('The PowerPoint writer did not initialize.'));
    script.onerror=()=>{PPTX_LOADING=null;script.remove();reject(new Error('The offline PowerPoint writer (vendor/pptxgen.bundle.js) could not be loaded. Keep the vendor folder next to index.html.'));};
    document.head.appendChild(script);
  });
  return PPTX_LOADING;
}
async function exportPowerPoint(scopeOverride){
  const btn=$('pptBtn'),scope=exportScopeValue(typeof scopeOverride==='string'?scopeOverride:null); btn.disabled=true;
  try{ await loadPptxRuntime(); }catch(error){ btn.disabled=false; showToast(error.message); return; }
  PPT_EXPORT_CONTEXT=buildExportContext(scope); PPT_SLIDES=[];
  try{ const pptx=new PptxGenJS(); pptx.layout='LAYOUT_WIDE'; pptx.theme={headFontFace:pptFont(),bodyFontFace:pptFont(),lang:'en-US'}; pptx.author='Roadmap Studio'; pptx.subject=`${PPT_EXPORT_CONTEXT.scopeLabel} · ${PPT_EXPORT_CONTEXT.scenario}`; pptx.title=S.fileName||DEFAULT_PROJECT_NAME;
    definePptMasters(pptx,PPT_EXPORT_CONTEXT);
    withExportScope(()=>{ if(scope==='current')addCurrentPptView(pptx); else addFullDeck(pptx); });
    pptFlushNotes(PPT_SLIDES);
    const blob=await repairChartWorkbooks(await pptx.write({outputType:'arraybuffer'})); dl(blob,exportFileName(scope==='current'?exportViewLabel():'Deck','pptx'));
  }catch(e){ console.error(e); showToast('PowerPoint export failed. '+(e?.message||'')); } finally{ PPT_EXPORT_CONTEXT=null;PPT_SLIDES=[];btn.disabled=false; } }
$('pptBtn').onclick=()=>exportPowerPoint();

/* ============ PRESENT ============ */
function presentationContextElement(){
  let el=$('presentationContext'); if(el)return el;
  el=document.createElement('div');el.id='presentationContext';el.className='presentation-context';el.setAttribute('role','status');
  Object.assign(el.style,{position:'fixed',top:'16px',left:'20px',right:'180px',zIndex:'61',display:'none',padding:'10px 14px',background:'rgba(251,251,253,.94)',border:'1px solid rgba(0,0,0,.09)',borderRadius:'8px',fontSize:'14px',fontWeight:'600',color:'#1d1d1f',boxShadow:'0 3px 18px rgba(0,0,0,.1)'});
  document.body.appendChild(el);return el;
}
function updatePresentationContext(){
  const el=presentationContextElement(),c=buildExportContext('current'),dated=S.items.filter(it=>it.start),axis=pptPillarAxis(dated);
  el.textContent=`${c.project} · ${c.scenario} · As of ${fmtDate(c.asOf)} · ${c.baseline} · ${c.weighting} · Grouping: ${c.grouping} · Timeline ${fmtDate(axis.start)} to ${fmtDate(addDays(axis.end,-1))}`;
  el.style.display=S.presenting?'block':'none';
}
$('presentBtn').onclick=()=>{ S.presenting=true; document.body.classList.add('presenting');
  document.body.classList.toggle('dark',S.dark); if(S.tab!=='road')setTab('road');
  const stage=document.querySelector('.stage');if(stage){stage.style.overflow='auto';stage.style.alignItems='flex-start';stage.style.justifyContent='flex-start';stage.style.paddingTop='64px';stage.style.height='100vh';stage.style.maxHeight='100vh';stage.style.minHeight='0';}
  updatePresentationContext();document.documentElement.requestFullscreen?.().catch(()=>{});renderTimeline(); };
$('exitPres').onclick=exitPres;
$('darkBtn').onclick=()=>{ S.dark=!S.dark; document.body.classList.toggle('dark',S.dark); $('darkBtn').textContent=S.dark?'Light':'Dark'; renderTimeline();updatePresentationContext(); };
function exitPres(){ S.presenting=false; document.body.classList.remove('presenting','dark');
  if(document.fullscreenElement)document.exitFullscreen?.(); const box=$('tlBox'),stage=document.querySelector('.stage');box.style.transform='';box.style.width='';
  if(stage){stage.style.overflow='';stage.style.alignItems='';stage.style.justifyContent='';stage.style.paddingTop='';stage.style.height='';stage.style.maxHeight='';stage.style.minHeight='';}presentationContextElement().style.display='none';renderTimeline(); }
document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&S.presenting)exitPres();});
document.addEventListener('keydown',e=>{if(!S.presenting)return;if(e.key==='Escape')exitPres();
  else if(e.key==='PageDown'||e.key==='PageUp'){e.preventDefault();const stage=document.querySelector('.stage'),direction=e.key==='PageDown'?1:-1;stage?.scrollBy({top:direction*stage.clientHeight*.82,behavior:'smooth'});}});
function fitPresentation(){ if(!S.presenting)return; const el=$('tlSvg'); if(!el)return;
  const w=el.width.baseVal.value,box=$('tlBox');box.style.transformOrigin='top left';box.style.transform='none';box.style.width=w+'px';updatePresentationContext(); }
