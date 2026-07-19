// Minimal path router — no library, no '#' in URLs.
// Old '#/console' links (QR codes, bookmarks) are transparently upgraded.

/** SPA navigation without a full page reload. */
export function navigate(path: string): void {
  if (window.location.pathname !== path) {
    window.history.pushState({}, "", path);
  }
  window.dispatchEvent(new PopStateEvent("popstate"));
}

/** Click handler for internal <a> links: SPA-navigate, keep middle-click/new-tab. */
export function linkClick(e: { preventDefault: () => void; metaKey?: boolean; ctrlKey?: boolean }, path: string): void {
  if (e.metaKey || e.ctrlKey) return; // let the browser open a new tab
  e.preventDefault();
  navigate(path);
}

/** One-time upgrade of legacy hash URLs ('/#/console' → '/console'). */
export function upgradeLegacyHash(): void {
  const h = window.location.hash;
  if (h.startsWith("#/")) {
    window.history.replaceState({}, "", h.slice(1) + window.location.search);
  }
}
