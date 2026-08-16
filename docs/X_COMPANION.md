# FrameNest X meme browser companion

This document is the operator and user setup guide for the unpacked Manifest
V3 companion under `extension/`. It does not authorize publication, NUC
deployment, signed-in X probing, or a yt-dlp pin change.

## What it does

An authenticated FrameNest user can:

- click the action-row **Save to FrameNest** control next to Share on an
  eligible X post (existing X request lifecycle; static X photographs
  currently fail closed as `X_NO_SUPPORTED_MEDIA`);
- open the FrameNest picker while an X composer is active;
- attach one published meme or one of that user's own live successful X media
  items (JPEG/PNG, GIF-style, or short video) onto the composer file input.

The companion never clicks Post, never copies cookies or X credentials, and
never talks to FrameNest from a content script.

## Stable unpacked ID and private-key custody

The committed `extension/manifest.json` `key` field pins a development public
key. The derived unpacked extension origin is:

```text
chrome-extension://omiihmnlkmieaafaphohakcgmbggppap
```

The matching private key is local-only at `private/companion-extension.pem.key`
(gitignored via `/private/`). Do not commit, log, or copy that file into chat,
issues, or deployment artifacts. Rotating the key changes the extension ID and
requires an allowlist update.

## Server allowlist (inert until set)

Default `FRAMENEST_COMPANION_EXTENSION_ORIGINS` is empty. Browser mutations
other than the two flagged X request routes stay on the exact Tailscale web
origin. To enable the companion:

```text
FRAMENEST_COMPANION_EXTENSION_ORIGINS=["chrome-extension://omiihmnlkmieaafaphohakcgmbggppap"]
```

Rollback: remove the key or set it to `[]` and restart. No CORS is enabled.

## Load in Brave or Chromium

1. Open `brave://extensions` or `chrome://extensions`.
2. Enable Developer mode.
3. Load unpacked and select the repository `extension/` directory.
4. Confirm the ID is `omiihmnlkmieaafaphohakcgmbggppap`.
5. Open the side panel or action popup, enter the exact FrameNest HTTPS
   origin (`https://<node>.<tailnet>.ts.net`, no path), and grant the host
   permission when prompted.
6. Use Reset to clear stored origin, in-flight claim ids, and the granted
   host permission.

Content scripts match only `https://x.com/*` and `https://twitter.com/*`. The
service worker has no X host permission.

## Residual gaps

- Static X photograph Save is not implemented in the pinned yt-dlp extractor.
- Live signed-in X DOM evidence is not part of repository acceptance.
- Larger-than-32-MiB attach uses optional `chrome.downloads` with Save As;
  it still does not auto-post.
