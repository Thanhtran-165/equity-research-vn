#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const SITE = path.join(ROOT, 'site');
const QA_LABEL = process.env.QA_LABEL || '';
const SCREENSHOTS = path.join(__dirname, QA_LABEL ? `screenshots-${QA_LABEL}` : 'screenshots');
const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8877';

const routes = [
  { id: 'master', path: '/' },
  { id: 'bond', path: '/chapters/bond.html' },
  { id: 'participation', path: '/chapters/participation.html' },
  { id: 'forecast', path: '/chapters/forecast.html' },
  { id: 'index-divergence', path: '/chapters/index-divergence.html' },
  { id: 'stock-divergence', path: '/chapters/stock-divergence.html' },
];

const viewports = [
  { id: 'desktop', width: 1440, height: 1100 },
  { id: 'mobile390', width: 390, height: 844 },
  { id: 'mobile320', width: 320, height: 800 },
];

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

async function main() {
  fs.mkdirSync(SCREENSHOTS, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const results = [];
  let mobileMenuPass = false;

  try {
    for (const viewport of viewports) {
      for (const route of routes) {
        const page = await browser.newPage({ viewport });
        const consoleErrors = [];
        const pageErrors = [];
        page.on('console', (message) => {
          if (message.type() === 'error' && !message.text().includes('favicon')) {
            consoleErrors.push(message.text());
          }
        });
        page.on('pageerror', (error) => pageErrors.push(error.message));

        const response = await page.goto(`${BASE_URL}${route.path}`, {
          waitUntil: 'networkidle',
          timeout: 60000,
        });
        process.stdout.write(`QA ${route.id}/${viewport.id} HTTP ${response ? response.status() : 'none'}\n`);
        await page.waitForSelector('main h1', { timeout: 60000 });
        const metrics = await page.evaluate(() => {
          const body = document.body;
          const html = document.documentElement;
          const details = [...document.querySelectorAll('details')];
          const tocLinks = [...document.querySelectorAll('.page-toc a[href^="#"]')];
          const visuals = [...document.querySelectorAll('.data-visual, .concept-map, .evidence-ladder, .period-strip, svg[role="img"]')];
          return {
            title: document.title,
            h1Count: document.querySelectorAll('main h1').length,
            h1Text: document.querySelector('main h1')?.textContent.trim() || '',
            scrollWidth: Math.max(body.scrollWidth, html.scrollWidth),
            innerWidth: window.innerWidth,
            detailsCount: details.length,
            detailsCollapsed: details.every((item) => !item.open),
            tocCount: tocLinks.length,
            tocTargetsExist: tocLinks.every((link) => document.getElementById(decodeURIComponent(link.hash.slice(1)))),
            visualCount: visuals.length,
            visualDescriptions: [...document.querySelectorAll('svg[role="img"]')].every((svg) => svg.querySelector('title') && svg.querySelector('desc')),
            navCount: document.querySelectorAll('.chapter-nav a').length,
            specialistCount: document.querySelectorAll('.specialist-card').length,
            externalReportCount: document.querySelectorAll('.external-report-link a').length,
          };
        });

        if (viewport.id !== 'desktop' && route.id === 'master') {
          const button = page.locator('.menu-button');
          await button.click();
          const expanded = await button.getAttribute('aria-expanded');
          const visible = await page.locator('#mobile-nav').isVisible();
          mobileMenuPass = mobileMenuPass || (expanded === 'true' && visible);
          await button.click();
        }

        const screenshot = path.join(SCREENSHOTS, `${route.id}-${viewport.id}.png`);
        if (route.id === 'master' || viewport.id === 'desktop') {
          await page.screenshot({ path: screenshot, fullPage: route.id !== 'master' });
        }

        results.push({
          route: route.id,
          path: route.path,
          viewport,
          httpStatus: response ? response.status() : null,
          consoleErrors,
          pageErrors,
          ...metrics,
          overflow: metrics.scrollWidth > metrics.innerWidth,
          screenshot: (route.id === 'master' || viewport.id === 'desktop')
            ? path.relative(ROOT, screenshot)
            : null,
        });
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }

  const failures = [];
  for (const result of results) {
    if (result.httpStatus !== 200) failures.push(`${result.route}/${result.viewport.id}: HTTP ${result.httpStatus}`);
    if (result.consoleErrors.length) failures.push(`${result.route}/${result.viewport.id}: console errors`);
    if (result.pageErrors.length) failures.push(`${result.route}/${result.viewport.id}: page errors`);
    if (result.h1Count !== 1) failures.push(`${result.route}/${result.viewport.id}: h1Count=${result.h1Count}`);
    if (result.overflow) failures.push(`${result.route}/${result.viewport.id}: horizontal overflow`);
    if (!result.detailsCollapsed) failures.push(`${result.route}/${result.viewport.id}: technical details open`);
    if (result.tocCount < 1) failures.push(`${result.route}/${result.viewport.id}: no TOC links`);
    if (!result.tocTargetsExist) failures.push(`${result.route}/${result.viewport.id}: broken TOC target`);
    if (result.visualCount < 1) failures.push(`${result.route}/${result.viewport.id}: no visual`);
    if (!result.visualDescriptions) failures.push(`${result.route}/${result.viewport.id}: missing SVG title/desc`);
    if (result.navCount !== 6) failures.push(`${result.route}/${result.viewport.id}: navCount=${result.navCount}`);
    if (result.route === 'master' && result.specialistCount !== 5) failures.push(`${result.route}/${result.viewport.id}: specialistCount=${result.specialistCount}`);
    if (result.route !== 'master' && result.externalReportCount !== 1) failures.push(`${result.route}/${result.viewport.id}: externalReportCount=${result.externalReportCount}`);
  }
  if (!mobileMenuPass) failures.push('mobile menu did not open');

  const screenshotHashes = {};
  for (const file of fs.readdirSync(SCREENSHOTS).sort()) {
    const filePath = path.join(SCREENSHOTS, file);
    if (fs.statSync(filePath).isFile()) screenshotHashes[file] = sha256(filePath);
  }

  const htmlHash = sha256(path.join(SITE, 'index.html'));
  const output = {
    status: failures.length ? 'FAIL_MASTER_RESEARCH_SITE_BROWSER_QA' : 'PASS_MASTER_RESEARCH_SITE_BROWSER_QA',
    baseUrl: BASE_URL,
    htmlSha256: htmlHash,
    routeCount: routes.length,
    viewportCount: viewports.length,
    checkCount: results.length,
    mobileMenuPass,
    failures,
    screenshotHashes,
    results,
  };
  const outputName = QA_LABEL ? `browser_qa.${QA_LABEL}.json` : 'browser_qa.json';
  fs.writeFileSync(path.join(__dirname, outputName), `${JSON.stringify(output, null, 2)}\n`);
  process.stdout.write(`${output.status}\n`);
  if (failures.length) {
    process.stderr.write(`${failures.join('\n')}\n`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(2);
});
