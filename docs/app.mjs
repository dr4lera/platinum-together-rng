import {NATURES,hex,distance} from './rng.mjs';
const $=id=>document.getElementById(id);
let snapshot=null,worker=null,example=false;
const DEFAULTS={stationary:0,roamer:4,birds:0};
const HELP={stationary:'Verified in 0.1.12 for Uxie, Azelf, Dialga, Palkia, Heatran, Reshiram, Victini, Xerneas, Yveltal and Zekrom. Giratina is not yet validated by this public tool.',roamer:'First Cresselia / Mesprit release only. The Pokémon is fixed when released, not when encountered later. Measured pre-generation offset: 4.',birds:'Requires an imported snapshot. Uses Oak’s eligible release slots, previous map, and route state. Re-release calculations are experimental.'};
for(let i=0;i<25;i++)$('sync').add(new Option(`On — ${NATURES[i]} lead`,String(i)));
const message=(id,text,error=false)=>{$(id).textContent=text;$(id).classList.toggle('error',error);};
function seedValue(s){s=s.trim().replace(/^0x/i,'');if(!/^[0-9a-f]{1,8}$/i.test(s))throw Error('Enter a seed of 1–8 hexadecimal digits.');return parseInt(s,16)>>>0;}
function uint(v,label,max=65535){if(!/^\d+$/.test(String(v))||Number(v)>max)throw Error(`${label} must be a whole number from 0 to ${max}.`);return Number(v);}
function importSnapshot(){
 try{
  const s=JSON.parse($('snapshot').value);
  if(s.schema!=='pt-rng-snapshot-v1')throw Error('This is not a PT RNG monitor snapshot. Use Copy snapshot in the monitor.');
  seedValue(s.seed);uint(s.tid,'TID');uint(s.sid,'SID');
  if(typeof s.version!=='string'||typeof s.sha256!=='string'||!Array.isArray(s.route_indexes)||s.route_indexes.length!==6||s.route_indexes.some(i=>!Number.isInteger(i)||i<0||i>28)||!Array.isArray(s.bird_release_slots)||s.bird_release_slots.some((i,k,a)=>![3,4,5].includes(i)||(k>0&&i<=a[k-1]))||!Number.isInteger(s.previous_map))throw Error('Snapshot context is incomplete or invalid. Reconnect and copy a fresh snapshot.');
  if(s.lead?.synchronize&&(!Number.isInteger(s.lead.nature)||s.lead.nature<0||s.lead.nature>24))throw Error('Invalid lead nature.');
  snapshot=s;example=s.version==='Example';$('seed').value=hex(seedValue(s.seed));$('tid').value=s.tid;$('sid').value=s.sid;
  $('sync').value=s.lead?.synchronize?String(s.lead.nature):'-1';
  message('import-status',example?'Example data loaded. Replace this with a live snapshot before hunting.':`Imported build ${s.version}. ${s.calibration||'Verify encounter calibration for your build.'}`);
 }catch(e){snapshot=null;example=false;message('import-status',e.message,true);}
}
$('import').addEventListener('click',importSnapshot);
$('demo').addEventListener('click',()=>{
 $('snapshot').value=JSON.stringify({schema:'pt-rng-snapshot-v1',version:'Example',sha256:'',seed:'12345678',tid:12345,sid:54321,lead:{synchronize:false,nature:0},route_indexes:[0,0,0,0,0,0],bird_release_slots:[3,4,5],previous_map:-1},null,2);
 importSnapshot();$('mode').value='stationary';updateMode();$('search-form').requestSubmit();
});
function updateMode(){const m=$('mode').value;$('offset').value=DEFAULTS[m];$('offset').disabled=m==='birds';$('sync-box').hidden=m!=='stationary';message('mode-help',HELP[m]);}
$('mode').addEventListener('change',updateMode);
function finish(){if(worker){worker.terminate();worker=null;}$('find').disabled=false;$('cancel').hidden=true;}
$('cancel').addEventListener('click',()=>{finish();message('result-status','Search cancelled.');});
function element(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
function render(results,options){
 $('results').replaceChildren();$('result-count').textContent=`${results.length} TARGET${results.length===1?'':'S'}`;
 message('result-status',results.length?`${example?'EXAMPLE ONLY · ':''}Predictions ready. Confirm the encounter model and live seed before interacting.`:'No shiny target in this range. Expand the search, or reset normally and import a fresh snapshot.');
 if(!results.length){$('results').append(element('div','No nearby target doesn’t mean shiny-locked. Each new seed gives a different search window.','empty'));return;}
 for(const r of results){
  const card=element('article',undefined,'target-card');const top=element('div',undefined,'target-top');top.append(element('strong',r.advances.toLocaleString()),element('span','RNG ADVANCES'));card.append(top);
  card.append(element('p',options.stride===2?`${r.advances/2} page turns only if each turn advances exactly 2.`:'Advanced mode: use measured RNG changes to reach this target.'));
  card.append(element('p',`TARGET ${r.seed} · PID ${r.pid}`,'seed-line'));
  card.append(element('h3',`${r.name?r.name+' · ':''}${NATURES[r.nature]} · Shiny prediction`));
  const row=element('div',undefined,'iv-row');['HP','ATK','DEF','SP.ATK','SP.DEF','SPEED'].forEach((label,i)=>{const c=element('div');c.append(element('small',label),element('b',r.ivs[i]));row.append(c);});card.append(row);
  if(r.birds)card.append(element('p',r.birds.map(b=>`${b.name}: ${b.shiny?'SHINY':'not shiny'}`).join(' · '),'bird-result'));
  const button=element('button',example?'Example only — import your game':'Track in monitor ↗','button secondary');button.type='button';button.disabled=example;
  button.addEventListener('click',async()=>{
   const target={schema:'pt-rng-target-v1',seed:r.seed,tid:options.tid,sid:options.sid,sha256:snapshot?.sha256||'',mode:options.mode};
   try{await navigator.clipboard.writeText(JSON.stringify(target));button.textContent='Copied — paste target in monitor';}
   catch{const t=element('textarea');t.value=JSON.stringify(target);t.readOnly=true;card.append(t);t.select();message('result-status','Clipboard unavailable. Copy the displayed target JSON manually.');}
  });card.append(button);$('results').append(card);
 }
}
$('search-form').addEventListener('submit',event=>{
 event.preventDefault();finish();
 try{
  const mode=$('mode').value,tid=uint($('tid').value,'TID'),sid=uint($('sid').value,'SID'),seed=seedValue($('seed').value);
  if(mode==='birds'){
   if(!snapshot)throw Error('Import a full monitor snapshot for Oak’s birds. Seed and IDs alone are not enough.');
   if(tid!==snapshot.tid||sid!==snapshot.sid)throw Error('Trainer IDs differ from the imported bird context. Copy and import a fresh snapshot.');
   if(!snapshot.bird_release_slots.length)throw Error('No birds are eligible for Oak to release in this snapshot. Knock out unwanted birds, beat the League afterward, then copy a fresh snapshot before talking to Oak.');
  }
  const options={seed,tid,sid,mode,sync:Number($('sync').value),limit:Number($('limit').value),stride:Number($('stride').value),offset:uint($('offset').value,'Offset',1000),snapshot};
  $('find').disabled=true;$('cancel').hidden=false;message('result-status','Searching locally…');
  worker=new Worker(new URL('./worker.mjs',import.meta.url),{type:'module'});
  worker.onmessage=({data})=>{finish();if(data.error)message('result-status',data.error,true);else render(data.results,options);};
  worker.onerror=()=>{finish();message('result-status','Could not start the predictor. Open this page over HTTPS or a local web server, and allow its local scripts.',true);};
  worker.postMessage(options);
 }catch(e){message('result-status',e.message,true);}
});
$('distance-form').addEventListener('submit',event=>{
 event.preventDefault();try{const n=distance(seedValue($('before').value),seedValue($('after').value));message('distance-result',`${n.toLocaleString()} advance${n===1?'':'s'}${n>1000000?' — unexpected jump; check the seeds and direction.':'.'}`);}catch(e){message('distance-result',e.message,true);}
});
