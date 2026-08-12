# Operations Report Templates

이 디렉터리는 사람이 작성하고 승인하는 운영 보고서의 빈 양식만 관리합니다.

```text
reports/
├── README.md
└── templates/
    ├── monthly-platform-report.md
    └── incident-report.md
```

## 사용 범위

| 양식 | 목적 | 작성·승인 책임 |
| --- | --- | --- |
| Monthly platform report | 신뢰성, 변경, 보안, 비용과 운영 조치를 월 단위로 검토 | Platform/Operations 작성, Security·FinOps·서비스 책임자 검토 |
| Incident report | 장애 영향, 타임라인, 사실·가설·원인, 복구와 재발 방지 조치를 기록 | Incident Commander 책임, 관련 운영팀 작성·검토 |

## 작성 원칙

1. `<...>`를 실제 값 또는 `not_available`과 사유로 교체합니다.
2. 사실, 가설, 미확인 사항과 실제 실행 조치를 구분합니다.
3. 원본 로그, 고객 데이터와 자격 증명은 Git에 저장하지 않습니다.
4. 보고서에는 ticket, UTC window, query나 변경 기록, 승인된 증적 위치와 사람의 서명을 연결합니다.
5. 실제 측정값이 없는 예시를 운영 실적처럼 사용하지 않습니다.

이 저장소에는 채워진 장애·월간 보고서 예시를 두지 않습니다. 실제 보고서는 승인된 ticket 또는 문서 저장소에서 보존합니다.
