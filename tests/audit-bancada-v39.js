const {chromium}=require('playwright');

(async()=>{
  const browser=await chromium.launch({headless:true});
  const results=[];
  for(const width of [320,360,375,390,412,430,768]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const errors=[];
    page.on('pageerror',error=>errors.push(String(error)));
    page.on('console',message=>{if(message.type()==='error')errors.push(message.text())});
    await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded',timeout:30000});
    await page.waitForTimeout(1400);
    const data=await page.evaluate(()=>{
      const api=window.ITA_BANCADA;
      const horizontalOverflow=document.documentElement.scrollWidth>document.documentElement.clientWidth+1;
      return {
        version:api?.version||null,
        registry:api?.audit?.()||[],
        horizontalOverflow,
        serviceWorkerSupported:'serviceWorker' in navigator,
        coreCss:Boolean([...document.styleSheets].find(sheet=>sheet.href?.includes('bancada-core-v1.css')))
      };
    });
    results.push({width,...data,errors:[...new Set(errors)]});
    await page.close();
  }
  console.log(JSON.stringify({audit:'Bancada Digital V39.1.0',generatedAt:new Date().toISOString(),results},null,2));
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1)});
