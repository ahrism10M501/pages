const { test, expect } = require('@playwright/test');

test('graph selection, connection reasons, deep links, keyboard and history', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('./graph/?node=post:nn2&view=graph');
  await expect(page.locator('.graph-node')).toHaveCount(11);
  await expect(page.locator('#detail-title')).toContainText('인공신경망2');
  await expect(page.locator('#graph-connections')).toContainText('같은 태그:');
  await expect(page.locator('#detail-link')).toHaveAttribute('href', '../posts/nn2/');
  const firstConnection = page.locator('#graph-connections button').first();
  const title = await firstConnection.textContent();
  await firstConnection.click();
  await expect(page.locator('#detail-title')).toHaveText(title);
  await expect(page.locator('#detail-title')).toBeFocused();
  await page.goBack();
  await expect(page.locator('#detail-title')).toContainText('인공신경망2');
  const isolated = page.getByRole('button', { name: '글: 초간단 ALU 만들기', exact: true });
  await isolated.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#detail-title')).toHaveText('초간단 ALU 만들기');
  await expect(page.locator('#graph-isolated')).toBeVisible();
  await expect(page).toHaveURL(/node=post%3Asimple_ALU/);
  await page.reload();
  await expect(page.locator('#detail-title')).toHaveText('초간단 ALU 만들기');
  await page.locator('#detail-link').click();
  await expect(page).toHaveURL(/posts\/simple_ALU\/$/);
  expect(errors).toEqual([]);
});

test('Twinkle nodes open the original anchor and unknown URL state recovers', async ({ page }) => {
  await page.goto('./graph/?node=twinkle:2026-04-28-leader&view=graph');
  await expect(page.locator('#detail-kind')).toHaveText('Twinkle');
  await expect(page.locator('#detail-title')).toHaveText('리더가 되려면');
  await expect(page.locator('#detail-link')).toHaveAttribute('href', '../twinkle/#2026-04-28-leader');
  await page.locator('#detail-link').click();
  await expect(page.locator('[id="2026-04-28-leader"]')).toBeVisible();
  await page.goto('./graph/?node=post:missing&view=bogus');
  await expect(page.locator('#graph-explorer')).toBeVisible();
  await expect(page.locator('#detail-title')).not.toBeEmpty();
});

test('mobile starts with a usable list and can switch to graph', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('./graph/');
  await expect(page.locator('#graph-records')).toBeVisible();
  await expect(page.locator('.graph-map')).toBeHidden();
  await page.getByRole('button', { name: '초간단 ALU 만들기의 연결 보기', exact: true }).click();
  await expect(page.locator('#detail-title')).toHaveText('초간단 ALU 만들기');
  await expect(page.locator('#detail-title')).toBeFocused();
  await page.getByRole('button', { name: '그래프 보기', exact: true }).click();
  await expect(page.locator('.graph-map')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test('without JavaScript every graph record remains a normal readable link', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:8765/pages/graph/');
  await expect(page.locator('#graph-records li')).toHaveCount(11);
  await expect(page.locator('#graph-tools')).toBeHidden();
  await page.locator('#graph-records a').first().click();
  await expect(page).toHaveURL(/posts\/matplotlib1\/$/);
  await context.close();
});
