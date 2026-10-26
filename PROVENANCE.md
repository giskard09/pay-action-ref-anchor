# Provenance — read this before drawing any conclusion

This document states exactly what is real and what is synthetic in this
worked example. Hard honesty is the point: the artifact is worthless if its
provenance is fuzzy.

## What is real

- `action_ref` is derived exactly per `action-ref-v1`
  ([argentum-core/docs/spec/action-ref.md](https://github.com/giskard09/argentum-core/blob/main/docs/spec/action-ref.md)):
  SHA-256 of the RFC 8785 JCS canonicalization of the four preimage fields
  (`agent_id`, `action_type`, `scope`, `timestamp`). The value in
  `artifacts/manifest.json` was independently cross-checked against
  argentum-core's own reference implementation
  (`plugins/agt_evidence_anchor/action_ref.py`) and matches byte-for-byte.
- The shape modeled (`MeteredSettlement`, `committed_usd`, single-shot
  settlement callback fired on `Drop`, `channel_id`, `tx_sig`/`receipt_url`
  tracing fields) is read from `solana-foundation/pay`'s own published
  source, not invented:
  - [`rust/crates/core/src/server/completion_stream.rs`](https://github.com/solana-foundation/pay/blob/main/rust/crates/core/src/server/completion_stream.rs)
    defines `MeteredSettlement` / `MeteredState { committed_usd: Mutex<f64>, callback }`,
    with the callback firing exactly once — on `Drop` — carrying the final
    committed USD total and nothing else.
  - [`rust/crates/core/src/server/payment.rs`](https://github.com/solana-foundation/pay/blob/main/rust/crates/core/src/server/payment.rs)
    defines `TrustedPaymentIdentity { payer, channel_id, original_host,
    payment_policy }` and the `payment_middleware` tracing span, which
    declares `tx_sig` and `receipt_url` fields.
- The on-chain anchor (once `artifacts/anchor.json` exists) is a real
  transaction on Base mainnet; the tx hash and block are independently
  checkable by anyone via `verifier/verify.py`.

## What is synthetic — declared

- **No running `pay` proxy instance was called.** `agent_id`, `timestamp`,
  `metering`, `settlement_policy`, and `result` (including
  `result.tx_sig_placeholder` and `result.receipt_url_placeholder`, which
  are not real) are all constructed in `scripts/produce.py`, not captured
  from a live metered request, a real MPP/x402 settlement, or Solana
  mainnet activity.
- **The `metering_digest` / `settlement_policy_digest` / `result_digest`
  envelope fields are this repo's own addition**, not part of
  `action-ref-v1`'s four-field hash. They exist to demonstrate — concretely,
  with anchored hashes — what a `pay` receipt carrying the committed-usage
  total, the settlement policy in force, and the result could look like if
  `pay` chose to emit one at the point `MeteredState` currently only fires
  an in-process callback. They do not enter the `action_ref` preimage; the
  spec is explicit that only the four canonical fields are hashed.

## What this therefore does and does not show

- **Does show:** the `action_ref` derivation applies unchanged to `pay`'s
  own documented metered-completion shape — same four fields, same JCS +
  SHA-256 path used by every other emitter in the spec's cross-reference
  list. Given a real metered request settling through a real `pay`
  instance, the identical path produces a verifiable, content-addressed
  identifier for that completion, closing the seam where today
  `committed_usd` is bookkept only in-process and released once, to a
  caller-supplied callback, with no externally checkable record.
- **Does not show:** that `pay` or the Solana Foundation has integrated,
  endorsed, or adopted `action_ref`. It is our worked example applying a
  public spec to `pay`'s public source. No claim of "pay integrated us," no
  claim of on-chain adoption, no cited quote. If someone reads it as
  adoption, that reading is wrong.
