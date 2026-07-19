# 3부 — 우리 환경 적응 가이드 (본론)

> 검증 환경: **GJC 0.10.1**, 2026-07-19 실호출. 엔진 코드 인용은 해당 버전 기준.

## 3-1. 왜 별도 가이드가 필요했나 — 사용 에이전트(벤더 구성)가 다르다

원본 가이드는 5구독 전제다. 우리 환경은 이랬다:

| 원본 전제 | 우리 환경 | 대응 |
|---|---|---|
| `anthropic` OAuth | 동일 (구독 OAuth) | ✅ 그대로 |
| `openai-codex` OAuth | 동일 (구독 OAuth) | ✅ 그대로 |
| `google-antigravity` OAuth | 직접 로그인 없음 — 대신 **로컬 OpenAI-호환 게이트웨이**가 같은 구독을 REST로 중계 | 🔁 `local-gateway` 커스텀 프로바이더로 치환 |
| `xai` API 키 (critic) | 키 없음 | 🔁 **제4계열 direct API**(DeepSeek)로 치환 |
| `opencode-go` API 키 | 없음 — DeepSeek direct API 사용 | 🔁 `deepseek` 프로바이더로 치환 |

GJC 프로필 활성화는 fail-closed라([2부 참조](02-multivendor-overview.md)) 원본 10개 번들은 이 구성에서 **0/10 활성화**된다.
치환 원칙은 단순하다: **설계 3원칙(강본체·cross-family critic·역할축)은 유지하고 벤더만 갈아 끼운다.**
결과물이 [`profiles/adapted-profiles.example.yml`](../profiles/adapted-profiles.example.yml) — 5개 번들(`daily-adapted` 등)이다.

## 3-2. 밟은 지뢰 ① — `auth: none` 프로바이더는 프로필을 통과하지 못한다

로컬 게이트웨이는 인증이 필요 없으니 자연스럽게 `auth: none`으로 선언하게 되는데,
그러면 **개별 모델 호출은 되지만 그 벤더가 낀 프로필은 전부 활성화 실패**한다.

원인 (엔진 `src/config/model-registry.ts`): keyless 프로바이더는 `kNoAuth` 센티널을 반환하고,
`isAuthenticated()`가 이를 명시적으로 거부한다.

**해법**: 더미 정적 apiKey를 준다. 게이트웨이가 `Authorization` 헤더를 무시하는지 curl로 먼저 확인.

```yaml
providers:
  local-gateway:
    baseUrl: http://127.0.0.1:8086/v1
    apiKey: local-dummy      # auth: none 대신 — 값은 아무거나
    api: openai-completions
```

## 3-3. 밟은 지뢰 ② — SSE 스트림을 닫지 않는 게이트웨이는 GJC를 행에 빠뜨린다

**증상**: curl 비스트리밍은 3초 응답, GJC 경유는 무한 대기 후 타임아웃.

**원인**: SSE 응답은 `Content-Length`가 없다. 게이트웨이가 HTTP/1.1 keep-alive 상태에서
`data: [DONE]` 을 보내고도 소켓을 안 닫으면, 스트림 끝을 EOF로 판정하는 클라이언트는 영원히 기다린다.

**해법** (Python `BaseHTTPRequestHandler` 계열 기준):

```python
finally:
    # SSE 는 Content-Length 가 없어 keep-alive 로는 클라이언트가 끝을 모른다.
    self.close_connection = True
```

**진단법**:

```bash
time curl -sN -m 30 -d '{"model":"...","messages":[{"role":"user","content":"hi"}],"stream":true}' \
  http://127.0.0.1:PORT/v1/chat/completions | tail -c 40
# [DONE] 후 즉시 종료 = 정상. -m 한도까지 매달림 = 이 버그.
```

## 3-4. 검증 절차 — 4단계

원본의 "Reply exactly: OK" 셀렉터 검증만으로는 부족하다. **서브에이전트 좌석은 툴콜(도구 호출)이 생명**인데
그건 `--no-tools` 검증에 안 잡힌다.

```bash
# ① 프로필 등록 확인 (API 호출 없음 — 틀린 이름 트릭)
gjc --mpreset __nope__ -p --no-session --no-tools "x"

# ② 활성화 + 본체 실호출 (인증 + 5좌석 셀렉터 해석 검증)
gjc --mpreset daily-adapted -p --no-session --no-tools "Reply exactly: OK"

# ③ 치환 좌석별 툴콜 스모크 (게이트웨이 툴 변환층까지)
mkdir -p /tmp/seat-smoke && cd /tmp/seat-smoke && echo "MAGIC_TOKEN=7f3a9" > probe.txt
gjc -p --no-session --model local-gateway/gemini-3-pro \
  "Use your read tool to read probe.txt in the current directory and reply with only the value of MAGIC_TOKEN."
# → "7f3a9" 가 나오면 read 툴 라운드트립 성공

# ④ 게이트웨이 스트림 종료 확인 (§3-3 진단)
```

## 3-5. MLBO 개요 — 좌석 배치를 "더" 최적화해야 하나?

