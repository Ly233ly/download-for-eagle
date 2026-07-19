(function () {
    "use strict";
    if (globalThis.__downloadTransferEnhancedCapture) return;
    globalThis.__downloadTransferEnhancedCapture = true;

    const MEDIA_EXTENSION = /\.(?:mp4|m4v|m4a|m4s|mp3|aac|flac|wav|ogg|opus|webm|mov|mkv|avi|flv|ts|m2ts|m3u8?|mpd)(?:$|[?#])/i;
    const MEDIA_TYPE = /^(?:audio|video)\//i;
    const MANIFEST_TYPE = /(?:mpegurl|dash\+xml)/i;
    const sent = new Set();

    function absoluteUrl(value) {
        try {
            const url = new URL(String(value || ""), location.href);
            return ["http:", "https:", "blob:"].includes(url.protocol) ? url.href : "";
        } catch (_error) {
            return "";
        }
    }

    function extensionFor(url, contentType = "") {
        const match = String(url).match(/\.([a-z0-9]{2,5})(?:$|[?#])/i);
        if (match) return match[1].toLowerCase();
        if (/mpegurl/i.test(contentType)) return "m3u8";
        if (/dash\+xml/i.test(contentType)) return "mpd";
        if (/video\/mp4/i.test(contentType)) return "mp4";
        if (/audio\/mp4/i.test(contentType)) return "m4a";
        return "";
    }

    function publish(value, contentType = "") {
        const url = absoluteUrl(value);
        if (!url || sent.has(url)) return;
        if (!MEDIA_EXTENSION.test(url) && !MEDIA_TYPE.test(contentType) && !MANIFEST_TYPE.test(contentType)) return;
        sent.add(url);
        if (sent.size > 2000) sent.delete(sent.values().next().value);
        window.postMessage({
            action: "downloadTransferAddMedia",
            url,
            href: location.href,
            ext: extensionFor(url, contentType),
            mime: contentType,
        }, location.origin);
    }

    function scanElements() {
        for (const element of document.querySelectorAll("video, audio, source")) {
            publish(element.currentSrc || element.src || element.getAttribute("src"), element.type || "");
        }
    }

    let scanPending = false;
    function scheduleElementScan() {
        if (scanPending) return;
        scanPending = true;
        queueMicrotask(() => {
            scanPending = false;
            scanElements();
        });
    }

    for (const entry of performance.getEntriesByType("resource")) publish(entry.name, entry.initiatorType || "");
    try {
        new PerformanceObserver(list => {
            for (const entry of list.getEntries()) publish(entry.name, entry.initiatorType || "");
        }).observe({ type: "resource", buffered: true });
    } catch (_error) { /* PerformanceObserver is optional. */ }

    const nativeFetch = globalThis.fetch;
    if (typeof nativeFetch === "function") {
        globalThis.fetch = async function (...args) {
            const response = await nativeFetch.apply(this, args);
            publish(response.url || args[0]?.url || args[0], response.headers?.get?.("content-type") || "");
            return response;
        };
    }

    const nativeOpen = XMLHttpRequest.prototype.open;
    const nativeSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (method, url, ...args) {
        this.__downloadTransferUrl = absoluteUrl(url);
        return nativeOpen.call(this, method, url, ...args);
    };
    XMLHttpRequest.prototype.send = function (...args) {
        this.addEventListener("loadend", () => {
            let contentType = "";
            try { contentType = this.getResponseHeader("content-type") || ""; } catch (_error) { /* ignored */ }
            publish(this.responseURL || this.__downloadTransferUrl, contentType);
        }, { once: true });
        return nativeSend.apply(this, args);
    };

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", scanElements, { once: true });
    else scanElements();
    new MutationObserver(scheduleElementScan).observe(document.documentElement, { childList: true, subtree: true });
})();
