# ADR-0063: Companion Side-Panel Web Host

## Status

`Accepted`

## Decision Date

`2026-08-17`

## Context

ADR-0061 accepted an unpacked Manifest V3 X companion whose service worker is
the only FrameNest network client, with `companion_mutation` limited to the two
X POST routes and with WAR limited to picker and Save on X hosts. ADR-0062
accepted a caller-private alias overlay and a Save popup. That Save popup
Cancel sentence is historical stale text relative to the later Save-popup
candidate; ADR-0062 is not edited in place.

The companion toolbar still cloned the in-page picker into the side panel. The
accepted product slice is that the side panel hosts the real FrameNest website
at the stored Tailscale origin, the in-page picker remains compact quick
attach, and Gallery may expose Attach only when that website is
companion-hosted. This is a new trust surface: MV3 side-panel hosting, an
https iframe of a Serve origin, `postMessage`, and a Gallery visual thaw in
extension context. It is not a silent rewrite of ADR-0061 or ADR-0062.

## Decision

Adopt a thin Manifest V3 side-panel shell that iframes the stored FrameNest
Tailscale origin after origin grant, plus a distinct web-bridge protocol and a
hosted-only Gallery Attach control:

1. **Three surfaces stay distinct.** Save (`ui/save.html|css|js`) remains the
   Worker 04 freeze. The in-page picker remains compact quick attach with one
   JPEG preview at a time. The side panel is not a picker clone.
2. **Shell plus iframe.** `ui/sidebar.html|js|css` is `side_panel.default_path`.
   `action.default_popup` is removed. `chrome.sidePanel.setPanelBehavior({
   openPanelOnActionClick: true })` runs on install and at service-worker
   startup. Empty `frameNestOrigin` shows Connect/Reset and does not set
   `iframe.src`. After existing `CONFIGURE_ORIGIN` (`acceptFrameNestOrigin`
   plus exact `origin + /*` optional host grant), the shell sets `iframe.src`
   to that origin only. The shell is not WAR. A blocked iframe is an honest
   shell error, not a new tab.
3. **Rejected hosting shortcuts.** No `externally_connectable`. No sandbox
   page. No manifest `content_security_policy.extension_pages`
   `frame-src https://*.ts.net` (CSP `*` matches one DNS label; Serve origins
   have more). No CORS. No `all_urls`. No content-script fetch of FrameNest or
   `pbs.twimg.com`. No application `X-Frame-Options` / `frame-ancestors`
   change in this candidate.
4. **Web bridge.** Protocol `v: "framenest.companion.web.v1"` is distinct from
   `framenest.companion.v1`. Types are `WEB_READY`, `HOST_HELLO`, `HOST_ACK`,
   `ATTACH_REQUEST`, and `ATTACH_RESULT`. The web sends `WEB_READY` only when
   `parent !== window`, with `targetOrigin` equal to the pinned unpacked
   extension origin `chrome-extension://omiihmnlkmieaafaphohakcgmbggppap`.
   The shell accepts only `event.source === iframe.contentWindow` and
   `event.origin` equal to the stored origin after `acceptFrameNestOrigin`.
   The web sets hosted true only after `HOST_HELLO` whose `event.origin` is
   that pinned extension origin. `?companion=1` and `parent !== window` alone
   are insufficient. `targetOrigin` is never `*`. `companion_host.js` owns
   `message` events; `app.js` does not listen for them.
5. **Attach authorization.** `ATTACH_REQUEST` carries only UUID `mediaId` and
   `locationId`. The shell forwards existing `TYPES.ATTACH_BEGIN`. The service
   worker builds the URL solely via `pathFor("content")` on the stored origin.
   Unbound composer returns `composer_unbound` with visible UI and no silent
   `fallbackDownload`. Oversize may still use existing `fallbackDownload`.
   `boundTabId` is assigned only from content-script senders whose
   `sender.origin` is `https://x.com` / `https://twitter.com` (including `www`
   hosts). Extension pages, the side panel, and WAR iframes must not overwrite
   it.
6. **Gallery thaw.** When companion-hosted and a supported location exists,
   Gallery replaces the bottom-right open-original control with an Attach
   button. Ordinary browser tabs keep open-original. Details, alias editor,
   lightbulb, and Analyze execution stay frozen. Zero new
   `companion_mutation` routes.
7. **Picker preview.** `TYPES.PREVIEW_FETCH` on `framenest.companion.v1`
   GETs `pathFor("preview")` as binary through the service worker, UUID-only,
   about 2 MiB. The picker renders one JPEG `<img>` plus title. Preview
   failure keeps the title.

## Consequences

Operators Reload unpacked after the manifest and shell change. First-run
Connect lives in the side-panel shell. Framing against live Tailscale Serve
and Brave Shields remains a named residual until a later probe. Independent
INFOSEC R3 acceptance of this trust surface is a later Worker. ADR-0061 origin
trust and ADR-0062 overlay semantics remain in force.

## References

- [ADR-0061](0061-x-meme-browser-companion.md)
- [ADR-0062](0062-per-user-media-alias-overlay.md)
- [ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
