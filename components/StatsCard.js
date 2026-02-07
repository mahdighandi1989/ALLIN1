export default function StatsCard({ data }) {
  // استفاده از optional chaining و مقدار پیش‌فرض
  const total = data?.stats?.total ?? 0;
  const completed = data?.stats?.completed ?? 0;
  const pending = data?.stats?.pending ?? 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">مجموع</h3>
        <p className="text-3xl font-bold text-blue-600">{total}</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">تکمیل شده</h3>
        <p className="text-3xl font-bold text-green-600">{completed}</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">در انتظار</h3>
        <p className="text-3xl font-bold text-yellow-600">{pending}</p>
      </div>
    </div>
  );
}