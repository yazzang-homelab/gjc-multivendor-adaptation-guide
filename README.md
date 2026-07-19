<div align="center">

<img src="assets/gajae.svg" alt="GJC 멀티벤더 오케스트레이션 — 가재 마스코트" width="100%">

# 🦞 GJC 멀티벤더 오케스트레이션 가이드

**AI 코딩 에이전트에게 "일 종류마다 다른 AI 모델"을 자동 배치하는 방법** —
표준 5구독 구성이 아닌 환경(로컬 게이트웨이·direct API·구독 일부 없음)에서도 되게 만드는 실전 기록.

[![GJC](https://img.shields.io/badge/engine-Gajae%20Code%20(GJC)-e23?style=flat-square)](https://github.com/Yeachan-Heo/gajae-code)
[![Verified](https://img.shields.io/badge/verified-GJC%200.10.1%20·%202026--07--19-brightgreen?style=flat-square)](docs/03-adaptation.md#검증-절차--4단계)
[![Upstream guide](https://img.shields.io/badge/derived%20from-gjc--multivendor--setup--guide-blue?style=flat-square)](https://github.com/project820/gjc-multivendor-setup-guide)
![License](https://img.shields.io/badge/license-CC%20BY%204.0-lightgrey?style=flat-square)

**📖 웹으로 읽기: [GitHub Pages](https://yazzang-homelab.github.io/gjc-multivendor-adaptation-guide/)** (GitHub Actions가 자동 빌드)

</div>

---

## 이 리포는 뭘 하나

AI 코딩 에이전트는 한 세션 안에서도 여러 "역할"을 쓴다 — 계획 짜는 역할, 코드 쓰는 역할, 결과를 비판하는 역할.
역할마다 **가장 잘하는 AI 모델이 다르다.** 그래서 역할별로 다른 벤더의 모델을 앉히는 게 "멀티벤더 오케스트레이션"이다.

문제는: 기존 가이드가 **특정 5개 구독을 모두 가진 사람** 기준이라는 것.
이 리포는 **구성이 다른 환경에서 좌석을 치환해 살리는 법**과, 그 과정에서 실제로 밟은 지뢰들, 그리고
세션 안에서 모드를 전환하는 **`/mlbo` 슬래시 커맨드**까지 정리한다.

## 📚 목차 — 3부 구성

| 부 | 문서 | 누구에게 |
|---|---|---|
| **1부** | [GJC 개요 및 설치](docs/01-gjc-intro.md) | GJC가 처음인 사람 — 뭔지, 왜 쓰는지, 어떻게 까는지 |
| **2부** | [멀티벤더 셋업 가이드 개요](docs/02-multivendor-overview.md) | 원본 [gjc-multivendor-setup-guide](https://github.com/project820/gjc-multivendor-setup-guide)의 핵심을 10분 요약 |
| **3부** | [우리 환경 적응 가이드](docs/03-adaptation.md) | **이 리포의 본론** — 벤더 구성이 다를 때의 좌석 치환 + 엔진 함정 2건 + `/mlbo` 커맨드 + MLBO(베이지안 최적화) 관점 |

부록: [치환 프로필 예제 YAML](profiles/adapted-profiles.example.yml) · [`/mlbo` 엔진 패치](patches/mlbo-slash-command/)

## ⚡ 3줄 요약

```bash
# 1. 프로필을 ~/.gjc/agent/models.yml 에 병합 (profiles/ 예제 참조)
# 2. 검증: 활성화 + 실호출 + 툴콜 스모크 (3부 §검증)
gjc --mpreset daily-adapted -p --no-session --no-tools "Reply exactly: OK"
# 3. 세션 안 모드 전환 (patches/ 의 로컬 패치 적용 후)
#    > /mlbo coding-sprint-adapted
```

## 라이선스 · 출처

- 이 문서: [CC BY 4.0](LICENSE)
- 번들 카탈로그·설계 원칙: [project820/gjc-multivendor-setup-guide](https://github.com/project820/gjc-multivendor-setup-guide) (CC BY 4.0) 파생
- 엔진: [Yeachan-Heo/gajae-code](https://github.com/Yeachan-Heo/gajae-code) — 코드 인용은 0.10.1 기준
