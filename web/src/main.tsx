import React, { lazy, Suspense, useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import Landing from "./Landing";
import ErrorBoundary from "./ErrorBoundary";
import "./index.css";

// The console pulls in MapLibre + Deck.gl + Recharts (~1.5 MB). Landing needs
// none of it, so the console is code-split out and only fetched at #/console.
const App = lazy(() => import("./App"));

function ConsoleFallback() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-slate-100 text-sm text-slate-500">
      <span className="animate-pulse">Loading console…</span>
    </div>
  );
}

/** Hash router: "#/console" → ops console, anything else → landing page. */
function Root() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const on = () => setHash(window.location.hash);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  if (hash.startsWith("#/console")) {
    return (
      <Suspense fallback={<ConsoleFallback />}>
        <App />
      </Suspense>
    );
  }
  return <Landing />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <Root />
    </ErrorBoundary>
  </React.StrictMode>,
);
