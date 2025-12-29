from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from database import SessionLocal, init_db, Notice
import uvicorn

app = FastAPI()

# CORS 설정: React Native 앱 접속 허용
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# [크롤링 & 저장 함수]
def crawl_and_save():
    print("🔄 크롤링 시작...")
    db = SessionLocal()
    url = "https://web.kangnam.ac.kr/menu/f19069e6134f8f8aa7f689a4a675e66f.do"
    
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('div.tbody > ul > li') or soup.select('.c-board-list li')
        
        for item in items:
            a_tag = item.select_one('dl dt a') or item.select_one('a')
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = "https://web.kangnam.ac.kr" + a_tag.get('href', '')
                
                if "데이터가 없습니다" in title or not title: 
                    continue
                
                # 1. DB에 이미 있는지 확인
                existing_notice = db.query(Notice).filter(Notice.title == title).first()
                
                if not existing_notice:
                    try:
                        new_notice = Notice(title=title, link=link)
                        db.add(new_notice)
                        # 2. flush를 통해 세션 내용을 DB 트랜잭션에 미리 반영 (중복 방지 핵심)
                        db.flush() 
                    except Exception as e:
                        db.rollback() # 에러 발생 시 해당 건만 취소
                        print(f"⚠️ 중복 건 건너뛰기: {title}")
        
        db.commit() # 모든 처리가 끝나면 한 번에 커밋
        print("✅ 크롤링 및 저장 완료")
        
    except Exception as e:
        print(f"❌ 크롤링 중 에러 발생: {e}")
        db.rollback()
    finally:
        db.close()

@app.on_event("startup")
def startup():
    init_db()
    crawl_and_save() # 시작 시 즉시 실행
    scheduler = BackgroundScheduler()
    scheduler.add_job(crawl_and_save, 'interval', minutes=60) # 1시간마다 반복
    scheduler.start()

# [API 엔드포인트]
@app.get("/api/notices")
def read_notices(db: Session = Depends(get_db)):
    return db.query(Notice).order_by(Notice.id.desc()).limit(30).all()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)