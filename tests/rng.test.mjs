import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nextSeed,distance,methodJ,method1,birds,shiny,search} from '../docs/rng.mjs';
const vectors=JSON.parse(readFileSync(new URL('./vectors.json',import.meta.url)));
test('browser calculations match historical golden vectors',()=>{
 for(const v of vectors){
  const p=v.mode==='stationary'?methodJ(parseInt(v.seed,16),v.sync):method1(parseInt(v.seed,16),v.offset);
  for(const key of ['pid','nature','ivs'])assert.deepEqual(p[key],v[key]);
 }
});
test('32-bit arithmetic matches independent BigInt calculation',()=>{
 for(const s of [0,1,0xffffffff,0x80000000,0xabcdef01])
  assert.equal(nextSeed(s),Number((BigInt(s)*0x41c64e6dn+0x6073n)&0xffffffffn));
});
test('distance crosses signed boundaries and wraps',()=>{
 for(const s of [0,0xffffffff,0x80000000,0x12345678]){
  let end=s;for(let i=0;i<1500;i++)end=nextSeed(end);
  assert.equal(distance(s,end),1500);assert.equal(distance(end,s),4294967296-1500);
 }
 assert.equal(distance(0,0),0);
});
test('Oak release matches native calibration and handles selected slots',()=>{
 const rows=birds(0x7e6d9b06,12345,54321);
 assert.deepEqual(rows.map(r=>r.pid),['5980A68B','6B6A463F','1D03049D']);
 assert.deepEqual(rows.map(r=>r.routeIndex),[14,11,20]);
 assert.equal(birds(1,12345,54321,[4],[0,0,0,0,5,0],-1)[0].name,'Zapdos');
 assert.deepEqual(birds(1,12345,54321,[]),[]);
});
test('search returns reachable shiny targets and respects page parity',()=>{
 const options={mode:'stationary',seed:0x12345678,tid:12345,sid:54321,sync:-1,offset:0,limit:50000,stride:2};
 const results=search(options);assert.ok(results.length>0);
 for(const r of results){
  assert.equal(r.advances%2,0);assert.equal(distance(options.seed,parseInt(r.seed,16)),r.advances);
  assert.ok(shiny(parseInt(r.pid,16),options.tid,options.sid));
  assert.equal(methodJ(parseInt(r.seed,16)).pid,r.pid);
 }
 assert.deepEqual(search({...options,limit:0}),[]);
});
