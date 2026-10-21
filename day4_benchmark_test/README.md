# DAY 4 · RNGD LLM Serving 성능 측정 실습

## 목적과 실행 위치

DAY 3에서 구축한 조별 `furiosa-ai/Qwen3-8B-FP8` 서버를 재사용한다. 각 조는 독립 RNGD 카드 1개와 SSH 계정 1개를 사용한다. `01_check_npu.sh`와 서버 시작·재시작은 Linux 서버에서, `02`~`05` Python 파일은 DAY 3 가상환경을 사용하는 Windows PC에서 실행한다. 한 조의 서버에는 측정 중 다른 API 클라이언트를 붙이지 않는다. 실제 장비 출력은 이 자료 제작 시점에 확인하지 못했으므로 **실제 장비 검증 필요**다.

| 파일 | 목적 | 실행 위치 | 성공 증거 |
|---|---|---|---|
| `01_check_npu.sh` | 카드·서버·메트릭 확인 | Linux | 배정 장치, 모델 목록, 메트릭 이름 |
| `02_check_metrics.py` | 메트릭 종류와 값 확인 | Windows | Counter·Gauge·Histogram 값 |
| `03_concurrency_benchmark.py` | 동시 1·2·4·8, 각 3회 | Windows | `concurrency_*.csv` |
| `04_prefix_cache_benchmark.py` | OFF/ON 각 3회 순차 실험 | Windows | `prefix_off.csv`, `prefix_on.csv` |
| `05_visualize_results.py` | 실제 CSV 분석·그림 3개 | Windows | `summary.csv`, PNG 3개 |

## 0. 조별 값 준비

DAY 3 기록지의 `npu:X`, 서버 포트, 모델 ID와 버전을 가져온다. FXB/모델 파일은 미리 준비한다. 카드 번호는 PCI-BDF와 `furiosa-smi info`로 다시 대조한다. 모델 로딩과 서버 재시작은 요청 지연시간에 포함하지 않는다.

Linux SSH 터미널에서 `furiosa-llm --version`, `furiosa-llm serve --help`, `furiosa-smi info`, `furiosa-smi ps`를 확인한다. 설치 버전에서 아래 옵션이 보이지 않으면 실행을 멈추고 강사에게 버전 차이를 알린다. 다른 조의 프로세스를 종료하지 않는다.

```bash
export TEAM_NPU_DEVICE=npu:0       # 예시: 반드시 배정표 값으로 교체
export TEAM_SERVER_PORT=18001      # 예시: 반드시 조별 배정 포트로 교체
export MODEL_ID=furiosa-ai/Qwen3-8B-FP8
bash 01_check_npu.sh
```

Windows PowerShell에서 DAY 3과 같은 SSH 터널을 별도 창에 유지한다. Windows의 `127.0.0.1`은 Linux 서버의 주소가 아니므로 터널의 **로컬 포트**에 접속한다.

```powershell
ssh -N -L 18001:127.0.0.1:18001 계정@서버주소
```

위 양쪽 18001은 예시다. 왼쪽은 Windows에서 비어 있는 포트, 오른쪽은 Linux 서버 포트다. 강사가 제공한 실제 값으로 바꾼다. `Copy-Item .env.example .env` 후 `OPENAI_BASE_URL=http://127.0.0.1:로컬포트/v1`, `MODEL_ID`를 수정한다. 인증 정책이 있으면 강사가 제공한 키를 환경변수나 로컬 `.env`에만 입력한다. `.env.example`의 `EMPTY`는 인증이 없는 교육용 서버의 SDK 인자이며 실제 비밀키가 아니다. `.env`를 공유하거나 ZIP에 넣지 않는다.

DAY 3 가상환경을 활성화하고 같은 디렉터리에서 설치한다.

```powershell
python -m pip install -r requirements.txt
python 02_check_metrics.py
```

`/v1/models`에 지정 모델이 나오고 `/metrics`에 `furiosa_llm_generation_tokens_total`이 있어야 실습을 진행한다. 출력 숫자는 서버마다 다르다.

## 1. 측정 정의

요청 시작 → 첫 HTTP/Streaming 이벤트 → **첫 비어 있지 않은 `delta.content`** → 마지막 이벤트 순서다. 이 코드의 `ttft_client_s`는 요청 시작부터 첫 콘텐츠 수신까지의 클라이언트 시간이고 `e2e_client_s`는 요청 시작부터 스트림 종료까지다. 첫 이벤트는 내용이 없을 수 있어 `first_event_s`를 TTFT로 대체하지 않는다. 서버의 TTFT Histogram은 계측 지점과 네트워크 구간이 달라 클라이언트 값과 정확히 일치하지 않을 수 있다.

