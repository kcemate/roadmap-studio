/* ============ SHARED DEFINITIONS ============
   Every view, drilldown, and export derives its numbers, names, and formats from this file.
   See README "Financial Definitions" for the rules these functions implement. */

/* Brand settings accepted for decks (validated in model.js). Defined here because exports bind controls at load. */
const BRAND_FONTS=['Arial','Calibri','Aptos','Helvetica','Georgia','Segoe UI','Verdana'];
const MAX_LOGO_CHARS=400*1024;

/* ---------- names ---------- */
const DEFAULT_PROJECT_NAME='Untitled roadmap';
const WORKING_PLAN_NAME='Working plan';
const LABELS={
  approval:'Approval', Approved:'Active', Proposed:'Proposed', realized:'Realized',
  contribution:'Pillar Contribution', projection:'Projection', register:'Initiative Register',
  exec:'Executive Summary', rollup:'Portfolio Rollup', road:'Roadmap', struct:'Structure', data:'Initiatives'
};
const COLUMN_LABELS={name:'Initiative',pillar:'Pillar',ws:'Workstream',start:'Start',end:'End',mile:'Milestone',status:'Status',approval:'Approval',valueType:'Savings / Avoidance',value:'$ Value',include:'In totals',realized:'% Realized',confidence:'Confidence',owner:'Owner'};

/* ---------- statuses ----------
   Cancelled initiatives leave every financial total (they are listed with excluded value).
   Blocked and On Hold stay in totals and are flagged for review. Unrecognized imported statuses
   load as Not Started, keep the original text in importedStatus, and are flagged for review. */
const STATUSES=['Not Started','On Track','At Risk','Blocked','On Hold','Complete','Cancelled'];
const STATUS_RULES={
  'Not Started':'In totals.','On Track':'In totals.','At Risk':'In totals; flagged as a risk.',
  'Blocked':'In totals; flagged for a decision.','On Hold':'In totals; flagged for review.','Complete':'In totals.',
  'Cancelled':'Excluded from every financial total, projection, and goal measure.'
};
function recognizeStatus(v){
  const s=textOf(v).trim().toLowerCase().replace(/[\s_-]+/g,' ');
  if(!s)return'Not Started';
  const exact=STATUSES.find(status=>status.toLowerCase()===s);if(exact)return exact;
  if(/cancel|abandon|dropped|withdrawn|terminated/.test(s))return'Cancelled';
  if(/block|stuck/.test(s))return'Blocked';
  if(/hold|pause|defer|parked|suspend/.test(s))return'On Hold';
  if(/risk|delay|behind|late|slip|\b(red|amber|yellow)\b/.test(s))return'At Risk';
  if(/complete|\bdone\b|closed|finished|delivered/.test(s))return'Complete';
  if(/\bnot\b|plan|backlog|future|\btodo\b|to do|queued/.test(s))return'Not Started';
  if(/track|green|progress|active|underway|started|ongoing/.test(s))return'On Track';
  return null;
}
function normStatus(v){ return recognizeStatus(v)||'Not Started'; }
function statusCountsInTotals(status){ return normStatus(status)!=='Cancelled'; }
function isRiskStatus(status){ return ['At Risk','Blocked'].includes(normStatus(status)); }

/* ---------- inclusion, timing, financial initiatives ---------- */
function isIncludedInTotals(it){ return !it||(it.includeInTotals!==false&&statusCountsInTotals(it.status)); }
function exclusionLabel(it){ return it.includeInTotals===false?'Excluded from portfolio totals':normStatus(it.status)==='Cancelled'?'Cancelled · excluded from totals':''; }
function itemDates(it){
  const start=projectionDateOf(it,'start'),end=it.milestone?start:projectionDateOf(it,'end');
  return{start,end};
}
/* Undated: no start, no end (unless a milestone), or an end before the start. Undated work stays in the
   portfolio but cannot be placed on a timeline or projected. */
function isUndated(it){ const{start,end}=itemDates(it); return !start||!end||end<start; }
/* A financial initiative is included in totals and carries planned value or recorded realization. */
function isFinancialInitiative(it,date=reportingDate()){
  return isIncludedInTotals(it)&&(itemValue(it)>0||Math.max(0,realizedItemValue(it,date))>0);
}

/* ---------- the single aggregation path ---------- */
function emptyTotals(){
  return{Total:0,Savings:0,Avoidance:0,Approved:0,Proposed:0,Realized:0,RealizedSavings:0,RealizedAvoidance:0,
    RealizedInPlan:0,RealizedBeyondPlan:0,Remaining:0,Expected:0,Undated:0,UndatedCount:0,Excluded:0,ExcludedCount:0,
    Count:0,FinancialCount:0,Cost:0,Net:0,
    buckets:{realized:{Savings:0,Avoidance:0},approved:{Savings:0,Avoidance:0},proposed:{Savings:0,Avoidance:0}}};
}
function addItemToTotals(out,it,date){
  const value=itemValue(it);
  if(!isIncludedInTotals(it)){out.Excluded+=value;out.ExcludedCount++;return;}
  const type=normValueType(it.valueType),approval=approvalStatus(it),realized=Math.max(0,realizedItemValue(it,date));
  const inPlan=Math.min(value,realized),cost=parseMoney(it.cost)||0;
  out.Count++;if(value>0||realized>0)out.FinancialCount++;
  out.Total+=value;out[type]+=value;out[approval]+=value;
  out.Realized+=realized;out['Realized'+type]+=realized;out.RealizedInPlan+=inPlan;out.RealizedBeyondPlan+=realized-inPlan;
  out.Remaining+=value-inPlan;out.Expected+=value*parseConfidence(it.confidence)/100;
  out.buckets.realized[type]+=inPlan;out.buckets[approval==='Approved'?'approved':'proposed'][type]+=value-inPlan;
  out.Cost+=cost;out.Net+=value-cost;
  if(isUndated(it)){out.Undated+=value;out.UndatedCount++;}
}
function portfolioTotals(items=S.items,date=reportingDate()){
  const out=emptyTotals();items.forEach(it=>addItemToTotals(out,it,date));return out;
}
// Retained name used by register, drilldown, and comparison code.
function portfolioFinancialTotals(items=S.items,date=reportingDate()){ return portfolioTotals(items,date); }

