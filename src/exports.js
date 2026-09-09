const PPT_SLIDE_W=13.333, PPT_SLIDE_H=7.5, PPT_BODY_FONT=18, PPT_MAIN_FONT=28, PPT_FONT_FACE='Arial';
const PPT_COLOR={ink:'1D1D1F',muted:'5D6168',hair:'E5E7EB',savings:'188038',avoidance:'2563EB',realizedSavings:'0B662E',realizedAvoidance:'163A8A',approved:'4B5058',proposed:'ECEEF1',realized:'167B62',target:'9A5700'};
let PPT_EXPORT_CONTEXT=null;

function exportReportingDate(){
  const value=typeof reportingDate==='function'?reportingDate():(S.asOfDate?parseAnyDate(S.asOfDate,'end',S.fyStart):new Date());
  return value instanceof Date&&!isNaN(value)?value:new Date();
}
function exportScenarioName(){
  const active=(S.scenarios||[]).find(s=>s.id===S.activeScenarioId);
  return active?.name||S.activeScenarioName||'Working plan';
}
function exportGroupingLabel(){ return S.roadmapGroup==='owner'?'Owner':'Structure'; }
function exportScopeValue(override){
  if(override==='current'||override==='full')return override;
  const control=$('pptScope');
  return control?.value==='current'||S.exportScope==='current'?'current':'full';
}
function exportViewLabel(tab=S.tab){
  return({road:'Roadmap',exec:'Executive Summary',rollup:'Portfolio Rollup',proj:'Projected Savings',stack:'Stacked Bar Chart',register:'Initiative Register'})[tab]||'Roadmap';
}
function buildExportContext(scope){
  return{
    scope,
    scopeLabel:scope==='current'?`Current view: ${exportViewLabel()}`:'Full deck',
    project:S.fileName||'Roadmap',
    scenario:exportScenarioName(),
    asOf:exportReportingDate(),
    baseline:S.baseline?'Baseline on':'No baseline',
    weighting:S.weightConfidence===false?'Unweighted':'Confidence weighted',
    grouping:exportGroupingLabel(),
    version:typeof APP_VERSION==='string'?APP_VERSION:'1.6.0'
  };
}
function exportContext(){ return PPT_EXPORT_CONTEXT||buildExportContext(exportScopeValue()); }
function addPptContext(slide,section,pageLabel='',overrides={}){
  const c={...exportContext(),...overrides}, right=[c.scenario,c.scopeLabel,pageLabel].filter(Boolean).join('  ·  ');
  slide.addText(pptBoundText(c.project,5.2,12,true),{x:.55,y:.16,w:5.2,h:.22,fontSize:12,bold:true,color:PPT_COLOR.ink,margin:0});
  slide.addText(pptBoundText(right,6.78,12),{x:6.0,y:.16,w:6.78,h:.22,fontSize:12,color:PPT_COLOR.muted,align:'right',margin:0,breakLine:false});
  addPptSafeLine(slide,.55,.42,12.78,.42,'E5E5EA',.65);
  const footer=`As of ${fmtDate(c.asOf)}  ·  ${c.weighting}${c.baseline==='Baseline on'?'  ·  Baseline comparison':''}`;
  slide.addText(footer,{x:.55,y:7.19,w:12.23,h:.22,fontSize:12,color:PPT_COLOR.muted,margin:0,align:'right'});
  slide.addNotes(`${c.project}\n${section}\n${right}\nAs of ${fmtDate(c.asOf)}\n${c.baseline}\n${c.weighting}\nGrouping: ${c.grouping}\nRoadmap Studio ${c.version}`);
}
function ensureExportScopeControl(){
  if($('pptScope')||!$('pptBtn'))return;
  const select=document.createElement('select');
  select.id='pptScope'; select.className='fy-select'; select.setAttribute('aria-label','PowerPoint export scope');
  select.title='Choose whether PowerPoint exports this view or the full deck';
  select.innerHTML='<option value="full">Full deck</option><option value="current">Current view</option>';
  select.value=S.exportScope==='current'?'current':'full';
  select.onchange=()=>{S.exportScope=select.value;};
  $('pptBtn').before(select);
}
ensureExportScopeControl();

$('pngBtn').onclick=()=>{ const el=$('tlSvg'); if(!el){alert('Open the Roadmap tab first.');return;}
  const xml=new XMLSerializer().serializeToString(el), img=new Image(), c=buildExportContext('current');
  img.onload=()=>{ const s=2,header=92,canvas=document.createElement('canvas');
    canvas.width=el.width.baseVal.value*s; canvas.height=(el.height.baseVal.value+header)*s; const x=canvas.getContext('2d');
    x.scale(s,s); x.fillStyle='#fbfbfd'; x.fillRect(0,0,canvas.width/s,header); x.fillStyle='#1d1d1f'; x.font='600 20px sans-serif';
    x.fillText(c.project,20,31); x.font='12px sans-serif'; x.fillStyle='#6e6e73';
    x.fillText(`${c.scenario}  ·  As of ${fmtDate(c.asOf)}  ·  ${c.baseline}  ·  ${c.weighting}  ·  Grouping: ${c.grouping}`,20,57);
    x.fillText(`Current view: Roadmap  ·  Roadmap Studio ${c.version}`,20,77); x.drawImage(img,0,header);
    canvas.toBlob(b=>dl(b,'roadmap.png'),'image/png'); };
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(xml); };

function pptHex(c){ return String(c||'').replace('#','').slice(0,6).toUpperCase()||'1D1D1F'; }
function pptItemColor(it){ if(it.status==='Not Started')return['1D1D1F','FFFFFF'];
  return normValueType(it.valueType)==='Avoidance'?['2563EB','FFFFFF']:['188038','FFFFFF']; }
function pptPackItems(items){ const sorted=[...items].filter(i=>i.start).sort((a,b)=>a.start-b.start||((a.end||a.start)-(b.end||b.start)));
  const laneEnds=[], sub=new Map(); sorted.forEach(it=>{ const end=it.end||it.start; let lane=laneEnds.findIndex(d=>d<it.start);
    if(lane<0){lane=laneEnds.length;laneEnds.push(end);} else laneEnds[lane]=end; sub.set(it.id,lane); });
  return{items:sorted,subs:Math.max(1,laneEnds.length),sub}; }
function pptPillarAxis(items){ const dated=items.filter(i=>i.start), todayU=exportReportingDate();
  const start=dated.length?quarterStart(new Date(Math.min(...dated.map(i=>i.start),todayU)),S.fyStart):fyStartOf(todayU,S.fyStart);
  let end=dated.length?nextQuarter(quarterStart(new Date(Math.max(...dated.map(i=>i.end||i.start),todayU)),S.fyStart)):nextQuarter(start);
  const quarters=[];for(let q=start;q<end||quarters.length<4;q=nextQuarter(q))quarters.push(q);
  end=nextQuarter(quarters[quarters.length-1]);return{start,end,quarters,todayU}; }
