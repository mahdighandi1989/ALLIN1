total_amount = (await db.execute(
          select(func.sum(Facility.amount)).where(Facility.is_deleted == False)
      )).scalar() or 0

      total_outstanding = (await db.execute(
          select(func.sum(Facility.outstanding)).where(Facility.is_deleted == False)
      )).scalar() or 0