# 보안 점검 체크리스트

테스트/코드 리뷰를 통해 아래 항목들을 점검했습니다. "확인 방법" 열은 실제로 어떻게
검증했는지를 나타냅니다 (자동화 테스트 `tests/`, 수동 스모크 테스트, 코드 리뷰).

| # | 취약점 분류 (OWASP 기준) | 점검 내용 | 조치 | 확인 방법 |
|---|---|---|---|---|
| 1 | SQL Injection | 검색, 로그인 등 모든 DB 조회가 문자열 조합 없이 SQLAlchemy ORM/파라미터 바인딩으로만 수행되는가 | Raw SQL 미사용. LIKE 검색 시 `%`, `_` 와일드카드 이스케이프 처리 | `tests/test_products.py::test_search_is_safe_and_functional` (SQLi 페이로드 입력 시 500/데이터 유출 없음 확인) |
| 2 | XSS (Stored/Reflected) | 상품명/설명, 소개글, 채팅 메시지 등 사용자 입력이 그대로 렌더링되는가 | 입력 시 `bleach.clean()`로 태그 제거 + Jinja2 autoescape(출력 시 2차 방어) + 채팅은 `textContent`로만 DOM에 삽입 | `tests/test_products.py::test_xss_in_title_is_not_rendered_as_html` |
| 3 | CSRF | 상태 변경(POST) 요청에 토큰 검증이 빠짐없이 적용되는가 | Flask-WTF `CSRFProtect` 전역 적용, 모든 폼에 `hidden_tag()`/`csrf_token()` 포함 | 수동 스모크 테스트: 토큰 없이 POST → 400 응답 확인 |
| 4 | 인증 - 비밀번호 저장 | 비밀번호가 평문/약한 해시로 저장되는가 | `werkzeug.security` PBKDF2-SHA256(600,000 iteration) 해시만 저장, 로그에도 원문 미기록 | 코드 리뷰 (`app/models.py User.set_password`) |
| 5 | 인증 - 계정 열거(User Enumeration) | 로그인 실패 메시지로 아이디 존재 여부가 드러나는가 | 아이디 미존재/비밀번호 오류를 동일한 메시지로 응답 | `tests/test_auth.py::test_login_wrong_password_generic_error`, `test_login_unknown_user_same_generic_error` |
| 6 | 인증 - 무차별 대입(Brute force) | 로그인/회원가입에 시도 횟수 제한이 있는가 | Flask-Limiter로 로그인 10회/분, 회원가입 10회/시간 제한 | 수동 스모크 테스트: 연속 11회 로그인 시도 시 429 응답 확인 |
| 7 | 인가 - IDOR (Broken Access Control) | 다른 유저의 상품을 URL 조작만으로 수정/삭제할 수 있는가 | 모든 수정/삭제 라우트에서 `seller_id == current_user.id or is_admin` 서버측 재검증 | `tests/test_products.py::test_edit_forbidden_for_non_owner` (403 확인) |
| 8 | 인가 - 관리자 페이지 | 일반 유저가 `/admin/*`에 접근 가능한가 | `admin_bp.before_request`에서 `login_required` + `admin_required` 강제 적용 (라우트별 데코레이터 누락 방지) | 코드 리뷰 (`app/admin/routes.py`) |
| 9 | 인가 - 채팅방 접근 | 1:1 채팅방 이름을 유추/위조해 타인의 대화를 엿볼 수 있는가 | 방 이름을 서버가 두 유저 ID로부터 직접 생성(`Message.dm_room`), Socket.IO `join`/`send_message` 이벤트에서 요청자가 방 참여자인지 서버측 재검증 | 코드 리뷰 (`app/chat/events.py::_room_is_authorized`) |
| 10 | 파일 업로드 | 실행 가능한 파일(.php 등)이나 경로 조작 파일명이 업로드되는가 | 확장자 화이트리스트 검증 + 저장 파일명은 서버가 생성한 UUID만 사용 (클라이언트 파일명 미신뢰), 4MB 용량 제한 | 수동 스모크 테스트: `.php` 업로드 시 거부, 정상 업로드 시 파일명이 UUID로 저장됨을 확인 |
| 11 | 민감정보 노출 / 설정 | SECRET_KEY, DB 접속정보 등이 코드에 하드코딩되어 커밋되는가 | `.env`(gitignore 처리)로 분리, `.env.example`만 커밋. 운영 설정에서 `DEBUG=False`, 에러 발생 시 스택트레이스 미노출 | 코드 리뷰 (`config.py`, `.gitignore`), 커스텀 500 에러 페이지 |
| 12 | 세션 관리 | 세션 쿠키가 JS로 탈취되거나 CSRF에 취약한가 | `HttpOnly`, `SameSite=Lax` 쿠키, 운영환경 `Secure` 플래그, 2시간 세션 만료 | 코드 리뷰 (`config.py`) |
| 13 | 오픈 리다이렉트 | 로그인 후 `next` 파라미터로 외부 사이트로 리다이렉트될 수 있는가 | `next` 파라미터의 scheme/netloc을 검사해 상대경로만 허용 | 코드 리뷰 (`app/auth/routes.py::_safe_redirect_target`) |
| 14 | 비즈니스 로직 - 송금 경쟁 조건 | 동시에 여러 송금 요청 시 잔액이 이중으로 차감/초과 인출되는가 | 하나의 DB 트랜잭션 내에서 송금 직전 잔액 재확인 후 커밋, `with_for_update()`로 운영 DB(Postgres/MySQL)에서는 row lock 적용 | `tests/test_wallet.py::test_transfer_insufficient_balance_rejected` 및 코드 리뷰 |
| 15 | 비즈니스 로직 - 신고 남용 | 동일 유저가 같은 대상을 반복 신고해 무고한 유저/상품을 강제 차단시킬 수 있는가 | `Report` 테이블에 `(reporter_id, target_type, target_id)` UNIQUE 제약 | `tests/test_reports.py::test_cannot_report_same_target_twice` |
| 16 | 비즈니스 로직 - 신고 자동 차단 정상 동작 | 신고 임계치 도달 시 실제로 상품이 숨겨지고 유저가 로그인 불가능해지는가 | 임계치 도달 시 `Product.status=BLOCKED` / `User.status=DORMANT`로 전환, 차단된 상품은 소유자/관리자 외 404 처리, 휴면 계정은 로그인 거부 | `tests/test_reports.py::test_product_auto_blocked_after_threshold` |
| 17 | 클릭재킹 / 보안 헤더 | 사이트가 iframe에 삽입되거나 MIME 스니핑 공격에 노출되는가 | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, CSP, `Referrer-Policy` 등 응답 헤더 적용 | 수동 스모크 테스트: 응답 헤더 확인 |
| 18 | 입력값 검증 | 가격/송금액에 음수·과대값·비정상 타입이 들어가는가 | WTForms `NumberRange`, `Length`, `Regexp` 검증을 서버측에서 필수 적용 (클라이언트 검증에 의존하지 않음) | `tests/test_wallet.py::test_cannot_transfer_negative_amount` |

## 기능 요구사항 체크리스트

| 요구사항 | 구현 여부 | 위치 |
|---|---|---|
| 회원가입/로그인 | ✅ | `app/auth` |
| 상품 등록/조회 | ✅ | `app/products` |
| 상품 검색 | ✅ | `app/products/routes.py::index` |
| 전체 채팅 | ✅ | `app/chat` (room="global") |
| 1:1 채팅 | ✅ | `app/chat` (room="dm:<id>:<id>") |
| 악성 유저/상품 신고 및 자동 차단 | ✅ | `app/reports` |
| 유저 간 송금 | ✅ | `app/wallet` |
| 관리자 전체 관리 기능 | ✅ | `app/admin` |
