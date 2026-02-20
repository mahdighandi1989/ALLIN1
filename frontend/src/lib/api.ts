# محاسبه تسهیلات در حال انقضا
 expiring_soon_facilities = db.query(Facility).filter(
     Facility.end_date >= today,
     Facility.end_date <= thirty_days_later
 ).count()