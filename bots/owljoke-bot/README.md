# 🦉 Owl Joke Bot

한국어 아재개그를 들려주는 디스코드 봇입니다.

## ✨ 기능

- `/joke` - 랜덤 농담 보기
- `/add_joke` - 새로운 농담 추가 (관리자 전용)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/YOUR_USERNAME/owljoke-bot.git
cd owljoke-bot
```

### 2. 가상환경 생성 및 패키지 설치
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
nano .env  # 토큰과 ID 입력
```

### 4. 실행
```bash
python main.py
```

### 5. 백그라운드 실행 (서버)
```bash
nohup python main.py > bot.log 2>&1 &
```

## 📁 파일 구조

```
owljoke-bot/
├── main.py           # 봇 메인 코드
├── jokes.json        # 농담 데이터베이스
├── requirements.txt  # 의존성 패키지
├── .env.example      # 환경변수 템플릿
├── .env              # 환경변수 (git 제외)
├── .gitignore        # git 제외 파일
└── README.md         # 설명서
```

## ⚙️ 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `DISCORD_TOKEN` | ✅ | Discord 봇 토큰 |
| `ALLOWED_USER_ID` | ✅ | 농담 추가 권한 유저 ID |
| `GUILD_ID` | ❌ | 테스트용 서버 ID |

## 🔧 관리 명령어

```bash
# 봇 상태 확인
ps aux | grep "python main.py"

# 로그 보기
tail -f bot.log

# 봇 중지
pkill -f "python main.py"

# 봇 재시작
pkill -f "python main.py" && source venv/bin/activate && nohup python main.py > bot.log 2>&1 &
```

## 📝 라이센스

MIT License
