typescript
    } catch (err: any) {
      let errorMessage = 'Failed to load dashboard data';
      if (err?.response?.status === 500) {
        errorMessage = 'Server error. Please try again later.';
      } else {
        errorMessage = err?.response?.data?.detail || err?.message || errorMessage;
      }
      setError(errorMessage);
      toast.error(errorMessage);
    }