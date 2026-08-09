# Linux 장애 분석 스크립트와 판단 가이드

이 디렉터리는 Linux 서버에서 장애가 발생했을 때 설정을 바꾸기 전에 현재 상태를 보존하는 읽기 전용 도구를 제공합니다. 스크립트 출력은 원인 확정이 아니라 증거 수집입니다. 단일 시점의 CPU 90%, 높은 `TIME_WAIT`, 낮은 `free` 값 하나만으로 장애 원인을 결론 내리지 않고 모니터링 추세, 애플리케이션 로그, 배포 시각과 함께 판단합니다.

## 스크립트 선택

| 상황 | 먼저 실행할 스크립트 | 추가 증거 | 확인하려는 질문 |
| --- | --- | --- | --- |
| 원인을 아직 모름 | `system-health-report.sh` | 알람 시작 시각, 최근 배포 | CPU·메모리·파일시스템·실패 서비스 중 어디가 비정상인가 |
| 접속 지연, timeout, 트래픽 급증 | `network-pressure-report.sh` | LB 요청량·응답시간·5xx, 애플리케이션 worker | NIC, accept backlog, socket queue, 재전송, conntrack 중 어디가 포화됐는가 |
| CPU 또는 load 급증 | `resource-pressure-report.sh` | 프로세스별 지표, profiler, 배포 diff | 실제 CPU 실행, I/O 대기, lock/blocked task, hypervisor steal 중 무엇인가 |
| 메모리 급증, OOM, swap | `resource-pressure-report.sh` | cgroup/container memory, heap·GC | 사용 가능한 메모리가 감소했는가, reclaim·swap·OOM이 실제 발생했는가 |
| `Too many open files` | `resource-pressure-report.sh` | 서비스 로그, FD type별 `lsof` | 시스템 전체 한계인가, 특정 프로세스 누수인가 |
| 디스크 가득 참 또는 I/O 지연 | `resource-pressure-report.sh` | 볼륨 지표, 파일 증가 경로 | block 용량, inode, 삭제 후 열린 파일, I/O latency 중 무엇인가 |
| 특정 systemd 서비스 장애 | `service-triage.sh --service ...` | upstream/downstream 상태 | MainPID, 종료 코드, socket, journal에 어떤 변화가 있는가 |
| 패치 전 영향 확인 | `patch-readiness.sh` | 백업·이중화·원복 계획 | 설치 후보, reboot 필요성, 실패 unit이 있는가 |

## 장애 대응 순서

1. 티켓 번호, 서버 역할, 환경, 알람 시작 시각과 시간대를 기록합니다.
2. 재시작, cache drop, log truncate, limit 변경 전에 읽기 전용 증적을 수집합니다.
3. `system-health-report.sh`로 전체 상태를 보고 증상에 맞는 전문 스크립트를 실행합니다.
4. 현재 값을 알람 발생 전 baseline과 비교하고 최소 5~10분 추세를 확인합니다.
5. 인프라 증거와 LB·애플리케이션·데이터베이스 지표의 시간축을 맞춥니다.
6. 사실, 영향, 가설, 반증, 누락 증거와 안전한 복구 후보를 구분해 보고합니다.
7. 변경은 승인된 runbook이나 pull request로 수행하고, 동일 지표가 회복되는지 확인합니다.

## 네트워크와 트래픽 압박

```bash
sudo ./scripts/operations/linux/network-pressure-report.sh \
  --sample-seconds 5 \
  --listen-queue-warning 80 \
  --socket-queue-warning 1048576 \
  --output /var/tmp/network-pressure.txt
```

### `ss`와 queue 해석

