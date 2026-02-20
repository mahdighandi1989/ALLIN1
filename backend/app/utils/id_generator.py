import uuid

def generate_facility_id() -> str:
    """Generate a unique facility ID with 'F' prefix"""
    return 'F' + str(uuid.uuid4()).replace('-', '').upper()[:8]