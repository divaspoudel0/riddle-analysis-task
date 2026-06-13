# T2.2.5 Cross-language Export Verification

Dataset: `smoke_test_25` (25 rows, languages: arz, eng, rus, tam, zho)
Versions: transformers=5.10.1, cachesaver=0.0.6
API keys present: none

| Provider | Category | Ran | Rows | Statuses | Languages | Tokens | Export |
|---|---|---|---|---|---|---|---|
| dummy | dummy | yes | 25 | success:25 | arz, eng, rus, tam, zho | no | OK |
| local-hf | local | yes | 25 | success:25 | arz, eng, rus, tam, zho | yes | OK |
| cohere-api | api | SKIPPED (COHERE_API_KEY not set) | - | - | - | - | - |
| together-aggregator | aggregator | SKIPPED (TOGETHER_API_KEY not set) | - | - | - | - | - |
