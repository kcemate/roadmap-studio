/* Read-only portfolio register: all initiatives, independent of grid filters. */
function initiativeRegisterData(){
  const groups=S.structure.map(p=>({id:p.id,name:p.name,items:S.items.filter(it=>it.pillarId===p.id)}));
  const orphaned=S.items.filter(it=>!S.structure.some(p=>p.id===it.pillarId));
  if(orphaned.length)groups.push({id:'register-unassigned',name:'Unassigned pillar',items:orphaned});
  groups.forEach(group=>{
    group.items=[...group.items].sort((a,b)=>(approvalStatus(a)==='Approved'?0:1)-(approvalStatus(b)==='Approved'?0:1)||String(a.name).localeCompare(String(b.name),undefined,{numeric:true,sensitivity:'base'}));
    group.totals=portfolioTotals(group.items,reportingDate());
  });
  return{groups:groups.filter(g=>g.items.length),totals:portfolioTotals(S.items,reportingDate()),count:S.items.length};
}
function registerTiming(it){
  const{start,end}=itemDates(it);
  if(it.milestone)return start?`${fmtDate(start)} (milestone)`:'Unscheduled';
  return fmtDateRange(start,end);
}
/* Register amounts are exact dollars on the web, in print, and in PowerPoint. Recurring annual inputs show both the
   entered annual amount and the lifetime value that enters totals. */
