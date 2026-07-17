importScripts("bootstrap.js");

const API_BASE = "http://127.0.0.1:47652";
const RETRY_ALARM = "retry-source-events";
const BOOTSTRAP_SECRET = String(globalThis.IDM_EAGLE_BOOTSTRAP_SECRET || "");
let flushPromise = null;
let fastRetryScheduled = false;
let autoPairPromise = null;

async function getState() {
  const [localState, sessionState] = await Promise.all([
    chrome.storage.local.get({ token: "", pendingEvents: [] }),
    chrome.storage.session.get({ token: "" })
  ]);
  const token = localState.token || sessionState.token || "";
  if (token && localState.token !== token) {
    await chrome.storage.local.set({ token });
  }
  return { ...localState, token };
}

async function saveToken(token) {
  await Promise.all([
    chrome.storage.local.set({ token }),
    chrome.storage.session.set({ token })
  ]);
  const state = await getState();
  if (state.token !== token) throw new Error("Chrome 未能保存配对状态，请刷新扩展后重试");
}

async function clearToken() {
  await Promise.all([
    chrome.storage.local.remove("token"),
    chrome.storage.session.remove("token")
  ]);
}

async function api(path, options = {}) {
  let { token } = await getState();
  if (!token && path !== "/api/pair" && path !== "/api/pair/auto") {
    await tryAutoPair();
    token = (await getState()).token;
  }
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let body = options.body;
  if (token && body && String(options.method || "GET").toUpperCase() === "POST") {
    try {
      body = JSON.stringify({ ...JSON.parse(body), authToken: token });
    } catch (_error) {
      // 保留非 JSON 请求体，由服务器按原方式处理。
    }
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, body, headers });
  const result = await response.json().catch(() => ({ ok: false, error: "本机助手返回格式错误" }));
  if (!response.ok || !result.ok) throw new Error(result.error || "本机助手连接失败");
  return result.data;
}

async function tryAutoPair() {
  const state = await getState();
  if (state.token) return true;
  if (!BOOTSTRAP_SECRET) return false;
  if (autoPairPromise) return autoPairPromise;
  autoPairPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/api/pair/auto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secret: BOOTSTRAP_SECRET })
      });
      const result = await response.json().catch(() => ({ ok: false }));
      if (!response.ok || !result.ok || !result.data?.token) return false;
      await saveToken(result.data.token);
      scheduleRetries();
      return true;
    } catch (_error) {
      return false;
    } finally {
      autoPairPromise = null;
    }
  })();
  return autoPairPromise;
}

async function pair(code) {
  const data = await api("/api/pair", { method: "POST", body: JSON.stringify({ code }) });
  if (!data?.token) throw new Error("本机助手未返回有效配对信息");
  await saveToken(data.token);
  scheduleRetries();
  flushEvents();
  return data;
}

async function currentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function siteStatus(domain) {
  return api("/api/site/status", {
    method: "POST",
    body: JSON.stringify({ domain })
  });
}

async function setSite(domain, enabled) {
  return api("/api/site", {
    method: "POST",
    body: JSON.stringify({ domain, enabled, includeSubdomains: true })
  });
}

async function queueSourceEvent(event) {
  if (flushPromise) await flushPromise;
  const state = await getState();
  const queue = Array.isArray(state.pendingEvents) ? state.pendingEvents : [];
  queue.push(event);
  await chrome.storage.local.set({ pendingEvents: queue.slice(-200) });
  scheduleRetries();
  return flushEvents();
}

function scheduleRetries() {
  chrome.alarms.create(RETRY_ALARM, { delayInMinutes: 0.5 });
  if (fastRetryScheduled) return;
  fastRetryScheduled = true;
  setTimeout(() => flushEvents(), 1000);
  setTimeout(() => flushEvents(), 2500);
  setTimeout(() => {
    fastRetryScheduled = false;
    flushEvents();
  }, 5000);
}

async function resolveDeferredSiteCheck(event) {
  if (!event.deferSiteCheck) return event;
  const domain = new URL(event.pageUrl).hostname;
  const site = await siteStatus(domain);
  const resolved = { ...event };
  delete resolved.deferSiteCheck;
  if (!site.enabled) resolved.eventType = "site_disabled";
  return resolved;
}

