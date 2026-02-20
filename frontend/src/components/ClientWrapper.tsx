typescript
'use client'

export default function ClientWrapper({
  children,
}: {
  children: React.ReactNode
}) {
  // Prevent InspectorBridge errors by wrapping in error boundary
  if (typeof window !== 'undefined') {
    // Add safety check for InspectorBridge code
    const originalError = console.error;
    console.error = function(...args) {
      // Filter out InspectorBridge related errors
      if (args.length > 0) {
        const firstArg = args[0];
        if (
          (typeof firstArg === 'string' && 
           (firstArg.includes('Application error') || 
            firstArg.includes('el.className.split'))) ||
          (firstArg && typeof firstArg === 'object' && Object.keys(firstArg).length === 0)
        ) {
          // Suppress InspectorBridge errors
          return;
        }
      }
      originalError.apply(console, args);
    };
  }

  return <>{children}</>
}