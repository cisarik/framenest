"""Retention ledger for the ADR-0085 Kronika sole identity.

Three live parts, none skippable, xfailable or disabled:

Part A pins SHA-256 values for the frozen blobs whose bytes no identity cut may
ever edit: the historical ADR bodies through 0084, the two superseded host
documents, and every applied Alembic revision through `0035`. A later cut may
move the Alembic directory path; it may not change those bytes.

Part B pins the exact set of tracked paths whose basename contains `framenest`
case-insensitively. Each later cut shrinks this set by an exact enumerated
difference, so a missed path rename fails loudly at the cut that owns it. The
expected set is a pinned literal in this file. It is deliberately not recomputed
from the working tree, which would make the assertion tautological.

Part C pins per-tree content-occurrence counts so that a missed content rename is
detectable even where the filename is already clean, as in
`deploy/ubuntu/fn-production-env-deploy`.

The question-12 living-prose `\bframenest\b` scan over the living document list
is deliberately NOT implemented at this cut. It is armed in cut C7. That intent
is recorded here only; no disabled or skipped placeholder test exists.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

_ALEMBIC_VERSIONS_GLOB = "src/*/infrastructure/persistence/alembic_environment/versions"

FROZEN_DOCUMENT_SHA256: dict[str, str] = {
    "docs/adr/0001-supported-python-version.md": "3f5698b977c44d3381752b98de2708817a43d3139805efdcdf1f6d4b3309b0dc",
    "docs/adr/0002-python-environment-and-dependency-manager.md": "6b014e4e6787a5ae090fed7fca1b7f27d2fdc59abb870fd165901a4e8761eddc",
    "docs/adr/0003-initial-server-api-framework.md": "141eb151a1bb20674d5c81a1d628806094835ad8ee3a7a5504dfa1ddfef55527",
    "docs/adr/0004-repository-layout.md": "4d8e198583b341155e98671b5848fdd1573e145613b60318008f64f31aab1b07",
    "docs/adr/0005-configuration-strategy.md": "e4ad7e14caa2c9494e40f47f19d912e527795b5caf426c390885abd1db3c4c35",
    "docs/adr/0006-macos-python-interpreter-provider.md": "e337088f8feaa132f173ad57cae6792ceb358a07f5f3b27a5756db08c3326d50",
    "docs/adr/0007-settings-library.md": "d24ce4e6a125a0b41ba9c8bcb5a79de4b64377c03ad851065d2699889d88178e",
    "docs/adr/0008-asgi-runtime.md": "8d8fe55e420585a03bb0fcf5c5530f2776885d76148c2c8d6ac5782fc65c47eb",
    "docs/adr/0009-structured-logging-approach.md": "b1e97bb44ba25e7e7974edef51fd0079c78c821b07a0b922f1c679ef3685e449",
    "docs/adr/0010-initial-persistence-foundation.md": "6a7462628d338d090664db0e85b81c705d2b70d77ad6aafebcda2f77c1cd8454",
    "docs/adr/0011-stable-domain-identities.md": "3bee51f271c6b666b380be2ea8a66eacfc32403775fe98b8b00f9b5026f7ec65",
    "docs/adr/0012-initial-device-registry.md": "31ebe857512cccf07a247482db85c310a31a208956c6484b01590dd2f261455b",
    "docs/adr/0013-initial-library-registry.md": "cd89a2fed1fc05945166323227ad7144be914639eb78bfd794dcf823bc94b9d1",
    "docs/adr/0014-safe-library-scan-preview.md": "a872d542cdc009c2132185f5a7f84d7c7e555ca92603f847ac8e61113ec9d311",
    "docs/adr/0015-deterministic-local-media-analysis-preparation.md": "bb74a7ccbccfafde314f853b8a57d2607b68376f011c7c5ec760c12ca7ab9fea",
    "docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md": "65c0e79675c903cf2e52fad4fda2cd97f9eb782c97d7ec5098bc18e2ba9fe5db",
    "docs/adr/0017-initial-local-web-application-delivery.md": "1e8172061476c223b56e1165cbf625bc2901e287e8f0383862d778d00331ce52",
    "docs/adr/0018-local-media-analysis-preview-api.md": "9356b06aaba319890c7d3e0fd83e8e230e059052b8dd0d3b70e9f85df2ac0d37",
    "docs/adr/0019-vlm-image-derivatives-and-nvidia-instruct-mode.md": "7cf3d261672e28ceeb028044e8ed9943ef0226b2d0e886e24aaed8fd4b53eb05",
    "docs/adr/0020-on-demand-ai-suggestion-review.md": "b7c11da86de2bec270c639578caca4426ff3a1450e6c1dc0c7fa716cc8e95f2e",
    "docs/adr/0021-tauri-desktop-shell.md": "e010ea1e35f50d413488616b91c3796c9826e17d7f80391fadf36a081b746fa1",
    "docs/adr/0022-selective-media-placement-and-server-aggregation.md": "85e074bc629ffe3b10f99f561a549cea0797f9dfe28257f42ffe468529f5652a",
    "docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md": "d5ddc82e437830ed5fff86c677de3a8fb69b514fccd2a5a49385dea5e3947fb1",
    "docs/adr/0024-cover-studio-and-ai-cover-candidates.md": "8476347d1dc5875a607d8c762d22156fbc79b7c316f16f3db22d6f334fe73388",
    "docs/adr/0025-minimum-persistent-media-catalog-foundation.md": "89348e9e15f1cff4f756d4a958d0b1f629053b1b31e7818cd0a760d6cfe9b53d",
    "docs/adr/0026-explicit-idempotent-scan-candidate-import.md": "b0c69889c064cb09bb453db05e54e6eb981deb7fc70159c6725f9c47e347a583",
    "docs/adr/0027-persistent-display-title-and-canonical-tags.md": "68488d3454c21c5cb714ab4caa4114c9d790674262d4a65db3d7accb174cf1e2",
    "docs/adr/0028-catalog-read-model-and-search-semantics.md": "c1b52c104e49ae5e6344d0564e024ca2f646217ffd0c8b6acf6a76332e10844c",
    "docs/adr/0029-persistent-plain-text-media-description.md": "7a6ab102a4cbeafc5255d95a3c4d6d24a5f5c5b21a09867ea5aa4d52377f05b0",
    "docs/adr/0030-automatic-processed-collection.md": "ea34b5f73c7f461bbaf6e98f72efd82ce5e3a6325666ab74be35c773de37abc5",
    "docs/adr/0031-fedora-systemd-service-foundation.md": "0673911c49929e11216051d856e1034d54c8b5c51f7d6a54765ffe244f054bc2",
    "docs/adr/0032-ubuntu-nuc-deployment-foundation.md": "7ebd7d912ce6a8245cc75644b138b419021aec63ca0a41a4693b4b003b811f9b",
    "docs/adr/0033-catalog-backup-and-recovery-foundation.md": "8ad14a7f6368024012af14a8f29ec1f6b74b8853d3ccbfcdf45fb15bd83f991b",
    "docs/adr/0034-canonical-analytic-programming-integration.md": "c4e0aa0318875d0eafb91b50f4b6cb32a355da749cbf5a001e917f07bc631060",
    "docs/adr/0035-authoritative-server-and-client-state-model.md": "f756d0b6a3b1c609dac5d88521c335daa97262682f5e15c945202b949961a7fd",
    "docs/adr/0036-production-ai-credentials-via-systemd.md": "10aa5f7da3f3ae3e6be31c8dcc1e92276d354b896269ec7d20be687faea1d01e",
    "docs/adr/0037-durable-upload-session-and-safe-ingest-foundation.md": "c61247b0fc6017bb881492bb0fde4bff28fd7281032bf81df8822521d6ea2e4c",
    "docs/adr/0038-bounded-upload-media-validation.md": "542719effd798f1957422aaa6eb3cda56756cfc21d0112cf4d2b61a70daa23e9",
    "docs/adr/0039-lifecycle-owned-upload-validation-orchestration.md": "ae81c662b369199a6ba67be7c31fbd72a51fbdadb768ea135424a1d0f8bbb10a",
    "docs/adr/0040-canonical-upload-byte-identity-foundation.md": "e732aff7a8e9cc4094593f67e95b3b84f12c9964b9785208a41a1e25fabdd7bc",
    "docs/adr/0041-exact-byte-upload-duplicate-disposition.md": "7a7a13819aca863581998c22191aba5bfd4461e2e1e1f850204b05c76624c4f2",
    "docs/adr/0042-atomic-upload-publication.md": "9db4a739ce428347c63c19af8984787e50860c6fdf71db63cdaf0d8430ab591c",
    "docs/adr/0043-upload-to-catalog-transaction.md": "5dfcaa971679bd181c636a3d997c19cd898b42b7c8d7b758a7583752a84824f1",
    "docs/adr/0044-durable-automatic-post-catalog-analysis.md": "c5085561a5af05a101c0c67fe8b61e082b33632d83680e39bd87784ed0b059c7",
    "docs/adr/0045-content-classification-and-movie-identification.md": "1c3fcd2e4296345f13b4729b5fb5acf22472ae45a0c39fc7c3eab8f5504a9470",
    "docs/adr/0046-youtube-manual-ingestion-and-provenance.md": "2812e17a005142a287448390d96113dae67c33cbd61a017142ddfd7032566c0f",
    "docs/adr/0047-operator-cli-configuration-and-working-directory-hygiene.md": "a07b054809e88b61102b40cbd0c497823ff685bc6544ad201f92b31aef0baf05",
    "docs/adr/0048-tailscale-remote-access-and-identity-foundation.md": "4c9ff4434a10f6e974c37afb50c4edfe5a0a4f1e010a8929a288b2a07ffff0d4",
    "docs/adr/0049-durable-content-publication-boundary.md": "fc6f9632230aa9d609428e20c7d301519f27d5399d0ef6fe1303206d0c52de07",
    "docs/adr/0050-durable-manual-cover-foundation.md": "8e296272fb96a7efe7e2efd1cd152112d951ec706a45ba0d9de71d533da1e951",
    "docs/adr/0051-administrator-catalog-removal.md": "8a8b0a26c27e4464dcc863eef9a6bedca3212fd39b28d48bf8fe414c33d022e5",
    "docs/adr/0052-automated-catalog-backup-retention-and-restore-verification.md": "a368387902d3d6cfe5496003700c86566d3022aca6620152c5d2486dff8246ba",
    "docs/adr/0053-ordinary-user-upload-submission-and-administrator-review-boundary.md": "1a2fb5067b6ea1108b859dec8bb4125363e4c77740d5a1167dbf58bf4b8d6192",
    "docs/adr/0054-requester-private-youtube-acquisition-and-promotion-boundary.md": "574a12bdb6d25c0e0c775926c4461746849591b665d12d2145006fbac7bc3eb0",
    "docs/adr/0055-youtube-creator-taxonomy-and-immutable-provenance.md": "91c998e802670fbc976ae6e6b39f150d571b043d5cc757145b86e4e17aca389c",
    "docs/adr/0056-off-device-catalog-backup-copy-and-restore-verification.md": "2b1c618ff3777723b3ccf1ea93b193c735e5617830663239094a8ff12c4163be",
    "docs/adr/0057-operator-workstation-pull-based-catalog-snapshot.md": "e9aed13900b76e7d251097b7f9bfb452663149205367670797a6ffc6c046a14d",
    "docs/adr/0058-independent-mullvad-egress-and-operator-network-recovery.md": "d97aa35ccc10fa93a168b4680835264a22faa4c8e5b264e6c0c1f6220bf1ea98",
    "docs/adr/0059-portable-media-sidecar-roundtrip-foundation.md": "4cecdb8c0a423993da81049db8580b953bfd1cea35407a99926057c128f3d8da",
    "docs/adr/0060-repeatable-immutable-nuc-release-update-contract.md": "55d76342c5262dc4871428f7c839673106cac0d36e05533087d13a44d4aabb60",
    "docs/adr/0061-x-meme-browser-companion.md": "2cd9b01780af9f3286621e60979d1c9141f99f6dc656f2a575cde7fe733cc2c5",
    "docs/adr/0062-per-user-media-alias-overlay.md": "eb6dd1badf56cf588b9fe1f7db3fada959361ca30acb9af5f606b3ef218d72cb",
    "docs/adr/0063-companion-side-panel-web-host.md": "936794900ace1ee45ce70fef6edd299cbd382524727e86a47e6c82e313546595",
    "docs/adr/0064-x-save-category-and-public-photo-acquisition.md": "16964ee944f7f15e5742e880966170a5e4300244dedb845ecd0fa671cc460490",
    "docs/adr/0065-x-save-edit-subset-and-acquisition-time-canonical-metadata-seed.md": "c50b6a63dc66981af8f7936e2f5a558e0cc4dbbd5290941630c33459b595b811",
    "docs/adr/0066-administrator-owned-x-automatic-generic-analysis.md": "722a2561efdbf2f21ccbe8a293bc5c2897547370c52b3d430d6c38c04f825694",
    "docs/adr/0067-administrator-companion-review-inbox-and-mutation-trust.md": "0cfd9c30db045d0085f48063d621791c15ad509d289195f6fb7108d368e4780b",
    "docs/adr/0068-companion-review-save-and-readiness-triggered-publication.md": "c51a3f422b414f14cfe915c3dc91ceaa2a4b1f11227168f086d64754cdb50bbf",
    "docs/adr/0069-five-tag-generic-media-suggestion-contract.md": "e2ae9a27c7d3a49919951798c7a15c66ae91a69fb8ccab6a614e65839e87e728",
    "docs/adr/0070-companion-exclusion-of-movie-workflows.md": "cd456428cc5b438e1dc9ceda7f5ba498a5bc92124de29dc5c42307b2ee8a0f12",
    "docs/adr/0071-native-side-panel-review-inbox-chrome.md": "9b7d99a14ba16ccd17338381f4f0ef67a86053a282197c78116b6019f3eaceb2",
    "docs/adr/0072-native-side-panel-unread-inbox-and-title-bar-history-chrome.md": "65482d8a0eeeb99ad0baf4c1d038ef82ec7e1e170be89053f2d19fed64b4d75c",
    "docs/adr/0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md": "9ceef42017ada04f5835ce1ece4fedd59be440c29cb0f1950f07d78f73823a5a",
    "docs/adr/0074-dual-audience-public-published-and-tailscale-workspace-boundary.md": "5cd52ec9b713dabaab48e53e2e0aaa203677f63e05d30320e54ed3501a1fd10b",
    "docs/adr/0075-nuc-development-test-target-and-routine-release-refresh.md": "5fce22c3e3c04655081858548bf76a3f2528d744aa3b901c492ad7e47490a7a7",
    "docs/adr/0076-companion-history-hosted-click-admin-analyzed-inbox-and-ordinary-own-history.md": "501699f5d70d0ffe06df7417742e40dba9a0f82624b41209f0eaa897bb55a5a5",
    "docs/adr/0077-ordinary-alias-edit-affordance-and-per-field-ai-suggestions.md": "8d8d535a2e82253a98fd96fe2685f2694dd297c86d1629a2e7dd50133d148aec",
    "docs/adr/0078-gallery-card-ai-per-field-review.md": "f366bdd747e9423822f5532670c74b5da3a952d8464fa6034bbfe52f6edd6297",
    "docs/adr/0079-administrator-automatic-analysis-runtime-setting.md": "c68f600be6a9bc2ed5b70763b177299335f37d22ed30b73bcd93333925da2aaa",
    "docs/adr/0080-immediate-editor-suggestion-reveal-and-in-modal-analysis.md": "1cb16f1184e5470f36b11fa59a77b11fb50116d1fb6db5b3941ad457309d449a",
    "docs/adr/0081-declarative-openai-compatible-provider-registry-and-administrator-vision-probe.md": "fc0391e43b878a6588a3ada610738249b3add0e03ae111af8b2a93a10a89909f",
    "docs/adr/0082-kronika-one-product-and-private-records.md": "150e3236b9b66f7ea9ec657aa183bdacc1660f27e79424bd0e65cadf02d73c33",
    "docs/adr/0083-modular-research-providers-and-administrator-curated-timeline.md": "a9bd8f5abb06a40b06d27addff8594f8d001909548aab1cc5b6b9b0d1fad956a",
    "docs/adr/0084-administrator-managed-research-settings-and-versioned-pricing.md": "8c59e6d4f239e5dc1ad7b1919817837f01c60db4f7666090519f76f14896db08",
    "docs/FEDORA_SERVICE.md": "c95b2c091cf6d7e82dc9d4b2ea1b7ec5161588094fb9758814c49756a1fad756",
    "docs/NUC_HOST_BASELINE.md": "f7a47391dded54c51bf863a711b18a8e6875420d2aa8ddc8fd2e943980cef98f",
}

FROZEN_ALEMBIC_SHA256: dict[str, str] = {
    "0001_initial_foundation.py": "7fe8de6d406bd7c7768c6ca66eff324185262d8e72586278a710a3cc609f295c",
    "0002_device_registry.py": "e43419d76e3161e99c78e5a694e032c58013e1e4794fd74df13542994a04cbdd",
    "0003_library_registry.py": "56aba5b474e76c04206df88785e590b33c5b5bfdc864bacacbee1da42fdf705b",
    "0004_media_catalog_foundation.py": "87c93511b47ad5a15b6361ffa69e227d6b44d12323eee3113888c80932c6a419",
    "0005_media_metadata_and_canonical_tags.py": "b325ad4316c3bee5466074697e6ed6a1cc8a50cd5a13ca59541ab7886ee2a6f7",
    "0006_persistent_media_description.py": "4c82d3af6e117bed3731c875be8e424a00fa2b3615d68e0c5b8e6b053de5864c",
    "0007_automatic_processed_collection.py": "28c0b5ca29cb853e0c0184eed05f554e5a3445af720cd9ec025a8d01d10cb818",
    "0008_upload_sessions.py": "95752e4f6373e5c151f38344c1ec210cd6ec982aa472000303b19345b96cf91d",
    "0009_upload_session_completeness.py": "7d92eebb8b471bf461d7b4386a67928ab5261dff4ec575da2c5dbcf6a1f451c4",
    "0010_upload_validation_evidence.py": "83713c2b3dc9a994bf89b8a3ee018048cdaf9d4dfc67b806e0001f7ebba80894",
    "0011_upload_byte_identities.py": "38c45926a7364ba46b1bcb1409a685b18e073dceb54c802f3f6972aa5d7f332b",
    "0012_upload_duplicate_disposition.py": "9624a19c4d300056eac682870c0fc61d6983f98376b3a432e9e19014626f59c7",
    "0013_atomic_upload_publication.py": "f6420a5ffc69ccd3c424763cb85322c4e4147293555d42165a1da0e9624b20b2",
    "0014_upload_catalog_linkage.py": "4b82a50134da2820ad0f8ea52077414540ea436c552f8c409839e9e16befb6f4",
    "0015_media_analysis_runs.py": "c3fbe3e7246599a211413aa976293c98f2cece3b1950090c8ad266effef35b00",
    "0016_still_image_media_kinds.py": "6a2bdd8e7ead7a5cd40f22c86c9362560bcb77d1ad9a138453b27808997ca4f8",
    "0017_content_classification_and_movie_identification.py": "2a02319fed16ded32ef1d398eab6424b5d303969b918268fbb5ee9795fc28484",
    "0018_analysis_run_history_and_active_uniqueness.py": "c2582e74f7b136ecb01a0254917b9647cbc5a922f058b8120eb107c1aac3435a",
    "0019_youtube_manual_acquisition.py": "d37e6210cfd47ad9fbeb012e269f2c2ebff2fdd6bff4f030c1839821dc0a1ee9",
    "0020_security_audit_events.py": "e18e1b55a903504894a9cb9a87de05b0085141a47b42faf3d9bdb81aa2a1f722",
    "0021_content_publication.py": "6920cd8a383c33f56c6baa5cd7b2230fd1d31fd63a195155c43800fa788f1c9b",
    "0022_media_covers.py": "3e5288979e523f8897ae31276e44a9950ed46c00181f95e23e474b21c1bdad3f",
    "0023_still_image_covers.py": "58efb070b5409ea69969203062de5e964de7770b86bd3faf230c8dae0cf059f7",
    "0024_catalog_removal_receipts.py": "f097eaba7ab5c088b346c710e51468cd06b7cfd75fe06c0635b058bed9d5ed03",
    "0025_upload_session_ownership_and_duplicate_mode.py": "c9415c84c9bfc94e36b142ab35a31c3dd5dd311b9b7a382777ed5e200b23900a",
    "0026_youtube_requester_ownership.py": "be7de26ad0fa780211e8a4219a00d66757f8def88e1e06ec589b1f153dc3fdc2",
    "0027_youtube_creator_taxonomy.py": "94358d837d80fc9b8944a23023b9e7b1cf061257025da569a82f65ce14f26934",
    "0028_x_requester_acquisition.py": "73b23326c3fadd78d823f7c0ddd0f5eb45395a6fdf91313d8bacd0ecdd55fa03",
    "0029_media_user_alias_overlay.py": "fde17806a87a07ae2292ed460c35c358f002b7a8dc16f78a1121076048496cd7",
    "0030_x_claim_requested_content_category.py": "b0d02e88f8373765138b455810662c8df6a0c1a53ccdb1f647cc5b0c91329ed2",
    "0031_companion_review_inbox.py": "3b6a4ff6d0a6a4f61ab098e9e2e1a658e566a4d2963086a0f7476e35908c5697",
    "0032_companion_review_tag_sources.py": "d3945b58903b2345caa81243dc867475e601afe743d6a5693815d91c61683dcd",
    "0033_media_analysis_proposals.py": "27a206cef7a114869fdad52110836e42fd0ef28116dd79ccf693c2a7845172d8",
    "0034_kronika_records.py": "f59b6bc28910378c5699057768c5740005ed12b56f79afbf1c18515b78823110",
    "0035_research_requests_and_accounting.py": "a05ab13a9d4bfa7f0d7fbe532d8c8d3cb43be1d826fc5a97d86a62ebc89c48c2",
    "__init__.py": "481b131444236a2cc2544f8a83585f28c52da320c73bbb94181edd5b1bc8447c",
}

EXPECTED_FRAMENEST_BASENAME_PATHS: frozenset[str] = frozenset(
    {
        "deploy/systemd/framenest-ai-credential-nvidia-nim.conf",
        "deploy/systemd/framenest-ai-credential-opencode-go.conf",
        "deploy/systemd/framenest-ai-credential-vercel-ai-gateway.conf",
        "deploy/systemd/framenest-catalog-backup.service",
        "deploy/systemd/framenest-catalog-backup.timer",
        "deploy/systemd/framenest-catalog-offdevice.service",
        "deploy/systemd/framenest-catalog-offdevice.timer",
        "deploy/systemd/framenest.env.example",
        "deploy/systemd/framenest-research-credential.conf",
        "deploy/systemd/framenest.service",
        "deploy/ubuntu/framenest-catalog-export-v1",
        "deploy/ubuntu/framenest-release",
        "deploy/ubuntu/framenest_release.py",
        "framenest",
        "scripts/operator/infosec/framenest_log_triage.sh",
        "scripts/operator/infosec/framenest_public_surface_check.sh",
        "scripts/operator/infosec/framenest_socket_permissions_check.sh",
        "scripts/operator/network/framenest_mullvad_egress.fish",
        "scripts/operator/network/framenest_mullvad_egress.sh",
        "scripts/operator/network/framenest_nuc_worker_gate.fish",
    }
)

PER_TREE_FRAMENEST_FILE_COUNT = {
    "src": 255,
    "tests": 320,
    "deploy": 19,
    "scripts": 7,
    "docs": 88,
    "extension": 12,
}

# Occurrence counts, not file counts. A content-only rename inside an already
# matching file leaves the file counts unchanged, so these are the measures that
# actually detect a missed content rename. See the `fn-production-env-deploy`
# case, whose filename is clean while its content names `framenest`.
PER_TREE_FRAMENEST_OCCURRENCE_COUNT = {
    "src": 2983,
    "tests": 4401,
    "deploy": 212,
    "scripts": 104,
    "docs": 1216,
    "extension": 199,
}

ENV_PREFIX_TOKEN_COUNT = 642
ENV_PREFIX_DISTINCT_NAME_COUNT = 101
ENV_PREFIX_BARE_SPELLING_COUNT = 16

MUTATION_HEADER = "X-FrameNest-Request"
MUTATION_HEADER_OCCURRENCE_COUNT = 59
MUTATION_HEADER_FILE_COUNT = 29

HOST_PATH_OCCURRENCE_COUNT = {
    "/opt/framenest": 204,
    "/etc/framenest": 76,
    "/var/lib/framenest": 94,
    "/var/cache/framenest": 21,
    "/mnt/framenest-catalog-offdevice": 13,
}

UNIT_ACCOUNT_OCCURRENCE_COUNT = {
    "User=framenest": 5,
    "Group=framenest": 5,
}

CAPITALIZED_OCCURRENCE_COUNT = 3364
CAPITALIZED_FILE_COUNT = 481

CONSOLE_SCRIPT_ENTRY_COUNT = 14

ENV_PREFIX_TOKEN_PATTERN = re.compile(r"FRAMENEST_[A-Z0-9_]+")
ENV_PREFIX_BARE_PATTERN = re.compile(r"FRAMENEST_(?![A-Z0-9_])")
CONSOLE_SCRIPT_PATTERN = re.compile(r"framenest-[a-z0-9-]+")

_SELF_RELATIVE_PATH = "tests/contract/test_kronika_identity_retention.py"


def _tracked_paths() -> list[str]:
    result = subprocess.run(
        ("git", "ls-files", "-z"),
        check=True,
        capture_output=True,
        cwd=REPOSITORY_ROOT,
    )
    raw = result.stdout.decode("utf-8")
    return sorted(
        entry
        for entry in raw.split("\0")
        # Submodule gitlinks are reported as directories and hold no repository
        # blob of this repository, so they are excluded exactly as `git grep`
        # does not descend into them.
        if entry and (REPOSITORY_ROOT / entry).is_file()
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _alembic_versions_directory() -> Path:
    candidates = sorted(REPOSITORY_ROOT.glob(_ALEMBIC_VERSIONS_GLOB))
    assert len(candidates) == 1, (
        "expected exactly one alembic versions directory, found "
        f"{[str(candidate) for candidate in candidates]}"
    )
    return candidates[0]


def _decoded_texts(relative_paths: list[str]) -> list[str]:
    """Decode tracked text files, skipping binaries exactly as `git grep -I` does."""
    return [text for _, text in _decoded_pairs(relative_paths)]


def _decoded_pairs(relative_paths: list[str]) -> list[tuple[str, str]]:
    """Pair each tracked text path with its decoded text, skipping binaries."""
    pairs: list[tuple[str, str]] = []
    for relative in relative_paths:
        raw = (REPOSITORY_ROOT / relative).read_bytes()
        if b"\0" in raw:
            continue
        pairs.append((relative, raw.decode("utf-8", errors="replace")))
    return pairs


# ---------------------------------------------------------------------------
# Part A - frozen-blob hashes
# ---------------------------------------------------------------------------


def test_frozen_adr_and_host_document_bytes_are_unchanged() -> None:
    mismatched = {
        relative: (expected, _sha256(REPOSITORY_ROOT / relative))
        for relative, expected in FROZEN_DOCUMENT_SHA256.items()
        if _sha256(REPOSITORY_ROOT / relative) != expected
    }

    assert not mismatched, f"frozen document bytes changed: {mismatched}"


def test_frozen_adr_and_host_document_set_is_complete() -> None:
    """Every ADR through 0084 plus the two host documents must be pinned."""
    present = {
        relative
        for relative in _tracked_paths()
        if re.fullmatch(r"docs/adr/\d{4}-.+\.md", relative)
        and int(relative.split("/")[-1][:4]) <= 84
    }
    present.add("docs/FEDORA_SERVICE.md")
    present.add("docs/NUC_HOST_BASELINE.md")

    assert present == set(FROZEN_DOCUMENT_SHA256), (
        "frozen document pin set drifted: "
        f"missing={sorted(present - set(FROZEN_DOCUMENT_SHA256))} "
        f"extra={sorted(set(FROZEN_DOCUMENT_SHA256) - present)}"
    )


def test_frozen_alembic_revision_bytes_are_unchanged() -> None:
    versions_directory = _alembic_versions_directory()
    mismatched = {
        name: (expected, _sha256(versions_directory / name))
        for name, expected in FROZEN_ALEMBIC_SHA256.items()
        if _sha256(versions_directory / name) != expected
    }

    assert not mismatched, f"applied alembic bytes changed: {mismatched}"


def test_frozen_alembic_revision_set_is_complete() -> None:
    versions_directory = _alembic_versions_directory()
    present = {path.name for path in versions_directory.iterdir() if path.is_file()}

    assert present == set(FROZEN_ALEMBIC_SHA256), (
        "frozen alembic pin set drifted: "
        f"missing={sorted(present - set(FROZEN_ALEMBIC_SHA256))} "
        f"extra={sorted(set(FROZEN_ALEMBIC_SHA256) - present)}"
    )


# ---------------------------------------------------------------------------
# Part B - path-name ledger
# ---------------------------------------------------------------------------


def test_framenest_basename_path_ledger_matches_exactly() -> None:
    measured = {
        relative
        for relative in _tracked_paths()
        if "framenest" in relative.rsplit("/", 1)[-1].lower()
    }

    assert measured == set(EXPECTED_FRAMENEST_BASENAME_PATHS), (
        "path-name ledger drifted: "
        f"unexpected={sorted(measured - set(EXPECTED_FRAMENEST_BASENAME_PATHS))} "
        f"missing={sorted(set(EXPECTED_FRAMENEST_BASENAME_PATHS) - measured)}"
    )


# ---------------------------------------------------------------------------
# Part C - content occurrence ledger
# ---------------------------------------------------------------------------


def _counted_paths() -> list[str]:
    """Tracked text paths excluding this ledger file.

    This file necessarily contains the very tokens it pins, so counting itself
    would be self-referential. Every later cut keeps it excluded.
    """
    return [relative for relative in _tracked_paths() if relative != _SELF_RELATIVE_PATH]


def test_per_tree_framenest_file_counts_match() -> None:
    """Count tracked files whose content contains `framenest` case-insensitively."""
    counted = _counted_paths()
    measured: dict[str, int] = {tree: 0 for tree in PER_TREE_FRAMENEST_FILE_COUNT}
    for relative, text in _decoded_pairs(counted):
        if "framenest" not in text.lower():
            continue
        for tree in measured:
            if relative.startswith(f"{tree}/"):
                measured[tree] += 1
                break

    assert measured == PER_TREE_FRAMENEST_FILE_COUNT


def test_per_tree_framenest_occurrence_counts_match() -> None:
    """Count `framenest` occurrences per tree, so a content-only rename fails."""
    measured: dict[str, int] = {tree: 0 for tree in PER_TREE_FRAMENEST_OCCURRENCE_COUNT}
    for relative, text in _decoded_pairs(_counted_paths()):
        occurrences = text.lower().count("framenest")
        if not occurrences:
            continue
        for tree in measured:
            if relative.startswith(f"{tree}/"):
                measured[tree] += occurrences
                break

    assert measured == PER_TREE_FRAMENEST_OCCURRENCE_COUNT


def test_environment_prefix_token_counts_match() -> None:
    texts = _decoded_texts(_counted_paths())
    tokens = [
        match
        for text in texts
        for match in ENV_PREFIX_TOKEN_PATTERN.findall(text)
    ]

    assert len(tokens) == ENV_PREFIX_TOKEN_COUNT
    assert len(set(tokens)) == ENV_PREFIX_DISTINCT_NAME_COUNT


def test_bare_environment_prefix_spellings_match() -> None:
    texts = _decoded_texts(_counted_paths())
    bare = [
        match
        for text in texts
        for match in ENV_PREFIX_BARE_PATTERN.findall(text)
    ]

    assert len(bare) == ENV_PREFIX_BARE_SPELLING_COUNT


def test_mutation_header_occurrence_counts_match() -> None:
    counted = _counted_paths()
    occurrences = 0
    files = 0
    for relative in counted:
        text = (REPOSITORY_ROOT / relative).read_bytes()
        if b"\0" in text:
            continue
        count = text.decode("utf-8", errors="replace").count(MUTATION_HEADER)
        if count:
            occurrences += count
            files += 1

    assert occurrences == MUTATION_HEADER_OCCURRENCE_COUNT
    assert files == MUTATION_HEADER_FILE_COUNT


def test_host_path_occurrence_counts_match() -> None:
    texts = _decoded_texts(_counted_paths())

    measured = {
        path: sum(text.count(path) for text in texts)
        for path in HOST_PATH_OCCURRENCE_COUNT
    }

    assert measured == HOST_PATH_OCCURRENCE_COUNT


def test_unit_account_occurrence_counts_match() -> None:
    texts = _decoded_texts(_counted_paths())

    measured = {
        marker: sum(text.count(marker) for text in texts)
        for marker in UNIT_ACCOUNT_OCCURRENCE_COUNT
    }

    assert measured == UNIT_ACCOUNT_OCCURRENCE_COUNT


def test_capitalized_framenest_occurrence_counts_match() -> None:
    counted = _counted_paths()
    occurrences = 0
    files = 0
    for relative in counted:
        raw = (REPOSITORY_ROOT / relative).read_bytes()
        if b"\0" in raw:
            continue
        count = raw.decode("utf-8", errors="replace").count("FrameNest")
        if count:
            occurrences += count
            files += 1

    assert occurrences == CAPITALIZED_OCCURRENCE_COUNT
    assert files == CAPITALIZED_FILE_COUNT


def test_framenest_console_script_entry_count_matches() -> None:
    text = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert len(CONSOLE_SCRIPT_PATTERN.findall(text)) == CONSOLE_SCRIPT_ENTRY_COUNT
