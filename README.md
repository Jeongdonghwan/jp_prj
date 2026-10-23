# 구마트래블 (クマトラベル) 홈페이지

일본인 관광객 대상 공항 송영·차량 대절 사이트. Flask 단일 페이지, 일본어 기본(`/`) + 한국어(`/ko`).

## 실행

```bash
pip install -r requirements.txt
cp .env.example .env      # LINE_URL, PHONE, ADMIN_PW, SMTP 채우기
python -m flask --app app run -p 8045
```

## 구조

| 경로 | 역할 |
|---|---|
| `app.py` | 라우트 전부 (메인, 문의, 후기, 관리, sitemap, robots) |
| `i18n/ja.json`, `ko.json` | 모든 문구. 템플릿에 문장 하드코딩 없음 |
| `templates/index.html` | 원페이지 템플릿 (히어로→서비스→요금/견적→차량→흐름→강점→갤러리→후기→FAQ→문의) |
| `templates/bear.svg` | 자체 곰 마스코트 |
| `static/img/` | WebP 변환된 이미지 (`tools/build_images.py`로 생성) |
| `data/` | `inquiries.json`, `reviews.json` (런타임 생성, git 제외) |

## 운영

- 후기 승인/삭제·문의 열람: `/admin/reviews?key=<ADMIN_PW>`
- 요금 변경: `app.py`의 `PRICES`
- LINE 공식계정이면 `LINE_URL=https://line.me/R/ti/p/@계정ID` — 견적 위젯이 `@계정ID`를 읽어 문의 내용을 프리필한다
- SMTP 비워두면 메일 없이 `data/*.json`에만 저장
- 이미지 재생성: `python tools/build_images.py <관광사진폴더> <차량사진폴더>`

## 이미지 출처

- 서울 풍경 9장: 사장님 제공 (출처 확인 필요)
- 차량 4장: Damian B Oh, Wikimedia Commons, CC BY-SA 4.0 (푸터에 표기함). 실차 촬영 후 교체 권장
