from app.database import Base

class FacilityNew(Base):
    __tablename__ = 'facilities'
    # تعریف تمام ستون‌های موجود به جز facility_no
    # اما باید لیست ستون‌ها را از metadata بگیریم.