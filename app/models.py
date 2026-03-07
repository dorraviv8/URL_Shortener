from sqlalchemy import Column, Integer, String
from database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    original_url = Column(String, nullable=False)
