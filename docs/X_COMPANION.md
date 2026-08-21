# FrameNest X meme browser companion

This document is the operator and user setup guide for the unpacked Manifest
V3 companion under `extension/`. It does not authorize publication, NUC
deployment, signed-in X probing, or a yt-dlp pin change.

## What it does

An authenticated FrameNest user can:

- hover (or keyboard-focus) a green **+** at the bottom-right of each image,
  video, or GIF in an eligible X post and click **Save to FrameNest** to open
  a Save popup (Title, Description, Category, Search tags, Save). Category is
  a compact fieldset with General, Meme, Movie, and YouTube; one choice applies
  to every media item in the post. The header close **X**, Escape, or a click
  outside cancel without a request and restore focus to that **+**. Save
  submits the post permalink, the chosen `content_category`, and an optional
  caller-private alias (title, description, and selected existing tag keys); it
  does not send a per-asset media URL. Public JPEG and PNG photographs catalog;
  WebP and other still formats fail closed without transcoding. Overlay copy
  distinguishes saving, saved, already saved, partial, failed, catalog-removed,
  and unknown transport; failed Save keeps the plus glyph and a danger border,
  not an × and not generic success. Ordinary users see only right-aligned
  **Save**.
  Users with `analysis.run` also see **Save and analyze by AI** to the left
  of Save; that control saves now and does not run analysis from this popup.
- click into the reply composer to reveal a floating **+** on the right of
  "Post your reply" (not inserted into the X input row), then open an in-page
  FrameNest search popup above that button;
- type `++` in that same reply composer (after start-of-field or whitespace,
  not inside `C++`) to open the picker and consume those two characters;
- type a search in that in-page picker (blank or cleared search lists no
  catalog hit and shows no preview chrome; on-screen arrows appear only after
  two or more hits), see the selected meme as one JPEG preview, and attach it
  with Enter or Attach onto the composer file input;
- open the toolbar side panel to use the real FrameNest website at the stored
  Tailscale origin, and attach a Gallery item onto the bound X composer. In that
  hosted Gallery, open-original stays bottom-right and Attach sits top-left on
  the card image. Ordinary browser tabs keep open-original only. Gallery 📎
  attaches after the reply composer is focused, and the shell reports Attached
  only when that composer file input accepted the bytes.

Save is a hover/focus overlay at the bottom-right of own media tiles, not an
action-row control. Click opens the Save popup instead of silently posting
`{ url }`. Text-only posts have no Save. Attach is shown when the
composer is focused, not on mouseover, and is not the side panel. The in-page
picker is compact quick attach with preview; it is not the full website.
Empty search shows no preview chrome; arrows appear after two or more hits;
typing `++` in the reply composer opens the picker and consumes the token.
After connect, the in-page picker has no Settings sheet; an empty origin tells
the user to connect FrameNest in the side panel. First-run and reconnect Connect
live in side-panel Settings next to the origin field; the title-bar control
reads Disconnect (existing Reset) when connected and opens Settings when
disconnected with an empty origin. The toolbar opens
that shell, which iframes FrameNest only after the stored origin is granted.
If the iframe does not load, the shell reports that FrameNest did not load and
does not open a new tab. If the iframe loads without the companion host, the
library stays visible and the shell says this server cannot host companion
Attach yet. Per-asset Save targeting remains deferred.

Attach floats on the focused reply field; it is not inserted into the X input
row. Inline reply Attach is re-injected when X replaces the composer tree and the
previous button is no longer in the document. Save keeps a plus glyph when
the request fails; failure is the `title` / `aria-label` and a danger border,
not an ×.

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
5. Open the toolbar side panel. On first run or after Disconnect, open Settings
   in the green title bar, enter the exact FrameNest HTTPS origin
   (`https://<node>.<tailnet>.ts.net`, no path), then click Connect in Settings
   and grant the host permission when prompted. After Connect, Settings closes,
   the shell iframes that origin, and the title-bar control reads Disconnect.
   The in-page Search memes picker has no Settings sheet.
6. Use Disconnect in the side-panel title bar to clear stored origin, in-flight
   claim ids, and the granted host permission. Settings then opens so reconnect
   stays in one place.

Content scripts match only `https://x.com/*` and `https://twitter.com/*`. The
service worker has no X host permission.

## Residual gaps

- Live signed-in X DOM evidence is not part of repository acceptance.
- Independent INFOSEC R3 of the private status-bridge seam and CDN transport
  remains a later grant.
- Side-panel iframe framing against live Tailscale Serve or Brave Shields is
  a named residual until a later operator probe.
- A FrameNest origin that does not ship `companion_host.js` can still appear
  in the side panel; Gallery Attach requires that host script on the served
  web.
- Larger-than-32-MiB attach uses optional `chrome.downloads` with Save As;
  it still does not auto-post.
