typescript
} catch (err: any) {
  let errorMessage = 'Failed to load dashboard data';
  if (err?.response) {
    // سرور پاسخ داده اما با وضعیت خطا
    if (err.response.status === 500) {
      errorMessage = 'Server error. Please try again later.';
    } else {
      errorMessage = err.response.data?.detail || err.response.data?.message || errorMessage;
    }
  } else if (err?.request) {
    // درخواست فرستاده شده اما پاسخی دریافت نشده
    errorMessage = 'No response from server. Please check your network connection.';
  } else {
    // مشکلی در تنظیم درخواست رخ داده است
    errorMessage = err?.message || errorMessage;
  }
  setError(errorMessage);
  toast.error(errorMessage);
}