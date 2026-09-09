// Run with NODE_PATH pointing to the directory containing playwright.
// Start a static server for web/ on 127.0.0.1:8765 (or set UI_URL).
// All backend responses use labeled sample data, no paid API or media pipeline.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const fs = require('node:fs');
const base = process.env.UI_URL || 'http://127.0.0.1:8765';
const file = {name:'video-mau.mp4',mimeType:'video/mp4',buffer:Buffer.from('sample')};
const screenshotDir = 'docs/ketqua';
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[]; page.on('pageerror', e=>errors.push(e.message));
    let uploadDelay=120;
    let uploads=0, rejectUpload=true, state='dang_chay', polls=0, inFlight=0, maxInFlight=0;
    let failPoll=false, failSave=false, failImage=false, boxPayload, termPayload;
    const sampleImage = '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><rect width="1280" height="720" fill="#becfba"/><text x="100" y="220" font-size="55" fill="#234638">KHUNG MAU / DU LIEU GIA LAP</text><text x="320" y="620" font-size="40">This is a sample subtitle.</text></svg>';
    let imageWidth=1280, imageHeight=720;
    await page.route('**/api/**', async route => {
      const req=route.request(), path=new URL(req.url()).pathname;
      if(path==='/api/video') { uploads++; await new Promise(r=>setTimeout(r,uploadDelay)); return route.fulfill(rejectUpload?{status:400,json:{detail:'Video không hợp lệ'}}:{status:202,json:{id:'sample-job',trang_thai:'cho'}}); }
      if(path==='/api/cong-viec/sample-job') {
        polls++; inFlight++; maxInFlight=Math.max(maxInFlight,inFlight);
        await new Promise(r=>setTimeout(r,100)); inFlight--;
        if(failPoll) return route.abort();
        return route.fulfill({json:{id:'sample-job',trang_thai:state,tien_do:state==='dang_chay'?0.42:1,buoc:'dịch phụ đề',co_ket_qua:['xong','suy_giam'].includes(state)}});
      }
      if(path.endsWith('/khung')) return route.fulfill({json:Array.from({length:8},(_,i)=>({i,giay:i+0.3,text:'Dữ liệu mẫu để kiểm tra vùng phụ đề'}))});
      if(/\/khung\/\d+$/.test(path)) return failImage?route.abort():route.fulfill({contentType:'image/svg+xml',body:sampleImage.replace('width="1280" height="720"',`width="${imageWidth}" height="${imageHeight}"`)});
      if(path.endsWith('/hop') && path.includes('/cong-viec/')) {boxPayload=req.postDataJSON();state='suy_giam';return route.fulfill({json:{id:'sample-job'}});}
      if(path.endsWith('/ket-qua')) return route.fulfill({contentType:'video/mp4',headers:{'Content-Disposition':'attachment; filename="sample_vi.mp4"'},body:'sample-result'});
      if(path==='/api/nhom') return route.fulfill({json:req.method()==='POST'?{ten:'Mẫu'}:[{ten:'Nhóm mẫu',blur_x:null}]});
      if(path.endsWith('/thuat-ngu')) {
        if(req.method()==='POST'){termPayload=req.postDataJSON();if(failSave)return route.fulfill({status:500,json:{detail:'Lưu thất bại'}});}
        return route.fulfill({json:{Ironhold:'Thành Sắt'}});
      }
      if(path.endsWith('/hop'))return route.fulfill({json:{x:.3,y:.855,w:.4,h:.09}});
      throw new Error('Unexpected API request '+path);
    });
    await page.goto(base);
    await page.evaluate(()=>document.fonts.ready);
    await page.waitForFunction(()=>document.getElementById('scene').dataset.scene==='webgl');
    await page.locator('#scene-toggle').click();
    assert.equal(await page.locator('#scene').getAttribute('data-motion'),'stopped');
    fs.mkdirSync(screenshotDir,{recursive:true});
    for(const width of [1440,768,360]) {
      await page.setViewportSize({width,height:1000});
      for(const id of ['tai-len','tien-do','khung','nhom']) {
        await page.locator(`nav a[href="#${id}"]`).click();
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${id} overflows at ${width}`);
      }
      await page.locator('nav a[href="#tai-len"]').click();
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:`${screenshotDir}/B-upload-${width}.png`,fullPage:true});
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.locator('#video-file').setInputFiles(file);
    await page.locator('.advanced').evaluate(e=>{e.open=true});
    await page.locator('[name=lang]').fill('');
    await page.locator('.advanced').evaluate(e=>{e.open=false});
    await page.locator('#upload-submit').click();
    assert.equal(await page.locator('.advanced').getAttribute('open'),'');
    assert.equal(uploads,0);
    await page.locator('[name=lang]').fill('en');
    await page.locator('.advanced').evaluate(e=>{e.open=false});
    await page.locator('#form-tai-len').evaluate(form=>{
      form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
      form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
    });
    await page.waitForFunction(()=>document.getElementById('bao').textContent.includes('Video không hợp lệ'));
    assert.equal(uploads,1,'Upload must not be duplicated');
    assert.equal(await page.locator('#video-file').evaluate(e=>e.files[0].name),file.name);
    console.log('PASS validation, duplicate upload, upload failure, layouts 360/768/1440');
    rejectUpload=false;
    await page.locator('#upload-submit').click();
    await page.waitForFunction(()=>document.getElementById('progress-label').textContent==='42%');
    assert.equal(await page.locator('#scene').getAttribute('data-motion'),'stopped');
    const before= polls;
    for(let i=0;i<20;i++) {
      await page.locator('nav a[href="#tai-len"]').click();
      await page.locator('nav a[href="#tien-do"]').click();
    }
    assert.equal(maxInFlight,1,'Only one poll may be in flight');
    assert(polls-before<8,'Navigation must not create polling loops');
    assert.equal(await page.locator('#scene canvas').count(),1);
    failPoll=true;
    await page.locator('#poll-retry').waitFor({state:'visible'});
    assert.equal(await page.locator('#progress-label').textContent(),'42%');
    await page.screenshot({path:`screenshotDir/B-progress.png`.replace('screenshotDir',screenshotDir),fullPage:true});
    failPoll=false; state='cho_chon_khung';
    await page.locator('#poll-retry').click();
    await page.locator('#khung').waitFor({state:'visible'});
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    assert.equal(await page.locator('#khung-thumbnails button').count(),8);
    for(const [k,v] of Object.entries({x:.2,y:.75,w:.5,h:.15}))await page.locator(`#form-toa-do [name=${k}]`).fill(String(v));
    await page.locator('#form-toa-do button').click();
    const saved=await page.locator('#khung-hop').textContent();
    await page.locator('#khung-toi').click();
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    assert.equal(await page.locator('#khung-hop').textContent(),saved);
    for(const [w,h] of [[1280,720],[1920,1080],[720,1280],[1080,1920]]) {
      imageWidth=w;imageHeight=h;
      await page.locator('#khung-toi').click();
      await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
      await page.locator('#khung-anh').evaluate((img, size)=>{img.src=img.src.split('?')[0]+'?size='+size}, w+'x'+h);
      await page.waitForFunction(([w,h])=>{const img=document.getElementById('khung-anh');return img.complete && img.naturalWidth===w && img.naturalHeight===h},[w,h]);
      await page.setViewportSize({width:w>h?768:360,height:900});
      await page.locator('#khung-canvas').scrollIntoViewIfNeeded();
      const bounds=await page.locator('#khung-canvas').boundingBox();
      const image=await page.locator('#khung-anh').boundingBox();
      assert(Math.abs(bounds.width-image.width)<1 && Math.abs(bounds.height-image.height)<1,'Canvas must match actual image');
      await page.mouse.move(bounds.x+bounds.width*.75,bounds.y+bounds.height*.9);
      await page.mouse.down();await page.mouse.move(bounds.x+bounds.width*.25,bounds.y+bounds.height*.7);await page.mouse.up();
      const vals=await page.locator('#form-toa-do').evaluate(f=>Object.fromEntries(['x','y','w','h'].map(k=>[k,Number(f.elements[k].value)])));
      for(const [k,v] of Object.entries({x:.25,y:.7,w:.5,h:.2}))assert(Math.abs(vals[k]-v)<.015,`${w}x${h} ${k} mismatch`);
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.locator('#form-toa-do [name=w]').fill('.99');
    await page.locator('#form-toa-do button').click();
    assert((await page.locator('#bao').textContent()).includes('Vùng phải nằm'));
    await page.locator('#form-toa-do [name=w]').fill('.5');
    await page.locator('#form-toa-do button').click();
    await page.screenshot({path:`${screenshotDir}/B-region.png`,fullPage:true});
    failImage=true;await page.locator('#khung-toi').click();
    await page.locator('#khung-anh').evaluate(img=>{img.src=img.src+'?failed=1'});
    await page.waitForFunction(()=>document.getElementById('image-status').textContent.includes('Không tải'));
    assert(await page.locator('#hop-gui').isDisabled());
    failImage=false;await page.locator('#khung-lui').click();
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    await page.locator('#hop-gui').click();
    await page.waitForFunction(()=>document.getElementById('viec-trang-thai').textContent.includes('còn dòng'));
    assert(Math.abs(boxPayload.x-.25)<.015 && Math.abs(boxPayload.w-.5)<.015);
    assert.equal(await page.locator('#tai-ket-qua').getAttribute('href'),'/api/cong-viec/sample-job/ket-qua');
    await page.locator('#tai-ket-qua').evaluate(a=>{a.href='data:video/mp4;base64,c2FtcGxl';a.download='sample_vi.mp4'});
    const downloadPromise=page.waitForEvent('download'); await page.locator('#tai-ket-qua').click();
    const download=await downloadPromise;assert.equal(download.suggestedFilename(),'sample_vi.mp4');
    await page.screenshot({path:`${screenshotDir}/B-result.png`,fullPage:true});
    console.log('PASS polling recovery, 20 navigation cycles, 8 frames, landscape/portrait coordinates, image error, degraded result/download');
    rejectUpload=true;uploadDelay=1000;
    await page.locator('nav a[href="#tai-len"]').click();
    const terminalPolls=polls;
    await page.locator('#upload-submit').click();
    await page.locator('nav a[href="#tien-do"]').click();
    await page.waitForFunction(()=>document.getElementById('bao').textContent.includes('Video không hợp lệ'));
    assert.equal(polls,terminalPolls,'Navigation during upload must not poll the old job');
    await page.locator('nav a[href="#nhom"]').click();
    await page.getByRole('button',{name:'Xem thuật ngữ'}).click();
    await page.getByRole('cell',{name:'Thành Sắt',exact:true}).waitFor();
    await page.locator('#form-thuat-ngu [name=goc]').fill('Ironhold');
    await page.locator('#form-thuat-ngu [name=dich]').fill('Thành Sắt');
    await page.locator('#form-thuat-ngu [name=khoa]').check();failSave=true;
    await page.locator('#form-thuat-ngu button').click();
    await page.waitForFunction(()=>document.getElementById('bao').textContent==='Lưu thất bại');
    assert.equal(await page.locator('#form-thuat-ngu [name=dich]').inputValue(),'Thành Sắt');
    assert.equal(termPayload.khoa,true);
    failSave=false;await page.locator('#form-thuat-ngu button').click();
    await page.waitForFunction(()=>document.getElementById('bao').textContent==='Đã lưu thuật ngữ.');
    await page.screenshot({path:`${screenshotDir}/B-glossary.png`,fullPage:true});
    await page.locator('nav a[href="#tai-len"]').click();
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(()=>document.getElementById('scene').dataset.scene==='static');
    assert.equal(await page.locator('#scene canvas').count(),0);
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.waitForFunction(()=>document.getElementById('scene').dataset.scene==='webgl');
    await page.locator('#scene canvas').evaluate(c=>c.dispatchEvent(new Event('webglcontextlost',{cancelable:true})));
    assert.equal(await page.locator('#scene canvas').count(),0);
    assert(await page.locator('.scene-fallback').isVisible());
    assert.deepEqual(errors,[]);
    const fallbackPage=await browser.newPage();
    await fallbackPage.route('**/scene.js',r=>r.abort());
    await fallbackPage.goto(base);
    await fallbackPage.locator('#video-file').setInputFiles(file);
    assert(await fallbackPage.locator('#upload-submit').isEnabled());
    assert(await fallbackPage.locator('.scene-fallback').isVisible());
    await fallbackPage.close();
    console.log('PASS glossary failed-save retention and lock payload, reduced motion, context loss and missing module fallback; no uncaught JS errors');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});




