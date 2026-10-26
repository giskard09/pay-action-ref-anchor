#!/usr/bin/env python3
"""
Produces an action_ref for a synthetic solana-foundation/pay metered
completion (the MeteredSettlement / completion_stream path), following
action-ref-v1 (argentum-core, JCS RFC 8785 + SHA-256) byte-for-byte, and
emits the artifacts needed to anchor + independently verify it.

PROVENANCE: this is NOT captured from a running `pay` proxy instance. The
shape (channel_id, metered record, completion settlement) is modeled on
pay's own source, as published:
rust/crates/core/src/server/completion_stream.rs (MeteredSettlement,
MeteredState.committed_usd: Mutex<f64>, callback fired once on Drop) and
rust/crates/core/src/server/payment.rs (TrustedPaymentIdentity.channel_id,
tx_sig/receipt_url tracing fields on payment_middleware's span). No claim
that pay emits action_ref today, and no claim of adoption or endorsement.
"""
import hashlib
import json
import os
import sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
os.makedirs(OUT_DIR, exist_ok=True)


def jcs(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# --- 1. The four required action-ref-v1 preimage fields --------------------
# Per argentum-core/docs/spec/action-ref.md: only these four fields enter the
# hash. Modeled on pay's own MeteredSettlement path: a metered endpoint
# settles via accumulated committed_usd, released once at Drop.
timestamp = "2026-10-26T15:00:00.000Z"
preimage = {
    "agent_id": "worked-example.pay-action-ref-anchor",
    "action_type": "pay.metered_completion",
    "scope": "mpp:channel:ch_7f3a9c",
    "timestamp": timestamp,
}
jcs_payload = jcs(preimage)
action_ref = sha256_hex(jcs_payload)

# --- 2. Additive envelope fields — pay-specific context ---------------------
# These do NOT enter the action_ref hash (per action-ref-v1: only the 4
# preimage fields are hashed). They travel alongside as declared context a
# downstream verifier can check independently — this is exactly the seam
# MeteredState.committed_usd / the Drop-fired callback leaves unclosed: the
# final committed total is bookkept in-process only, never emitted as a
# record a verifier can check without trusting pay's own logs.
metering = {
    "endpoint_path": "/v1/completions",
    "channel_id": "ch_7f3a9c",
    "payer": "worked-example-payer",
    "increments_base_units": [120000, 95000, 140000],
    "decimals": 6,
}
metering_digest = sha256_hex(jcs(metering))

settlement_policy = {
    "auth_scheme": "mpp",
    "payment_policy": "per_request_metered",
}
settlement_policy_digest = sha256_hex(jcs(settlement_policy))

result = {
    "status": "settled",
    "committed_usd": "0.355000",
    "tx_sig_placeholder": "1" * 88,  # synthetic — not a real Solana signature
    "receipt_url_placeholder": "https://example.invalid/receipts/synthetic",
}
result_digest = sha256_hex(jcs(result))

envelope = {
    "packet_version": "1.0",
    "action_ref": action_ref,
    "hash_algo": "sha256",
    "preimage_format": "jcs-rfc8785-v1",
    "preimage": preimage,
    "endpoint_path": metering["endpoint_path"],
    "metering_digest": metering_digest,
    "settlement_policy_digest": settlement_policy_digest,
    "result_digest": result_digest,
    "generated_at_utc": timestamp,
}

manifest = {
    "fixture_id": "pay-metered-completion-worked-example",
    "spec": "action-ref-v1 (argentum-core, docs/spec/action-ref.md)",
    "preimage": preimage,
    "jcs_payload": jcs_payload,
    "action_ref": action_ref,
    "anchor_ref_bytes32": "0x" + action_ref,
    "anchor_registry": "0x49fEcA52bC634a9Ab773226D16619deC547794aa",
    "anchor_chain": "Base mainnet (chainId 8453)",
    "envelope": envelope,
    "metering": metering,
    "settlement_policy": settlement_policy,
    "result": result,
    "provenance": (
        "Synthetic worked example. The shape is modeled on solana-foundation/"
        "pay's own public source: rust/crates/core/src/server/"
        "completion_stream.rs (MeteredSettlement, MeteredState.committed_usd: "
        "Mutex<f64>, single-shot callback fired on Drop with the final "
        "committed total) and rust/crates/core/src/server/payment.rs "
        "(TrustedPaymentIdentity.channel_id; payment_middleware's tracing "
        "span declares tx_sig/receipt_url fields). NOT captured from a "
        "running pay proxy instance or a real MPP/x402 settlement. "
        "result.tx_sig_placeholder and receipt_url_placeholder are not real. "
        "No claim that pay emits action_ref today, and no claim of "
        "integration, adoption, or endorsement by solana-foundation/pay."
    ),
}

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")

print("=== pay-action-ref-anchor : producer ===")
print(f"jcs_payload = {jcs_payload}")
print(f"action_ref  = {action_ref}")
print(f"anchor ref (bytes32) = 0x{action_ref}")
print(f"wrote {OUT_DIR}/manifest.json")
