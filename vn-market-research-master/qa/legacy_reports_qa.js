#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const mode = process.env.QA_MODE || 'local';
const master = 'https://vn-market-research-master.vercel.app';
const reports = [
  { id: 'bond', local: 'http://127.0.0.1:8878', production: 'https://vn10y-nghien-cuu.vercel.app', chapter: `${master}/chapters/bond.html` },
  { id: 'participation', local: 'http://127.0.0.1:8879', production: 'https://equity-volume-breadth.vercel.app', chapter: `${master}/chapters/participation.html` },
  { id: 'forecast', local: 'http://127.0.0.1:8880', production: 'https://equity-multivariate-forecast.vercel.app', chapter: `${master}/chapters/forecast.html` },
  { id: 'index-divergence', local: 'http://127.0.0.1:8881', production: 'https://equity-divergence-study.vercel.app', chapter: `${master}/chapters/index-divergence.html` },
  { id: 'stock-divergence', local: 'http://127.0.0.1:8882', production: 'https://equity-stock-volume-divergence.vercel.app', chapter: `${master}/chapters/stock-divergence.html` },
];
const viewports = [
  { id: 'desktop', width: 1440, height: 1100 },
  { id: 'mobile390', width: 390, height: 844 },
  { id: 'mobile320', width: 320, height: 800 },
];

async function main() {
  const screenshotDir = path.join(__dirname, `screenshots-legacy-${mode}`);
  fs.mkdirSync(screenshotDir, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const results = [];
  try {
    for (const report of reports) {
      for (const viewport of viewports) {
        const page = await browser.newPage({ viewport });
        const consoleErrors = [];
        const pageErrors = [];
        const failedResources = [];
        page.on('console', message => {
          const text = message.text();
          if (message.type() === 'error' && !text.includes('favicon') && !text.includes('Failed to load resource: the server responded with a status of 404')) consoleErrors.push(text);
        });
        page.on('pageerror', error => pageErrors.push(error.message));
        page.on('response', response => {
          if (response.status() >= 400 && !response.url().includes('favicon')) failedResources.push(`${response.status()} ${response.url()}`);
        });
        const url = report[mode];
        const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
        await page.waitForSelector('.master-report-bar');
        await page.waitForTimeout(600);
        const metrics = await page.evaluate(({ master, chapter }) => {
          const bar = document.querySelector('.master-report-bar');
          const links = [...bar.querySelectorAll('a')].map(a => a.href.replace(/\/$/, ''));
          const canvases = [...document.querySelectorAll('canvas')];
          return {
            h1Count: document.querySelectorAll('h1').length,
            bannerVisible: !!bar && getComputedStyle(bar).display !== 'none',
            masterLink: links.includes(master),
            chapterLink: links.includes(chapter),
            linkCount: links.length,
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth,
            canvasCount: canvases.length,
            canvasRendered: canvases.every(c => c.getBoundingClientRect().width > 0 && c.getBoundingClientRect().height > 0),
          };
        }, { master, chapter: report.chapter });
        let screenshot = null;
        if (viewport.id !== 'mobile390') {
          screenshot = path.join(screenshotDir, `${report.id}-${viewport.id}.png`);
          await page.screenshot({ path: screenshot, fullPage: false });
        }
        results.push({
          report: report.id,
          viewport,
          url,
          httpStatus: response ? response.status() : null,
          consoleErrors,
          pageErrors,
          failedResources,
          overflow: metrics.scrollWidth > metrics.innerWidth,
          screenshot: screenshot ? path.relative(ROOT, screenshot) : null,
          ...metrics,
        });
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }

  const failures = [];
  for (const result of results) {
    const label = `${result.report}/${result.viewport.id}`;
    if (result.httpStatus !== 200) failures.push(`${label}: HTTP ${result.httpStatus}`);
    if (result.consoleErrors.length) failures.push(`${label}: console errors`);
    if (result.pageErrors.length) failures.push(`${label}: page errors`);
    if (result.failedResources.length) failures.push(`${label}: failed resources`);
    if (result.h1Count !== 1) failures.push(`${label}: h1Count=${result.h1Count}`);
    if (!result.bannerVisible) failures.push(`${label}: banner hidden`);
    if (!result.masterLink || !result.chapterLink || result.linkCount !== 2) failures.push(`${label}: backlink contract`);
    if (result.overflow) failures.push(`${label}: horizontal overflow`);
    if (result.canvasCount < 1 || !result.canvasRendered) failures.push(`${label}: charts not rendered`);
  }
  const output = {
    status: failures.length ? 'FAIL_LEGACY_REPORT_BACKLINK_BROWSER_QA' : 'PASS_LEGACY_REPORT_BACKLINK_BROWSER_QA',
    mode,
    reportCount: reports.length,
    viewportCount: viewports.length,
    checkCount: results.length,
    failures,
    results,
  };
  fs.writeFileSync(path.join(__dirname, `legacy_reports_qa.${mode}.json`), `${JSON.stringify(output, null, 2)}\n`);
  console.log(output.status);
  if (failures.length) {
    console.error(failures.join('\n'));
    process.exit(1);
  }
}

main().catch(error => {
  console.error(error);
  process.exit(2);
});
