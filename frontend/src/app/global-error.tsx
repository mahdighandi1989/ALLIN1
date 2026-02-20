useEffect(() => {
  if (error?.message) {
    console.error('Global application error:', error.message, error)
  }
}, [error])