# 🔧 GJC 멀티벤더 프로필 — 비표준 환경 적응 가이드

> [gjc-multivendor-setup-guide](https://github.com/project820/gjc-multivendor-setup-guide)의 10개 번들은
> **5구독(anthropic · openai-codex · google-antigravity · xai · opencode-go) 전제**다.
> 벤더 구성이 다르면(일부 구독 없음, 로컬 OpenAI-호환 게이트웨이 사용, direct API 대체)
> **10개 번들 전부 활성화에 실패한다** — 프로필 활성화가 fail-closed이기 때문이다.
>
> 이 리포는 그 상황에서 **좌석을 치환해 살리는 방법**과, 실제로 부딪힌 **엔진/게이트웨이 함정 2건**,
> 그리고 **치환 좌석 검증 절차**를 정리한다.

- 검증 환경: **GJC(Gajae Code) 0.10.1** · 2026-07-19 실호출 검증
- 원본 가이드: [project820/gjc-multivendor-setup-guide](https://github.com/project820/gjc-multivendor-setup-guide) v2.0.1 (CC BY 4.0)
- GJC 엔진: [Yeachan-Heo/gajae-code](https://github.com/Yeachan-Heo/gajae-code)

---

## 목차

1. [왜 전부 실패하는가 — fail-closed 활성화](#1-왜-전부-실패하는가--fail-closed-활성화)
2. [좌석 치환 원칙](#2-좌석-치환-원칙)
3. [함정 ①: `auth: none` 프로바이더는 프로필을 통과하지 못한다](#3-함정--auth-none-프로바이더는-프로필을-통과하지-못한다)
4. [함정 ②: SSE `[DONE]` 후 연결을 닫지 않는 게이트웨이는 GJC를 행에 빠뜨린다](#4-함정--sse-done-후-연결을-닫지-않는-게이트웨이는-gjc를-행에-빠뜨린다)
5. [치환 프로필 예제](#5-치환-프로필-예제)
6. [검증 절차 — 4단계](#6-검증-절차--4단계)
7. [벤치마크로 더 최적화해야 하나? — 원본 신뢰의 경계](#7-벤치마크로-더-최적화해야-하나--원본-신뢰의-경계)

---

## 1. 왜 전부 실패하는가 — fail-closed 활성화

GJC의 프로필 활성화(`--mpreset`)는 두 단계로 프로바이더를 검사한다
(소스: `src/config/model-profile-activation.ts`, `src/config/model-profiles.ts`):

1. `required_providers` 목록 **+ `model_mapping`의 모든 셀렉터에서 파생된 프로바이더**를 합산한다.
   → `required_providers`에서 빼도 매핑에 남아 있으면 여전히 검사 대상이다. **우회 불가.**
2. 그중 하나라도 미인증이면 활성화가 즉시 예외로 죽는다:

```text
Error: Model profile "daily" requires credentials for: google-antigravity.
Run /login and configure the missing provider(s), then retry.
```

원본 10개 번들은 전부 `google-antigravity` / `xai` / `opencode-go` 중 최소 하나를 요구하므로,
이 셋이 없는 환경에서는 **0/10 활성화**된다. 설치 자체는 되지만 전부 죽은 프로필이다.

> ⚠️ 원클릭 `install.sh`는 기본 프로필을 `daily`로 영구 설정한다. 벤더가 모자란 환경에서 그대로 돌리면
> **새 세션이 전부 활성화 실패 상태**가 된다. 반드시 `GJC_SETUP_DEFAULT=none`으로 설치하거나 수동 병합하라.

### 진단 트릭: 프로필 로스터 확인

일부러 틀린 이름을 주면 API 호출 없이 등록된 프로필 전체 목록이 나온다:

```bash
gjc --mpreset __nope__ -p --no-session --no-tools "x"
# Error: Unknown model profile "__nope__". Available profiles: claude-fable, daily-ours, ...
```

---

## 2. 좌석 치환 원칙

원본 가이드의 설계 3원칙은 벤더가 바뀌어도 유지한다:

| 원칙 | 치환 시 지키는 방법 |
|---|---|
| **강한 본체(default) 고정** | default는 보유한 최상위 구독 모델로 (예: Anthropic Opus). 절대 저가 모델로 내리지 않는다 |
| **critic = cross-family** | 본체와 다른 벤더면 됨. grok이 없으면 **제4계열 direct API**(DeepSeek, GLM 등)로 대체 |
| **역할축 유지** | 장문맥/멀티모달 → architect, 코딩특화 → executor, 추론/분해 → planner |

이 리포의 치환 예 (원본 → 대체):

| 원본 좌석 | 없을 때 대체 | 비고 |
|---|---|---|
| `google-antigravity/gemini-3.1-pro-low:high` | **로컬 OpenAI-호환 게이트웨이의 Gemini** (`local-gateway/gemini-…`) | Antigravity CLI 등을 REST로 감싼 자가 게이트웨이. §3·§4 함정 주의 |
| `xai/grok-4.5:high` (critic) | **`deepseek/deepseek-v4-pro`** 등 제4계열 direct API | 원본 스스로도 grok critic은 "결함회수 최강 근거 0건, 제3계열 dissent일 뿐"이라 명시 — 계열 독립성만 유지하면 등가 |
| `opencode-go/deepseek-v4-flash` | **`deepseek/deepseek-v4-flash`** direct API | 동일 모델, 프로바이더 경로만 다름 |

커스텀 프로바이더는 `~/.gjc/agent/models.yml`의 `providers:` 블록에 선언하고,
프로필은 같은 파일의 `profiles:` 블록에 추가한다 → [§5 예제](#5-치환-프로필-예제).

---

## 3. 함정 ①: `auth: none` 프로바이더는 프로필을 통과하지 못한다

로컬 게이트웨이는 인증이 필요 없어서 자연스럽게 이렇게 선언하게 된다:

```yaml
providers:
  local-gateway:
    baseUrl: http://127.0.0.1:8086/v1
    auth: none          # ❌ 프로필 required_providers 검사를 절대 통과 못 함
    api: openai-completions
```

**이러면 개별 모델 호출(`--model local-gateway/...`)은 되지만, 이 프로바이더가 낀 프로필은 전부 활성화 실패한다.**

원인 (GJC 0.10.1 `src/config/model-registry.ts`):

```ts
// keyless 프로바이더는 kNoAuth 센티널을 반환하고,
if (this.#keylessProviders.has(provider) && !this.authStorage.hasAuth(provider)) {
    return kNoAuth;
}
// isAuthenticated 는 kNoAuth 를 명시적으로 거부한다.
export function isAuthenticated(apiKey) {
    return Boolean(apiKey) && apiKey !== kNoAuth;
}
```

### 해결: 더미 apiKey

```yaml
providers:
  local-gateway:
    baseUrl: http://127.0.0.1:8086/v1
    apiKey: local-dummy   # ✅ 정적 문자열이면 뭐든 통과. 게이트웨이가 Authorization 헤더를 무시하면 무해
    api: openai-completions
```

게이트웨이가 `Authorization: Bearer local-dummy`를 받아도 무시하는지 curl로 먼저 확인할 것.

> 이는 엔진 쪽 갭으로 볼 여지가 있다(keyless 프로바이더를 프로필에 못 쓰는 설계).
> 상류(gajae-code)에 제보할 가치가 있는 항목.

---

## 4. 함정 ②: SSE `[DONE]` 후 연결을 닫지 않는 게이트웨이는 GJC를 행에 빠뜨린다

**증상**: curl 비스트리밍은 2~3초에 응답하는데, GJC 경유 호출은 무한 대기 후 타임아웃.

```bash
# 비스트리밍 — 즉답 ✅
curl -m 20 -d '{"model":"...","messages":[...]}' http://127.0.0.1:PORT/v1/chat/completions

# 스트리밍 — [DONE] 까지 다 왔는데 연결이 안 끊겨 curl 이 -m 한도까지 매달림 ❌
curl -N -m 60 -d '{"model":"...","messages":[...],"stream":true}' http://127.0.0.1:PORT/v1/chat/completions
```

**원인**: SSE 응답은 `Content-Length`가 없다. 게이트웨이가 HTTP/1.1 keep-alive로 동작하면서
`data: [DONE]` 송신 후 소켓을 닫지 않으면, 스트림 종료를 EOF로 판정하는 클라이언트(GJC 포함)는
끝을 알 수 없어 매달린다.

**해결** (Python `http.server` 계열 게이트웨이 기준 — `BaseHTTPRequestHandler`):

```python
def _stream_completion(self, ...):
    try:
        ...
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        # SSE 는 Content-Length 가 없어 keep-alive 로는 클라이언트가 끝을 모른다.
        # 스트림 종료 후 반드시 연결을 닫는다.
        self.close_connection = True
```

다른 프레임워크도 원리는 같다: **SSE 응답이 끝나면 연결을 닫거나(`Connection: close`),
chunked 인코딩을 올바르게 종료하라.**

---

## 5. 치환 프로필 예제

전체 파일: [`profiles/adapted-profiles.example.yml`](./profiles/adapted-profiles.example.yml)

```yaml
profiles:
  daily-adapted:                       # ★ 원본 daily 치환 — 평소 기본
    required_providers: [anthropic, openai-codex, local-gateway]
    model_mapping:
      default:   anthropic/claude-opus-4-8:medium
      executor:  openai-codex/gpt-5.6-terra:high
      planner:   openai-codex/gpt-5.6-sol:high
      architect: local-gateway/gemini-3-pro
      critic:    local-gateway/gemini-3-pro     # 본체(Anthropic)와 cross-family
```

수록 번들 5종: `daily-adapted` · `coding-sprint-adapted` · `cyber-cop-adapted` ·
`llm-council-adapted`(4계열: Anthropic/OpenAI/Google/DeepSeek) · `eco-adapted`.

사용:

```bash
gjc --mpreset daily-adapted            # 이번 세션만
gjc --mpreset daily-adapted --default  # 영구 (주의: bare gjc 동작이 바뀜)
```

xai·Fable credits 전제 번들(`dream-team`·`ultimate-*`·`escalation`)은 해당 인증 확보 전엔 치환 불가로 남겨둔다.

---

## 6. 검증 절차 — 4단계

원본 가이드의 "Reply exactly: OK" 셀렉터 검증만으로는 부족하다. **서브에이전트 좌석은 툴콜이 생명**인데,
그건 `--no-tools` 검증에 안 잡힌다. 4단계로 검증하라:

```bash
# ① 프로필 로스터 등록 확인 (API 호출 없음)
gjc --mpreset __nope__ -p --no-session --no-tools "x"

# ② 활성화 + 본체 실호출 (required_providers 인증 + 5좌석 셀렉터 해석 검증)
gjc --mpreset daily-adapted -p --no-session --no-tools "Reply exactly: OK"

# ③ 치환 좌석별 툴콜 스모크 — 게이트웨이 툴 변환층까지 검증
mkdir -p /tmp/seat-smoke && cd /tmp/seat-smoke && echo "MAGIC_TOKEN=7f3a9" > probe.txt
gjc -p --no-session --model local-gateway/gemini-3-pro \
  "Use your read tool to read probe.txt in the current directory and reply with only the value of MAGIC_TOKEN."
# → "7f3a9" 가 나오면 read 툴 라운드트립 성공

# ④ 게이트웨이 스트림 종료 확인 (함정 ② 진단)
time curl -sN -m 30 -d '{"model":"...","messages":[{"role":"user","content":"hi"}],"stream":true}' \
  http://127.0.0.1:PORT/v1/chat/completions | tail -c 40
# [DONE] 후 즉시 종료돼야 정상. -m 한도까지 매달리면 함정 ② 참조.
```

---

## 7. 벤치마크로 더 최적화해야 하나? — 원본 신뢰의 경계

**절반만 신뢰하라.** 무엇이 이전되고 무엇이 안 되는지 구분해야 한다.

### 원본 근거가 그대로 이전되는 것

- **그대로 쓰는 좌석** (anthropic Opus, openai-codex gpt-5.6 계열): 원본의 셀렉터 실호출 그린 +
  공개 벤치마크 근거가 동일 프로바이더 경로로 이전된다.
- **설계 원칙** (강본체 / cross-family critic / 실패신호 기반 effort 에스컬레이션): 벤더 무관.

### 이전되지 **않는** 것 — 치환 좌석

- 원본의 `gemini-3.1-pro` 벤치 수치는 **게이트웨이 경유 다른 모델**(예: gemini-3-pro)에 적용 안 됨.
  게이트웨이는 effort 접미사 미지원, `maxTokens` 캡, 툴콜 변환층 등 자체 특성이 있다.
- grok→DeepSeek critic 치환도 마찬가지 — 다만 원본 스스로 grok critic 좌석에 "critic-특화 근거 0건"을
  인정했으므로, 잃는 것은 '검증된 우위'가 아니라 계열 다양성뿐이다(이건 유지됨).

### 그럼 자체 벤치마크 스위트를 돌려야 하나? — **아니다. ROI가 안 나온다.**

- **위임은 드물다.** 실측(14일, 세션 142개): task 위임이 발생한 세션은 **~7%**.
  나머지 93%는 본체(default) 혼자 처리한다. 서브에이전트 좌석을 벤치마크로 미세조정해도
  체감 품질의 대부분은 본체 좌석이 결정한다 — 원본의 "본체는 절대 양보 불가" 원칙의 실측 재확인.
- 소규모 자체 E2E 벤치는 프런티어 모델 간 실제 격차보다 **노이즈가 크다** (n이 작을수록 순위가 뒤집힌다).
- 원본의 근거도 E2E 오케스트레이션 벤치마크가 아니라 **공개 벤치 priors + 셀렉터 실호출**이다.
  같은 수준의 근거는 §6 검증 절차로 이미 확보된다.

### 권장 대체 루프 (벤치마크 스위트 대신)

1. **기능 스모크** (§6-③) — 치환 좌석이 역할 수행에 필요한 기능(툴콜·장문맥)을 실제로 하는지.
2. **실패신호 기반 교체** — 특정 역할이 반복 실패하면 그 좌석만 상향/교체. 원본의 effort 사다리 철학과 동일.
3. **사용 텔레메트리** — 세션 로그에서 위임 빈도·실패 패턴을 주기 점검. 위임률이 유의미하게 오르면
   그때 좌석 최적화의 ROI가 생긴다.

---

## 라이선스 · 출처

- 이 문서: [CC BY 4.0](./LICENSE)
- 원본 카탈로그·설계 원칙: [project820/gjc-multivendor-setup-guide](https://github.com/project820/gjc-multivendor-setup-guide) (CC BY 4.0) — 좌석표·번들 구조를 파생·치환함
- GJC 엔진: [Yeachan-Heo/gajae-code](https://github.com/Yeachan-Heo/gajae-code) — 코드 인용은 0.10.1 기준
