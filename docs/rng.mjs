// Independent 32-bit arithmetic, shared by the browser worker and Node tests.
export const ROUTES=[342,343,344,345,346,347,349,350,353,354,356,362,363,365,366,367,371,373,380,382,383,385,388,391,467,392,395,200,204];
export const NATURES=['Hardy','Lonely','Brave','Adamant','Naughty','Bold','Docile','Relaxed','Impish','Lax','Timid','Hasty','Serious','Jolly','Naive','Modest','Mild','Quiet','Bashful','Rash','Calm','Gentle','Sassy','Careful','Quirky'];
export const nextSeed=s=>(Math.imul(s,0x41c64e6d)+0x6073)>>>0;
export const hex=n=>(n>>>0).toString(16).toUpperCase().padStart(8,'0');
export const shiny=(pid,tid,sid)=>(tid^sid^(pid&65535)^(pid>>>16))<8;
export const ivs=w=>[0,5,10,20,25,15].map(i=>(w>>>i)&31);
export function distance(seed,target){
 let a=0x41c64e6d,c=0x6073,count=0,bit=1;
 for(let i=0;i<32;i++){
  if((seed&bit)!==(target&bit)){seed=(Math.imul(seed,a)+c)>>>0;count=(count|bit)>>>0;}
  c=Math.imul(c,(a+1)>>>0)>>>0;a=Math.imul(a,a)>>>0;bit=(bit<<1)>>>0;
 }
 return count;
}
export function method1(s,offset=4){
 for(let i=0;i<offset;i++)s=nextSeed(s);
 s=nextSeed(s);const lo=s>>>16;s=nextSeed(s);const pid=(lo|((s>>>16)<<16))>>>0;
 s=nextSeed(s);const x=s>>>16;s=nextSeed(s);const y=s>>>16;
 return {pid:hex(pid),nature:pid%25,ivs:ivs((x&32767)|((y&32767)<<15)),endSeed:s};
}
export function methodJ(s,sync=-1){
 const draw=()=>{s=nextSeed(s);return s>>>16;};
 const nature=sync>=0&&Math.floor(draw()/32768)===0?sync:Math.floor(draw()/2622);
 let pid;
 for(let i=0;i<20000;i++){
  pid=(draw()|(draw()<<16))>>>0;
  if(pid%25===nature)break;
  if(i===19999)throw Error('PID generation exceeded safety bound.');
 }
 const x=draw(),y=draw();
 return {pid:hex(pid),nature,ivs:ivs((x&32767)|((y&32767)<<15)),endSeed:s};
}
export function birds(s,tid,sid,slots=[3,4,5],indexes=[0,0,0,0,0,0],previous=-1){
 const out=[];
 for(const slot of slots){
  const p=method1(s,0);s=p.endSeed;delete p.endSeed;
  let route;
  do{s=nextSeed(s);route=Math.floor((s>>>16)/2260);}while(route===indexes[slot]||ROUTES[route]===previous);
  out.push({...p,name:({3:'Moltres',4:'Zapdos',5:'Articuno'})[slot],routeIndex:route,shiny:shiny(parseInt(p.pid,16),tid,sid)});
 }
 return out;
}
export function predict(s,options){
 const {mode,tid,sid,sync=-1,offset=0,snapshot}=options;
 if(mode==='birds'){
  const list=birds(s,tid,sid,snapshot.bird_release_slots,snapshot.route_indexes,snapshot.previous_map);
  const picked=list.find(p=>p.shiny)||list[0];
  return {...picked,birds:list,shinyCount:list.filter(p=>p.shiny).length};
 }
 for(let i=0;i<offset;i++)s=nextSeed(s);
 const p=mode==='roamer'?method1(s,0):methodJ(s,sync);delete p.endSeed;
 return {...p,shiny:shiny(parseInt(p.pid,16),tid,sid)};
}
export function search(options){
 let s=options.seed;const out=[];
 for(let i=0;i<=options.limit;i++){
  if(i%options.stride===0){
   const p=predict(s,options);
   if(p.shiny){out.push({...p,seed:hex(s),advances:i});if(out.length>=5)break;}
  }
  s=nextSeed(s);
 }
 return out;
}