**MLBO = Multi-Agent LLM Bayesian Optimization.** 역할별 모델 배치(좌석표)를 사람의 감이 아니라
**베이지안 최적화**로 찾는 접근이다 (대표 연구: [MALBO, arXiv 2511.11788](https://arxiv.org/abs/2511.11788)).

비전공자용 요약 — "베이지안"이 뭐냐면:

> 미지의 함수(어떤 좌석표가 얼마나 좋은가)를 **확률적 믿음**으로 다루고, 비싼 실험을 한 번 할 때마다
> 베이즈 정리로 그 믿음을 갱신하는 것. 맛집 탐방과 같다 — 몇 번 먹어본 경험으로 "이 동네 이런 가게가
> 맛있을 확률"을 갱신하고, 다음 방문지는 *기대 맛 + 안 가본 정도 보너스*가 최대인 곳을 고른다.
> 전수조사(grid search)나 아무 데나 찍기(random search)보다 실험 횟수가 훨씬 적게 든다.

좌석표 문제에 딱 맞는 이유: 평가 1회가 비싸고(구성 하나 = 벤치 수십 회 실행 = 토큰 비용), 기울기가 없고,
변수 대부분이 범주형(모델 선택)이다. MALBO는 랜덤 서치 대비 구성 비용 45%+ 절감,
역할특화 이질 팀으로 최대 65.8% 비용 절감을 보고했다.

**그래서 우리도 돌려야 하나? — 대부분은 아니다.** 실측 근거:

- 우리 사용 로그(14일, 세션 142개)에서 서브에이전트 위임이 발생한 세션은 **~7%**.
  나머지 93%는 본체 혼자 처리한다. 좌석 미세조정의 ROI 상한이 그만큼 낮다.
- 소규모 자체 벤치는 프런티어 모델 간 실제 격차보다 노이즈가 크다.
- 모델 카탈로그가 주 단위로 바뀌는 시대에 최적점의 유통기한이 짧다.

**권장 루프**: 기능 스모크(§3-4) → 실패신호 기반 좌석 교체 → 위임률이 유의미해지면 그때 MALBO식 파레토 탐색.
단, **자동 채점 가능한 대량 배치 파이프라인**(번역·리뷰 봇 등)이라면 얘기가 다르다 — 그건 검증된 절감 수단이다.

이 관점을 기리며(그리고 기억하기 쉽게) 모드 전환 커맨드 이름을 `/mlbo`로 지었다 →

## 3-6. `/mlbo` — 세션 안에서 모드 전환하는 슬래시 커맨드

`gjc --mpreset`은 세션을 새로 열어야 한다. 작업 중에 "지금부터 리뷰 모드"로 갈아타고 싶다면?

```text
> /mlbo                        ← 모드 목록 + 현재 상태
> /mlbo coding-sprint-adapted  ← 자동완성 드롭다운에 설명 각주 표시
Mode activated: coding-sprint-adapted
  default   anthropic/claude-opus-4-8:medium
  executor  anthropic/claude-opus-4-8:high
  planner   openai-codex/gpt-5.6-sol:high
  architect local-gateway/gemini-3-pro
  critic    openai-codex/gpt-5.6-terra:high
> /mlbo off                    ← 영구 기본 프로필로 복귀
```

상태바의 본체 모델·effort 표시가 즉시 바뀌는 것으로 적용을 확인할 수 있다.

### ⚠ 왜 "로컬 엔진 패치"인가 — 정직한 설명

GJC 0.10.x~0.11.x는 사용자 확장 표면이 **의도적으로 격리(quarantine)**돼 있다:

- `~/.gjc/agent/extensions/` 파일시스템 확장 — 세션에서 로드되지 않음 (SDK 주석: *"Extension/module discovery is quarantined"*)
- 플러그인 번들(`gajae-plugin.json`) — 훅에서 `registerCommand`가 **명시적 거부** (*security_policy*), 신규 top-level 슬래시 커맨드 금지
- 0.11.2 CHANGELOG도 동일 정책 유지 확인

따라서 커스텀 슬래시 커맨드는 현재로선 **`builtin-registry.ts` 로컬 패치**가 유일한 경로다.
[`patches/mlbo-slash-command/`](../patches/mlbo-slash-command/)가 그 구현이다:

```bash
# 설치 (멱등 — 재실행 안전, 자동 백업)
patches/mlbo-slash-command/apply-mlbo.sh
# gjc update 후에는 패키지가 덮어써지므로 다시 실행
```

스크립트가 하는 일: ① `activateModelProfile` import 추가, ② 센티널로 감싼 커맨드 블록을
`/effort` 커맨드 앞에 삽입, ③ 백업 생성. 커맨드 본체는 엔진의 공식 프로필 활성화 API
(`activateModelProfile`)를 그대로 호출하므로 CLI `--mpreset`과 의미가 동일하다.

> 업스트림에 "프리셋 활성화 텍스트 커맨드(/mpreset)" 기능 요청을 올릴 가치가 있는 갭이다.
> 엔진이 공식 지원하면 이 패치는 삭제하면 된다.

---

**부록**: [프로필 예제 YAML](../profiles/adapted-profiles.example.yml) · [패치 소스](../patches/mlbo-slash-command/)
