typescript
if (facilitiesResult.status === 'fulfilled') {
  setData(facilitiesResult.value)
} else {
  // سعی در استخراج پیام خطا از پاسخ بک‌اند
  let errorMessage = 'Failed to load facilities data'
  const reason = facilitiesResult.reason
  if (reason && typeof reason === 'object') {
    // اگر reason یک Response باشد
    if (reason instanceof Response) {
      // می‌توانیم متن پاسخ را بخوانیم
      try {
        const errorData = await reason.json()
        errorMessage = errorData.detail || errorMessage
      } catch (e) {
        // اگر نتوانستیم JSON را بخوانیم، از statusText استفاده می‌کنیم
        errorMessage = reason.statusText || errorMessage
      }
    } else if (reason.message) {
      errorMessage = reason.message
    }
  }
  toast.error(errorMessage)
  console.error('Facilities load error:', facilitiesResult.reason)
}