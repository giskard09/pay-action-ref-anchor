# pay-action-ref-anchor

A worked example that derives an **`action_ref`** — a deterministic,
content-addressed identifier for an agent action
([`action-ref-v1`](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)) —
for a synthetic **solana-foundation/pay** metered completion, and anchors it
permissionlessly on-chain, giving it a property the call itself does not
have on its own: an **externally verifiable, third-party-checkable record of
what was committed**, independent of `pay`'s own in-process bookkeeping.

The timestamp of the anchor is the point. This is not outreach and not a
claim of adoption — it is a worked example, byte-exact against the public
spec and `pay`'s own published source.

> **Provenance, up front (read `PROVENANCE.md` for the full statement).**
> The `action_ref` here is derived exactly per `action-ref-v1` and
> cross-checked against argentum-core's own reference implementation. The
> shape (`MeteredSettlement`, `committed_usd`, `channel_id`, `tx_sig`/
> `receipt_url`) is modeled on `pay`'s own **published source**
> ([`solana-foundation/pay`](https://github.com/solana-foundation/pay)) —
> but it was **NOT produced by a running `pay` instance**: no live metered
> request, no real MPP/x402 settlement, no Solana mainnet activity. Nothing
> here — on-chain or in this repo — implies that the Solana Foundation
> integrated, endorsed, or participated. It is our worked example applying
> a public spec to their public source shape.

## The gap

`solana-foundation/pay` meters usage through `MeteredSettlement`: each
increment is recorded into `MeteredState.committed_usd` (`Mutex<f64>`), and
the final total is released exactly once — when the last owner drops — to a
caller-supplied callback. That's correct and sufficient for the proxy to
charge the right amount. It leaves a different question open: once that
callback fires, what's the durable, third-party-checkable record of what
was actually committed and delivered, separate from the in-process value
itself? A verifier who wasn't present — a downstream dispute process, an
auditor, the agent's own operator reviewing activity later — has no
externally checkable reference for the committed total, the channel it
belongs to, or the policy it settled under, without trusting the emitting
process's own logs (which, by construction, no longer hold the value once
the `MeteredState` has dropped).

`action_ref` closes part of that gap: it's a content-addressed identifier
any party can recompute from four declared fields (`agent_id`, `action_type`,
`scope`, `timestamp`) — no trust in the emitting system required. This repo
extends that with an **envelope** carrying `metering_digest`,
`settlement_policy_digest`, and `result_digest` — hashes of the exact
context a verifier would need to confirm what was metered and what the
final committed total was, independently recomputable from the declared
JSON.

```
   pay metered completion                    public chain (Base)
   ┌───────────────────────────┐            ┌────────────────────────┐
   │ agent_id, action_type,     │  JCS+SHA256│ AnchorRegistry         │
   │ scope, timestamp           │───────────▶│  anchor(bytes32 ref)   │
   │ + metering/policy/result   │  action_ref│  Anchored(ref,by,time) │
   │   digests (envelope)       │            └────────────────────────┘
   └───────────────────────────┘             operator-independent
   committed_usd dropped once,               timestamp / finality
   no external record today

```

## Doctrine: spec-agnostic to pay's format

We derive `action_ref` from the four canonical fields only. We do **not**
ask `pay` to adopt any anchoring infrastructure, change its API, or emit any
new fields. The integration lives entirely in how a receipt *could* be
shaped and anchored; `pay`'s metered-completion shape is the input, the
anchor is the added property.

## What's here

| Path | What it is |
|------|-----------|
| `scripts/produce.py` | Derives `action_ref` per `action-ref-v1` (JCS RFC 8785 + SHA-256) for a synthetic `pay` metered completion, plus the `metering_digest`/`settlement_policy_digest`/`result_digest` envelope. |
| `verifier/verify.py` | Independent (stdlib-only) verifier: recomputes all four digests from the declared JSON and confirms the matching `Anchored` event on Base mainnet. |
| `artifacts/` | The canonical instance: `manifest.json` (preimage, digests, envelope) and `anchor.json` (tx/block, once anchored). |
| `scripts/anchor.sh` | The exact `cast` command used to anchor `action_ref`. |
| `PROVENANCE.md` | Exactly what is and isn't real about this artifact. Read it. |

## Reproduce

```bash
# 1. derive action_ref + the envelope digests
python3 scripts/produce.py artifacts

# 2. anchor action_ref on Base mainnet (see scripts/anchor.sh)

# 3. independently verify the derivation and the on-chain anchor
python3 verifier/verify.py
```

## The anchor

- **Registry:** `0x49fEcA52bC634a9Ab773226D16619deC547794aa` (same CREATE2
  address on Base 8453, Arbitrum One 42161, Ink 57073).
- **Function:** `anchor(bytes32 ref)` — permissionless, no owner/roles/funds.
- **Event:** `Anchored(bytes32 indexed ref, address indexed anchoredBy, uint256 timestamp)`.
- The anchored `ref` for this instance and its tx/block are in
  `artifacts/anchor.json`.

## License

This repo is MIT.
