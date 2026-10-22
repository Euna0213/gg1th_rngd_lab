# gg1th_rngd_lab

FuriosaAI **RNGD** NPU 실습 저장소입니다.
이 문서는 실습을 시작하기 전에 필요한 **환경 셋팅** 절차를 다룹니다.
https://furiosa.ai/rngd
https://developer.furiosa.ai/latest/en/get_started/furiosa_llm.html
---

## 1. 실습 환경

| 항목 | 버전 / 내용 |
|---|---|
| NPU | FuriosaAI RNGD |
| OS | Ubuntu 22.04 (Linux 6.8) |
| Python | 3.12 (`.python-version`) |
| 패키지 관리자 | [uv](https://docs.astral.sh/uv/) 0.13 이상 |
| furiosa-llm | v2026.4.0 |
| furiosa-smi | 2026.1.1 |

> `furiosa-llm`, `furiosa-smi`는 실습 서버에 시스템 전역으로 미리 설치되어 있습니다.
> (`/usr/local/bin/furiosa-llm`, `/usr/bin/furiosa-smi`)

### 1-1. Furiosa RNGD 위한 실습환경 구성
노션 문서 참고
```
https://app.notion.com/p/RNGD_SSH_uv_-fff1c1324de582768e6a81605dd5418a?source=copy_link
```
동일한 내용 저장되어 있음 : docs/RNGD_SSH_uv_init_.pdf

---

## 2. github 연결 및 저장소 clone
### 2-1. github 연결
노션문서 참고
```
https://app.notion.com/p/github-7141c1324de583b0a5de0110c6521d5b?source=copy_link
```
### 2-2. github 저장소 clone
```bash
cd ~
git clone git@github.com:magpia000/gg1th_rngd_lab.git rngd-lab
cd rngd-lab
```
---

## 3. Python 가상환경 구성
### 3-1. 가상환경 만들기
```
uv init --bare --python 3.12 --pin-python 
```

### 3-2. 의존성 설치
`pyproject.toml`과 `uv.lock`에 정의된 의존성으로 `.venv`를 생성합니다.

```bash
uv sync
```

설치되는 주요 패키지

| 패키지 | 용도 |
|---|---|
| `httpx`, `requests` | furiosa-llm API 서버 호출 |
| `numpy`, `pandas` | 결과 데이터 처리 |

### 3-3. 가상환경 활성화
선택 사항입니다. `uv run`을 쓰면 생략할 수 있습니다.

```bash
source .venv/bin/activate
```

---

## 4. 환경 확인

### 4-1. Python 환경

```bash
uv run python check_env.py
```

출력 예시

```
=== RNGD 실습환경 확인 ===
사용자: std2
홈 디렉터리: /home/std2
Python 버전: 3.12.x
Python 실행 경로: /home/std2/rngd-lab/.venv/bin/python
프로젝트 위치: /home/std2/rngd-lab
```

`Python 실행 경로`가 프로젝트의 `.venv`를 가리키는지 확인합니다.

### 4-2. NPU 장치

```bash
furiosa-smi info
```

```
+------+--------+-------------------+---------+---------+--------------+
| Arch | Device | Firmware          | Temp.   | Power   | PCI-BDF      |
+------+--------+-------------------+---------+---------+--------------+
| rngd | npu7   | 2026.4.0, 93d67f3 | 33.90°C | 38.00 W | 0000:c4:00.0 |
+------+--------+-------------------+---------+---------+--------------+
```

할당된 RNGD 장치가 보이면 정상입니다. 실시간 사용량은 다음으로 확인합니다.

```bash
watch -n 1 furiosa-smi status
```

### 4-3. furiosa-llm

```bash
furiosa-llm version
```

---

## 5. 디렉터리 구조

```
rngd-lab/
├── README.md
├── pyproject.toml        # 프로젝트 의존성
├── uv.lock               # 의존성 잠금 파일
├── .python-version       # Python 3.12
├── check_env.py          # 실습 환경 확인 스크립트
├── docs/                 # 환경 구성 문서 (SSH, uv)
├── day1_npu_chat_test/   # Day 1: 모델 서빙과 API 호출
├── day2_furiosa_sdk/     # Day 2: Furiosa SDK 직접 추론
├── day3_npu_api/         # Day 3: OpenAI 호환 API 서버와 챗봇
├── day4_benchmark_test/  # Day 4: 서빙 성능 측정
└── day4_fxb_ex/          # Day 4 보충: FXB CLI
```

---

## 6. 실습 흐름

모델을 NPU에 올리는 방법을 단계적으로 배운다.
**서버로 서빙하고 호출 → SDK로 직접 추론 → API 서버와 챗봇 → 성능 측정**
순서로 진행한다. 각 폴더의 `DAY0N_실습내용.md`에 자세한 절차가 있다.

| Day | 폴더 | 주제 | 핵심 |
|---|---|---|---|
| 1 | `day1_npu_chat_test` | 모델 서빙과 API 호출 | `furiosa-llm serve`로 서버를 띄우고 `curl`·`requests`로 호출 |
| 2 | `day2_furiosa_sdk` | Furiosa SDK 직접 추론 | Python `LLM` 클래스로 모델을 직접 로딩해 추론 |
| 3 | `day3_npu_api` | API 서버와 챗봇 | OpenAI 호환 서버, SSH 터널, Streaming·Multi-turn 챗봇 |
| 4 | `day4_benchmark_test` | 서빙 성능 측정 | 동시성·Prefix Caching 벤치마크, 결과 시각화 |
| 4 보충 | `day4_fxb_ex` | FXB CLI | 컴파일된 NPU 실행 번들(FXB) 조회·검증·빌드 |

### Day 1. 모델 서빙과 API 호출 (`day1_npu_chat_test`)

1. `furiosa-llm serve furiosa-ai/Qwen3-8B-FP8`로 Qwen3-8B 모델 서버를 실행한다.
   (`--reasoning-parser qwen3`, Thinking 모드 비활성화)
2. 다른 터미널에서 `watch -n 1 furiosa-smi status`로 NPU 사용량을 관찰한다.
3. `curl`로 `/v1/chat/completions`를 호출해 추론을 확인한다.
4. 이미지 입력 모델 `Qwen3-VL-4B-Instruct`로 같은 과정을 반복한다.
5. `npu_chat_qwen3-8b.py`, `npu_chat_qwen3-VL-4b.py`로 Python에서 호출한다.
6. `memory_budget.py`로 파라미터 수와 비트 수에 따른 가중치 크기 이론값을 계산한다.

### Day 2. Furiosa SDK 직접 추론 (`day2_furiosa_sdk`)

서버 없이 Python 프로세스가 NPU에 모델을 직접 로딩한다.
`with LLM(...)` 블록을 벗어나면 NPU 자원이 반환되는 패턴이 핵심이다.

```bash
uv run 00_preflight.py                                         # 환경·장치 점검
uv run 01_first_inference.py                                   # 첫 채팅 추론
uv run 02_batch_inference.py --batch-size 1 --output A_batch1.jsonl   # 배치 추론
uv run 02_batch_inference.py --batch-size 3 --output B_batch3.jsonl
uv run 03_sampling_experiment.py                               # 프롬프트·샘플링 비교
```

한 스크립트가 끝나 NPU를 반환한 뒤 다음 스크립트를 실행한다.

### Day 3. API 서버와 챗봇 (`day3_npu_api`)

모델을 서버에 한 번 올리고 HTTP API로 질문한다.

1. `01_check_server.sh`로 카드 점유, 서빙 옵션, 포트를 점검한다.
2. `02_run_llm_server.sh`로 조별 카드에 API 서버를 실행한다.
3. SSH 포트 포워딩(`-L`)으로 PC에서 서버에 연결한다.
4. `03_api_client.py`: 모델 목록 조회와 일반 Chat Completion
5. `04_streaming_chat.py`: Single-turn Streaming 챗봇
6. `05_multiturn_chat.py`: 클라이언트가 대화 이력을 관리하는 Multi-turn 챗봇 (`/reset`, `/exit`)

### Day 4. 서빙 성능 측정 (`day4_benchmark_test`)

Day 3 서버를 그대로 사용해 성능을 측정한다.

```bash
bash 01_check_npu.sh                  # 카드·서버·메트릭 확인
uv run python 02_check_metrics.py     # /metrics의 Counter·Gauge·Histogram 확인
uv run python 03_concurrency_benchmark.py --repeats 3 --max-tokens 64
uv run python 04_prefix_cache_benchmark.py --mode off --repeats 3   # OFF 서버
uv run python 04_prefix_cache_benchmark.py --mode on  --repeats 3   # ON 서버
uv run python 05_visualize_results.py                # summary.csv, 그래프 3개
uv run streamlit run 06_dashboard.py                 # Streamlit 대시보드
```

- **동시성:** 동시 요청 1·2·4·8을 각 3회 보내 지연시간(TTFT, E2E)과 처리량을 잰다.
- **Prefix Caching:** 서버를 `--no-enable-prefix-caching`으로 한 번, 기본값으로 한 번 띄워 같은 공통 문맥 요청의 TTFT를 비교한다. ON에서 Hit Counter가 늘었는지 함께 확인한다.
- 서버 `/metrics`의 Counter 증가량으로 실제 토큰 수를 계산한다.

### Day 4 보충. FXB CLI (`day4_fxb_ex`)

FXB(Furiosa Executable Bundle)는 모델 가중치와 별개인 컴파일된 NPU 실행 번들이다.

1. `fxb cache ls`로 캐시를 조회하고 공개된 FXB를 내려받는다.
2. `fxb show`, `fxb inspect`, `fxb check`로 메타데이터와 호환성을 확인한다.
3. 호환 FXB로 `furiosa-llm serve`를 실행해 API를 검증한다.
4. `fxb build --dry-run`으로 컴파일 계획을 확인한다. (실제 빌드는 선택)
5. `hf_fxb_list.py`로 Hugging Face의 `furiosa-ai` 모델 중 `.fxb`가 있는 것을 조회한다.
