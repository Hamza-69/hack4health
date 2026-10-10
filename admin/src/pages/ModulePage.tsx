import { READY, TOKEN, TOKEN_REQUEST } from "@h4h/module-ui/protocol";
import { useEffect, useRef } from "react";
import { useOutletContext, useParams } from "react-router";
import { api } from "../api";
import type { LayoutContext } from "../Layout";

/** Embeds a module's UI and hands it admin tokens over postMessage when it asks. */
export default function ModulePage() {
  const { name } = useParams();
  const { modules } = useOutletContext<LayoutContext>();
  const module = modules.find((m) => m.name === name);
  const frame = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (!module) return;
    const origin = new URL(module.ui_url).origin;

    async function sendToken() {
      const { token } = await api<{ token: string }>(`/admin/modules/${module!.name}/token`, { method: "POST" });
      frame.current?.contentWindow?.postMessage({ type: TOKEN, token }, origin);
    }

    function onMessage(event: MessageEvent) {
      if (event.source !== frame.current?.contentWindow || event.origin !== origin) return;
      if (event.data?.type === READY || event.data?.type === TOKEN_REQUEST) sendToken().catch(console.error);
    }

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [module]);

  if (!module) return <p className="p-6 text-sm text-gray-500">{modules.length ? `No module "${name}".` : "Loading…"}</p>;
  return <iframe key={module.name} ref={frame} src={module.ui_url} title={module.title} className="h-full w-full border-0" />;
}
