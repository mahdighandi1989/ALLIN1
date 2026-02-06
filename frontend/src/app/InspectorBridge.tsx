"use client";
// 🌉 Inspector Bridge Script - Client Component for Next.js App Router
// ارتباط با Inspector از طریق WebSocket (حل مشکل cross-origin)
import { useEffect } from "react";

// Extend Window interface for inspector bridge
declare global {
  interface Window {
    __inspectorBridgeLoaded?: boolean;
  }
}

interface InspectorMessage {
  type: string;
  command?: string;
  selector?: string;
  url?: string;
  role?: string;
  action?: string;
  elementInfo?: string;
  position?: { xPercent: number; yPercent: number };
  pageUrl?: string;
  timestamp?: number;
  elements?: ElementInfo[];
}

interface ElementInfo {
  index: number;
  tag: string;
  text: string;
  id: string;
  href: string;
}

export default function InspectorBridge() {
  useEffect(() => {
    if (typeof window === "undefined" || window.__inspectorBridgeLoaded) return;
    window.__inspectorBridgeLoaded = true;

    const isInIframe = window !== window.parent;
    const WS_URL = "wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1";
    let ws: WebSocket | null = null;
    let wsReady = false;
    let messageQueue: InspectorMessage[] = [];

    console.log("🌉 Inspector Bridge: Active (WebSocket mode)");

    // 🌐 اتصال WebSocket
    const connectWS = () => {
      if (!WS_URL || WS_URL === "wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1") return;
      try {
        ws = new WebSocket(WS_URL);
        ws.onopen = () => { if (ws) ws.send(JSON.stringify({ type: "register", role: "bridge" })); };
        ws.onmessage = (event: MessageEvent) => {
          try {
            const msg: InspectorMessage = JSON.parse(event.data);
            if (msg.type === "registered") {
              wsReady = true;
              console.log("🌉 Inspector Bridge: WebSocket connected");
              messageQueue.forEach(m => ws?.send(JSON.stringify(m)));
              messageQueue = [];
              ws?.send(JSON.stringify({ type: "inspector-bridge-ready", pageUrl: window.location.href, isInIframe, timestamp: Date.now() }));
            } else if (msg.type === "command") {
              handleCommand(msg);
            }
          } catch (e) {
            // Silently handle parse errors
          }
        };
        ws.onclose = () => { wsReady = false; setTimeout(connectWS, 3000); };
        ws.onerror = () => {
          // Silently handle connection errors
        };
      } catch (e) {
        // Silently handle initialization errors
      }
    };

    const handleCommand = (msg: InspectorMessage) => {
      if (msg.command === "click" && msg.selector) {
        const el = document.querySelector(msg.selector) as HTMLElement | null;
        if (el) el.click();
      } else if (msg.command === "navigate" && msg.url) {
        window.location.href = msg.url;
      } else if (msg.command === "get-elements") {
        const elements: ElementInfo[] = [];
        document.querySelectorAll("a, button, input, textarea, select, [role=button]").forEach((el, i) => {
          const htmlEl = el as HTMLElement & { value?: string; href?: string };
          elements.push({
            index: i,
            tag: el.tagName.toLowerCase(),
            text: (htmlEl.innerText || htmlEl.value || "").trim().slice(0, 50),
            id: el.id,
            href: htmlEl.href || ""
          });
        });
        sendToInspector("elements-list", { elements });
      }
    };

    const sendToInspector = (action: string, data: { elementInfo?: string; position?: { xPercent: number; yPercent: number }; elements?: ElementInfo[] }) => {
      const message: InspectorMessage = {
        type: "inspector-bridge-event", action,
        elementInfo: data.elementInfo || "", position: data.position || { xPercent: 50, yPercent: 50 },
        pageUrl: window.location.href, timestamp: Date.now()
      };
      if (ws && wsReady) ws.send(JSON.stringify(message));
      else if (ws) messageQueue.push(message);
      if (isInIframe) { try { window.parent.postMessage(message, "*"); } catch(e) { /* ignore */ } }
    };

    const getElementInfo = (el: HTMLElement | null): string => {
      if (!el) return "";
      const htmlEl = el as HTMLElement & { value?: string };
      const text = (el.innerText || htmlEl.value || "").trim().slice(0, 30);
      const tag = el.tagName?.toLowerCase() || "";
      return text ? `${tag} "${text}"` : tag;
    };

    const handleClick = (e: Event) => { sendToInspector("click", { elementInfo: getElementInfo(e.target as HTMLElement) }); };
    const handleInput = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA") {
        sendToInspector("input", { elementInfo: getElementInfo(target) });
      }
    };
    let scrollTimeout: ReturnType<typeof setTimeout> | null = null;
    const handleScroll = () => {
      if (scrollTimeout) clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => { sendToInspector("scroll", { elementInfo: "page" }); }, 200);
    };

    document.addEventListener("click", handleClick, true);
    document.addEventListener("input", handleInput, true);
    document.addEventListener("scroll", handleScroll, true);

    connectWS();
    const heartbeat = setInterval(() => { if (ws && wsReady) try { ws.send(JSON.stringify({ type: "ping" })); } catch(e) { /* ignore */ } }, 25000);

    // فالبک postMessage
    if (isInIframe) {
      try { window.parent.postMessage({ type: "inspector-bridge-ready", pageUrl: window.location.href }, "*"); } catch(e) { /* ignore */ }
    }

    return () => {
      document.removeEventListener("click", handleClick, true);
      document.removeEventListener("input", handleInput, true);
      document.removeEventListener("scroll", handleScroll, true);
      clearInterval(heartbeat);
      if (ws) { try { ws.close(); } catch(e) { /* ignore */ } }
    };
  }, []);

  return null;
}
// 🌉 End of Inspector Bridge Script
