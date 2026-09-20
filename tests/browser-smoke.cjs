// Run with Playwright installed: node tests/browser-smoke.cjs
// PLAYWRIGHT_MODULE may name an existing installation. App must run on localhost:8765.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];
  page.on('pageerror', err=>errors.push(err.message));
  try {
    await page.goto('http://127.0.0.1:8765');
    await page.getByRole('button',{name:'What makes LEO different from GEO?',exact:false}).waitFor();
    assert.equal(await page.locator('html').getAttribute('lang'),'en');
    await page.getByRole('button',{name:'繁體中文',exact:true}).click();
    assert.equal(await page.locator('html').getAttribute('lang'),'zh-TW');
    await page.getByRole('button',{name:'連接 AI ↗',exact:true}).click();
    await page.getByRole('heading',{name:'連接你的學習助手。'}).waitFor();
    await page.keyboard.press('Escape');
    await page.getByRole('button',{name:'English',exact:true}).click();
    await page.locator('#question').fill('What is a gateway?');
    await page.locator('#question').press('Enter');
    await page.locator('.message.assistant').waitFor();
    assert.match(await page.locator('.message.assistant').innerText(),/not an AI answer/);
    assert.ok(await page.locator('.source-card').count()>0);
    assert.match(await page.locator('.page-link').first().getAttribute('href'),/^\/document#page=\d+$/);
    await page.getByRole('button',{name:'繁體中文',exact:true}).click();
    assert.match(await page.locator('.message.user').innerText(),/What is a gateway/);
    assert.match(await page.locator('.message.assistant').innerText(),/not an AI answer/);
    assert.match(await page.locator('#source-heading').innerText(),/參考來源/);
    // Inject only the external answer boundary to exercise rendered answer translation and citation UI.
    const fixture={id:'ui-fixture',page:29,section:'Ground segment',text:'A gateway connects satellite links to a ground network.',labels:[],warning:'',version:'2.0'};
    await page.route('**/api/chat',r=>r.fulfill({json:{mode:'answer',sources:[fixture],sections:[{kind:'evidence',text:'A gateway connects satellite links to ground networks.',citations:['ui-fixture']}],retrieval:'keyword'}}));
    await page.route('**/api/translate',r=>r.fulfill({json:{sections:[{kind:'evidence',text:'閘道站連接衛星鏈路與地面網路。',citations:['ui-fixture']}],sources:[fixture]}}));
    await page.getByRole('button',{name:'English',exact:true}).click();
    await page.locator('#question').fill('Explain a gateway');
    await page.locator('#send').click();
    await page.getByText('A gateway connects satellite links to ground networks.',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Translate to Chinese',exact:true}).click();
    await page.getByText('閘道站連接衛星鏈路與地面網路。',{exact:true}).waitFor();
    assert.equal(await page.locator('.citation').last().innerText(),'p. 29');
    await page.getByRole('button',{name:'Show original',exact:true}).click();
    await page.getByText('A gateway connects satellite links to ground networks.',{exact:true}).waitFor();
    await page.unroute('**/api/chat');
    await page.locator('#question').fill('chocolate cake recipe');
    await page.locator('#send').click();
    await page.getByText('I could not find document passages that support an answer.',{exact:false}).waitFor();
    await page.getByRole('button',{name:'New conversation',exact:false}).click();
    assert.equal(await page.locator('.message').count(),0);
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.getByRole('button',{name:'繁體中文',exact:true}).click();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    if(process.env.QA_OUTPUT){
      fs.mkdirSync(process.env.QA_OUTPUT,{recursive:true});
      await page.screenshot({path:path.join(process.env.QA_OUTPUT,'mobile-chinese.png'),fullPage:true});
      await page.setViewportSize({width:1440,height:1050});
      await page.getByRole('button',{name:'English',exact:true}).click();
      await page.screenshot({path:path.join(process.env.QA_OUTPUT,'desktop-english.png'),fullPage:true});
    }
    assert.deepEqual(errors,[]);
    console.log('PASS: English/Chinese UI, real retrieval, source links, history preservation, translation UI (fixture), unsupported query, reset, mobile layout, no browser errors.');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
