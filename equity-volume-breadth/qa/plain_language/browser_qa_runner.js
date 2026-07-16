const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const url = 'file:///Users/bobo/ZCodeProject/equity-volume-breadth/index.html';
  const shotDir = '/Users/bobo/ZCodeProject/equity-volume-breadth/screenshots';
  const viewports = [
    { name: 'desktop', w: 1440, h: 1100 },
    { name: 'mobile-390', w: 390, h: 844 },
    { name: 'small-320', w: 320, h: 800 },
  ];
  const results = { viewports: {}, charts_rendered: 0, console_errors: [], overflow_issues: [] };

  for (const vp of viewports) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    page.on('pageerror', err => errors.push(String(err)));

    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Check canvas rendered (non-zero size)
    const canvasInfo = await page.evaluate(() => {
      const canvases = document.querySelectorAll('canvas');
      return Array.from(canvases).map(c => ({
        id: c.id, w: c.offsetWidth, h: c.offsetHeight,
        hasContent: c.width > 0 && c.height > 0
      }));
    });

    // Check horizontal overflow
    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    const overflows = overflow.scrollWidth > overflow.innerWidth;

    // Screenshot (hero + full)
    await page.screenshot({ path: path.join(shotDir, `${vp.name}-hero.png`) });
    await page.screenshot({ path: path.join(shotDir, `${vp.name}-full.png`), fullPage: true });

    // For desktop also screenshot the OOS section
    if (vp.name === 'desktop') {
      const oosEl = await page.$('#oos-giai-thich');
      if (oosEl) await oosEl.screenshot({ path: path.join(shotDir, 'desktop-oos.png') });
      const mainEl = await page.$('#dien-truoc');
      if (mainEl) await mainEl.screenshot({ path: path.join(shotDir, 'desktop-results.png') });
      results.charts_rendered = canvasInfo.filter(c => c.hasContent).length;
    }

    results.viewports[vp.name] = {
      canvas_count: canvasInfo.length,
      canvas_rendered: canvasInfo.filter(c => c.hasContent).length,
      canvas_details: canvasInfo,
      console_errors: errors,
      scrollWidth: overflow.scrollWidth,
      innerWidth: overflow.innerWidth,
      overflow: overflows,
    };
    if (errors.length) results.console_errors.push({ viewport: vp.name, errors });
    if (overflows) results.overflow_issues.push({ viewport: vp.name, scrollWidth: overflow.scrollWidth, innerWidth: overflow.innerWidth });

    await ctx.close();
  }

  await browser.close();

  // Gate checks
  const allChartsRender = Object.values(results.viewports).every(v => v.canvas_rendered === 3);
  const noConsoleErrors = results.console_errors.length === 0;
  const noOverflow = results.overflow_issues.length === 0;

  results.gate_summary = {
    charts_rendered_ok: allChartsRender,
    zero_console_errors: noConsoleErrors,
    no_horizontal_overflow: noOverflow,
    overall_pass: allChartsRender && noConsoleErrors && noOverflow,
  };

  fs.writeFileSync(
    '/Users/bobo/ZCodeProject/equity-volume-breadth/qa/plain_language/browser_qa.json',
    JSON.stringify(results, null, 2)
  );
  console.log('GATE:', results.gate_summary.overall_pass ? 'PASS' : 'FAIL');
  console.log('charts:', results.charts_rendered, '/ 4');
  console.log('console errors:', results.console_errors.length);
  console.log('overflow issues:', results.overflow_issues.length);
  process.exit(results.gate_summary.overall_pass ? 0 : 1);
})();