| 증거 | 의미 | 다음 확인 |
| --- | --- | --- |
| `ss -lnt`의 `Recv-Q` | 애플리케이션이 아직 `accept()`하지 못한 연결 수 | worker/thread 고갈, event loop 정지, CPU·FD 한계 |
| listening socket의 `Send-Q` | Linux에서 설정된 listen backlog 최대치 | `Recv-Q / Send-Q` 비율과 지속 시간 |
| established socket의 `Recv-Q` | 애플리케이션이 아직 읽지 않은 바이트 | 소비 처리 지연, thread/GC/CPU 정지 |
| established socket의 `Send-Q` | 상대가 아직 확인하지 않은 전송 바이트 | 상대 지연, packet loss, congestion, network path |
| `ListenOverflows`, `ListenDrops` 증가 | accept queue가 실제로 넘쳤을 가능성 | 동일 시각 timeout·5xx와 backlog 한계 |
| retransmit 증가 | 손실, 혼잡 또는 응답 지연 후보 | 증가율, NIC drop, 경로·상대 endpoint |
| `softnet_stat` drop/time squeeze 증가 | 커널이 수신 packet 처리를 따라가지 못하는 후보 | softirq CPU, RSS/RPS, NIC queue, instance 크기 |
| conntrack 80% 이상 | 신규 연결 추적 여유 감소 | 신규 연결률, NAT/firewall, 90% 접근 여부 |

`TIME_WAIT` 수가 많다는 사실만으로 장애는 아닙니다. 신규 연결률과 ephemeral port 범위, `EADDRNOTAVAIL`, conntrack 사용률, 재사용 설계와 함께 봐야 합니다. `netstat`은 `ss`가 없는 구형 환경의 fallback이며, 스크립트는 우선 `ss`를 사용합니다.

직접 확인할 때의 최소 명령은 다음과 같습니다.

```bash
ss -s
ss -lntp
ss -ant | awk 'NR > 1 {count[$1]++} END {for (state in count) print state, count[state]}'
nstat -az | grep -E 'TcpRetransSegs|ListenOverflows|ListenDrops|TCPBacklogDrop'
ip -s link
```

endpoint와 process 정보는 내부 주소와 서비스 이름을 포함하므로 보고서를 `confidential`로 취급합니다.

## CPU와 load 급증

```bash
sudo ./scripts/operations/linux/resource-pressure-report.sh \
  --sample-seconds 5 \
  --top 20 \
  --output /var/tmp/resource-pressure.txt
```

| 확인값 | 해석 |
| --- | --- |
| `top`의 `us` | 사용자 코드가 소비한 CPU 비율 |
| `sy` | kernel, syscall, network·storage 처리 비중 |
| `wa` | CPU 부족이 아니라 I/O 완료를 기다리는 시간 후보 |
| `st` | 가상화 환경에서 다른 workload 때문에 빼앗긴 CPU 시간 |
| `vmstat r` | 실행 중이거나 CPU를 기다리는 runnable task 수 |
| `vmstat b` | I/O 등 uninterruptible sleep 상태 task 수 |
| `/proc/pressure/cpu` | task가 CPU를 기다린 시간의 비율과 누적값 |
| load / logical CPU | runnable과 uninterruptible task 압박의 1차 비교값 |

CPU 사용률이 높아도 처리량이 함께 증가하고 지연이 안정적이면 정상일 수 있습니다. 반대로 CPU가 낮아도 `wa`, `b`, memory 또는 I/O PSI가 높으면 storage나 reclaim 대기 때문에 서비스가 느릴 수 있습니다. 프로세스를 종료하기 전에 PID, thread 수, CPU·RSS 추세, 최근 배포와 요청량을 보존합니다.

## 메모리와 OOM

- `free`의 빈 메모리보다 `/proc/meminfo`의 `MemAvailable`을 우선 봅니다. Linux page cache는 필요할 때 회수될 수 있으므로 cache가 크다는 이유만으로 장애로 판단하지 않습니다.
- swap 사용량이 있다는 사실보다 `vmstat`의 `si`·`so`가 현재 계속 증가하는지 확인합니다.
- memory PSI, `pgmajfault`, `allocstall`, `oom_kill`과 kernel journal을 같은 시간축으로 봅니다.
- container 또는 systemd cgroup 제한이 host 전체 메모리보다 먼저 OOM을 일으킬 수 있으므로 해당 cgroup의 `memory.current`, `memory.max`, `memory.events`를 추가 확인합니다.
- Java나 managed runtime은 RSS뿐 아니라 heap, off-heap, direct buffer와 GC pause를 분리합니다.

