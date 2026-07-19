function isLockUrl(url) {
    for (const item of G.blockUrl || []) {
        if (!item.state) continue;
        item.url.lastIndex = 0;
        if (item.url.test(url)) return true;
    }
    return false;
}

// Candidate URLs and request headers can contain cookies, authorization data,
// or temporary signatures. They are intentionally session-only.
function saveMediaData(data, callback = undefined) {
    if (!chrome.storage.session) {
        callback?.();
        return;
    }
    chrome.storage.session.set({ MediaData: data }, callback);
}

function loadMediaData(callback) {
    if (!chrome.storage.session) {
        callback({ MediaData: {} });
        return;
    }
    chrome.storage.session.get({ MediaData: {} }, callback);
}

function isSafeRegularExpression(pattern) {
    const value = String(pattern || "");
    if (!value || value.length > 256) return false;
    if (/\\[1-9]/.test(value)) return false;
    if (/\([^)]*[+*][^)]*\)[+*{]/.test(value)) return false;
    if (/\([^)]*\{\d+,?\d*\}[^)]*\)[+*{]/.test(value)) return false;
    if (/(?:\.\*|\.\+){2,}/.test(value)) return false;
    if ((value.match(/\|/g) || []).length > 32) return false;
    return true;
}
