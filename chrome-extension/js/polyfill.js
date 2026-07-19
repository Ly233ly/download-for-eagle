// Firefox and older Chromium builds do not expose the optional side-panel API.
if (!chrome.sidePanel?.setPanelBehavior) {
    chrome.sidePanel = {
        setOptions: function () {},
        setPanelBehavior: function () {},
    };
}
