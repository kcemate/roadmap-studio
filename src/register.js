/* Read-only portfolio register: all initiatives, independent of grid filters. */
function initiativeRegisterData(){
  const groups=S.structure.map(p=>({id:p.id,name:p.name,items:S.items.filter(it=>it.pillarId===p.id)}));
  const orphaned=S.items.filter(it=>!S.structure.some(p=>p.id===it.pillarId));
  if(orphaned.length)groups.push({id:'register-unassigned',name:'Unassigned pillar',items:orphaned});
  groups.forEach(group=>{
    group.items=[...group.items].sort((a,b)=>(approvalStatus(a)==='Approved'?0:1)-(approvalStatus(b)==='Approved'?0:1)||String(a.name).localeCompare(String(b.name),undefined,{numeric:true,sensitivity:'base'}));
    group.totals=portfolioFinancialTotals(group.items,reportingDate());
  });
  return{groups:groups.filter(g=>g.items.length),totals:portfolioFinancialTotals(S.items,reportingDate()),count:S.items.length};
}
function registerTiming(it){
  const start=parseAnyDate(it.start,'start',S.fyStart),end=parseAnyDate(it.end,'end',S.fyStart);
  if(it.milestone)return start?`${fmtDate(start)} (milestone)`:'Unscheduled';
  if(!start&&!end)return'Unscheduled';
  return `${start?fmtDate(start):'Start not set'} - ${end?fmtDate(end):'End not set'}`;
}
function registerCells(it){
  const included=isIncludedInTotals(it);
  return[
    `${it.name||'Untitled initiative'}${included?'':'\nExcluded from portfolio totals'}`,
    approvalLabel(approvalStatus(it)),
    `${normValueType(it.valueType)}\n${fmtGoalMoney(itemValue(it),false)}`,
    fmtGoalMoney(realizedItemValue(it,reportingDate()),false),
    registerTiming(it),
    it.owner||'Unassigned'
  ];
}
const REGISTER_HEADINGS=['Initiative','Category','Savings / Avoidance + Value','Realized $','Timing','Owner'];
function registerTotalsText(totals){
  return `Savings ${fmtGoalMoney(totals.Savings,false)} · Avoidance ${fmtGoalMoney(totals.Avoidance,false)} · Realized ${fmtGoalMoney(totals.Realized,false)}`;
}
function renderInitiativeRegister(){
  const data=initiativeRegisterData();
  $('registerContext').textContent=`${S.fileName||'Roadmap'} · ${exportScenarioName()} · As of ${fmtDate(reportingDate())}`;
  $('registerSummary').textContent=`${data.count} ${data.count===1?'initiative':'initiatives'} · ${registerTotalsText(data.totals)}`;
  $('registerBody').innerHTML=data.groups.length?data.groups.map(group=>`<section class="register-group">
    <table class="register-table" aria-label="${esc(group.name)} initiatives">
      <colgroup><col style="width:30%"><col style="width:11%"><col style="width:16%"><col style="width:13%"><col style="width:18%"><col style="width:12%"></colgroup>
      <thead><tr class="register-pillar"><th colspan="6" scope="colgroup"><p class="register-repeat-context">${esc($('registerContext').textContent)}</p><h3>${esc(group.name)}</h3><p>${group.items.length} initiatives · ${esc(registerTotalsText(group.totals))}</p></th></tr>
      <tr class="register-columns">${REGISTER_HEADINGS.map(label=>`<th scope="col">${esc(label)}</th>`).join('')}</tr></thead>
      <tbody>${group.items.map(it=>{const cells=registerCells(it);return `<tr class="register-row" data-id="${esc(it.id)}">${cells.map((text,i)=>`<${i?'td':'th scope="row"'} data-label="${esc(REGISTER_HEADINGS[i])}">${i===0?`<span>${esc(it.name||'Untitled initiative')}</span>${isIncludedInTotals(it)?'':'<small class="register-excluded">Excluded from portfolio totals</small>'}`:esc(text).replace(/\n/g,'<br>')}</${i?'td':'th'}>`).join('')}</tr>`;}).join('')}</tbody>
    </table></section>`).join(''):'<p class="register-empty">No initiatives yet.</p>';
}
function prepareRegisterPrint(){
  renderInitiativeRegister();document.body.classList.add('register-print');
}
function printInitiativeRegister(){
  prepareRegisterPrint();
  try{window.print();}catch(error){document.body.classList.remove('register-print');throw error;}
}
window.addEventListener('beforeprint',()=>{if(S.tab==='register')prepareRegisterPrint();});
window.addEventListener('afterprint',()=>document.body.classList.remove('register-print'));
$('registerPrint').onclick=printInitiativeRegister;
$('registerPpt').onclick=()=>exportPowerPoint('current');

