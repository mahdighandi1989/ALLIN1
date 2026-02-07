export default function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <h2 className="text-2xl font-bold text-red-600 mb-4">خطایی رخ داده است</h2>
        <p className="text-gray-700 mb-2">مشکلی در نمایش این صفحه وجود دارد.</p>
        <pre className="bg-gray-800 text-white p-4 rounded overflow-auto text-sm mb-4">
          {error.message}
        </pre>
        <button
          onClick={resetErrorBoundary}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
        >
          تلاش مجدد
        </button>
      </div>
    </div>
  );
}