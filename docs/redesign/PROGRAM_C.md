# Program C — AI SKU & Asset Health Twin

**Customer promise:** STT intake, assistant draft WO (confirm card), prediction, Health Twin view.  
**Window:** S13+ — **data-gated**; separately priced AI SKU.  
**Depends on:** A5 failure/downtime data; B4 for channel intake; B3 rules for twin inputs.

## Capabilities

| Capability | MVP model choice | Deploy note |
|------------|------------------|-------------|
| STT (mic → title/desc) | Cloud Whisper-class; fallback device dictation | Gulf/Egyptian Arabic WER; PDPL residency |
| AI assistant creates WO | Small LLM as **extractor only**; slot-fill + **confirm card**; no write tools | Tenant-scoped retrieval of site/asset |
| Predictive | Rules → Weibull/MTBF → LightGBM only after hundreds of failures/type | Cold-start is #1 AI risk |
| Digital Twin | **Asset Health Twin** UI (type + risk + open WOs) | **Not** BIM/IoT |

Feature-flag all AI behind `ai_maintenance` / new flags; per-tenant AI budget + `AiInvocation` log.

## Explicit non-goals in this package

- Full BIM / IoT Digital Twin (separate undated initiative).
- Auto-create WO from WhatsApp or LLM without human confirm.
