'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f3f4f6',
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            padding: '24px',
            maxWidth: '500px',
            width: '100%'
          }}>
            <h2 style={{ color: '#dc2626', marginBottom: '16px', fontSize: '20px' }}>
              Application Error
            </h2>
            <div style={{
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '4px',
              padding: '16px',
              marginBottom: '16px'
            }}>
              <p style={{
                fontFamily: 'monospace',
                fontSize: '14px',
                color: '#991b1b',
                wordBreak: 'break-all'
              }}>
                {error.message || 'An unexpected error occurred'}
              </p>
              {error.stack && (
                <details style={{ marginTop: '8px' }}>
                  <summary style={{ cursor: 'pointer', color: '#b91c1c', fontSize: '12px' }}>
                    Stack trace
                  </summary>
                  <pre style={{
                    fontSize: '10px',
                    overflow: 'auto',
                    maxHeight: '200px',
                    marginTop: '8px'
                  }}>
                    {error.stack}
                  </pre>
                </details>
              )}
            </div>
            <button
              onClick={() => reset()}
              style={{
                width: '100%',
                padding: '10px 16px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
