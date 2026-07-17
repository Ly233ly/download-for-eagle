const siteLabel = document.querySelector("#site");
const pairing = document.querySelector("#pairing");
const controls = document.querySelector("#controls");
const codeInput = document.querySelector("#code");
const pairButton = document.querySelector("#pair");
const enabledInput = document.querySelector("#enabled");
const manualButton = document.querySelector("#manual");
const ignoreButton = document.querySelector("#ignore");
const statusLabel = document.querySelector("#status");

let domain = "";

function message(payload) {
  return chrome.runtime.sendMessage(payload);
}

function setStatus(text, type = "") {
  statusLabel.textContent = text;
  statusLabel.className = type;
}

async function refresh() {
  const response = await message({ type: "currentTab" });
  if (!response.ok || !response.data?.url?.startsWith("http")) {
    throw new Error("当前页面不是普通网页");
  }
  domain = new URL(response.data.url).hostname;
  siteLabel.textContent = domain;

  const auth = await message({ type: "authState" });
  if (!auth.ok || !auth.data?.paired) {
    pairing.hidden = false;
    controls.hidden = true;
    return;
  }

  const site = await message({ type: "siteStatus", domain });
  if (!site.ok) {
    if (/配对/.test(site.error || "")) {
      await message({ type: "resetAuth" });
      pairing.hidden = false;
      controls.hidden = true;
      setStatus("配对验证失败，请先重启桌面助手，再重新配对。", "error");
      return;
    }
    throw new Error(site.error);
  }
  enabledInput.checked = Boolean(site.data.enabled);
  pairing.hidden = true;
  controls.hidden = false;
}

pairButton.addEventListener("click", async () => {
  try {
    const code = codeInput.value.trim();
    if (!/^\d{6}$/.test(code)) throw new Error("请输入六位数字配对码");
    const result = await message({ type: "pair", code });
    if (!result.ok) throw new Error(result.error);
    setStatus("配对成功", "success");
    await refresh();
  } catch (error) {
    setStatus(error.message, "error");
  }
});

enabledInput.addEventListener("change", async () => {
  const desired = enabledInput.checked;
  try {
    const result = await message({ type: "setSite", domain, enabled: desired });
    if (!result.ok) throw new Error(result.error);
    setStatus(desired ? "本网站已开启自动导入" : "本网站已关闭自动导入", "success");
  } catch (error) {
    enabledInput.checked = !desired;
    setStatus(error.message, "error");
  }
});

manualButton.addEventListener("click", async () => {
  try {
    if (!enabledInput.checked) throw new Error("请先开启本网站自动导入");
    const result = await message({ type: "manualSource" });
    if (!result.ok) throw new Error(result.error);
    setStatus("当前网页已记录，可继续点击 IDM 下载；即使记录失败，视频仍会导入。", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

ignoreButton.addEventListener("click", async () => {
  try {
    const result = await message({ type: "ignoreNext" });
    if (!result.ok) throw new Error(result.error);
    setStatus("下一次 IDM 下载将不会导入", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

refresh().catch((error) => setStatus(error.message, "error"));
