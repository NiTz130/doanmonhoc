// Run with NODE_PATH pointing to the directory containing playwright.
// Start a static server for web/ on 127.0.0.1:8765 (or set UI_URL).
// All backend responses use labeled sample data, no paid API or media pipeline.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const fs = require('node:fs');
const base = process.env.UI_URL || 'http://127.0.0.1:8765';
const file = {name:'video-mau.mp4',mimeType:'video/mp4',buffer:Buffer.from('sample')};
const screenshotDir = process.env.SCREENSHOT_DIR || 'docs/ketqua';
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[]; page.on('pageerror', e=>errors.push(e.message));
    let uploadDelay=120;
    let uploads=0, rejectUpload=true, state='dang_chay', polls=0, inFlight=0, maxInFlight=0;
    let stepBuoc='dịch phụ đề';
    let failPoll=false, failSave=false, failImage=false, staleHop=true, boxPayload, termPayload;
    const sampleImage = '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><rect width="1280" height="720" fill="#becfba"/><text x="100" y="220" font-size="55" fill="#234638">KHUNG MAU / DU LIEU GIA LAP</text><text x="320" y="620" font-size="40">This is a sample subtitle.</text></svg>';
    let imageWidth=1280, imageHeight=720;
    await page.route('**/api/**', async route => {
      const req=route.request(), path=new URL(req.url()).pathname;
      if(path==='/api/video') { uploads++; await new Promise(r=>setTimeout(r,uploadDelay)); return route.fulfill(rejectUpload?{status:400,json:{detail:'Video không hợp lệ'}}:{status:202,json:{id:'sample-job',trang_thai:'cho'}}); }
      if(path==='/api/cong-viec/sample-job') {
        polls++; inFlight++; maxInFlight=Math.max(maxInFlight,inFlight);
        await new Promise(r=>setTimeout(r,100)); inFlight--;
        if(failPoll) return route.abort();
        return route.fulfill({json:{id:'sample-job',trang_thai:state,tien_do:state==='dang_chay'?0.42:1,buoc:stepBuoc,co_ket_qua:['xong','suy_giam'].includes(state)}});
      }
      if(path.endsWith('/khung')) return route.fulfill({json:Array.from({length:43},(_,i)=>({i,giay:i+0.3,text:'Dữ liệu mẫu để kiểm tra vùng phụ đề'}))});
      if(/\/khung\/\d+$/.test(path)) return failImage?route.abort():route.fulfill({contentType:'image/svg+xml',body:sampleImage.replace('width="1280" height="720"',`width="${imageWidth}" height="${imageHeight}"`)});
      if(path.endsWith('/hop') && path.includes('/cong-viec/')) {
        boxPayload=req.postDataJSON();
        if(staleHop) {staleHop=false;return route.fulfill({status:409,json:{detail:'Phụ đề gốc đã đổi'}});}
        state='suy_giam';return route.fulfill({json:{id:'sample-job'}});
      }
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
    // Parallax bam con tro. Dung roi ma van doc layout thi moi lan re chuot o bat
    // cu dau trong trang cung bat mot lan reflow, ca luc dang ve hop.
    await page.evaluate(()=>{const el=document.getElementById('scene');window.__doc=0;
      const goc=el.getBoundingClientRect.bind(el);el.getBoundingClientRect=()=>{window.__doc++;return goc();};});
    await page.mouse.move(700,300); await page.mouse.move(760,340);
    assert(await page.evaluate(()=>window.__doc)>0,'canh dang chay thi parallax phai bam con tro');
    await page.locator('#scene-toggle').click();
    assert.equal(await page.locator('#scene').getAttribute('data-motion'),'stopped');
    await page.evaluate(()=>{window.__doc=0;});
    await page.mouse.move(600,300); await page.mouse.move(650,350);
    assert.equal(await page.evaluate(()=>window.__doc),0,'canh dung thi parallax khong duoc doc layout');
    fs.mkdirSync(screenshotDir,{recursive:true});
    for(const width of [1440,768,360]) {
      await page.setViewportSize({width,height:1000});
      for(const id of ['tai-len','tien-do','khung','nhom']) {
        await page.locator(`nav a[href="#${id}"]`).click();
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${id} overflows at ${width}`);
      }
      await page.locator('nav a[href="#tai-len"]').click();
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:`${screenshotDir}/B-upload-${width}.png`,fullPage:true,animations:'disabled'});
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.locator('#video-file').setInputFiles(file);
    // Chon xong phai thay ngay: dong chu mo o duoi hop thi nguoi moi dung khong nhin ra.
    assert(await page.locator('#drop-zone').evaluate(e=>e.classList.contains('da-chon')),'O tha tep phai doi hinh khi da chon video');
    assert(await page.locator('#file-name').evaluate(e=>e.classList.contains('co-file')),'Ten tep da chon phai duoc lam noi bat');
    assert((await page.locator('#file-name').textContent()).startsWith('✓ Đã chọn:'),'Ten tep phai co dau xac nhan');
    await page.locator('#form-tai-len .advanced').evaluate(e=>{e.open=true});
    await page.locator('[name=lang]').fill('');
    await page.locator('#form-tai-len .advanced').evaluate(e=>{e.open=false});
    await page.locator('#upload-submit').click();
    assert.equal(await page.locator('#form-tai-len .advanced').getAttribute('open'),'');
    assert.equal(uploads,0);
    await page.locator('[name=lang]').fill('en');
    await page.locator('#form-tai-len .advanced').evaluate(e=>{e.open=false});
    await page.locator('#form-tai-len').evaluate(form=>{
      form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
      form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
    });
    await page.waitForFunction(()=>document.getElementById('bao').textContent.includes('Video không hợp lệ'));
    assert.equal(uploads,1,'Upload must not be duplicated');
    assert.equal(await page.locator('#video-file').evaluate(e=>e.files[0].name),file.name);
    console.log('PASS validation, duplicate upload, upload failure, parallax va guard cua no, layouts 360/768/1440');
    rejectUpload=false;
    await page.locator('#upload-submit').click();
    await page.waitForFunction(()=>document.getElementById('progress-label').textContent==='42%');
    assert.equal(await page.locator('#scene').getAttribute('data-motion'),'stopped');
    // Stepper bam theo enum `buoc` that cua dieu_phoi. Ten ngoai enum ("canh_bao",
    // hay mot buoc moi them) chi duoc giu nguyen den dang sang, khong tat het.
    const denBuoc=b=>page.locator(`#tien-trinh li[data-buoc=${b}]`).getAttribute('data-trang-thai');
    stepBuoc='dich';
    await page.waitForFunction(()=>document.querySelector('#tien-trinh li[data-buoc=dich]').dataset.trangThai==='dang');
    assert(await page.locator('#thanh-chay').evaluate(e=>e.classList.contains('chay')),'dang chay thi thanh tien do phai co dai sang quet');
    assert.equal(await denBuoc('sub_goc'),'xong','buoc da qua phai sang xanh');
    assert.equal(await denBuoc('render'),'cho','buoc chua toi phai con tat');
    stepBuoc='canh_bao';
    const p0=polls; while(polls<p0+2) await page.waitForTimeout(150);
    assert.equal(await denBuoc('dich'),'dang','buoc ngoai enum khong duoc keo stepper ve 0');
    stepBuoc='dịch phụ đề';
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
    await page.screenshot({path:`screenshotDir/B-progress.png`.replace('screenshotDir',screenshotDir),fullPage:true,animations:'disabled'});
    failPoll=false; state='cho_chon_khung';
    await page.locator('#poll-retry').click();
    await page.locator('#khung').waitFor({state:'visible'});
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    // Mot khung moi cue: 43 phu de thi phai co du 43 anh de kiem hop phu het chua.
    assert.equal(await page.locator('#khung-thumbnails button').count(),43);
    assert.equal(await page.locator('#khung-thumbnails img').first().getAttribute('loading'),'lazy','43 anh tai cung luc se vo, phai lazy');
    assert((await page.locator('#khung-nhan').textContent()).startsWith('khung 1/43'));
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
    // Hop phai sua duoc tai cho: ve lai tu dau chi vi thieu vai pixel la viec phai
    // lam di lam lai, vi con phai bao tron cau hai dong qua ca 8 khung.
    const datHop=async v=>{for(const [k,n] of Object.entries(v))await page.locator(`#form-toa-do [name=${k}]`).fill(String(n));await page.locator('#form-toa-do button').click();};
    const docHop=()=>page.locator('#form-toa-do').evaluate(f=>Object.fromEntries(['x','y','w','h'].map(k=>[k,Number(f.elements[k].value)])));
    const keo=async(tu,den)=>{
      await page.locator('#khung-canvas').scrollIntoViewIfNeeded();
      const b=await page.locator('#khung-canvas').boundingBox();
      await page.mouse.move(b.x+b.width*tu[0],b.y+b.height*tu[1]);
      await page.mouse.down();
      await page.mouse.move(b.x+b.width*den[0],b.y+b.height*den[1],{steps:4});
      await page.mouse.up();
    };
    const gan=async(mong,ten)=>{const v=await docHop();
      for(const k of ['x','y','w','h'])assert(Math.abs(v[k]-mong[k])<.015,`${ten}: ${k}=${v[k]} mong ${mong[k]}`);};

    await datHop({x:.2,y:.7,w:.5,h:.2});
    await keo([.2,.7],[.15,.65]);                 // goc tren-trai: hai canh cung doi
    await gan({x:.15,y:.65,w:.55,h:.25},'keo goc tren-trai');
    await keo([.4,.9],[.4,.95]);                  // canh duoi: chi cao doi
    await gan({x:.15,y:.65,w:.55,h:.30},'keo canh duoi');
    await keo([.425,.8],[.525,.8]);               // keo giua hop: doi cho, giu kich thuoc
    await gan({x:.25,y:.65,w:.55,h:.30},'keo giua hop de doi cho');
    await keo([.9,.2],[.95,.25]);                 // ngoai hop: van la ve hop moi
    await gan({x:.9,y:.2,w:.05,h:.05},'keo ngoai hop phai ve hop moi');
    await datHop({x:.25,y:.65,w:.55,h:.30});

    // Mau neo duoi con tro phai to len va sang mau: keo dung canh tren mot o cao
    // vai pixel thi phai thay ro minh dang tom cai nao truoc khi bam. Doc thang
    // pixel canvas vi mau neo khong phai phan tu DOM.
    const neoDo=()=>page.locator('#khung-canvas').evaluate(c=>c.getContext('2d')
      .getImageData(Math.round(c.width*.25),Math.round(c.height*.65),1,1).data[0]);
    const choNeo=async(dk,ten)=>{for(let i=0;i<30;i++){if(dk(await neoDo()))return;await page.waitForTimeout(50);}
      throw new Error(`${ten}: kenh do = ${await neoDo()}`);};
    const bNeo=await page.locator('#khung-canvas').boundingBox();
    await choNeo(d=>d<210,'chua cham phai la do son #c2362b');
    await page.mouse.move(bNeo.x+bNeo.width*.25,bNeo.y+bNeo.height*.65);
    await choNeo(d=>d>210,'cham vao goc tren-trai phai sang len #e0483a');
    await page.mouse.move(5,5);
    await choNeo(d=>d<210,'roi con tro ra phai tro lai nhu cu');

    // Phu de nhay cho: sang khung 11, chuyen sang pham vi rieng, ve vung tren dinh,
    // roi ap cho ca dai 11-13. Vung chung cua ca video phai khong bi dong vao.
    await page.locator('#khung-thumbnails button').nth(10).click();
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    await page.locator('[name=pham_vi][value=rieng]').check();
    await datHop({x:.3,y:.05,w:.3,h:.10});
    await page.locator('#form-day').locator('xpath=ancestor::details').evaluate(e=>{e.open=true});
    await page.locator('#form-day [name=tu]').fill('11');
    await page.locator('#form-day [name=den]').fill('13');
    await page.locator('#form-day button').click();
    assert((await page.locator('#bao').textContent()).includes('câu 11–13'));
    assert.equal(await page.locator('#khung-thumbnails button.rieng').count(),3,'3 cau phai duoc danh dau rieng');

    // Khung 11 dung vung rieng; khung 1 van dung vung chung. Doi khung phai doi hop.
    await page.locator('#khung-thumbnails button').nth(10).click();
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    assert.equal(await page.locator('[name=pham_vi]:checked').getAttribute('value'),'rieng');
    await gan({x:.3,y:.05,w:.3,h:.10},'khung trong dai phai dung vung rieng');
    await page.locator('#khung-thumbnails button').nth(0).click();
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    assert.equal(await page.locator('[name=pham_vi]:checked').getAttribute('value'),'chung');
    await gan({x:.25,y:.65,w:.55,h:.30},'khung ngoai dai phai dung vung chung');

    await page.locator('#form-toa-do [name=w]').fill('.99');
    await page.locator('#form-toa-do button').click();
    assert((await page.locator('#bao').textContent()).includes('Vùng phải nằm'));
    await page.locator('#form-toa-do [name=w]').fill('.5');
    await page.locator('#form-toa-do button').click();
    await page.screenshot({path:`${screenshotDir}/B-region.png`,fullPage:true,animations:'disabled'});
    failImage=true;await page.locator('#khung-toi').click();
    await page.locator('#khung-anh').evaluate(img=>{img.src=img.src+'?failed=1'});
    await page.waitForFunction(()=>document.getElementById('image-status').textContent.includes('Không tải'));
    assert(await page.locator('#hop-gui').isDisabled());
    failImage=false;await page.locator('#khung-lui').click();
    await page.waitForFunction(()=>document.getElementById('image-status').textContent==='');
    await page.locator('#hop-luu-nhom').check();
    await page.locator('#hop-gui').click();
    await page.waitForFunction(()=>document.getElementById('bao').textContent.includes('Phụ đề gốc đã đổi'));
    assert(await page.locator('#hop-gui').isEnabled(),'409 stale phai cho phep gui lai');
    await page.locator('#hop-gui').click();
    await page.waitForFunction(()=>document.getElementById('viec-trang-thai').textContent.includes('còn dòng'));
    assert.equal(boxPayload.vung.length,2,'mot hop chung + mot hop cho dai cau');
    const [chung,rieng]=boxPayload.vung;
    assert.equal(chung.cue,null,'hop chung phai mang cue=null');
    assert(Math.abs(chung.x-.25)<.015 && Math.abs(chung.w-.5)<.015);
    assert.deepEqual(rieng.cue,[10,11,12],'hop rieng phai mang dung chi so cau 11-13');
    assert.equal(boxPayload.che_do_vung,'thay_the','Frontend moi phai gui ro mode replacement');
    assert(Math.abs(rieng.y-.05)<.015,'hop rieng phai giu toa do rieng cua no');
    assert.equal(boxPayload.luu_nhom,true,'Tich o mac dinh nhom phai di kem hop');
    assert.equal(await page.locator('#tai-ket-qua').getAttribute('href'),'/api/cong-viec/sample-job/ket-qua');
    await page.locator('#tai-ket-qua').evaluate(a=>{a.href='data:video/mp4;base64,c2FtcGxl';a.download='sample_vi.mp4'});
    const downloadPromise=page.waitForEvent('download'); await page.locator('#tai-ket-qua').click();
    const download=await downloadPromise;assert.equal(download.suggestedFilename(),'sample_vi.mp4');
    await page.screenshot({path:`${screenshotDir}/B-result.png`,fullPage:true,animations:'disabled'});
    state='loi';
    await page.locator('nav a[href="#tai-len"]').click();
    await page.locator('nav a[href="#tien-do"]').click();
    await page.waitForFunction(()=>document.getElementById('viec-trang-thai').textContent.startsWith('Lỗi'));
    assert(await page.locator('#upload-submit').isEnabled(),'job loi phai mo lai thao tac tai len');
    console.log('PASS polling recovery, stepper theo enum buoc, shimmer thanh tien do, mau neo bat con tro, 20 navigation cycles, 43 frames (one per cue, lazy), landscape/portrait coordinates, resize/move box, per-cue regions, group-default flag, image error, degraded result/download');
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
    await page.screenshot({path:`${screenshotDir}/B-glossary.png`,fullPage:true,animations:'disabled'});
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




