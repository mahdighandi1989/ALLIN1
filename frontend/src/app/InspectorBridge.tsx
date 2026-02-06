"use client";
// 🌉 Inspector Bridge Script - Client Component for Next.js App Router
// ارتباط با Inspector از طریق WebSocket (حل مشکل cross-origin)
import { useEffect } from "react";

export default function InspectorBridge() {
  useEffect(() => {
    if (typeof window === "undefined" || window.__inspectorBridgeLoaded) return;
    window.__inspectorBridgeLoaded = true;

    const isInIframe = window !== window.parent;
    const WS_URL = "wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1";
    let ws = null;
    let wsReady = false;
    let messageQueue = [];

    console.log("🌉 Inspector Bridge: Active (WebSocket mode)");

    // 🌐 اتصال WebSocket
    const connectWS = () => {
      if (!WS_URL || WS_URL === "wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1") return;
      try {
        ws = new WebSocket(WS_URL);
        ws.onopen = () => { ws.send(JSON.stringify({ type: "register", role: "bridge" })); };
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "registered") {
              wsReady = true;
              console.log("🌉 Inspector Bridge: WebSocket connected");
              messageQueue.forEach(m => ws.send(JSON.stringify(m)));
              messageQueue = [];
              ws.send(JSON.stringify({ type: "inspector-bridge-ready", pageUrl: window.location.href, isInIframe, timestamp: Date.now() }));
            } else if (msg.type === "command") {
              handleCommand(msg);
            }
          } catch (e) {}
        };
        ws.onclose = () => { wsReady = false; setTimeout(connectWS, 3000); };
        ws.onerror = () => {};
      } catch (e) {}
    };

    const handleCommand = (msg) => {
      if (msg.command === "click") {
        const el = document.querySelector(msg.selector);
        if (el) el.click();
      } else if (msg.command === "navigate") {
        window.location.href = msg.url;
      } else if (msg.command === "get-elements") {
        const elements = [];
        document.querySelectorAll("a, button, input, textarea, select, [role=button]").forEach((el, i) => {
          elements.push({ index: i, tag: el.tagName.toLowerCase(), text: (el.innerText || el.value || "").trim().slice(0, 50), id: el.id, href: el.href || "" });
        });
        sendToInspector("elements-list", { elements });
      }
    };

    const sendToInspector = (action, data) => {
      const message = {
        type: "inspector-bridge-event", action,
        elementInfo: data.elementInfo || "", position: data.position || { xPercent: 50, yPercent: 50 },
        pageUrl: window.location.href, timestamp: Date.now()
      };
      if (ws && wsReady) ws.send(JSON.stringify(message));
      else if (ws) messageQueue.push(message);
      if (isInIframe) { try { window.parent.postMessage(message, "*"); } catch(e) {} }
    };

    const getElementInfo = (el) => {
      if (!el) return "";
      const text = (el.innerText || el.value || "").trim().slice(0, 30);
      const tag = el.tagName?.toLowerCase() || "";
      return text ? `${tag} "${text}"` : tag;
    };

    const handleClick = (e) => { sendToInspector("click", { elementInfo: getElementInfo(e.target) }); };
    const handleInput = (e) => {
      if (e.target?.tagName === "INPUT" || e.target?.tagName === "TEXTAREA") {
        sendToInspector("input", { elementInfo: getElementInfo(e.target) });
      }
    };
    let scrollTimeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => { sendToInspector("scroll", { elementInfo: "page" }); }, 200);
    };

    document.addEventListener("click", handleClick, true);
    document.addEventListener("input", handleInput, true);
    document.addEventListener("scroll", handleScroll, true);

    connectWS();
    const heartbeat = setInterval(() => { if (ws && wsReady) try { ws.send(JSON.stringify({ type: "ping" })); } catch(e) {} }, 25000);

    // فالبک postMessage
    if (isInIframe) {
      try { window.parent.postMessage({ type: "inspector-bridge-ready", pageUrl: window.location.href }, "*"); } catch(e) {}
    }

    return () => {
      document.removeEventListener("click", handleClick, true);
      document.removeEventListener("input", handleInput, true);
      document.removeEventListener("scroll", handleScroll, true);
      clearInterval(heartbeat);
      if (ws) { try { ws.close(); } catch(e) {} }
    };
  }, []);

  return null;
}
// 🌉 End of Inspector Bridge Script