function registerValueText(it){
  const lifetime=fmtMoneyExact(itemValue(it))||'$0';
  return it.benefitKind==='recurring'&&it.valueBasis==='annual'?`${lifetime}\n(${fmtMoneyExact(it.value)||'$0'} per year)`:lifetime;
}
function registerCells(it){
  const excluded=exclusionLabel(it),status=normStatus(it.status);
  return[
    `${it.name||'Untitled initiative'}${excluded?`\n${excluded}`:''}`,
    `${approvalLabel(approvalStatus(it))}\n${status}`,
    `${normValueType(it.valueType)}\n${registerValueText(it)}`,
    fmtMoneyExact(Math.max(0,realizedItemValue(it,reportingDate())))||'$0',
    registerTiming(it),
    `${it.owner||'Unassigned'}${it.nextStep?`\nNext: ${it.nextStep}`:''}`
  ];
}
const REGISTER_HEADINGS=['Initiative','Approval / Status','Savings / Avoidance + Value','Realized $','Timing','Owner / Next step'];
function registerTotalsText(totals){
  return `Savings ${fmtMoneyExact(totals.Savings)} · Avoidance ${fmtMoneyExact(totals.Avoidance)} · Realized ${fmtMoneyExact(totals.Realized)}${totals.Excluded?` · Excluded ${fmtMoneyExact(totals.Excluded)}`:''}`;
}
function renderInitiativeRegister(){
  const data=initiativeRegisterData();
  $('registerContext').textContent=`${S.fileName||DEFAULT_PROJECT_NAME} · ${exportScenarioName()} · As of ${fmtDate(reportingDate())}`;
  $('registerSummary').textContent=`${countLabel(data.count,'initiative')} · ${registerTotalsText(data.totals)}`;
  $('registerBody').innerHTML=data.groups.length?data.groups.map(group=>`<section class="register-group">
    <table class="register-table" aria-label="${esc(group.name)} initiatives">
      <colgroup><col style="width:30%"><col style="width:11%"><col style="width:16%"><col style="width:13%"><col style="width:18%"><col style="width:12%"></colgroup>
      <thead><tr class="register-pillar"><th colspan="6" scope="colgroup"><p class="register-repeat-context">${esc($('registerContext').textContent)}</p><h3>${esc(group.name)}</h3><p>${countLabel(group.items.length,'initiative')} · ${esc(registerTotalsText(group.totals))}</p></th></tr>
      <tr class="register-columns">${REGISTER_HEADINGS.map(label=>`<th scope="col">${esc(label)}</th>`).join('')}</tr></thead>
      <tbody>${group.items.map(it=>{const cells=registerCells(it);return `<tr class="register-row" data-id="${esc(it.id)}">${cells.map((text,i)=>`<${i?'td':'th scope="row"'} data-label="${esc(REGISTER_HEADINGS[i])}">${i===0?`<span>${esc(it.name||'Untitled initiative')}</span>${exclusionLabel(it)?`<small class="register-excluded">${esc(exclusionLabel(it))}</small>`:''}`:esc(text).replace(/\n/g,'<br>')}</${i?'td':'th'}>`).join('')}</tr>`;}).join('')}</tbody>
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
function registerPptLines(value,width,font=PPT_TYPE.body,bold=false){
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
/* Register appendix: exact dollars, the same columns as the web register, 14 pt body, rows never split. */
function addPptInitiativeRegister(pptx){
  const data=initiativeRegisterData(),widths=[3.55,1.6,2.15,1.5,2.0,1.53],font=PPT_TYPE.body,lineH=.235,bodyTop=2.2,bodyMax=4.3;
  const pages=[];
  data.groups.forEach(group=>{
    let rows=[],height=0;
    group.items.forEach(it=>{
      const cells=registerCells(it).map((text,i)=>registerPptLines(text,widths[i]-.18,font,i===0));
      const h=Math.max(.5,Math.max(...cells.map(lines=>lines.length))*lineH+.16);
      if(h>bodyMax){
        if(rows.length)pages.push({group,rows});
        pages.push({group,rows:[],detail:it});rows=[];height=0;return;
      }
      if(rows.length&&height+h>bodyMax){pages.push({group,rows});rows=[];height=0;}
      rows.push({it,cells,h});height+=h;
    });
    if(rows.length)pages.push({group,rows});
  });
  if(!pages.length)pages.push({group:{name:'All pillars',totals:data.totals},rows:[]});
  pages.forEach((page,index)=>{
    const slide=pptSlide(pptx);
    addPptContext(slide,'Initiative Register',`Register ${index+1}/${pages.length}`);
    pptTitle(slide,`Initiative Register: ${page.group.name}`);
    const t=page.group.totals;
    pptText(slide,pptBoundText(registerTotalsText(t),12.3,PPT_TYPE.body),.5,1.35,12.33,.3,PPT_TYPE.body,{color:PPT_COLOR.muted});
    if(page.detail){
      const it=page.detail,cells=registerCells(it),nameLines=registerPptLines(cells[0],12.2,font,true);
      pptText(slide,nameLines.join('\n'),.56,1.85,12.2,nameLines.length*lineH+.12,font,{bold:true,wrap:true,valign:'top',objectName:`register-row:${it.id}:0`});
      const detailWidths=[2.1,3,3,4.2];let dx=.5;
      cells.slice(1,5).forEach((value,i)=>{
        pptText(slide,REGISTER_HEADINGS[i+1],dx+.06,4.3,detailWidths[i]-.2,.3,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted});
        pptText(slide,registerPptLines(value,detailWidths[i]-.2,font).join('\n'),dx+.06,4.65,detailWidths[i]-.2,.8,font,{wrap:true,valign:'top',objectName:`register-row:${it.id}:${i+1}`});dx+=detailWidths[i];
      });
      pptText(slide,REGISTER_HEADINGS[5],.56,5.6,2,.26,PPT_TYPE.caption,{bold:true,color:PPT_COLOR.muted});
      pptText(slide,registerPptLines(cells[5],12.2,font).join('\n'),.56,5.9,12.2,.7,font,{wrap:true,valign:'top',objectName:`register-row:${it.id}:5`});
      pptText(slide,'Excluded initiatives do not count. Cancelled initiatives count only recorded actuals.',.5,6.68,8.5,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted});
      pptItemNotes(slide,[it]);return;
    }
    let x=.5;
    REGISTER_HEADINGS.forEach((label,i)=>{pptText(slide,registerPptLines(label,widths[i]-.18,PPT_TYPE.caption,true).join('\n'),x+.06,1.78,widths[i]-.18,.36,PPT_TYPE.caption,{bold:true,wrap:true,color:PPT_COLOR.muted,valign:'bottom'});x+=widths[i];});
    let y=bodyTop;addPptSafeLine(slide,.5,y,12.83,y,PPT_COLOR.hair);
    page.rows.forEach(row=>{
      x=.5;
      row.cells.forEach((lines,i)=>{pptText(slide,lines.join('\n'),x+.06,y+.08,widths[i]-.18,row.h-.12,font,{bold:i===0,wrap:true,valign:'top',breakLine:false,objectName:`register-row:${row.it.id}:${i}`,paraSpaceAfterPt:0,lineSpacingMultiple:1});x+=widths[i];});
      y+=row.h;addPptSafeLine(slide,.5,y,12.83,y,PPT_COLOR.hair,.5);
    });
    if(!page.rows.length)pptText(slide,'No initiatives yet.',.56,bodyTop+.2,10,.4,PPT_TYPE.body);
    pptText(slide,'Excluded initiatives do not count. Cancelled initiatives count only recorded actuals.',.5,6.68,8.5,.24,PPT_TYPE.caption,{color:PPT_COLOR.muted});
    pptItemNotes(slide,page.rows.map(row=>row.it));
  });
}
