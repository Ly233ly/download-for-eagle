(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    root.EagleBridgeCandidateLogic = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    const SITE_ICON = /(?:^|[\/_\-.])(favicon|apple-touch-icon|site-icon|site-logo)(?:[\/_\-.]|$)/i;
    const FRAME_DATA_URL = /^data:image\/(?:jpeg|png|webp);base64,[a-z0-9+/=]+$/i;
    const MAX_FRAME_DATA_URL_LENGTH = 300000;

    function safeThumbnailUrl(value) {
        try {
            const url = new URL(String(value || ""));
            return ["http:", "https:"].includes(url.protocol) && url.href.length <= 4096 ? url.href : "";
        } catch (_error) {
            return "";
        }
    }

    function safeFrameDataUrl(value) {
        const frame = String(value || "");
        return frame.length >= 32
            && frame.length <= MAX_FRAME_DATA_URL_LENGTH
            && FRAME_DATA_URL.test(frame)
            ? frame : "";
    }

    function canonicalMediaSource(value) {
        try {
            const url = new URL(String(value || ""), "https://invalid.local/");
            if (!["http:", "https:", "blob:"].includes(url.protocol)) return "";
            return url.protocol === "blob:"
                ? `blob:${url.pathname.split("/").slice(0, 2).join("/")}`
                : `${url.origin}${url.pathname}`;
        } catch (_error) {
            return "";
        }
    }

    function fnv1a(value) {
        let hash = 0x811c9dc5;
        for (const char of String(value || "")) {
            hash ^= char.charCodeAt(0);
            hash = Math.imul(hash, 0x01000193) >>> 0;
        }
        return hash.toString(36);
    }

    function stableVisualKey(source, ordinal = 0, duration = 0) {
        const canonical = canonicalMediaSource(source);
        const durationSecond = Number.isFinite(Number(duration)) ? Math.round(Number(duration)) : 0;
        return `player-${fnv1a(`${canonical}|${Number(ordinal) || 0}|${durationSecond}`)}`;
    }

    function resolveVisualMatch(players, mediaUrl) {
        const target = canonicalMediaSource(mediaUrl);
        if (!target) return { kind: "none", selected: null, matches: [] };
        const matches = (Array.isArray(players) ? players : []).filter(player =>
            (Array.isArray(player?.sources) ? player.sources : [])
                .some(source => canonicalMediaSource(source) === target)
        );
        return {
            kind: matches.length ? "exact" : "none",
            selected: matches[0] || null,
            matches
        };
    }

    function qualityHeight(value) {
        const match = String(value || "").match(/(?:^|\D)(\d{2,5})\s*p(?:\D|$)/i);
        return match ? Number(match[1]) || 0 : 0;
    }

    function sortedQualities(values) {
        const unique = new Map();
        for (const value of Array.isArray(values) ? values : []) {
            const height = qualityHeight(value);
            if (height >= 100 && height <= 10000) unique.set(height, `${height}p`);
        }
        return [...unique.entries()].sort((left, right) => right[0] - left[0]).map(([, label]) => label);
    }

    function reconstructByteRangeUrl(value) {
        let url;
        try { url = new URL(String(value || "")); } catch (_error) { return null; }
        const parameters = new Map([...url.searchParams].map(([name, parameter]) => [name.toLowerCase(), { name, parameter }]));
        const startEntry = parameters.get("bytestart");
        const endEntry = parameters.get("byteend");
        if (!startEntry || !endEntry || !/^\d+$/.test(startEntry.parameter) || !/^\d+$/.test(endEntry.parameter)) return null;
        const start = Number(startEntry.parameter);
        const end = Number(endEntry.parameter);
        if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || end < start) return null;
        url.searchParams.delete(startEntry.name);
        url.searchParams.delete(endEntry.name);
        return { url: url.href, start, end, span: end - start + 1 };
    }

    function decodeBase64Text(value) {
        const source = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
        if (!source || source.length > 8192) return "";
        try { return atob(source + "=".repeat((4 - source.length % 4) % 4)); } catch (_error) { return ""; }
    }

    function parseInstagramCdnMetadata(value) {
        let url;
        try { url = new URL(String(value || "")); } catch (_error) { return null; }
        if (!/(^|\.)(?:cdninstagram\.com|fbcdn\.net)$/i.test(url.hostname)) return null;
        const reconstructed = reconstructByteRangeUrl(url.href);
        if (!reconstructed) return null;
        const rawMetadata = decodeBase64Text(url.searchParams.get("efg"));
        if (!rawMetadata) return null;
        let metadata;
        try { metadata = JSON.parse(rawMetadata); } catch (_error) { return null; }
        const assetId = rawMetadata.match(/"xpv_asset_id"\s*:\s*"?(\d+)"?/i)?.[1] || "";
        if (!assetId) return null;
        const tag = String(metadata?.vencode_tag || "").slice(0, 180);
        const role = /(?:^|[_.-])audio(?:$|[_.-])/i.test(tag) ? "audio" : "video";
        const duration = Math.max(0, Number(metadata?.duration_s || 0));
        const bitrate = Math.max(0, Number(metadata?.bitrate || 0));
        const rank = tag.match(/(?:^|[_-])q(\d{1,3})(?:$|[_-])/i)?.[1] || "";
        const bitrateLabel = bitrate ? `${Math.round(bitrate / 1000)} Kbps` : "";
        return {
            url: reconstructed.url,
            role,
            streamId: `${role}-${rank || bitrate || reconstructed.start}`,
            groupKey: `instagram:${assetId}`,
            title: `Instagram 视频${duration ? ` · ${Math.round(duration)} 秒` : ""}`,
            label: [role === "audio" ? "音频" : "视频", rank ? `Q${rank}` : "", bitrateLabel].filter(Boolean).join(" · "),
            bitrate,
            duration,
            estimatedSize: duration && bitrate ? Math.ceil(duration * bitrate / 8) : 0,
            separateAv: true,
            reconstructedRange: true
        };
    }

    function chooseContentPageUrl(currentValue, linkValues) {
        let current;
        try { current = new URL(String(currentValue || "")); } catch (_error) { return ""; }
        if (!["http:", "https:"].includes(current.protocol)) return "";
        const safeContentQuery = url => {
            const rules = [
                ["v", /^\/watch\/?$/i],
                ["video_id", /^\/(?:watch|video|videos)\/?$/i],
                ["modal_id", /^\/(?:jingxuan|discover)\/?$/i],
                ["story_fbid", /^\/(?:watch|video|videos|[^/]+)\/?$/i]
            ];
            for (const [name, pathRule] of rules) {
                const value = url.searchParams.get(name) || "";
                if (pathRule.test(url.pathname) && /^[a-z0-9_-]{5,80}$/i.test(value)) return [name, value];
            }
            return null;
        };
        const canonical = value => {
            try {
                const url = new URL(String(value || ""), current.href);
                if (url.origin !== current.origin || !["http:", "https:"].includes(url.protocol)) return null;
                const contentQuery = safeContentQuery(url);
                url.search = "";
                url.hash = "";
                url.pathname = url.pathname.replace(/\/+$/, "") || "/";
                if (contentQuery) url.searchParams.set(contentQuery[0], contentQuery[1]);
                return url;
            } catch (_error) { return null; }
        };
        const mediaPath = /\/(?:p|reel|reels|video|videos|clip|clips|status|post|posts|pin)\/[a-z0-9_-]+$/i;
        const discussionPath = /\/comments\/[a-z0-9_-]+(?:\/[a-z0-9_-]+)?$/i;
        const storyPath = /\/stories\/[a-z0-9_.-]+\/[a-z0-9_-]+$/i;
        const compoundVideoPath = /\/(?:video|clip)[-_][a-z0-9_-]+$/i;
        const isContentUrl = url => mediaPath.test(url.pathname)
            || discussionPath.test(url.pathname)
            || storyPath.test(url.pathname)
            || compoundVideoPath.test(url.pathname)
            || Boolean(safeContentQuery(url));
        const currentCanonical = canonical(current.href);
        if (currentCanonical && isContentUrl(currentCanonical)) return currentCanonical.href;
        const candidates = [...new Set((Array.isArray(linkValues) ? linkValues : [])
            .map(canonical)
            .filter(url => url && isContentUrl(url))
            .map(url => url.href))];
        candidates.sort((left, right) => new URL(left).pathname.length - new URL(right).pathname.length || left.localeCompare(right));
        return candidates[0] || "";
    }

    function parseManifestQualities(source, kind = "") {
        const text = String(source || "");
        if (!text || text.length > 2_000_000) return [];
        const manifestKind = String(kind || "").toLowerCase();
        const heights = [];
        if (manifestKind.includes("mpd") || /<MPD(?:\s|>)/i.test(text)) {
            for (const match of text.matchAll(/\bheight\s*=\s*["'](\d{2,5})["']/gi)) {
                heights.push(`${match[1]}p`);
            }
        } else {
            for (const match of text.matchAll(/\bRESOLUTION\s*=\s*(\d{2,5})\s*[x×]\s*(\d{2,5})/gi)) {
                heights.push(`${match[2]}p`);
            }
        }
        return sortedQualities(heights);
    }

    function parseVimeoPlayerConfig(source) {
        const text = String(source || "");
        const marker = "window.playerConfig";
        const markerIndex = text.indexOf(marker);
        if (markerIndex < 0 || text.length > 2_000_000) return null;
        const start = text.indexOf("{", markerIndex + marker.length);
        const end = text.lastIndexOf("}");
        if (start < 0 || end <= start) return null;
        let config;
        try { config = JSON.parse(text.slice(start, end + 1)); } catch (_error) { return null; }
        const video = config?.video;
        const files = config?.request?.files;
        const hls = files?.hls;
        if (!video || !hls || typeof hls !== "object") return null;
        const cdns = hls.cdns && typeof hls.cdns === "object" ? hls.cdns : {};
        const selectedCdn = cdns[hls.default_cdn] || Object.values(cdns)[0];
        const url = safeThumbnailUrl(selectedCdn?.avc_url || selectedCdn?.url);
        if (!url || !/\.m3u8(?:$|[?#])/i.test(url)) return null;
        const streams = [
            ...(Array.isArray(files?.dash?.streams) ? files.dash.streams : []),
            ...(Array.isArray(files?.dash?.streams_avc) ? files.dash.streams_avc : [])
        ];
        const availableQualities = sortedQualities(streams.map(stream => stream?.quality));
        const fallbackHeight = Number(video.height) || 0;
        if (!availableQualities.length && fallbackHeight > 0) availableQualities.push(`${fallbackHeight}p`);
        const videoId = String(video.id || "").replace(/[^a-z0-9_-]/gi, "").slice(0, 100);
        if (!videoId) return null;
        return {
            url,
            extension: "m3u8",
            mimeType: "application/vnd.apple.mpegurl",
            groupKey: `vimeo:${videoId}`,
            title: String(video.title || "").slice(0, 220),
            width: Number(video.width) || 0,
            height: fallbackHeight,
            duration: Number(video.duration) || 0,
            thumbnailUrl: safeThumbnailUrl(video.thumbnail_url),
            availableQualities,
            label: availableQualities[0] ? `最高 ${availableQualities[0]}` : "自动质量",
            separateAv: Boolean(hls.separate_av)
        };
    }

    function selectThumbnail(sources = {}) {
        for (const kind of ["exact", "playing", "visible", "nearby", "metadata"]) {
            const values = Array.isArray(sources[kind]) ? sources[kind] : [];
            for (const value of values) {
                const url = safeThumbnailUrl(value);
                if (!url) continue;
                if (kind === "metadata" && SITE_ICON.test(new URL(url).pathname)) continue;
                return url;
            }
        }
        return "";
    }

    function waitForSnapshot(isReady, readSnapshot, timeoutMs = 2000, pollMs = 20) {
        return new Promise(resolve => {
            const started = Date.now();
            const check = () => {
                if (isReady() || Date.now() - started >= timeoutMs) {
                    resolve(readSnapshot());
                    return;
                }
                setTimeout(check, pollMs);
            };
            check();
        });
    }

    return {
        safeThumbnailUrl,
        safeFrameDataUrl,
        stableVisualKey,
        resolveVisualMatch,
        reconstructByteRangeUrl,
        parseInstagramCdnMetadata,
        chooseContentPageUrl,
        parseManifestQualities,
        parseVimeoPlayerConfig,
        selectThumbnail,
        waitForSnapshot
    };
});
