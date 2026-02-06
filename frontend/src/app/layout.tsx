
// 🌉 Inspector Bridge Script - Auto-injected
// این کد را در ابتدای فایل اصلی پروژه اضافه کنید
if (typeof window !== 'undefined' && !window.__inspectorBridgeLoaded) {
  window.__inspectorBridgeLoaded = true;

  const isInIframe = window !== window.parent;
  if (isInIframe) {
    console.log('🌉 Inspector Bridge: Active in iframe');

    const sendToInspector = (action, data) => {
      try {
        window.parent.postMessage({
          type: 'inspector-bridge-event',
          action,
          elementInfo: data.elementInfo || '',
          position: data.position || { xPercent: 50, yPercent: 50 },
          pageUrl: window.location.href,
          timestamp: Date.now()
        }, '*');
      } catch (e) { console.warn('Bridge send failed:', e); }
    };

    const getElementInfo = (el) => {
      if (!el) return '';
      const text = (el.innerText || el.value || '').trim().slice(0, 30);
      const tag = el.tagName?.toLowerCase() || '';
      return text ? `${tag} "${text}"` : tag;
    };

    document.addEventListener('click', (e) => {
      sendToInspector('click', { elementInfo: getElementInfo(e.target) });
    }, true);

    document.addEventListener('input', (e) => {
      if (e.target?.tagName === 'INPUT' || e.target?.tagName === 'TEXTAREA') {
        sendToInspector('input', { elementInfo: getElementInfo(e.target) });
      }
    }, true);

    let scrollTimeout;
    document.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        sendToInspector('scroll', { elementInfo: 'صفحه' });
      }, 200);
    }, true);

    window.parent.postMessage({ type: 'inspector-bridge-ready', pageUrl: window.location.href }, '*');
  }
}
// 🌉 End of Inspector Bridge Script

import type { Metadata } from 'next'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/lib/auth'
import './globals.css'

export const metadata: Metadata = {
  title: 'Banking Operations',
  description: 'Banking Operations Management System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
          <Toaster position="top-right" />
        </AuthProvider>
      </body>
    </html>
  )
}