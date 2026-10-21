// Optional browser QA: install Playwright separately, or set PLAYWRIGHT_PATH.
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const {mkdirSync}=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(process.argv[2]||'http://127.0.0.1:8765');
  await page.getByRole('button',{name:'Try an example'}).click();
  await page.waitForFunction(()=>document.querySelectorAll('.target-card').length>0);
  assert.match(await page.locator('#result-status').innerText(),/EXAMPLE ONLY/);
  assert.equal(await page.locator('.target-card button').first().isDisabled(),true);
  await page.locator('#seed').fill('notaseed');await page.getByRole('button',{name:'Find shiny targets'}).click();
  assert.match(await page.locator('#result-status').innerText(),/hexadecimal/);
  await page.locator('#snapshot').fill('{bad json');await page.locator('#import').click();
  assert.equal(await page.locator('#import-status').evaluate(e=>e.classList.contains('error')),true);
  await page.locator('#seed').fill('12345678');await page.locator('#mode').selectOption('birds');
  await page.getByRole('button',{name:'Find shiny targets'}).click();
  assert.match(await page.locator('#result-status').innerText(),/full monitor snapshot/);
  const snap={schema:'pt-rng-snapshot-v1',version:'0.1.13',sha256:'test-only',seed:'12345678',tid:12345,sid:54321,lead:{synchronize:false},route_indexes:[0,0,0,0,0,0],bird_release_slots:[],previous_map:-1};
  await page.locator('#snapshot').fill(JSON.stringify(snap));await page.locator('#import').click();
  await page.getByRole('button',{name:'Find shiny targets'}).click();
  assert.match(await page.locator('#result-status').innerText(),/No birds are eligible/);
  snap.bird_release_slots=[3,4,5];await page.locator('#snapshot').fill(JSON.stringify(snap));await page.locator('#import').click();
  await page.getByRole('button',{name:'Find shiny targets'}).click();
  await page.waitForFunction(()=>document.querySelector('#result-status').textContent.startsWith('Predictions ready'));
  assert.ok(await page.locator('.target-card').count());
  await page.locator('#before').fill('00000000');await page.locator('#after').fill('00006073');
  await page.getByRole('button',{name:'Measure',exact:true}).click();assert.equal(await page.locator('#distance-result').innerText(),'1 advance.');
  await page.locator('#mode').selectOption('stationary');await page.getByRole('button',{name:'Find shiny targets'}).click();
  await page.waitForFunction(()=>document.querySelector('#result-status').textContent.startsWith('Predictions ready'));
  mkdirSync('verification-local',{recursive:true});await page.goto(process.argv[2]||'http://127.0.0.1:8765');
  await page.screenshot({path:'verification-local/desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,'mobile overflow');
  await page.screenshot({path:'verification-local/mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);console.log('Browser QA passed: demo, bad input, bird eligibility, search worker, seed distance, desktop and mobile.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
