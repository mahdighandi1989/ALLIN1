"total_amount": sum(float(f.amount) if f.amount is not None else 0 for f in facilities),
"total_outstanding": sum(float(f.outstanding) if f.outstanding is not None else 0 for f in facilities)