import { useEffect, useRef, useState } from "react";
import AccessibleRoutingPanel from "./AccessibleRoutingPanel";
import App from "./App";
import { fetchJson, systemSnapshotToken, type SystemResponse } from "./api";
import DerivedInspector from "./DerivedInspector";
import PlatformInspector from "./PlatformInspector";

const SNAPSHOT_POLL_INTERVAL_MS = 15_000;

export default function AutoRefreshingApp() {
  const activeToken = useRef<string | null>(null);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const checkForSnapshotChange = async () => {
      try {
        const current = await fetchJson<SystemResponse>("/api/v1/system");
        if (cancelled) return;
        const nextToken = systemSnapshotToken(current);
        if (activeToken.current === null) {
          activeToken.current = nextToken;
          return;
        }
        if (activeToken.current !== nextToken) {
          activeToken.current = nextToken;
          setRevision((value) => value + 1);
        }
      } catch {
        // App-level error handling remains authoritative. A transient watcher failure must not
        // destroy an otherwise usable dashboard or replace the last known data with placeholders.
      }
    };

    void checkForSnapshotChange();
    const interval = window.setInterval(() => {
      void checkForSnapshotChange();
    }, SNAPSHOT_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <>
      <App key={`dashboard-${revision}`} />
      <AccessibleRoutingPanel key={`accessible-routing-${revision}`} />
      <DerivedInspector key={`derived-${revision}`} />
      <PlatformInspector key={`platform-${revision}`} />
    </>
  );
}
