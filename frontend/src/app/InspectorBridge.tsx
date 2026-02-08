// @ts-nocheck
"use client";
// 🌉 Inspector Bridge Script - Client Component for Next.js App Router
// Version: 2.3
// ارتباط با Inspector از طریق WebSocket (حل مشکل cross-origin)
import { useEffect } from "react";

declare global {
  interface Window {
    __inspectorBridgeLoaded?: boolean;
  }
}

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

    // Debounce
    const DEBOUNCE_MS = 100;
    let lastEventTime = 0;
    let messagesSent = 0;
    const shouldSend = () => {
      const now = Date.now();
      if (now - lastEventTime < DEBOUNCE_MS) return false;
      lastEventTime = now;
      return true;
    };

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
        pageUrl: window.location.href, timestamp: Date.now(),
        level: data.level || null, source: "imported-project"
      };
      if (ws && wsReady) ws.send(JSON.stringify(message));
      else if (ws) messageQueue.push(message);
      if (isInIframe) { try { window.parent.postMessage(message, "*"); } catch(e) {} }
    };

    const getElementInfo = (el) => {
      if (!el) return "";
      const text = (el.innerText || el.value || "").trim().slice(0, 50);
      const tag = el.tagName?.toLowerCase() || "";
      const id = el.id ? "#" + el.id : "";
      const cls = el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : "";
      const tagLabels = {
        "button": "دکمه", "a": "لینک", "input": "فیلد ورودی", "textarea": "فیلد متن",
        "select": "منوی انتخاب", "img": "تصویر", "form": "فرم", "div": "بخش", "span": "متن",
        "p": "پاراگراف", "h1": "عنوان اصلی", "h2": "عنوان", "h3": "عنوان", "nav": "منوی ناوبری",
        "header": "سربرگ", "footer": "پاورقی", "li": "آیتم لیست", "table": "جدول", "video": "ویدیو"
      };
      const typeLabel = tagLabels[tag] || tag;
      if (text) return `${typeLabel} "${text}"`;
      return typeLabel + (id || cls || "");
    };

    const getPositionPercent = (e) => ({
      xPercent: (e.clientX / window.innerWidth) * 100,
      yPercent: (e.clientY / window.innerHeight) * 100
    });

    // window capture phase (بالاترین اولویت)
    const handleClick = (e) => {
      if (!shouldSend()) return;
      sendToInspector("click", { elementInfo: getElementInfo(e.target), position: getPositionPercent(e) });
    };
    const handleInput = (e) => {
      if (!shouldSend()) return;
      if (e.target?.tagName === "INPUT" || e.target?.tagName === "TEXTAREA") {
        sendToInspector("input", { elementInfo: getElementInfo(e.target) });
      }
    };
    const handleFocus = (e) => {
      if (!shouldSend()) return;
      if (e.target && e.target !== document && e.target !== document.body) {
        sendToInspector("focus", { elementInfo: getElementInfo(e.target) });
      }
    };
    let scrollTimeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => { sendToInspector("scroll", { elementInfo: "صفحه" }); }, 200);
    };

    window.addEventListener("click", handleClick, true);
    window.addEventListener("input", handleInput, true);
    window.addEventListener("scroll", handleScroll, true);
    window.addEventListener("focus", handleFocus, true);

    // 🆕 فالبک pointerdown
    const handlePointerDown = (e) => {
      setTimeout(() => {
        if (Date.now() - lastEventTime > 180) {
          sendToInspector("click", { elementInfo: getElementInfo(e.target) + " (pointerdown)", position: getPositionPercent(e) });
        }
      }, 200);
    };
    window.addEventListener("pointerdown", handlePointerDown, true);

    // 🔵 رهگیری تمام متدهای کنسول
    let consoleLogCount = 0;
    const MAX_CONSOLE_LOGS = 200;

    const interceptConsole = (level, origFn) => (...args) => {
      origFn.apply(console, args);
      if (consoleLogCount >= MAX_CONSOLE_LOGS) return;
      consoleLogCount++;
      const msg = args.map(a => typeof a === "object" ? JSON.stringify(a).slice(0, 200) : String(a).slice(0, 200)).join(" ").slice(0, 500);
      if (msg.includes("Inspector Bridge") || msg.includes("🌉")) return;
      sendToInspector(level === "error" ? "console-error" : "console-log", { elementInfo: msg, level });
    };

    const origLog = console.log, origWarn = console.warn, origError = console.error, origInfo = console.info, origDebug = console.debug;
    console.log = interceptConsole("log", origLog);
    console.warn = interceptConsole("warn", origWarn);
    console.error = interceptConsole("error", origError);
    console.info = interceptConsole("info", origInfo);
    console.debug = interceptConsole("debug", origDebug);

    // 🔴 خطاهای JS
    let errorCount = 0;
    const MAX_ERRORS = 50;

    const handleError = (event) => {
      if (errorCount >= MAX_ERRORS) return;
      errorCount++;
      let errorInfo = String(event.message || "Unknown error").slice(0, 150);
      if (event.filename) errorInfo += ` (at ${event.filename.split("/").pop()}:${event.lineno})`;
      sendToInspector("error", { elementInfo: errorInfo, level: "error" });
    };

    const handleRejection = (event) => {
      if (errorCount >= MAX_ERRORS) return;
      errorCount++;
      const reason = (event.reason?.message || event.reason?.toString()) || "Promise rejected";
      sendToInspector("error", { elementInfo: String(reason).slice(0, 150), level: "error" });
    };

    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleRejection);

    // 🔍 MutationObserver + اسکن دوره‌ای - تشخیص لایه‌های خطا
    const __attachedOverlays = new WeakSet();
    const isOverlay = (node) => {
      try {
        const s = window.getComputedStyle(node);
        const z = parseInt(s.zIndex) || 0;
        return (s.position === "fixed" || s.position === "absolute") && (z > 1000 || (node.offsetWidth > window.innerWidth*0.8 && node.offsetHeight > window.innerHeight*0.5));
      } catch(e) { return false; }
    };
    const attachOverlay = (node) => {
      if (__attachedOverlays.has(node)) return;
      __attachedOverlays.add(node);
      sendToInspector("error-overlay", { elementInfo: "لایه خطا: " + (node.textContent||"").slice(0,200), level: "error" });
      node.addEventListener("click", (e) => {
        sendToInspector("click", { elementInfo: getElementInfo(e.target) + " (overlay)", position: getPositionPercent(e) });
      }, true);
      node.addEventListener("pointerdown", (e) => {
        sendToInspector("click", { elementInfo: getElementInfo(e.target) + " (overlay pointerdown)", position: getPositionPercent(e) });
      }, true);
      if (node.shadowRoot) {
        node.shadowRoot.addEventListener("click", (e) => {
          sendToInspector("click", { elementInfo: getElementInfo(e.target) + " (shadow)", position: { xPercent: 50, yPercent: 50 } });
        }, true);
      }
    };

    let overlayObs;
    try {
      overlayObs = new MutationObserver((mutations) => {
        mutations.forEach(m => m.addedNodes.forEach(node => {
          if (node.nodeType !== 1) return;
          if (isOverlay(node)) attachOverlay(node);
        }));
      });
      if (document.body) overlayObs.observe(document.body, { childList: true, subtree: true });
      else document.addEventListener("DOMContentLoaded", () => overlayObs.observe(document.body, { childList: true, subtree: true }));
    } catch(e) {}

    // 🔁 اسکن دوره‌ای
    const overlayScan = setInterval(() => {
      try {
        document.querySelectorAll('[style*="position: fixed"], [style*="position:fixed"], nextjs-portal, [id*="overlay"], [id*="error"], [class*="overlay"]').forEach(el => {
          if (isOverlay(el)) attachOverlay(el);
          if (el.shadowRoot && !__attachedOverlays.has(el)) attachOverlay(el);
        });
      } catch(e) {}
    }, 2000);

    connectWS();
    const heartbeat = setInterval(() => { if (ws && wsReady) try { ws.send(JSON.stringify({ type: "ping" })); } catch(e) {} }, 25000);

    // فالبک postMessage
    if (isInIframe) {
      try { window.parent.postMessage({ type: "inspector-bridge-ready", pageUrl: window.location.href }, "*"); } catch(e) {}
    }

    return () => {
      window.removeEventListener("click", handleClick, true);
      window.removeEventListener("pointerdown", handlePointerDown, true);
      window.removeEventListener("input", handleInput, true);
      window.removeEventListener("scroll", handleScroll, true);
      window.removeEventListener("focus", handleFocus, true);
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleRejection);
      console.log = origLog; console.warn = origWarn; console.error = origError; console.info = origInfo; console.debug = origDebug;
      if (overlayObs) overlayObs.disconnect();
      clearInterval(heartbeat);
      clearInterval(overlayScan);
      if (ws) { try { ws.close(); } catch(e) {} }
    };
  }, []);

  return null;
}
// 🌉 End of Inspector Bridge Script
