# 경제 브리프 — 완전 무료 자동 갱신 버전

API 비용 없이, 서버 없이, GitHub의 무료 기능만으로 매일 아침 자동으로
경제 뉴스를 갱신하는 정적 사이트입니다.

- 뉴스 출처: 한국경제 RSS (무료, 로그인/키 불필요)
- 자동화: GitHub Actions (매일 KST 07:00 실행)
- 호스팅: GitHub Pages (무료)
- 예상 비용: **0원**

---

## 배포 방법 (한 번만 하면 됨, 10분)

1. **GitHub 계정 만들기** (무료) → https://github.com/join

2. **새 저장소 생성**
   - 우측 상단 `+` → `New repository`
   - 이름: `economic-brief` (원하는 이름으로 변경 가능)
   - `Public`으로 설정 (Private이면 Pages 무료 사용에 제약이 있을 수 있음)

3. **이 폴더의 모든 파일 업로드**
   - 저장소 페이지에서 `Add file` → `Upload files`
   - `index.html`, `news.json`, `README.md`, `scripts/`, `.github/` 폴더 전부 그대로 올리기
   - (Git에 익숙하면 `git push`로 올려도 됩니다)

4. **Actions 쓰기 권한 켜기** (자동 커밋을 위해 필요)
   - 저장소 `Settings` → `Actions` → `General`
   - `Workflow permissions`에서 `Read and write permissions` 선택 → 저장

5. **GitHub Pages 켜기**
   - `Settings` → `Pages`
   - `Source`: `Deploy from a branch`
   - `Branch`: `main` / `/ (root)` 선택 → 저장
   - 몇 분 뒤 `https://내아이디.github.io/economic-brief/` 로 접속 가능

6. **첫 실행은 수동으로 한 번**
   - 저장소 상단 `Actions` 탭 → `Update Economic Brief` 선택
   - `Run workflow` 버튼 클릭 → 몇 초 뒤 `news.json`이 최신 뉴스로 갱신됨

이후로는 **매일 아침 7시(한국시간)에 자동으로** 실행되어 `news.json`이 갱신되고,
사이트를 새로고침하면 그날의 뉴스가 그대로 반영됩니다.

---

## 친구에게 공유하기

배포가 끝나면 아래 링크만 보내주면 됩니다.

```
https://내아이디.github.io/economic-brief/
```

친구가 접속할 때마다 가장 최근 자동 갱신된 뉴스를 보게 됩니다.
버튼을 누르거나 API를 호출하는 과정이 없어서, 몇 명이 접속하든 비용이 들지 않습니다.

---

## 커스터마이징

- **뉴스 출처/카테고리 변경**: `scripts/update_news.py` 안의 `FEEDS` 딕셔너리에서
  RSS 주소를 바꾸면 됩니다. (다른 언론사 RSS 주소로 교체 가능)
- **갱신 시각 변경**: `.github/workflows/update-news.yml`의
  `cron: '0 22 * * *'` 부분을 수정하세요. (UTC 기준 시각이며, KST = UTC+9)
- **디자인 수정**: `index.html`의 `<style>` 태그 안 색상(`--gold`, `--bg` 등)을 바꾸면 됩니다.