// Explicit line breaks keep complete names editable in PowerPoint without autofit.
function registerPptLines(value,width,font=16,bold=false){
  const lines=[];
  String(value).split('\n').forEach(paragraph=>{
    let line='';
    for(const word of paragraph.split(/\s+/)){
      if(pptTextWidthIn(line?`${line} ${word}`:word,font,bold)<=width*.94){line=line?`${line} ${word}`:word;continue;}
      if(line){lines.push(line);line='';}
      for(const char of word){
        if(line&&pptTextWidthIn(line+char,font,bold)>width*.94){lines.push(line);line='';}
        line+=char;
      }
    }
    lines.push(line);
  });
  return lines;
}
function addPptInitiativeRegister(pptx){
  const data=initiativeRegisterData(),widths=[3.65,1.25,2.05,1.6,2.05,1.55],font=16,lineH=.27;
  const pages=[];
  data.groups.forEach(group=>{
    let rows=[],height=0;
    group.items.forEach(it=>{
      const cells=registerCells(it).map((text,i)=>registerPptLines(text,widths[i]-.18,font,i===0));
      const h=Math.max(.64,Math.max(...cells.map(lines=>lines.length))*lineH+.2);
      if(h>3.75){
        if(rows.length)pages.push({group,rows});
        pages.push({group,rows:[],detail:it});rows=[];height=0;return;
      }
      if(rows.length&&height+h>3.75){pages.push({group,rows});rows=[];height=0;}
      rows.push({it,cells,h});height+=h;
    });
    if(rows.length)pages.push({group,rows});
  });
  if(!pages.length)pages.push({group:{name:'All pillars',totals:data.totals},rows:[]});
  pages.forEach((page,index)=>{
    const slide=pptx.addSlide();slide.background={color:'FFFFFF'};
    addPptContext(slide,'Initiative Register',`Register ${index+1}/${pages.length}`,{weighting:'Unweighted values'});
    pptTitle(slide,'Initiative Register');
    const groupLines=registerPptLines(page.group.name,12.1,20,true);
    pptText(slide,groupLines.join('\n'),.6,1.23,12.1,Math.min(.65,groupLines.length*.3),20,{bold:true,wrap:true});
    const t=page.group.totals;
    pptText(slide,`Savings ${fmtMoneyShort(t.Savings,true)}   ·   Avoidance ${fmtMoneyShort(t.Avoidance,true)}   ·   Realized ${fmtMoneyShort(t.Realized,true)}`,.6,1.96,12.1,.32,16,{color:PPT_COLOR.muted});
    if(page.detail){
      const it=page.detail,cells=registerCells(it),nameLines=registerPptLines(cells[0],12.05,16,true);
      pptText(slide,nameLines.join('\n'),.66,2.4,12.05,nameLines.length*.27+.12,16,{bold:true,wrap:true,valign:'top',objectName:`register-row:${it.id}:0`});
      const detailWidths=[2.1,3,3,4.05];let dx=.6;
      cells.slice(1,5).forEach((value,i)=>{
        pptText(slide,registerPptLines(REGISTER_HEADINGS[i+1],detailWidths[i]-.2,14,true).join('\n'),dx+.06,4.4,detailWidths[i]-.2,.48,14,{bold:true,wrap:true});
        pptText(slide,registerPptLines(value,detailWidths[i]-.2,16).join('\n'),dx+.06,4.95,detailWidths[i]-.2,.74,16,{wrap:true,valign:'top',objectName:`register-row:${it.id}:${i+1}`});dx+=detailWidths[i];
      });
      pptText(slide,'Owner',.66,5.89,1.2,.3,14,{bold:true});
      pptText(slide,registerPptLines(cells[5],10.6,16).join('\n'),2,5.89,10.6,.81,16,{wrap:true,valign:'top',objectName:`register-row:${it.id}:5`});
      pptText(slide,'Totals exclude marked initiatives. All initiative values are shown.',.6,6.86,12,.25,12,{color:PPT_COLOR.muted});
      pptItemNotes(slide,[it]);return;
    }
    let x=.6;
    REGISTER_HEADINGS.forEach((label,i)=>{pptText(slide,registerPptLines(label,widths[i]-.18,14,true).join('\n'),x+.06,2.5,widths[i]-.18,.48,14,{bold:true,wrap:true});x+=widths[i];});
    let y=3.03;addPptSafeLine(slide,.6,y,12.75,y,PPT_COLOR.hair);
    page.rows.forEach(row=>{
      x=.6;
      row.cells.forEach((lines,i)=>{pptText(slide,lines.join('\n'),x+.06,y+.1,widths[i]-.18,row.h-.16,font,{bold:i===0,wrap:true,valign:'top',breakLine:false,objectName:`register-row:${row.it.id}:${i}`,paraSpaceAfterPt:0,lineSpacingMultiple:1});x+=widths[i];});
      y+=row.h;addPptSafeLine(slide,.6,y,12.75,y,PPT_COLOR.hair,.5);
    });
    if(!page.rows.length)pptText(slide,'No initiatives yet.',.66,3.23,10,.4,18);
    pptText(slide,'Totals exclude marked initiatives. All initiative values are shown.',.6,6.86,12,.25,12,{color:PPT_COLOR.muted});
    pptItemNotes(slide,page.rows.map(row=>row.it));
  });
}