## 파일 디스크립터

스크립트는 `/proc/sys/fs/file-nr`로 시스템 전체 사용량을, `/proc/<pid>/fd`와 `/proc/<pid>/limits`로 프로세스별 FD 수와 soft limit을 비교합니다. 프로세스 전체 command line과 환경 변수는 수집하지 않습니다.

다음 증거가 함께 있을 때 FD 고갈 가능성이 높습니다.

- 서비스 로그의 `EMFILE`, `ENFILE`, `Too many open files`
- 특정 PID의 FD 수가 soft limit의 80~90%에 지속적으로 접근
- socket, pipe, 삭제된 파일 등 동일 FD type이 계속 증가
- 신규 연결 또는 파일 open 실패가 사용자 영향 시각과 일치

limit을 바로 올리면 누수를 늦출 뿐 해결하지 못할 수 있습니다. `lsof -p <PID>`는 파일 경로와 endpoint를 노출할 수 있으므로 승인된 호스트에서만 실행하고 type별 개수부터 확인합니다.

```bash
ls -1 /proc/<PID>/fd | wc -l
grep 'Max open files' /proc/<PID>/limits
lsof -nP -p <PID> | awk 'NR > 1 {count[$5]++} END {for (type in count) print type, count[type]}'
```

## 디스크, inode와 I/O

| 현상 | 확인 증거 | 주의점 |
| --- | --- | --- |
| block 용량 부족 | `df -P`, mount별 80/90% | 파일 삭제 전 보존·소유자·retention 확인 |
| inode 부족 | `df -Pi` | 작은 파일이 많으면 block 여유가 있어도 생성 실패 |
| 삭제했는데 용량 미회수 | `lsof +L1` | 열린 FD를 가진 프로세스가 닫을 때까지 공간 미회수 |
| I/O 지연 | `iostat -xz`, `vmstat wa/b`, I/O PSI | `await`, queue와 device class baseline을 함께 비교 |
| filesystem/device 오류 | kernel journal | I/O error가 있으면 반복 write보다 데이터 보호와 escalation 우선 |

루트에서 무제한 `du`나 `find`를 실행하면 장애 중인 디스크에 추가 부하를 줄 수 있습니다. mount와 상위 경로를 좁히고 `timeout`, 낮은 I/O priority, 승인된 유지보수 절차를 사용합니다.

## 초기 경보 기준

다음 값은 공통 출발점이며 workload baseline과 SLO에 맞게 조정합니다. 스크립트의 warning은 한 시점의 후보이고, 운영 알람은 지속 시간과 사용자 영향을 포함해야 합니다.

| 영역 | Warning 후보 | Critical 후보 |
| --- | --- | --- |
| CPU | 80% 이상 10분 | 90% 이상 5분이며 지연·error 동반 |
| Memory | 사용률 80% 이상 또는 `MemAvailable` 20% 미만 지속 | 90% 이상, `MemAvailable` 10% 미만, OOM·reclaim stall |
| Disk block/inode | 80% 이상 | 90% 이상 또는 write/create 실패 |
| Process FD | soft limit 80% 이상 | 90% 이상 또는 `EMFILE` 발생 |
| Listen queue | backlog 80% 이상 지속 | overflow/drop 증가와 timeout 동반 |
| Conntrack | 최대치 80% 이상 | 90% 이상 또는 신규 연결 실패 |
| I/O | PSI·`await`가 baseline 초과 | 지연 SLO 위반 또는 kernel I/O error |

## 보고서 필수 항목

- 사건 번호, 환경, host·서비스 역할, 수집 시각과 명령
- 사용자 영향과 시작·종료 시각
- 정상 baseline 대비 달라진 수치
- 확인된 사실과 아직 검증하지 않은 가설
- 최근 배포, traffic, dependency 변화
- 수행한 변경, 승인자, 변경 전후 지표
- 민감한 endpoint·경로·사용자 정보의 마스킹 여부
- 후속 담당자, 다음 확인 시각과 재발 방지 backlog
