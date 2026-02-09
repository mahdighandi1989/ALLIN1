typescript
export async function dashboard() {
  if (AUTH_DISABLED) {
    return mockDashboard;
  }
  const response = await api.get<DashboardStats>('/stats/dashboard');
  return response.data;
}