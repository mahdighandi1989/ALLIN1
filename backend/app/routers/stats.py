recent_customers_result = await db.execute(
            select(Customer)
            .options(
                load_only(
                    Customer.id,
                    Customer.account_no,
                    Customer.name,
                    Customer.status,
                    Customer.created_at,
                )
            )
            .where(Customer.is_deleted == False)
            .order_by(Customer.created_at.desc())
            .limit(5)
        )