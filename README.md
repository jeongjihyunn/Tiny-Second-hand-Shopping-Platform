# Tiny Second-hand Shopping Platform

간단한 중고거래 웹 플랫폼입니다. Flask 기반으로 회원가입/로그인, 상품 등록·조회·검색,
전체/1:1 실시간 채팅, 유저·상품 신고 및 자동 차단, 유저 간 송금(포인트), 관리자 페이지를
제공합니다. Secure Coding 과제용으로 개발 전 과정에서 보안 약점을 최소화하는 것을 목표로
구현했습니다.

## 주요 기능

- 회원가입 / 로그인 / 로그아웃 / 마이페이지 (소개글, 비밀번호 변경)
- 상품 등록 / 조회 / 검색 / 수정 / 삭제 / 판매완료 처리 (이미지 업로드 포함)
- 전체 채팅(실시간) + 1:1 채팅(실시간, Socket.IO) + 메시지함(받은 1:1 대화 목록)
- 유저/상품 신고, 일정 횟수 이상 신고 시 자동 차단(상품) / 자동 휴면(유저)
- 유저 간 포인트 송금 및 거래 내역 조회
- 관리자 페이지: 회원/상품/신고 관리

## 기술 스택

- Python 3.10+, Flask 3, Flask-SQLAlchemy(SQLite), Flask-Login, Flask-WTF(CSRF),
  Flask-SocketIO, Flask-Limiter, bleach
- 프론트: Jinja2 템플릿 + 순수 CSS/JS (별도 프레임워크 없음)

## 환경 설정 (Ubuntu / WSL 기준)

```bash
# 1. 프로젝트 클론
git clone <이 저장소 URL>
cd secure-coding-platform

# 2. 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 파일 생성
cp .env.example .env
# .env를 열어 SECRET_KEY를 아래 명령으로 생성한 랜덤 값으로 반드시 교체하세요.
python3 -c "import secrets; print(secrets.token_hex(32))"

# 5. (선택) 관리자 계정 생성 - admin / ChangeMe123!  (생성 후 반드시 비밀번호 변경)
python3 seed.py

# 6. 서버 실행
python3 run.py
# -> http://127.0.0.1:5000 접속
```

### 테스트 실행

```bash
pip install -r requirements.txt   # pytest 포함
python3 -m pytest -q
```

15개의 pytest 테스트가 인증, 상품 CRUD/IDOR, XSS/SQLi 방어, 송금, 신고 자동차단 로직을 검증합니다.

## 프로젝트 구조

```
app/
  auth/        회원가입, 로그인, 마이페이지
  products/    상품 CRUD, 검색, 이미지 업로드
  chat/        전체/1:1 채팅 (Socket.IO)
  reports/     신고 및 자동 차단 로직
  wallet/      유저간 송금
  admin/       관리자 대시보드
  models.py    SQLAlchemy 모델 (User, Product, Message, Report, Transaction)
  utils.py     보안 관련 유틸 (파일 업로드 검증, 입력값 sanitize, admin 데코레이터)
  templates/   Jinja2 템플릿
  static/      CSS, 업로드된 이미지
tests/         pytest 테스트
config.py      환경별 설정 (개발/운영/테스트)
run.py         앱 실행 진입점
seed.py        (선택) 데모 관리자 계정 생성 스크립트
SECURITY_CHECKLIST.md   보안 점검 체크리스트
```

## 보안 관련 참고

구현 과정에서 검토·적용한 보안 조치는 `SECURITY_CHECKLIST.md`와 제출 보고서에 상세히
정리되어 있습니다. 요약:

- 비밀번호: PBKDF2-SHA256 해시 저장 (평문 저장/로깅 없음)
- SQL Injection: SQLAlchemy ORM(파라미터 바인딩)만 사용, raw SQL 없음
- XSS: Jinja2 autoescape + 입력값 bleach sanitize + 클라이언트 측 textContent 렌더링(채팅)
- CSRF: 모든 상태 변경 요청에 Flask-WTF CSRF 토큰 필수
- 파일 업로드: 확장자 화이트리스트, 랜덤 파일명(UUID), 4MB 용량 제한
- 인가(Authorization): 상품 수정/삭제, 관리자 페이지 등에서 소유자/관리자 여부 서버측 재검증 (IDOR 방지)
- 세션: HttpOnly, SameSite=Lax 쿠키, 운영환경에서 Secure 플래그 활성화
- 무차별 대입 공격 방지: 로그인/회원가입 rate limiting (Flask-Limiter)
- 보안 헤더: CSP, X-Frame-Options, X-Content-Type-Options 등 적용
- 신고 남용 방지: 동일 대상에 대한 중복 신고 차단(DB unique constraint)
- 에러 처리: 커스텀 에러 페이지로 스택트레이스 등 민감정보 노출 방지

## 라이선스

[WHS-4th] 시큐어 코딩 과제 제출용 프로젝트입니다.
