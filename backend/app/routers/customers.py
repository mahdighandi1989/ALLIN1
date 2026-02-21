if search:
            search_filter = and_(
                Customer.is_deleted == False,
                Customer.name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)