/* ---------- goals ----------
   One goal basis: identified planned value (Active + Proposed, lifetime, unweighted) against the goal.
   A goal of zero or blank means "No goal set". Confidence-weighted projections are reported as a share
   of the goal on the Projection view, never as a second gap. */
function portfolioGoal(){ const g=parseMoney(S.projectionTarget); return g!==''&&g>0?g:''; }
function portfolioStretchGoal(){ const g=parseMoney(S.stretchGoal); return g!==''&&g>0?g:''; }
function goalStatus(t=portfolioTotals()){
  const goal=portfolioGoal(),stretch=portfolioStretchGoal();
  if(goal==='')return{set:false,goal:'',stretch,identified:t.Total,active:t.Approved,proposed:t.Proposed,realized:t.Realized,gap:null};
  return{set:true,goal,stretch,identified:t.Total,active:t.Approved,proposed:t.Proposed,realized:t.Realized,gap:goal-t.Total,
    identifiedPct:t.Total/goal*100,activePct:t.Approved/goal*100,realizedPct:t.Realized/goal*100,
    proposedNeeded:Math.max(0,Math.min(t.Proposed,goal-t.Approved))};
}
function goalHeadline(gs=goalStatus()){
  if(!gs.set)return gs.identified?`No goal set · ${fmtMoneyShort(gs.identified)} identified opportunity`:'No goal set · add initiative values to build the portfolio';
  if(!gs.identified)return`No opportunity identified toward the ${fmtMoneyShort(gs.goal)} goal`;
  if(gs.gap>0)return`Identified opportunity is ${fmtMoneyShort(gs.gap)} short of the ${fmtMoneyShort(gs.goal)} goal`;
  if(gs.gap<0)return`Identified opportunity exceeds the ${fmtMoneyShort(gs.goal)} goal by ${fmtMoneyShort(-gs.gap)}`;
  return`Identified opportunity meets the ${fmtMoneyShort(gs.goal)} goal`;
}
function goalGapText(gs=goalStatus()){
  if(!gs.set)return'No goal set';
  return gs.gap>0?`${fmtMoneyShort(gs.gap)} to goal`:gs.gap<0?`${fmtMoneyShort(-gs.gap)} above goal`:'Goal reached';
}

/* ---------- formatting ----------
   Money: summaries, charts, and slides use three significant figures with the unit promoted after
   rounding ($999.5K -> $1M). Inputs, the register, and notes use exact dollars (cents kept when entered).
   Percent: one decimal at most, trailing zero removed; tiny non-zero shares show "<0.1%". */
function fmtMoneyShort(v){
  const n=parseMoney(v),x=n===''?0:n;
  const a=Math.abs(x),sign=x<0?'-':'';
  if(Math.round(a)===0)return'$0';
  if(Math.round(a)<1000)return`${sign}$${Math.round(a)}`;
  const units=[[1e3,'K'],[1e6,'M'],[1e9,'B'],[1e12,'T']];
  let k=0;units.forEach(([u],i)=>{if(a>=u)k=i;});
  const render=(scaled)=>{const d=scaled>=100?0:scaled>=10?1:2,s=scaled.toFixed(d);return s.includes('.')?s.replace(/0+$/,'').replace(/\.$/,''):s;};
  let text=render(a/units[k][0]);
  while(Number(text)>=1000&&k<units.length-1){k++;text=render(a/units[k][0]);}
  return`${sign}$${text}${units[k][1]}`;
}
function fmtMoneyExact(v){
  const n=parseMoney(v);if(n===''||n==null)return'';
  const cents=Math.round(n*100)%100!==0;
  return n.toLocaleString('en-US',{style:'currency',currency:'USD',minimumFractionDigits:cents?2:0,maximumFractionDigits:cents?2:0});
}
function fmtPct(n){
  if(n===''||n==null||!Number.isFinite(Number(n)))return'0%';
  const v=Number(n),r=Math.round(v*10)/10;
  if(v>0&&r===0)return'<0.1%';
  return`${String(r).replace(/\.0$/,'')}%`;
}
function fmtShare(pct){ return fmtPct(pct); }
function fmtGoalProgress(value,goal){ return goal?fmtPct(value/goal*100):'—'; }
function fmtDateRange(start,end){
  if(!start&&!end)return'Unscheduled';
  return`${start?fmtDate(start):'Start not set'} – ${end?fmtDate(end):'End not set'}`;
}
function fyLabel(fy,fyStart=S.fyStart){ return fyStart===0?String(fy):`FY${fy}`; }