let PPT_MEASURE_CONTEXT=null;
function pptTextWidthIn(value,fontPt,bold=false){if(!PPT_MEASURE_CONTEXT)PPT_MEASURE_CONTEXT=document.createElement('canvas').getContext('2d');PPT_MEASURE_CONTEXT.font=`${bold?'700':'400'} ${fontPt*96/72}px ${PPT_FONT_FACE}`;return PPT_MEASURE_CONTEXT.measureText(String(value||'')).width/96;}
function pptBoundText(value,widthIn,fontPt,bold=false){const text=String(value||''),limit=Math.max(0,widthIn)*.97;if(pptTextWidthIn(text,fontPt,bold)<=limit)return text;let lo=0,hi=text.length;while(lo<hi){const mid=Math.ceil((lo+hi)/2),candidate=`${text.slice(0,mid).trimEnd()}…`;if(pptTextWidthIn(candidate,fontPt,bold)<=limit)lo=mid;else hi=mid-1;}return `${text.slice(0,lo).trimEnd()}…`;}
function pptWrapText(value,width,font=18,maxLines=2,bold=false){
  const words=String(value||'').split(/\s+/),lines=[];let line='';
  while(words.length){const word=words.shift(),next=line?`${line} ${word}`:word;
    if(pptTextWidthIn(next,font,bold)<=width*.96){line=next;continue;}
    if(line){lines.push(line);line='';words.unshift(word);}else{lines.push(pptBoundText(word,width,font,bold));}
    if(lines.length===maxLines-1){lines.push(pptBoundText(words.join(' '),width,font,bold));return lines.join('\n');}
  }
  if(line)lines.push(line);return lines.slice(0,maxLines).join('\n');
}
function pptText(slide,text,x,y,w,h,font=18,extra={}){
  slide.addText(String(text),{x,y,w,h,fontFace:PPT_FONT_FACE,fontSize:font,color:PPT_COLOR.ink,margin:0,breakLine:false,wrap:false,valign:'mid',...extra});
}
function pptTitle(slide,text){pptText(slide,pptBoundText(text,12.18,30,true),.55,.62,12.18,.5,30,{bold:true,objectName:'slide-title'});}
function pptMetric(slide,label,value,x,y,w=3.8,color=PPT_COLOR.ink){
  pptText(slide,label,x,y,w,.28,16,{color:PPT_COLOR.muted});
  pptText(slide,pptBoundText(value,w,28,true),x,y+.36,w,.43,28,{bold:true,color});
}
function pptBalancedPages(items,max=2){
  const pages=Math.max(1,Math.ceil(items.length/max)),size=Math.floor(items.length/pages),extra=items.length%pages,out=[];let offset=0;
  for(let i=0;i<pages;i++){const count=size+(i<extra?1:0);out.push(items.slice(offset,offset+count));offset+=count;}return out;
}
function pptItemNotes(slide,items){
  slide.addNotes(items.map(it=>`${it.name}\n${normValueType(it.valueType)} ${fmtMoney(itemValue(it))}; ${isIncludedInTotals(it)?'Included':'Excluded from portfolio totals'}; ${approvalLabel(approvalStatus(it))}; ${it.status}; Owner: ${it.owner||'Unassigned'}\n${it.start?fmtDate(it.start):'Unscheduled'} to ${it.end?fmtDate(it.end):'Unscheduled'}; Realized ${fmtMoney(realizedItemValue(it,exportReportingDate()))}`).join('\n\n'));
}
function pptAddFullNameNotes(slide,entries){const names=[...new Set(entries.filter(Boolean).map(String))];if(names.length)slide.addNotes(`Full names\n${names.join('\n')}`);}
function addPptMetric(slide,label,value,x,color){ slide.addShape('roundRect',{x,y:1.02,w:1.88,h:.6,fill:{color:'FFFFFF'},line:{color:'ECECF0',width:.7}});
  slide.addShape('roundRect',{x:x+.14,y:1.2,w:.22,h:.08,fill:{color},line:{color}});
  slide.addText(pptBoundText(value,1.26,17,true),{x:x+.44,y:1.1,w:1.26,h:.22,fontSize:17,bold:true,color:'1D1D1F',margin:0});
  slide.addText(label,{x:x+.44,y:1.35,w:1.26,h:.18,fontSize:12,bold:true,color:'6E6E73',margin:0}); }
function addPptSafeLine(slide,x1,y1,x2,y2,color,width=1,opts={}){
  const dx=x2-x1, dy=y2-y1;
  const shape={x:Math.min(x1,x2),y:Math.min(y1,y2),w:Math.abs(dx),h:Math.abs(dy),line:{color,width,transparency:opts.transparency||0}};
  if(opts.objectName)shape.objectName=opts.objectName;
  if(opts.dashType)shape.line.dashType=opts.dashType;
  if(shape.w>0&&shape.h>0&&dx*dy<0)shape.flipV=true;
  slide.addShape('line',shape);
}
function pptFiscalBands(axis,X){ const bands=[]; let fy=fqOf(axis.quarters[0],S.fyStart).fy, start=axis.quarters[0];
  axis.quarters.forEach((q,i)=>{ const qFy=fqOf(q,S.fyStart).fy; if(qFy!==fy){ bands.push({fy,start,end:q}); fy=qFy; start=q; }
    if(i===axis.quarters.length-1)bands.push({fy,start,end:axis.end}); });
  return bands.map(b=>({...b,x:X(b.start),w:X(b.end)-X(b.start)})); }
