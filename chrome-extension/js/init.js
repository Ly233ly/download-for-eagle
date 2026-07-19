// Runtime configuration for media discovery. Downloading, merging and Eagle
// delivery deliberately live in the desktop application.
var G = {
    initSyncComplete: false,
    initLocalComplete: true,
    initMediaComplete: false,
    blockUrlSet: new Set(),
    deepSearchTemporarilyClose: null,
};
var cacheData = { init: true };

chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    G.tabId = tabs[0]?.id || -1;
});

G.OptionLists = {
    Ext: [
        "flv", "hlv", "f4v", "mp4", "mp3", "wma", "wav", "m4a", "webm",
        "ogg", "ogv", "mov", "mkv", "m4s", "m3u8", "m3u", "mpeg", "avi",
        "wmv", "asf", "movie", "divx", "mpeg4", "vid", "aac", "mpd", "weba", "opus"
    ].map(ext => ({ ext, size: 0, operator: ">=", unit: "KB", state: true })),
    Type: [
        "audio/*", "video/*", "application/ogg", "application/vnd.apple.mpegurl",
        "application/x-mpegurl", "application/mpegurl", "application/octet-stream-m3u8",
        "application/dash+xml", "application/m4s"
    ].map(type => ({ type, size: 0, operator: ">=", unit: "KB", state: true })),
    Regex: [
        { type: "ig", regex: "https://cache\\.video\\.[a-z]*\\.com/dash\\?tvid=.*", ext: "json", state: false },
        { type: "ig", regex: ".*\\.bilivideo\\.(com|cn).*\\/live-bvc\\/.*m4s", ext: "", blackList: true, state: false },
        { type: "ig", regex: "(^https://scontent[a-z0-9-]*\\.cdninstagram\\.com/.*)&bytestart=.*", ext: "", blackList: false, state: false },
        { type: "ig", regex: "(^https://.*\\.fbcdn\\.net/.*)&bytestart=.*", ext: "", blackList: false, state: false },
    ],
    autoClearMode: 1,
    checkDuplicates: true,
    enable: true,
    badgeNumber: true,
    blockUrl: [],
    blockUrlWhite: false,
    maxLength: 9999,
    sidePanel: false,
    deepSearch: false,
};

G.isFirefox = navigator.userAgent.includes("Firefox") && typeof browser !== "undefined" && Boolean(browser.runtime?.getBrowserInfo);
const browserVersion = navigator.userAgent.match(/(?:Chrome|Firefox)\/([\d]+)/);
G.version = browserVersion?.[1] ? Number.parseInt(browserVersion[1], 10) : 93;
G.scriptList = new Map([
    ["search.js", { key: "search", refresh: true, allFrames: true, world: "MAIN", tabId: new Set() }],
]);

function compileRangeMap(items, keyName) {
    return new Map(items.map(source => {
        const item = { ...source, operator: source.operator ?? ">=" };
        if (item.operator === "~") {
            const [minimum, maximum] = String(item.size || "").split("-");
            item.min = minimum ? Number.parseInt(minimum, 10) : 0;
            item.max = maximum ? Number.parseInt(maximum, 10) : 0;
        }
        return [item[keyName], item];
    }));
}

function compileRegexRules(items) {
    return items.map(source => {
        const item = { ...source };
        let regex;
        if (!isSafeRegularExpression(item.regex)) item.state = false;
        else {
            try { regex = new RegExp(item.regex, item.type); }
            catch (_error) { item.state = false; }
        }
        return { regex, ext: item.ext, blackList: item.blackList, state: item.state };
    });
}

function compileBlockedUrls(items) {
    return items.map(item => ({ url: wildcardToRegex(item.url), state: item.state }));
}

function applyOptions(items) {
    items.Ext = compileRangeMap(items.Ext, "ext");
    items.Type = compileRangeMap(items.Type, "type");
    items.Regex = compileRegexRules(items.Regex);
    items.blockUrl = compileBlockedUrls(items.blockUrl);
    G = { ...items, ...G };
    chrome.sidePanel?.setPanelBehavior?.({ openPanelOnActionClick: Boolean(items.sidePanel) });
    chrome.action.setIcon({ path: "/icons/icon-128.png" });
    G.initSyncComplete = true;
}

function InitOptions() {
    loadMediaData(function (items) {
        cacheData = items.MediaData?.init ? {} : (items.MediaData || {});
        G.initMediaComplete = true;
    });
    chrome.storage.sync.get(G.OptionLists, function (items) {
        applyOptions(chrome.runtime.lastError ? { ...G.OptionLists } : items);
        chrome.tabs.query({}, function (tabs) {
            for (const tab of tabs) {
                if (!tab.url) continue;
                if (isLockUrl(tab.url)) G.blockUrlSet.add(tab.id);
            }
        });
    });
}

InitOptions();

chrome.storage.onChanged.addListener(function (changes) {
    if (changes.MediaData) {
        if (changes.MediaData.newValue?.init) cacheData = {};
        return;
    }
    for (const [key, change] of Object.entries(changes)) {
        const value = change.newValue ?? G.OptionLists[key];
        if (key === "Ext") G.Ext = compileRangeMap(value, "ext");
        else if (key === "Type") G.Type = compileRangeMap(value, "type");
        else if (key === "Regex") G.Regex = compileRegexRules(value);
        else if (key === "blockUrl") G.blockUrl = compileBlockedUrls(value);
        else if (key === "sidePanel") chrome.sidePanel?.setPanelBehavior?.({ openPanelOnActionClick: Boolean(value) });
        else G[key] = value;
    }
});

function wildcardToRegex(urlPattern) {
    const regexPattern = String(urlPattern || "")
        .replace(/[.+^${}()|[\]\\]/g, "\\$&")
        .replace(/\*/g, ".*")
        .replace(/\?/g, ".");
    return new RegExp(`^${regexPattern}$`, "i");
}