`output_tokens_per_s`는 서버 Counter `furiosa_llm_generation_tokens_total`의 측정 전후 차이 ÷ 측정 구간 초다. **전체 서버 출력 처리량**이며 단일 요청의 TPOT(첫 토큰 이후 토큰 간 시간)과 다르다. Streaming `usage.completion_tokens`는 응답에 있을 때만 요청 행에 기록한다. 없으면 빈 칸으로 둔다. Counter 측정 중 서버를 재시작하거나 다른 요청이 들어오면 해당 회차를 폐기한다. `requests_per_s`는 완료 요청 수 ÷ 버스트 구간 초다.

TPOT의 클라이언트 근사는 출력이 2토큰 이상일 때 `(E2E−TTFT)/(출력 토큰 수−1)`이다. 이는 네트워크와 스트림 종료 구간도 포함할 수 있어 서버 ITL과 다르다. 이 실습 코드는 개별 Streaming 이벤트를 토큰으로 오인하지 않기 위해 TPOT를 직접 산출하지 않는다. Prefix CSV의 `output_tokens_per_s`는 순차 단일 요청의 Counter 변화량을 그 요청의 클라이언트 E2E로 나눈 참고값으로, 동시성 실험의 버스트 전체 TPS와 직접 비교하지 않는다.

`furiosa_llm_prefix_cache_hits`와 `...queries`는 **요청 건수가 아니라 캐시된 토큰 수와 조회한 토큰 수**의 Counter라 전후 차이를 읽는다. `...kv_cache_usage_percent`는 이름과 달리 1이 100%인 순간 Gauge다. 예를 들어 0.25는 25%이며 CSV에는 원값 0.25를 기록한다. `..._seconds_sum`과 `..._seconds_count`는 Histogram의 합·관측 수로, 두 시점 차이를 나누면 구간 평균을 추정할 수 있다. `_bucket`은 지연시간 구간별 누적 관측 수다. `02_check_metrics.py`가 유형과 존재 여부를 보여 준다.

## 2. 동시성 실험 · 45분

DAY 3 서버를 켠 상태에서 모델 준비 완료와 터널을 확인한다. 아래 명령은 워밍업 1건을 CSV에서 제외한 뒤 고정 크기의 **버스트**를 실행한다. 동시 요청 1·2·4·8을 각 3회 보내며, 지속적으로 동시 요청 수를 유지하는 부하 시험은 아니다. 프롬프트의 길이는 비슷하게 설계했고, 요청 앞에 고유 식별자를 넣어 공통 접두부 캐시 영향을 줄인다. 이것이 캐시를 완전히 제거한다고 보장하지는 않으므로 Hit Counter 변화도 기록한다.

```powershell
python 03_concurrency_benchmark.py --repeats 3 --max-tokens 64
```

예상 출력 형태: `동시 4 / 반복 2: 평균 E2E [실제값]s, 전체 Output TPS [실제값]`와 CSV 저장 위치가 표시된다. `results/concurrency_runs.csv`에 12행(4조건×3회), `concurrency_requests.csv`에 45행(1+2+4+8=15요청×3회)이 있어야 한다. 응답이 짧게 끝나 실제 생성 토큰 수가 서로 다를 수 있으므로 TPS 해석에는 `output_tokens_total`을 함께 본다. P95는 적은 표본의 최근접 순위값으로 참고만 한다.

핵심 코드: `Barrier`가 요청 시작을 맞추고 `ThreadPoolExecutor`가 병렬 전송한다. `window_s`는 버스트 시작부터 모든 요청 완료까지다. 서버 Counter 차이를 사용하므로 콘솔의 글자 수를 토큰 수로 간주하지 않는다.

## 3. Prefix Caching OFF/ON · 50분

각 조의 서버 프로세스를 정상 종료한 뒤 **같은 카드·같은 모델·같은 포트**로 재시작한다. `--no-enable-prefix-caching`은 공식 비활성화 옵션이다. 2026.4 계열의 기본 설정은 ON이지만 설치 버전과 시작 로그에서 확인한다. 아래 명령은 공식 문서의 Qwen3 서빙 옵션을 사용한다. 터미널 A에서 실행하고 준비 완료를 기다린다.

```bash
# A: OFF 서버
furiosa-llm serve "$MODEL_ID" --devices "$TEAM_NPU_DEVICE" \
  --host 127.0.0.1 --port "$TEAM_SERVER_PORT" \
  --reasoning-parser qwen3 \
  --default-chat-template-kwargs '{"enable_thinking": false}' \
  --no-enable-prefix-caching
```

터미널 B에서 `curl -fsS http://127.0.0.1:${TEAM_SERVER_PORT}/v1/models`와 `/metrics`를 확인한 후 Windows에서 실행한다.

```powershell
python 04_prefix_cache_benchmark.py --mode off --repeats 3 --max-tokens 48
```