function pptBarLabelBox(it,font,sx,ex,bw,timeX,timeW){
  const insideW=Math.max(.15,bw-.14);
  const name=String(it.name||'Initiative'),tail=name.match(/(?:^|\s)([A-Z]|\d{1,3})$/)?.[1],first=name.split(/\s+/)[0];
  const distinct=tail?`${first} ${tail}`:null,full=roadmapLabel(it),text=distinct&&pptTextWidthIn(distinct,font)<=insideW*.97?distinct:pptBoundText(full,insideW-.04,font);
  return{x:sx+.07,w:insideW,inside:true,align:'left',text};
}
function pptFinancialTotals(items){
  if(typeof portfolioFinancialTotals==='function')return portfolioFinancialTotals(items);
  return items.filter(it=>typeof isIncludedInTotals!=='function'||isIncludedInTotals(it)).reduce((totals,it)=>{
    const value=itemValue(it), realized=typeof realizedItemValue==='function'?realizedItemValue(it,exportReportingDate()):0;
    totals[normValueType(it.valueType)]+=value; totals.Realized+=realized; totals.Total+=value; return totals;
  },{Savings:0,Avoidance:0,Realized:0,Total:0});
}
function pptRoadmapReferenceRows(p,items){
  const order=new Map((p.workstreams||[]).map((w,i)=>[w.id,i]));
  return [...items].sort((a,b)=>(order.get(a.wsId)||0)-(order.get(b.wsId)||0)||(a.start||Infinity)-(b.start||Infinity)).map((it,i)=>({it,ref:String(i+1).padStart(2,'0'),workstream:(p.workstreams||[]).find(w=>w.id===it.wsId)?.name||'Unassigned'}));
}
function addPptPillarSlide(pptx,p,idx,total,options={}){
  const allItems=options.items||S.items.filter(i=>i.pillarId===p.id),totals=pptFinancialTotals(allItems),axis=options.axis||pptPillarAxis(allItems);
  const pages=pptBalancedPages(pptRoadmapReferenceRows(p,allItems),4),timeX=4.58,timeW=8.05,bodyY=3.05,rowH=.86;
  const X=d=>timeX+Math.max(0,Math.min(1,(d-axis.start)/(axis.end-axis.start)))*timeW;
  pages.forEach((rows,pageIndex)=>{
    const slide=pptx.addSlide();slide.background={color:'FFFFFF'};addPptContext(slide,'Roadmap',`${options.kind||'Pillar'} ${idx+1}/${total} · Page ${pageIndex+1}/${pages.length}`);
    pptTitle(slide,p.name);pptMetric(slide,'SAVINGS',fmtMoneyShort(totals.Savings,true),.6,1.28,3.5,PPT_COLOR.savings);
    pptMetric(slide,'AVOIDANCE',fmtMoneyShort(totals.Avoidance,true),4.7,1.28,3.5,PPT_COLOR.avoidance);
    pptMetric(slide,'REALIZED',fmtMoneyShort(totals.Realized,true),8.8,1.28,3.8,PPT_COLOR.realized);
    const bottom=bodyY+Math.max(1,rows.length)*rowH;
    pptText(slide,'Initiative / workstream',.6,2.65,3.65,.25,16,{color:PPT_COLOR.muted});
    pptFiscalBands(axis,X).forEach((band,i)=>{
      if(i%2)slide.addShape('rect',{x:band.x,y:2.35,w:band.w,h:bottom-2.35,fill:{color:'F7F8FA'},line:{transparency:100}});
      if(band.w>.45)pptText(slide,`FY${band.fy}`,band.x,2.38,band.w,.28,14,{bold:true,align:'center'});
    });
    axis.quarters.forEach(q=>{const x=X(q),w=X(nextQuarter(q))-x;
      addPptSafeLine(slide,x,2.72,x,bottom,PPT_COLOR.hair,.6);
      if(w>.38)pptText(slide,`Q${fqOf(q,S.fyStart).q}`,x,2.73,w,.24,14,{color:PPT_COLOR.muted,align:'center'});
    });
    const asOfX=X(axis.todayU);addPptSafeLine(slide,asOfX,3,asOfX,bottom,'A6A8AE',1,{dashType:'dash'});
    if(!rows.length)pptText(slide,'No initiatives in this pillar',.6,3.25,8,.4,20,{color:PPT_COLOR.muted});
    rows.forEach(({it,ref,workstream},rowIndex)=>{
      const y=bodyY+rowIndex*rowH,hasDate=!!it.start,name=`${ref}  ${it.name||'Untitled initiative'}`;
      pptText(slide,pptWrapText(name,3.66,18,2,true),.6,y+.025,3.66,.57,18,{bold:true,wrap:true,valign:'top',objectName:`initiative-label:${it.id}`});
      const detail=`${workstream} · ${fmtMoneyShort(itemValue(it),true)}`;
      pptText(slide,pptBoundText(detail,3.66,14),.6,y+.63,3.66,.22,14,{color:PPT_COLOR.muted,objectName:`initiative-detail:${it.id}`});
      addPptSafeLine(slide,.6,y+rowH-.015,12.63,y+rowH-.015,PPT_COLOR.hair,.45);
      if(!hasDate){pptText(slide,`Unscheduled  ${normValueType(it.valueType)} ${fmtMoneyShort(itemValue(it),true)}`,timeX+.1,y+.14,timeW-.2,.32,18,{color:PPT_COLOR.muted});return;}
      const sx=X(it.start),ex=X(addDays(it.end||it.start,1)),bw=Math.max(.025,ex-sx),by=y+.13,col=pptItemColor(it),complete=it.status==='Complete';
      slide.addShape(it.milestone?'diamond':'roundRect',{x:it.milestone?sx-.08:sx,y:by,w:it.milestone?.16:bw,h:it.milestone?.38:.38,rectRadius:.04,
        fill:{color:complete?'D8DADD':col[0]},line:{color:it.status==='At Risk'?'B45309':(complete?'D8DADD':col[0]),width:it.status==='At Risk'?1.7:0},objectName:`initiative-bar:${it.id}`});
      const full=roadmapLabel(it),label=pptTextWidthIn(full,18)<=bw-.18?full:ref,ink=complete?PPT_COLOR.ink:'FFFFFF';
      if(!it.milestone&&pptTextWidthIn(label,18)<=bw-.16)pptText(slide,label,sx+.08,by+.025,bw-.16,.32,18,{color:ink,objectName:`initiative-bar-label:${it.id}`});
      else{
        const rightSpace=timeX+timeW-ex,labelW=.46,labelX=rightSpace>=labelW+.1?ex+.1:Math.max(timeX,sx-labelW-.1);
        pptText(slide,ref,labelX,by+.025,labelW,.32,18,{bold:true,objectName:`initiative-reference:${it.id}`});
      }
    });
    const legend=[['188038','Savings'],['2563EB','Avoidance'],['1D1D1F','Not Started'],['D8DADD','Complete']];
    legend.forEach(([color,label],i)=>{const x=.65+i*2.55;slide.addShape('rect',{x,y:6.84,w:.17,h:.13,fill:{color},line:{transparency:100}});pptText(slide,label,x+.26,6.79,2.15,.24,14,{color:PPT_COLOR.muted});});
    pptAddFullNameNotes(slide,[p.name,...rows.map(r=>r.workstream)]);pptItemNotes(slide,rows.map(r=>r.it));
  });
}
function addPptExecutiveSummarySlide(pptx){
  const slide=pptx.addSlide(), data=executiveSummaryData(), total=data.totals.Total, goal=executiveGoalValue();
  const stretchGoal=executiveStretchGoalValue();
  const ink='1D1D1F', ink2='6E6E73', ink3='8E8E93', hair='E5E5EA', bg='FBFBFD', white='FFFFFF';
  const savingsColor='28A745', realizedSavingsColor='0B662E', avoidanceColor='3B73E8', realizedAvoidanceColor='163A8A', gold='B45309', gapColor='E5E5EA';
  const delta=Math.abs(total-goal);
  const headline=!total?`No opportunity identified toward the ${fmtMoneyShort(goal,true)} goal`
    :total>goal?`Identified opportunity exceeds the goal by ${fmtMoneyShort(delta,true)}`
    :total<goal?`The portfolio needs ${fmtMoneyShort(delta,true)} more in identified opportunity`
    :'Identified opportunity covers the goal, with value still to realize';
  const savings=data.totals.Savings, avoidance=data.totals.Avoidance;
  const realizedSavings=data.buckets.realized.Savings, realizedAvoidance=data.buckets.realized.Avoidance;
  const identifiedPct=goal?total/goal*100:0, realizedPct=goal?data.totals.Realized/goal*100:0;
  const fmtGoalPct=value=>`${value.toFixed(value%1===0?0:1).replace(/\.0$/,'')}%`;
  slide.background={color:bg};
  addPptContext(slide,'Executive Summary');
  pptTitle(slide,headline);

  const blockY=1.45, blockH=stretchGoal?1.74:1.62, blockW=5.0;
  const addGoalBlock=(x,fill,label,pctValue,note,labelColor,kind,value)=>{
    slide.addShape('roundRect',{x,y:blockY,w:blockW,h:blockH,rectRadius:.08,fill:{color:fill},line:{color:fill}});
    slide.addText(label,{x:x+.28,y:blockY+.19,w:blockW-.56,h:.28,fontSize:16,bold:true,color:labelColor,align:'center',margin:0});
    slide.addText(fmtGoalPct(pctValue),{x:x+.28,y:blockY+.55,w:blockW-.56,h:.5,fontFace:PPT_FONT_FACE,fontSize:46,bold:true,color:white,align:'center',margin:0});
    slide.addText(note,{x:x+.28,y:blockY+(stretchGoal?1.07:1.2),w:blockW-.56,h:.25,fontSize:stretchGoal?14:16,color:'F2F2F7',align:'center',margin:0});
    if(stretchGoal)pptText(slide,`${fmtGoalProgress(value,stretchGoal)} of stretch goal`,x+.28,blockY+1.36,blockW-.56,.22,14,{color:labelColor,align:'center',objectName:`executive-stretch-${kind}`});
  };
  addGoalBlock(1.25,ink,'IDENTIFIED OPPORTUNITY',identifiedPct,`${fmtMoneyShort(total,true)} identified toward goal`,'D1D1D6','identified',total);
  addGoalBlock(7.08,realizedSavingsColor,'REALIZED IN ACTUALS',realizedPct,`${fmtMoneyShort(data.totals.Realized,true)} recognized in actuals`,'DDF4E5','realized',data.totals.Realized);

  const legend=[
    {x:.78,color:realizedSavingsColor,label:'Realized savings',w:2.45},
    {x:3.8,color:savingsColor,label:'Savings remaining',w:2.45},
    {x:6.78,color:realizedAvoidanceColor,label:'Realized avoidance',w:2.55},
    {x:9.9,color:avoidanceColor,label:'Avoidance remaining',w:2.65},
  ];
  legend.forEach(item=>{
    slide.addShape('ellipse',{x:item.x,y:3.42,w:.14,h:.14,fill:{color:item.color},line:{color:item.color}});
    slide.addText(item.label,{x:item.x+.23,y:3.37,w:item.w,h:.28,fontSize:16,color:PPT_COLOR.muted,margin:0});
  });

  const barX=.76, barY=3.88, barW=11.82, barH=.64, axisMax=Math.max(goal,stretchGoal||0,total,1);
  const X=value=>barX+Math.max(0,Math.min(1,value/axisMax))*barW;
  const realizedSavingsEnd=X(realizedSavings), savingsEnd=X(savings), realizedAvoidanceEnd=X(savings+realizedAvoidance), totalEnd=X(total), goalX=X(goal), radius=.32;
  slide.addShape('roundRect',{x:barX,y:barY,w:barW,h:barH,rectRadius:.08,fill:{color:gapColor},line:{color:gapColor}});
  const segments=[
    {start:barX,end:realizedSavingsEnd,color:realizedSavingsColor},
    {start:realizedSavingsEnd,end:savingsEnd,color:savingsColor},
    {start:savingsEnd,end:realizedAvoidanceEnd,color:realizedAvoidanceColor},
    {start:realizedAvoidanceEnd,end:totalEnd,color:avoidanceColor},
  ].filter(seg=>seg.end-seg.start>.001);
  segments.forEach((seg,index)=>{
    const width=Math.max(.01,seg.end-seg.start), first=index===0, last=index===segments.length-1&&Math.abs(totalEnd-(barX+barW))<.001;
    if(first||last){
      slide.addShape('roundRect',{x:seg.start,y:barY,w:width,h:barH,rectRadius:.08,fill:{color:seg.color},line:{color:seg.color}});
      if(first&&seg.end<barX+barW)slide.addShape('rect',{x:Math.max(seg.start,seg.end-radius),y:barY,w:Math.min(radius,width),h:barH,fill:{color:seg.color},line:{color:seg.color,transparency:100}});
      if(last&&seg.start>barX)slide.addShape('rect',{x:seg.start,y:barY,w:Math.min(radius,width),h:barH,fill:{color:seg.color},line:{color:seg.color,transparency:100}});
    }else slide.addShape('rect',{x:seg.start,y:barY,w:width,h:barH,fill:{color:seg.color},line:{color:seg.color,transparency:100}});
  });

  const savingsW=savingsEnd-barX, avoidanceW=totalEnd-savingsEnd;
  if(savingsW>=1.55)pptText(slide,'SAVINGS',barX+.12,barY+.17,savingsW-.24,.3,18,{bold:true,color:white,align:'center'});
  if(avoidanceW>=1.65)pptText(slide,'AVOIDANCE',savingsEnd+.12,barY+.17,avoidanceW-.24,.3,18,{bold:true,color:white,align:'center'});

  const targets=[
    {kind:'goal',value:goal,x:goalX,color:gold,label:'GOAL'},
  ];
  if(stretchGoal)targets.push({kind:'stretch',value:stretchGoal,x:X(stretchGoal),color:PPT_COLOR.muted,label:'STRETCH GOAL'});
  targets.forEach(target=>{
    target.amount=fmtGoalMoney(target.value);
    target.w=Math.max(pptTextWidthIn(target.amount,16,true),pptTextWidthIn(target.label,14,true))+.16;
    target.labelX=Math.max(barX,Math.min(target.x-target.w,barX+barW-target.w));
  });
  // Keep both captions readable even when a large portfolio puts the markers close together.
  if(targets.length>1&&targets[0].labelX+targets[0].w+.2>targets[1].labelX){
    targets[0].labelX=Math.max(barX,targets[1].labelX-targets[0].w-.2);
    targets[1].labelX=Math.max(targets[1].labelX,targets[0].labelX+targets[0].w+.2);
  }
  targets.forEach(target=>{
    addPptSafeLine(slide,target.x,barY-.1,target.x,barY+barH+.06,target.color,1.7,
      {objectName:`executive-${target.kind}-marker`,...(target.kind==='stretch'?{dashType:'dash'}:{})});
    const anchor=Math.max(target.labelX+.04,Math.min(target.x,target.labelX+target.w-.04));
    addPptSafeLine(slide,target.x,barY+barH+.06,anchor,4.62,target.color,.75);
    pptText(slide,target.amount,target.labelX,4.66,target.w,.27,16,{bold:true,color:target.color,align:'right',objectName:`executive-${target.kind}-amount`});
    pptText(slide,target.label,target.labelX,4.97,target.w,.24,14,{bold:true,color:target.color,align:'right',objectName:`executive-${target.kind}-label`});
  });

  const financialItems=S.items.filter(it=>isIncludedInTotals(it)&&itemValue(it)>0),actuals=pptFinancialTotals(financialItems);
  pptText(slide,`Savings ${fmtMoneyShort(savings,true)}`,.78,5.46,4.0,.38,24,{bold:true,color:savingsColor});
  pptText(slide,`${fmtMoneyShort(actuals.RealizedSavings,true)} realized savings`,.78,5.92,4.0,.3,18,{color:realizedSavingsColor});
  pptText(slide,`Avoidance ${fmtMoneyShort(avoidance,true)}`,5.05,5.46,4.3,.38,24,{bold:true,color:avoidanceColor});
  pptText(slide,`${fmtMoneyShort(actuals.RealizedAvoidance,true)} realized avoidance`,5.05,5.92,4.3,.3,18,{color:realizedAvoidanceColor});
  const goalDetail=total<goal?`${fmtMoneyShort(goal-total,true)} to goal`:total>goal?`${fmtMoneyShort(total-goal,true)} above goal`:'Goal reached';
  slide.addText(goalDetail,{x:9.5,y:5.46,w:3.08,h:.38,fontSize:24,bold:true,color:ink,align:'right',margin:0});

  addPptSafeLine(slide,.78,6.46,12.58,6.46,hair,.75);
  pptText(slide,'Dark segments show the realized portion of each opportunity, capped at its planned value.',.78,6.62,11.8,.32,16,{color:PPT_COLOR.muted});
  slide.addNotes(`Goal: ${fmtMoney(goal)}. ${stretchGoal?`Stretch goal entered independently: ${fmtMoney(stretchGoal)}. Stretch percentages use this amount, with no automatic multiplier. `:''}Headline percentages and the gap remain relative to the portfolio goal. The dollar scale includes all entered goals and the full identified portfolio.`);
  slide.addNotes('Realization uses recorded actual dollars where entered, otherwise reported realization percentages or dated phases. Actual totals are not confidence-weighted. Realized values are not added to the identified portfolio total. Dark bar segments are capped to each opportunity; uncapped actual totals are displayed separately.');
}
function addPptPortfolioRollupSlide(pptx){
  const data=portfolioRollupData(),pages=pptBalancedPages(data.groups||[],2),timeX=4.15,timeW=8.48,bodyY=2.95,groupH=1.69;
  const axisStart=utc(data.minYear,0,1),axisEnd=utc(data.maxYear+1,0,1),X=d=>timeX+Math.max(0,Math.min(1,(d-axisStart)/(axisEnd-axisStart)))*timeW;
  pages.forEach((groups,pageIndex)=>{
    const slide=pptx.addSlide();slide.background={color:'FFFFFF'};addPptContext(slide,'Portfolio Rollup',`Page ${pageIndex+1}/${pages.length}`);pptTitle(slide,pageIndex?'Portfolio Rollup (continued)':'Portfolio Rollup');
    [['TOTAL PORTFOLIO',data.totals.Total],['ACTIVE',data.totals.Approved],['PROPOSED',data.totals.Proposed],['REALIZED',data.totals.Realized]].forEach(([label,value],i)=>pptMetric(slide,label,fmtMoneyShort(value,true),.6+i*3.13,1.32,2.95,i===3?PPT_COLOR.realized:PPT_COLOR.ink));
    if(!data.items.length){pptText(slide,'No initiatives to roll up',.6,3,11,.5,24,{color:PPT_COLOR.muted});return;}
    const bottom=bodyY+Math.max(1,groups.length)*groupH;
    for(let year=data.minYear;year<=data.maxYear;year++){
      const x=X(utc(year,0,1)),nx=X(utc(year+1,0,1));
      if((year-data.minYear)%2)slide.addShape('rect',{x,y:2.53,w:nx-x,h:bottom-2.53,fill:{color:'F7F8FA'},line:{transparency:100}});
      addPptSafeLine(slide,x,2.53,x,bottom,PPT_COLOR.hair,.6);
      if(nx-x>.42)pptText(slide,String(year),x,2.56,nx-x,.3,16,{bold:true,align:'center'});
    }
    groups.forEach((group,i)=>{
      const y=bodyY+i*groupH;
      addPptSafeLine(slide,.6,y,12.63,y,PPT_COLOR.hair,.85);
      pptText(slide,pptBoundText(group.p.name,7.7,20,true),.6,y+.08,7.7,.33,20,{bold:true,objectName:`rollup-pillar:${group.p.id}`});
      pptText(slide,`Realized ${fmtMoneyShort(group.summary.realized,true)}`,8.7,y+.09,3.93,.3,18,{align:'right',color:PPT_COLOR.realized});
      APPROVAL_STATES.forEach((approval,ai)=>{
        const b=group.summary[approval],ly=y+.53+ai*.55,bucketRows=group.items.filter(row=>row.approval===approval),scheduled=bucketRows.filter(row=>row.start&&row.end),unscheduled=bucketRows.filter(row=>!row.start||!row.end);
        pptText(slide,approvalLabel(approval),.6,ly,1.34,.3,18,{bold:true});
        pptText(slide,`${b.count} ${b.count===1?'initiative':'initiatives'}`,2.08,ly-.02,1.8,.23,14,{color:PPT_COLOR.muted,align:'right'});
        pptText(slide,fmtMoneyShort(b.value,true),2.05,ly+.23,1.83,.28,18,{bold:true,align:'right',objectName:`rollup-value:${group.p.id}:${approval}`});
        if(!b.count){pptText(slide,`No ${approvalLabel(approval).toLowerCase()} initiatives`,timeX+.12,ly+.06,6.5,.28,18,{color:PPT_COLOR.muted});return;}
        if(unscheduled.length)pptText(slide,`Unscheduled ${unscheduled.length} · ${fmtMoneyShort(unscheduled.reduce((sum,row)=>sum+row.value,0),true)}`,timeX+.1,ly+.34,timeW-.2,.2,14,{color:PPT_COLOR.target,align:'right'});
        if(!scheduled.length)return;
        const start=new Date(Math.min(...scheduled.map(row=>row.start))),end=new Date(Math.max(...scheduled.map(row=>row.end))),sx=X(start),ex=X(addDays(end,1)),bw=Math.max(.03,ex-sx),by=ly+.07;
        const value=scheduled.reduce((sum,row)=>sum+row.value,0),actual=scheduled.reduce((sum,row)=>sum+row.realized,0),ratio=value?Math.min(1,actual/value):0;
        slide.addShape('roundRect',{x:sx,y:by,w:bw,h:.37,rectRadius:.04,fill:{color:approval==='Approved'?PPT_COLOR.approved:PPT_COLOR.proposed},line:{color:approval==='Approved'?PPT_COLOR.approved:'A7ABB2',width:.6},objectName:`rollup-bar:${group.p.id}:${approval}`});
        if(ratio>0)slide.addShape('rect',{x:sx,y:by,w:bw*ratio,h:.37,fill:{color:PPT_COLOR.realized},line:{transparency:100}});
        const label=`${scheduled.length} · ${fmtMoneyShort(value,true)}`;
        if(pptTextWidthIn(label,18,true)<bw-.2&&(approval==='Approved'||ratio===0))pptText(slide,label,sx+.1,by+.025,bw-.2,.3,18,{bold:true,color:approval==='Approved'?'FFFFFF':PPT_COLOR.ink});
      });
      pptAddFullNameNotes(slide,[group.p.name]);
    });
    slide.addShape('rect',{x:.62,y:6.68,w:.2,h:.15,fill:{color:PPT_COLOR.realized},line:{transparency:100}});
    pptText(slide,'Realized share of scheduled value; bar length represents dates',.95,6.61,10.8,.3,16,{color:PPT_COLOR.muted});
    slide.addNotes(`${data.items.length} initiatives\nSavings + Avoidance\nSelected as active: ${fmtMoney(data.totals.Approved)}\nSelected as proposed: ${fmtMoney(data.totals.Proposed)}\nCaptured to date: ${fmtMoney(data.totals.Realized)}\nApproval is independent of Savings or Avoidance. Row amounts include unscheduled initiatives; time bars include scheduled initiatives only.`);
  });
}
function pptProjectionBand(slide,points,X,Y,plot){
  if(points.length<2)return;
  const point=(p,key)=>({x:X(p.date)-plot.x,y:Y(p[key])-plot.y});
  // One native polygon follows the actual trajectories instead of interval rectangles.
  slide.addShape('custGeom',{x:plot.x,y:plot.y,w:plot.w,h:plot.h,points:[...points.map(p=>point(p,'Combined')),...[...points].reverse().map(p=>point(p,'Savings')),{close:true}],fill:{color:PPT_COLOR.avoidance,transparency:91},line:{transparency:100},objectName:'projection-avoidance-band'});
}
function pptProjectionLabelPositions(entries,top,bottom,gap=.75){
  const rows=entries.map(e=>({...e,labelY:e.y-.25})).sort((a,b)=>a.labelY-b.labelY);
  rows.forEach((r,i)=>{r.labelY=Math.max(top,r.labelY,i?rows[i-1].labelY+gap:top);});
  for(let i=rows.length-1;i>=0;i--)rows[i].labelY=Math.min(rows[i].labelY,bottom-(rows.length-1-i)*gap);
  return rows;
}
function addPptProjectionSlide(pptx){
  const slide=pptx.addSlide(),end=selectedProjectionEnd(),data=projectionPoints(end),totals=projectionTotalsAt(data.items,end),target=projectionTargetValue();
  const baseline=S.showBaseline!==false?baselineProjectionPoints(end):null,run=data.run||projectionRunRateTotals(data.items),baselineLast=baseline?.points?.[baseline.points.length-1];
  slide.background={color:'FFFFFF'};addPptContext(slide,'Projected savings trajectory');pptTitle(slide,`Projected by ${fmtDate(end)}`);
  pptMetric(slide,'Savings + Avoidance',fmtMoneyShort(totals.Combined,true),.6,1.32,5.6,PPT_COLOR.avoidance);
  const gap=target===''?null:target-totals.Combined;
  pptMetric(slide,target===''?'Target not set':`Target ${fmtMoneyShort(target,true)}`,gap===null?'No target comparison':gap>0?`${fmtMoneyShort(gap,true)} below target`:gap<0?`${fmtMoneyShort(-gap,true)} above target`:'Target covered',7.05,1.32,5.55,PPT_COLOR.ink);
  slide.addNotes(`Projected savings trajectory\nSavings ${fmtMoney(totals.Savings)}\nAvoidance ${fmtMoney(totals.Avoidance)}\nRealized ${fmtMoney(totals.Realized)}\nExpected ${fmtMoney(run.expected)}\nAnnualized ${fmtMoney(run.annualized)}\n${baselineLast?`Baseline ${fmtMoney(baselineLast.Combined)}; change ${fmtMoney(totals.Combined-baselineLast.Combined)}`:'No baseline'}\nValue added by Avoidance: ${fmtMoney(totals.Avoidance)}. Avoidance lift is the difference between the two planned trajectories. Actuals are never confidence weighted.`);
  if(!data.items.length){pptText(slide,'No dated financial initiatives',.6,3.35,11,.45,24,{color:PPT_COLOR.muted});return;}
  const plot={x:1.05,y:2.64,w:8.37,h:3.53},baseMax=baseline?Math.max(...baseline.points.map(p=>p.Combined)):0;
  const dataMax=Math.max(...data.points.map(p=>Math.max(p.Combined,p.Realized)),baseMax,1),showTarget=target!==''&&target<=dataMax*1.8;
  const maxY=niceProjectionMax(Math.max(dataMax,showTarget?target:0)),span=Math.max(1,data.axis.end-data.axis.start);
  const X=d=>plot.x+Math.max(0,Math.min(1,(d-data.axis.start)/span))*plot.w,Y=v=>plot.y+plot.h-Math.max(0,Math.min(1,v/maxY))*plot.h;
  [0,.25,.5,.75,1].forEach(f=>{const value=f*maxY,y=Y(value);addPptSafeLine(slide,plot.x,y,plot.x+plot.w,y,PPT_COLOR.hair,.65);
    pptText(slide,fmtMoneyShort(value,true),.08,y-.12,.82,.25,14,{align:'right',color:PPT_COLOR.muted});});
  const candidates=[];
  for(let q=quarterStart(data.axis.start,S.fyStart);q<=data.axis.end;q=nextQuarter(q)){
    const x=X(q),fq=fqOf(q,S.fyStart);addPptSafeLine(slide,x,plot.y+plot.h-.06,x,plot.y+plot.h,'C9CDD4',.7);
    if(fq.q===1||!candidates.length)candidates.push({x,label:S.fyStart===0?String(fq.fy):`FY${fq.fy}`});
  }
  let lastX=-Infinity;
  candidates.forEach(c=>{const x=Math.max(plot.x,Math.min(c.x,plot.x+plot.w-.83));if(x-lastX<.83)return;
    pptText(slide,c.label,x,6.31,.83,.26,14,{color:PPT_COLOR.muted});lastX=x;});
  pptProjectionBand(slide,data.points,X,Y,plot);
  const series=[{key:'Combined',label:'Savings + Avoidance',color:PPT_COLOR.avoidance,points:data.points,width:2.6},
    {key:'Savings',label:'Savings only',color:PPT_COLOR.savings,points:data.points,width:2.1}];
  if(S.projectionShowRealized!==false)series.push({key:'Realized',label:'Realized to date',color:'70757D',points:data.points,width:1.4,dashType:'dash'});
  if(baseline?.points?.length)series.push({key:'Combined',label:'Baseline',color:'905C43',points:baseline.points,width:1.5,dashType:'dash'});
  const labels=[];
  series.forEach(s=>{
    for(let i=1;i<s.points.length;i++)addPptSafeLine(slide,X(s.points[i-1].date),Y(s.points[i-1][s.key]),X(s.points[i].date),Y(s.points[i][s.key]),s.color,s.width,{dashType:s.dashType,objectName:`projection-line:${s.label}`});
    const last=s.points[s.points.length-1];labels.push({...s,value:last[s.key],x:X(last.date),y:Y(last[s.key])});
  });
  if(showTarget){const y=Y(target);addPptSafeLine(slide,plot.x,y,plot.x+plot.w,y,PPT_COLOR.target,1.3,{dashType:'dash',objectName:'projection-target-line'});
    pptText(slide,'Target',plot.x+.12,Math.max(plot.y,y-.29),1.2,.25,14,{color:PPT_COLOR.target});}
  pptProjectionLabelPositions(labels,plot.y,plot.y+plot.h-.59).forEach(s=>{
    addPptSafeLine(slide,s.x,s.y,9.77,s.labelY+.32,s.color,.9,{dashType:s.dashType});
    pptText(slide,s.label,9.95,s.labelY,2.77,.24,16,{color:s.color,objectName:`projection-label:${s.label}`});
    pptText(slide,fmtMoneyShort(s.value,true),9.95,s.labelY+.28,2.77,.3,20,{bold:true,color:s.color,objectName:`projection-value:${s.label}`});
  });
  const note=`Avoidance adds ${fmtMoneyShort(totals.Avoidance,true)}${target!==''&&!showTarget?'  ·  Target shown above, outside chart scale':''}`;
  pptText(slide,note,.6,6.73,12.0,.28,16,{color:PPT_COLOR.muted});
}
function pptStackRows(){
  const savings=stackedBreakdown('savings'), combined=stackedBreakdown('combined');
  const rowMap=new Map(stackedPillarRows().map(row=>[row.p.id,row]));
  const rows=[...rowMap.values()].filter(row=>row.Savings>0||row.Combined>0).sort((a,b)=>b.Combined-a.Combined);
  const leader=rows.find(row=>row.Combined>0)||rows[0]||null;
  const support=['525A63','A46638','8A638F','A1AA86','4D8590','B56D7A','A69B57','78716C','766C9F','BD8265','638871','AE5664','778AA4','9D8565','69724B','986E7F','558E8A','7D6270','9E9A80','546D78'];
  const colors={}; rows.forEach((row,i)=>{colors[row.p.id]=support[i%support.length];});
  return{savings,combined,rows,leader,colors};
}
function pptStackSegments(data,colors){
  const order=new Map(Object.keys(colors).map((id,i)=>[id,i]));
  return [...data.segments].sort((a,b)=>order.get(a.p.id)-order.get(b.p.id)).map(seg=>({...seg,color:colors[seg.p.id]||seg.color}));
}
function addPptExecutiveStackBar(slide,data,colors,x,title){
  const barX=x+.42,barY=3.06,barW=1.0,barH=3.08;
  pptText(slide,title,x-.06,2.1,2.02,.5,18,{bold:true,align:'center',wrap:true});
  pptText(slide,fmtMoneyShort(data.total,true),x-.06,2.66,2.02,.35,24,{bold:true,align:'center'});
  if(!data.total){pptText(slide,'No financial values',x-.06,4.2,2.02,.6,18,{color:PPT_COLOR.muted,align:'center',wrap:true});return;}
  let y=barY+barH;
  pptStackSegments(data,colors).forEach(seg=>{
    const h=barH*seg.value/data.total,sy=y-h;
    slide.addShape('rect',{x:barX,y:sy,w:barW,h,fill:{color:seg.color},line:{color:seg.color,transparency:100},objectName:`contribution-segment:${data.key}:${seg.p.id}`});
    if(h>=.36)pptText(slide,fmtShare(seg.pct),barX+.05,sy+h/2-.15,barW-.1,.3,18,{bold:true,color:['A1AA86','A69B57'].includes(seg.color)?PPT_COLOR.ink:'FFFFFF',align:'center'});
    y=sy;
  });
  pptText(slide,'100% composition',x-.11,6.32,2.12,.28,16,{color:PPT_COLOR.muted,align:'center'});
}
function pptContributionTable(slide,rows,stack,full=false){
  const x=full?.65:5.62,nameW=full?5.2:2.25,rowY=full?2.42:3.3,rowH=full?.67:.62;
  const col=full?{s:7.0,sp:8.52,c:10.0,cp:11.7}:{s:8.15,sp:9.38,c:10.28,cp:11.68};
  const headY=full?1.55:2.45;
  pptText(slide,'Pillar',x,headY+.15,nameW,.3,18,{bold:true});
  pptText(slide,'Savings only',col.s-.08,headY,2.05,.28,16,{bold:true,align:'center'});
  pptText(slide,'Savings + Avoidance',col.c-.08,headY,2.54,.28,16,{bold:true,align:'center'});
  [[col.s,1.1,'Value'],[col.sp,.7,'Share'],[col.c,1.18,'Value'],[col.cp,.88,'Share']].forEach(([xx,w,label])=>pptText(slide,label,xx,headY+.36,w,.25,14,{align:'right',color:PPT_COLOR.muted}));
  addPptSafeLine(slide,x,headY+.74,12.6,headY+.74,PPT_COLOR.hair,.6);
  rows.forEach((row,i)=>{const y=rowY+i*rowH,sPct=stack.savings.total?row.Savings/stack.savings.total*100:0,cPct=stack.combined.total?row.Combined/stack.combined.total*100:0;
    slide.addShape('rect',{x,y:y+.08,w:.12,h:.12,fill:{color:stack.colors[row.p.id]},line:{transparency:100}});
    pptText(slide,pptWrapText(row.p.name,nameW-.22,18,2,true),x+.22,y,nameW-.22,.53,18,{bold:true,wrap:true,objectName:`contribution-pillar:${row.p.id}`});
    [[col.s,1.1,fmtMoneyShort(row.Savings,true),'savings','dollar'],[col.sp,.7,fmtShare(sPct),'savings','share'],[col.c,1.18,fmtMoneyShort(row.Combined,true),'combined','dollar'],[col.cp,.88,fmtShare(cPct),'combined','share']].forEach(([xx,w,value,kind,field])=>
      pptText(slide,value,xx,y+.07,w,.32,18,{align:'right',bold:kind==='combined',objectName:`contribution-${field}:${kind}:${row.p.id}`}));
    addPptSafeLine(slide,x,y+rowH-.035,12.6,y+rowH-.035,PPT_COLOR.hair,.45);
  });
  pptAddFullNameNotes(slide,rows.map(r=>r.p.name));
}
function addPptStackedSlide(pptx){
  const slide=pptx.addSlide(),stack=pptStackRows(),savings=stack.savings,combined=stack.combined;
  const top=combined.segments.length?[...combined.segments].sort((a,b)=>b.value-a.value)[0]:null;
  slide.background={color:'FFFFFF'};addPptContext(slide,'Pillar value concentration');
  pptTitle(slide,top?`One pillar carries ${fmtShare(top.pct)} of identified value`:'Pillar value concentration');
  pptText(slide,pptWrapText(top?`Pillar contribution: ${top.p.name}`:'Pillar contribution: no financial values',12.0,20,2),.6,1.25,12,.63,20,{color:PPT_COLOR.muted,wrap:true});
  addPptExecutiveStackBar(slide,savings,stack.colors,.7,'Savings only');
  addPptExecutiveStackBar(slide,combined,stack.colors,3.02,'Savings +\nAvoidance');
  addPptSafeLine(slide,5.25,2.17,5.25,6.54,PPT_COLOR.hair,.7);
  pptContributionTable(slide,stack.rows.slice(0,5),stack);
  pptText(slide,'Colors identify pillars. Both bars represent 100%, not equal dollar values.',.6,6.75,12.0,.28,16,{color:PPT_COLOR.muted});
  slide.addNotes('Pillar value concentration\nRanked contribution\nSavings-only / Total impact\nThe same pillar colors and order are used across both normalized bars. Dollar amounts are separate from percent shares.');
  const remaining=stack.rows.slice(5),pages=pptBalancedPages(remaining,6);
  if(remaining.length)pages.forEach((rows,i)=>{
    const detail=pptx.addSlide();detail.background={color:'FFFFFF'};addPptContext(detail,'Pillar value concentration',`Contribution detail ${i+1}/${pages.length}`);pptTitle(detail,'Pillar contribution (continued)');pptContributionTable(detail,rows,stack,true);
  });
}
function pptRoadmapGroups(){
  if(S.roadmapGroup!=='owner')return S.structure.map(p=>({p,items:S.items.filter(it=>it.pillarId===p.id),kind:'Pillar'}));
  const owners=[...new Set(S.items.map(it=>it.owner||'Unassigned'))].sort((a,b)=>a==='Unassigned'?1:b==='Unassigned'?-1:a.localeCompare(b));
  return owners.map((owner,index)=>{const id=`ppt-owner-${index}`,items=S.items.filter(it=>(it.owner||'Unassigned')===owner).map(it=>({...it,wsId:id}));
    return{p:{id:`owner:${owner}`,name:owner,workstreams:[{id,name:`${items.length} ${items.length===1?'initiative':'initiatives'}`}]},items,kind:'Owner'};});
}
function addPptRoadmapSlides(pptx){const groups=pptRoadmapGroups(),axis=pptPillarAxis(S.items);groups.forEach((group,index)=>addPptPillarSlide(pptx,group.p,index,groups.length,{...group,axis}));}
function addCurrentPptView(pptx){
  if(S.tab==='register')addPptInitiativeRegister(pptx);
  else if(S.tab==='exec')addPptExecutiveSummarySlide(pptx);
  else if(S.tab==='rollup')addPptPortfolioRollupSlide(pptx);
  else if(S.tab==='proj')addPptProjectionSlide(pptx);
  else if(S.tab==='stack')addPptStackedSlide(pptx);
  else addPptRoadmapSlides(pptx);
}
async function exportPowerPoint(scopeOverride){ if(typeof PptxGenJS!=='function'){alert('PowerPoint export is unavailable.');return;}
  const btn=$('pptBtn'),scope=exportScopeValue(typeof scopeOverride==='string'?scopeOverride:null); btn.disabled=true; PPT_EXPORT_CONTEXT=buildExportContext(scope);
  try{ const pptx=new PptxGenJS(); pptx.layout='LAYOUT_WIDE'; pptx.theme={headFontFace:PPT_FONT_FACE,bodyFontFace:PPT_FONT_FACE,lang:'en-US'}; pptx.author='Roadmap Studio'; pptx.subject=`${PPT_EXPORT_CONTEXT.scopeLabel} · ${PPT_EXPORT_CONTEXT.scenario}`; pptx.title=S.fileName||'Roadmap';
    if(scope==='current')addCurrentPptView(pptx);
    else{addPptExecutiveSummarySlide(pptx);addPptPortfolioRollupSlide(pptx);addPptProjectionSlide(pptx);addPptStackedSlide(pptx);addPptRoadmapSlides(pptx);}
    if(scope==='full'&&$('registerAppendix').checked)addPptInitiativeRegister(pptx);
    const blob=await pptx.write({outputType:'blob'}); dl(blob,`${S.fileName||'roadmap'} — roadmap.pptx`);
  }catch(e){ console.error(e); alert('PowerPoint export failed.'); } finally{ PPT_EXPORT_CONTEXT=null;btn.disabled=false; } }
$('pptBtn').onclick=exportPowerPoint;

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
window.addEventListener('resize',()=>{if(S.view==='studio'&&(S.tab==='road'||S.presenting))renderTimeline(); if(S.view==='studio'&&S.tab==='exec')renderExecutiveSummary(); if(S.view==='studio'&&S.tab==='rollup')renderPortfolioRollup(); if(S.view==='studio'&&S.tab==='proj')renderProjection(); if(S.view==='studio'&&S.tab==='stack')renderStackedCharts();});
