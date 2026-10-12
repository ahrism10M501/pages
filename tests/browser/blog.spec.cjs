const { test, expect } = require('@playwright/test');

test('archive, search, original URLs, math, notebook output and notes', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('./blog/');
  await expect(page.locator('[data-post]')).toHaveCount(7);
  await expect(page.getByRole('link', { name: /pandas/i })).toHaveCount(0);
  const input = page.getByRole('searchbox', { name: '글 검색' });
  await input.fill('XOR');
  await expect(page.locator('[data-post]:visible')).toHaveCount(1);
  await page.locator('[data-post]:visible a').click();
  await expect(page).toHaveURL(/posts\/nn2\/$/);
  await expect(page.locator('#post-content')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('#post-content h2').first()).toBeVisible();
  await page.goto('./posts/nn1/');
  await expect(page.locator('#post-content')).toHaveAttribute('aria-busy', 'false');
  expect(await page.locator('.katex').count()).toBeGreaterThan(0);
  await page.goto('./posts/Gaussian_%20Z-score_Normalization/');
  await expect(page.locator('h1')).toContainText('Z-score');
  await expect(page.locator('#post-content')).toHaveAttribute('aria-busy', 'false');
  expect(await page.locator('.nb-code').count()).toBeGreaterThan(0);
  const download = await page.getByRole('link', { name: '노트북 원본 다운로드' }).getAttribute('href');
  expect((await page.request.get(new URL(download, page.url()).href)).ok()).toBeTruthy();
  await page.goto('./posts/matplotlib1/');
  await expect(page.locator('#post-content')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.cell-output-image')).toHaveCount(21);
  await page.goto('./twinkle/#2026-04-28-leader');
  await expect(page.locator('.note')).toHaveCount(4);
  await expect(page.locator('[id="2026-04-28-leader"] .markdown-source')).toHaveCount(0);
  await expect(page.locator('[id="2026-04-28-leader"]')).toContainText('리더가 되려면');
  expect(errors).toEqual([]);
});

test('search recovers from no results and whitespace', async ({ page }) => {
  await page.goto('./blog/');
  const input = page.getByRole('searchbox', { name: '글 검색' });
  await input.fill('no-such-post-123');
  await expect(page.locator('[data-post]:visible')).toHaveCount(0);
  await expect(page.locator('#search-empty')).toBeVisible();
  await input.fill('  ');
  await expect(page.locator('[data-post]:visible')).toHaveCount(7);
  await expect(page.locator('#search-empty')).toBeHidden();
});

test('archive and navigation work without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:8765/pages/blog/');
  await expect(page.locator('[data-post]')).toHaveCount(7);
  await expect(page.locator('.search')).toBeHidden();
  await page.getByRole('navigation', { name: '주 메뉴' }).getByRole('link', { name: '소개' }).click();
  await expect(page.getByRole('heading', { name: '프로젝트와 활동' })).toBeVisible();
  await context.close();
});

for (const width of [375, 1280]) {
  test('readable layout at ' + width + 'px', async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    for (const path of ['./', './about/', './blog/', './twinkle/', './graph/', './posts/nn1/', './posts/matplotlib1/']) {
      await page.goto(path);
      if (path.includes('posts/')) await expect(page.locator('#post-content')).toHaveAttribute('aria-busy', 'false');
      await expect(page.locator('main')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
      if (path === './') {
        await expect(page.locator('meta[property="og:title"]')).toHaveAttribute('content', /Ahrism/);
        await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', 'https://ahrism10m501.github.io/pages/');
      }
    }
  });
}
