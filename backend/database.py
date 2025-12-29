from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# SQLite 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./notices.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 공지사항 테이블 모델
class Notice(Base):
    __tablename__ = "kangnam_notices"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True) # 제목 중복 방지
    link = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)