async function flushEventsOnce() {
  const state = await getState();
  if (!state.token || !Array.isArray(state.pendingEvents) || state.pendingEvents.length === 0) return;
  let nextIndex = 0;
  for (; nextIndex < state.pendingEvents.length; nextIndex += 1) {
    let event = state.pendingEvents[nextIndex];
    try {
      event = await resolveDeferredSiteCheck(event);
      state.pendingEvents[nextIndex] = event;
      await api("/api/source", { method: "POST", body: JSON.stringify(event) });
    } catch (error) {
      break;
    }
  }
  await chrome.storage.local.set({ pendingEvents: state.pendingEvents.slice(nextIndex).slice(-200) });
}

function flushEvents() {
  if (flushPromise) return flushPromise;
  flushPromise = flushEventsOnce().finally(() => {
    flushPromise = null;
  });
  return flushPromise;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    if (message.type === "pair") return pair(message.code);
    if (message.type === "authState") {
      await tryAutoPair();
      const state = await getState();
      return { paired: Boolean(state.token) };
    }
    if (message.type === "resetAuth") {
      await clearToken();
      return { paired: false };
    }
    if (message.type === "currentTab") return currentTab();
    if (message.type === "siteStatus") return siteStatus(message.domain);
    if (message.type === "setSite") return setSite(message.domain, message.enabled);
    if (message.type === "sourceEvent") {
      const tab = sender.tab;
      const pageUrl = message.pageUrl || tab?.url || "";
      const domain = new URL(pageUrl).hostname;
      let enabled = false;
      let deferSiteCheck = false;
      try {
        enabled = (await siteStatus(domain)).enabled;
      } catch (_error) {
        deferSiteCheck = true;
      }
      return queueSourceEvent({
        pageUrl,
        pageTitle: message.pageTitle || tab?.title || "",
        mediaUrl: message.mediaUrl || "",
        eventType: deferSiteCheck || enabled
          ? (message.eventType || "download_intent")
          : "site_disabled",
        tabId: tab?.id,
        capturedAt: message.capturedAt || Date.now(),
        ...(deferSiteCheck ? { deferSiteCheck: true } : {})
      });
    }
    if (message.type === "manualSource") {
      const tab = await currentTab();
      return queueSourceEvent({
        pageUrl: tab.url,
        pageTitle: tab.title || "",
        mediaUrl: "",
        eventType: "manual",
        tabId: tab.id,
        capturedAt: Date.now()
      });
    }
    if (message.type === "ignoreNext") {
      const tab = await currentTab();
      return queueSourceEvent({
        pageUrl: tab.url,
        pageTitle: tab.title || "",
        mediaUrl: "",
        eventType: "ignore",
        tabId: tab.id,
        capturedAt: Date.now()
      });
    }
    throw new Error("未知操作");
  })().then((data) => sendResponse({ ok: true, data })).catch((error) => {
    sendResponse({ ok: false, error: error.message });
  });
  return true;
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === RETRY_ALARM) flushEvents();
});

chrome.runtime.onStartup.addListener(() => tryAutoPair().then(flushEvents));
chrome.runtime.onInstalled.addListener(() => tryAutoPair().then(flushEvents));

const recentVideoRequests = new Map();
const VIDEO_REQUEST = /\.(mp4|mov|mkv|webm|avi|m4v|mpeg|mpg|ts|m2ts|wmv)(?:$|[?#])/i;

chrome.webRequest.onBeforeRequest.addListener((details) => {
  if (details.tabId < 0 || !VIDEO_REQUEST.test(details.url)) return;
  chrome.tabs.get(details.tabId).then(async (tab) => {
    if (!tab.url?.startsWith("http")) return;
    const key = `${details.tabId}:${tab.url}`;
    const now = Date.now();
    if (now - (recentVideoRequests.get(key) || 0) < 10000) return;
    recentVideoRequests.set(key, now);
    if (recentVideoRequests.size > 500) {
      for (const [entryKey, capturedAt] of recentVideoRequests) {
        if (now - capturedAt > 5 * 60 * 1000) recentVideoRequests.delete(entryKey);
      }
    }
    const domain = new URL(tab.url).hostname;
    let enabled = false;
    let deferSiteCheck = false;
    try {
      enabled = (await siteStatus(domain)).enabled;
    } catch (_error) {
      deferSiteCheck = true;
    }
    if (!enabled && !deferSiteCheck) return;
    await queueSourceEvent({
      pageUrl: tab.url,
      pageTitle: tab.title || "",
      mediaUrl: details.url,
      eventType: "video_request",
      tabId: tab.id,
      capturedAt: now,
      ...(deferSiteCheck ? { deferSiteCheck: true } : {})
    });
  }).catch(() => {});
}, { urls: ["http://*/*", "https://*/*"] });
