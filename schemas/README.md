# Runtime JSON Schemas

`schemas/`는 Monitoring Agent와 Portal/Gateway·후속 시스템 사이의 machine-readable 데이터 계약입니다.

| Schema | Boundary |
| --- | --- |
| `incident-request.schema.json` | Portal/Gateway가 생성하는 read-only incident request의 필드·형식·비용·scope 제한 |
| `incident-report.schema.json` | Monitoring Agent가 내보내는 상태·사실·가설·gap·evidence와 mutation 금지 결과 |

## Current Implementation Boundary

현재 Python runtime은 외부 `jsonschema` package에 의존하지 않고 `agent-runtime/.../contracts.py`에서 요청 규칙을 다시 검증합니다. Schema 파일은 Portal/Gateway와 downstream contract의 기준이며, 단위시험이 required field·enum·read-only 핵심 규칙과 runtime 출력의 정렬을 확인합니다.

이는 완전한 JSON Schema engine 검증과 동일하지 않습니다. production Gateway에서는 Draft 2020-12 validator와 format checker를 사용하고, schema version과 `$id`를 승인된 Schema Registry에 고정해야 합니다.

## Change Rule

1. Schema 변경과 runtime contract 변경을 같은 pull request에 포함합니다.
2. `examples/incidents`의 valid fixture와 invalid case test를 함께 갱신합니다.
3. 생성 report가 required field, status enum과 `executed_mutations.maxItems=0`을 만족하는지 확인합니다.
4. backward compatibility와 consumer migration을 검토한 후 `schema_version`을 변경합니다.
5. Schema나 example의 존재를 live 운영 증적 또는 배포 완료로 해석하지 않습니다.

