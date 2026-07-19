# 2부 — gjc-multivendor-setup-guide 개요

> **원본 주소: https://github.com/project820/gjc-multivendor-setup-guide** (v2.0.1, CC BY 4.0)
> 5개 구독(claude·gpt·grok·gemini·opencode go)을 역할별로 쪼개 쓰는 검증된 프로필 카탈로그다.
> 이 문서는 그 핵심만 요약한다. 세부 근거·벤치마크·검증 매트릭스는 원본을 읽어라.

## 왜 멀티벤더인가 — 한 문장

**모든 걸 제일 잘하는 단일 모델은 없다.** 코딩 1위, 장기 계획 1위, 장문맥 리뷰 1위가 각각 다른 벤더라서,
역할마다 그 축의 1위를 앉히면 같은 돈으로 더 좋은 결과가 나온다.

## 설계 3원칙 (이건 벤더가 바뀌어도 유지된다)

1. **본체(default)는 절대 양보 불가** — 일상 작업 대부분은 본체 혼자 처리한다. 본체를 싸구려 모델로 내리면
   전체 체감 품질이 무너진다. 원본은 Anthropic 플래그십(Opus/Fable) 고정.
2. **critic은 cross-family** — 검증자는 본체와 *다른 벤더*여야 한다. 같은 회사 모델은 같은 실수를
   좋게 봐주는 경향(self-preference bias)이 있다.
3. **effort는 실패했을 때만 올린다** — `medium→high`는 점수 +1~2에 토큰 수십 배. 선제적 `max`는 낭비.

## 카탈로그 구조 — 4계층 10번들

| Tier | 번들 | 용도 |
|---|---|---|
| Core | ⭐ daily / 🏎 coding-sprint / 🚨 cyber-cop | 평소 / 구현 스프린트 / PR 리뷰·보안 감사 |
| Premium | 🏆 ultimate-opus / 🧪 ultimate-sol / 🔥 dream-team | 정확성 최우선 실험군 |
| Workflow | 🏛 llm-council / 🛡 escalation | 다계열 합의 / 실패 시 구원투수 |
| Specialized | 💸 eco / 🗺 monorepo | 저단가 대량 작업 / 초대형 코드베이스 |

원클릭 설치(`install.sh`)가 이 번들들을 `~/.gjc/agent/models.yml`에 병합하고 기본 프로필을 `daily`로 잡는다.

## 원본이 전제하는 5구독

| 구독 | provider-id | 인증 |
|---|---|---|
| Claude | `anthropic` | 구독 OAuth |
| ChatGPT | `openai-codex` | 구독 OAuth |
| Gemini (Google AI Pro/Ultra) | `google-antigravity` | 구독 OAuth |
| Grok | `xai` | API 키 |
| OpenCode Go | `opencode-go` | API 키 |

**⚠ 여기가 함정이다.** GJC의 프로필 활성화는 fail-closed다 — 프로필이 요구하는 벤더 중
하나라도 인증이 없으면 그 프로필은 통째로 죽는다. 10개 번들 전부가 `google-antigravity`/`xai`/`opencode-go`
중 최소 하나를 요구하므로, **이 셋이 없는 환경에서는 설치해도 0개가 동작한다.**

그 상황을 해결하는 것이 이 리포의 본론이다 →

---

**다음 → [3부: 우리 환경 적응 가이드](03-adaptation.md)** — 좌석 치환 · 엔진 함정 · `/mlbo`