OFF 서버를 `Ctrl+C`로 종료하고 카드가 해제되는지 확인한다. 같은 모델을 **비활성화 옵션 없이** 다시 실행한다.

```bash
# B: ON 서버 (해당 버전의 기본 활성화 상태와 로그 확인)
furiosa-llm serve "$MODEL_ID" --devices "$TEAM_NPU_DEVICE" \
  --host 127.0.0.1 --port "$TEAM_SERVER_PORT" \
  --reasoning-parser qwen3 \
  --default-chat-template-kwargs '{"enable_thinking": false}'
```

```powershell
python 04_prefix_cache_benchmark.py --mode on --repeats 3 --max-tokens 48
```

각 모드는 다른 시작 문맥으로 워밍업 1건을 제외하고, 동일한 긴 System Prompt와 질문 4개를 순차로 3회 실행한다. 모드별 12행이 생긴다. `first`는 각 서버 재시작 후 공통 문맥의 첫 요청 한 건, `later`는 후속 요청 11건이다. **ON의 Hit Counter 증가를 확인해야** 캐시 재사용을 말할 수 있다. Hit가 없거나 TTFT가 개선되지 않아도 결과 그대로 기록한다. `--mode`는 CSV 표기만 지정하므로 실제 서버 시작 명령과 로그를 보고서에 남긴다. 서버 로딩·재시작 시간은 요청 측정에서 제외한다. OFF→ON 순서의 시간 경과 효과가 남으므로 결론을 과장하지 않는다.

## 4. 분석 · 20분

```powershell
python 05_visualize_results.py
```

실제 CSV가 없으면 종료하고 임의 숫자를 만들지 않는다. `results/01_throughput_by_concurrency.png`, `02_latency_by_concurrency.png`, `03_prefix_ttft_comparison.png`와 `summary.csv`를 생성한다. 축은 조건과 단위를 표시한다. 평균 막대 오차는 조건별 3회 간 표준편차다. Prefix 막대는 first 1건과 later 11건의 평균이라 표본 수가 다르다. Hit Counter·요청 길이·KV 사용률과 함께 판단한다.

## 5. 결과 기록과 오류 해결

`reports/performance_report_template.md`에 장치 번호·PCI-BDF·SDK 버전·실험 조건·실제 표·그래프 해석·최적화 제안을 채운다. 학생 A는 Linux 서버/장치를, 학생 B는 CSV/분석을 담당한 후 Prefix 실험에서 역할을 교대한다. 두 사람이 모두 실행과 해석을 경험한다.

| 증상 | 확인·조치 |
|---|---|
| 카드가 바쁘다 | `furiosa-smi ps`로 자기 조 서버가 중복 실행 중인지 확인하고 본인 프로세스만 종료한다. |
| Linux `curl` 연결 거부 | 모델 준비 완료 로그, 포트, 서버 프로세스를 확인한다. |
| Windows 연결 거부 | SSH 터널 창, 로컬 포트, `.env`의 `/v1` 경로를 확인한다. |
| 모델 목록 불일치 | `/v1/models`의 실제 ID와 `MODEL_ID`를 맞춘다. |
| Counter가 없다/감소한다 | `/metrics` 노출, SDK 버전, 재시작 여부를 확인하고 해당 회차를 폐기한다. |
| 출력 CSV가 없다 | 벤치마크 완료 여부와 `results/` 쓰기 권한을 확인한다. |
| ON인데 Hit=0 | 같은 System Prompt가 토큰 단위로 일치하는지, 실제 ON 서버인지, 캐시 용량/메트릭을 확인한다. |
| 그래프 단계에서 중단 | 4개 동시성×3회, OFF/ON의 first/later가 모두 있는지 확인한다. |
| 실험이 오래 걸린다 | 강사가 모델과 FXB를 사전 준비한다. 측정 조건을 임의로 줄여 필수 3회를 생략하지 않는다. |

## 근거

- FuriosaAI [LLM Serving](https://developer.furiosa.ai/latest/en/furiosa_llm/furiosa-llm-serve.html): 서빙 CLI, OpenAI 호환 API, `/metrics`.
- FuriosaAI [Prefix Caching](https://developer.furiosa.ai/latest/en/furiosa_llm/prefix-caching.html): 기본 활성화, `--no-enable-prefix-caching`, 동일 접두부 재사용.
- FuriosaAI [Qwen3](https://developer.furiosa.ai/latest/en/furiosa_llm/models/qwen3.html): Qwen3-8B-FP8 모델 및 RNGD 카드 구성.
- FuriosaAI [성능 최적화](https://developer.furiosa.ai/latest/en/furiosa_llm/performance-optimization.html): Batching과 스케줄링.

문서 확인일: 2026-10-17. 설치 서버의 실제 SDK·FXB·장치·메트릭은 **실제 장비 검증 필요**다.
