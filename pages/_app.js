import { ErrorBoundary } from 'react-error-boundary';
import ErrorFallback from '../components/ErrorFallback';

function MyApp({ Component, pageProps }) {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Component {...pageProps} />
    </ErrorBoundary>
  );
}

export default MyApp;