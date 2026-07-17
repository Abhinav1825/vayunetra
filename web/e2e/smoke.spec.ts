import { expect, test } from "@playwright/test";

// The core judge journey: land → open console → see the auto-opened cell story
// → switch to the enforcement worklist → open a dossier. Deterministic parts
// only (no fixed-coordinate canvas clicks).

test("landing renders and links into the console", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /operations layer for urban air quality/i })).toBeVisible();
  await page.getByRole("link", { name: /open the console/i }).first().click();
  await expect(page).toHaveURL(/#\/console/);
});

test("console loads the map shell and the tab bar", async ({ page }) => {
  await page.goto("/#/console");
  await expect(page.getByRole("button", { name: "Action", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "What-if", exact: true })).toBeVisible();
  // Map Layers panel is part of the left rail and always renders.
  await expect(page.getByText("Map Layers")).toBeVisible();
});

test("a cell story auto-opens with an explanation (never an empty box)", async ({ page }) => {
  await page.goto("/#/console");
  // H8: the best cell opens on load; C1: it always carries a "Why" section.
  await expect(page.getByText("Cell story", { exact: false })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/Why —/)).toBeVisible();
});

test("enforcement worklist renders and a dossier opens", async ({ page }) => {
  await page.goto("/#/console");
  await page.getByRole("button", { name: "Action", exact: true }).click();
  await expect(page.getByText("Enforcement Worklist")).toBeVisible();
  const dossier = page.getByRole("button", { name: /evidence dossier/i }).first();
  await expect(dossier).toBeVisible({ timeout: 15_000 });
  await dossier.click();
  await expect(page.getByText(/Regulatory citations/i)).toBeVisible();
});

test("what-if tab shows the simulator", async ({ page }) => {
  await page.goto("/#/console");
  await page.getByRole("button", { name: "What-if", exact: true }).click();
  await expect(page.getByText("What-if Simulator")).toBeVisible();
  await expect(page.getByRole("button", { name: /run simulation/i })).toBeVisible();
});
