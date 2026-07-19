# 4부 — 내 구성으로 만들기 (범용 치환 레시피)

> 3부는 "우리 환경"의 기록이다. **당신의 벤더 구성은 또 다를 것이다** — 구독이 2개뿐일 수도,
> OpenRouter 만능키 하나일 수도, 사내 게이트웨이일 수도 있다. 이 문서는 어떤 조합이든
> 같은 절차로 좌석표를 만드는 레시피다.

## Step 0 — 내가 가진 것 인벤토리

프로바이더는 인증 방식 기준으로 세 종류다:

| 종류 | 예 | GJC 연결 방법 |
|---|---|---|
| **구독 OAuth** | Claude 구독, ChatGPT 구독, Google AI Pro/Ultra, Copilot | 세션 안에서 `/login <provider>` |
| **direct API 키** | DeepSeek, OpenRouter, Groq, xAI, GLM/Z.ai … | 환경변수 또는 `models.yml`의 `apiKeyEnv` |
| **로컬/사내 게이트웨이** | OpenAI-호환 프록시, ollama, LiteLLM … | `models.yml`에 커스텀 프로바이더 선언 — **[3부 함정 ①·②](03-adaptation.md#3-2-밟은-지뢰---auth-none-프로바이더는-프로필을-통과하지-못한다) 필독** |

지금 뭐가 인증돼 있는지 확인:

```bash
# 등록된 프로필 로스터 + 활성화 에러 메시지가 곧 진단 도구다
gjc --mpreset __nope__ -p --no-session --no-tools "x"
gjc --mpreset daily -p --no-session --no-tools "x"
# → "requires credentials for: ..." 에 나오는 이름이 당신에게 없는 벤더다
```

## Step 1 — 좌석별 선택 규칙

각 역할에 필요한 건 "그 축의 최강"이지 특정 브랜드가 아니다. **가진 것 중에서** 고르면 된다:

| 좌석 | 필요한 능력 | 선택 규칙 (위에서부터, 가진 것 중) |
|---|---|---|
| `default` (본체) | 도구호출 신뢰성·정직성 | **가진 것 중 최상위 플래그십. 절대 타협 금지.** 나머지 좌석을 다 포기해도 본체는 지켜라 |
| `executor` | 실코딩 (SWE류) | 코딩특화 구독 모델 → 코딩형 direct API(DeepSeek·GLM·Kimi 등) → 없으면 본체와 동일 모델 |
| `planner` | 추론·순서 분해 | 추론축 강한 모델 → 없으면 본체와 동일 모델의 낮은 effort |
| `architect` | 장문맥(≥200K)·코드리뷰 | 컨텍스트 창이 가장 큰 모델 → 게이트웨이 Gemini류 → 본체 |
| `critic` | **계열 독립성** (성능보다 중요) | 본체와 *다른 벤더*면 뭐든 OK. 저가 모델도 충분 — 독립적 시선이 목적 |

불변식 두 개만 지켜라 (원본 가이드의 검증된 원칙):

1. `required_providers` **최소 2벤더** — 1벤더뿐이면 이 가이드 대상이 아니다. GJC **내장 프로필**(`claude-opus`, `codex-medium` 등)을 그냥 써라.
2. `critic`은 본체와 **cross-family** — 같은 회사 모델은 같은 실수를 좋게 봐준다.

## Step 2 — 흔한 구성별 예시

### A. Claude 구독 + ChatGPT 구독 (2벤더 — 가장 흔한 조합)

```yaml
daily-mine:
  required_providers: [anthropic, openai-codex]
  model_mapping:
    default:   anthropic/claude-opus-4-8:medium
    executor:  openai-codex/gpt-5.6-terra:high
    planner:   openai-codex/gpt-5.6-sol:high
    architect: anthropic/claude-opus-4-8:high     # 1M ctx
    critic:    openai-codex/gpt-5.6-terra:high    # cross-family ✅
```

### B. ChatGPT 구독 + Gemini 구독 (Anthropic 없음)

본체는 가진 것 중 최상 라우터로. (원본은 Anthropic 라우터를 선호하지만, 없는 걸 어쩌겠나 — 가진 패로 친다.)

```yaml
daily-mine:
  required_providers: [openai-codex, google-antigravity]
  model_mapping:
    default:   openai-codex/gpt-5.6-sol:high
    executor:  openai-codex/gpt-5.6-terra:high
    planner:   openai-codex/gpt-5.6-sol:high
    architect: google-antigravity/gemini-3.1-pro-low:high   # 1M ctx·멀티모달
    critic:    google-antigravity/gemini-3.1-pro-low:high   # cross-family ✅
```

### C. Claude 구독 + OpenRouter 만능키 (타 계열을 키 하나로)

```yaml
daily-mine:
  required_providers: [anthropic, openrouter]
  model_mapping:
    default:   anthropic/claude-opus-4-8:medium
    executor:  openrouter/deepseek/deepseek-v4-pro
    planner:   openrouter/openai/gpt-5.6-sol
    architect: anthropic/claude-opus-4-8:high
    critic:    openrouter/google/gemini-3.1-pro-preview     # 제3계열 dissent
```

### D. 구독 1개 + 로컬 게이트웨이 / ollama

우리(3부)와 같은 패턴이다. 반드시: 게이트웨이에 **더미 `apiKey`**(함정 ①), **SSE 종료 확인**(함정 ②),
그리고 **툴콜 스모크**(§Step 4) — 로컬 모델은 툴콜 포맷이 약한 경우가 많아서 architect/critic처럼
툴 쓰는 좌석에 앉히기 전에 꼭 검증하라.

## Step 3 — 템플릿 채워서 병합

[`profiles/template.yml`](../profiles/template.yml)을 복사해 placeholder를 채우고
`~/.gjc/agent/models.yml`에 붙여넣는다 (백업 먼저!):

```bash
cp ~/.gjc/agent/models.yml ~/.gjc/agent/models.yml.bak-$(date +%Y%m%d-%H%M%S)
# template.yml 의 profiles: 블록을 models.yml 에 병합
```

## Step 4 — 검증 + /mlbo 개인화

1. [3부 §3-4의 4단계 검증](03-adaptation.md#3-4-검증-절차--4단계)을 그대로 돌린다.
   특히 **③ 툴콜 스모크**는 좌석마다 — 셀렉터가 응답하는 것과 도구를 쓸 줄 아는 건 다른 문제다.
2. `/mlbo` 자동완성 각주도 내 프로필로: [`patches/mlbo-slash-command/mlbo-block.ts`](../patches/mlbo-slash-command/mlbo-block.ts)의
   `subcommands` 목록을 내 프로필 이름·설명으로 바꾼 뒤 `apply-mlbo.sh` 실행.
   (핸들러는 어떤 프로필 이름이든 받으므로 목록은 순전히 UX용 각주다.)

## 주의 — effort 표기는 모델군마다 다르다

`:high`가 어디서나 통하는 게 아니다. 모델군별 유효 등급·침묵 클램프(범위 밖 등급이 에러 없이
하향되는 것)는 [원본 가이드의 effort 치트시트](https://github.com/project820/gjc-multivendor-setup-guide#3-2-추론등급effort-치트시트)가
가장 정확하다. 새 좌석을 앉히면 낮은 effort로 실호출 한 번, 올려서 한 번 — 두 번은 쏴보고 확정하라.

---

**이전 ← [3부: 우리 환경 적응 가이드](03-adaptation.md)** · **[홈](../README.md)**
