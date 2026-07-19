# 1부 — GJC(Gajae Code) 개요 및 설치

> **원본(공식) 주소: https://github.com/Yeachan-Heo/gajae-code**
> 이 문서는 공식 README의 대체물이 아니라, 이 가이드를 따라오는 데 필요한 최소한의 배경 지식이다.

## GJC가 뭔가

GJC는 터미널에서 돌아가는 **AI 코딩 에이전트**다. Claude Code나 Codex CLI 같은 부류라고 보면 된다.
채팅으로 지시하면 파일을 읽고, 코드를 고치고, 명령을 실행하고, 테스트를 돌린다.

비전공자용 비유: **"터미널에 상주하는 AI 개발자 한 명"**이다. 다만 이 개발자는 혼자가 아니라,
필요할 때 아래 4명의 전문가를 하청으로 부른다:

| 역할 | 하는 일 | 비유 |
|---|---|---|
| `default` (본체) | 대화·판단·도구 사용 — 항상 깨어 있음 | 팀장 |
| `planner` | 작업 순서와 완료 기준 설계 | 기획자 |
| `executor` | 실제 코드 작성·수정 | 개발자 |
| `architect` | 큰 코드베이스 탐색·구조 리뷰 | 아키텍트 |
| `critic` | 결과물 흠집 내기(적대적 검증) | 감리 |

**핵심 아이디어: 이 5개 좌석에 서로 다른 AI 모델을 앉힐 수 있다.**
좌석 배치 세트를 "프로필(모델 프리셋)"이라 부르고, 이게 이 가이드 전체의 주제다.

## 설치

공식 문서가 항상 우선이다: https://github.com/Yeachan-Heo/gajae-code

```bash
# bun 이 있다면 (권장)
bun install -g gajae-code

# 또는 npm
npm install -g gajae-code

gjc --version     # 확인
gjc               # 대화형 세션 시작
```

첫 실행 후 쓸 AI 벤더에 로그인한다 (구독 OAuth 방식):

```text
/login anthropic       # Claude 구독
/login openai-codex    # ChatGPT 구독 (base GPT 제공)
# 그 외 벤더는 2부·3부 참조
```

## 최소 개념 사전

| 용어 | 뜻 |
|---|---|
| **셀렉터** | 모델 지정 문자열. `벤더/모델:추론등급` 형식 — 예: `anthropic/claude-opus-4-8:medium` |
| **effort(추론등급)** | 모델이 "얼마나 오래 생각할지". `low → medium → high → xhigh` 순으로 비싸고 느려짐 |
| **프로필(mpreset)** | 5좌석 배치 세트. `gjc --mpreset <이름>` 으로 활성화 |
| **`models.yml`** | `~/.gjc/agent/models.yml` — 커스텀 벤더·프로필을 선언하는 파일 |
| **`config.yml`** | `~/.gjc/agent/config.yml` — 기본 프로필·폴백 체인 등 설정 |

## 프로필 다루기 기본기

```bash
gjc --mpreset codex-medium            # 이번 세션만 해당 프로필
gjc --mpreset codex-medium --default  # 영구 기본값으로
gjc --mpreset __nope__ -p --no-session --no-tools "x"
# ↑ 일부러 틀린 이름 → 등록된 프로필 전체 목록이 에러 메시지로 나옴 (진단 트릭)
```

세션 안에서는 `Ctrl+L` → 프리셋 랜딩 화면에서 대화형으로 고를 수도 있다.

---

**다음 → [2부: 멀티벤더 셋업 가이드 개요](02-multivendor-overview.md)** — "그래서 어느 좌석에 어느 모델을 앉히는 게 검증돼 있나"
