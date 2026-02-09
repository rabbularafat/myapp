chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (tab && tab.url && !tab.url.includes("google.com")) {
      chrome.tabs.update(activeInfo.tabId, { url: "https://www.google.com" });
    }
  });
});

// Also handle new tabs that are created as active
chrome.tabs.onCreated.addListener((tab) => {
  if (tab.active) {
    chrome.tabs.update(tab.id, { url: "https://www.google.com" });
  }
});
