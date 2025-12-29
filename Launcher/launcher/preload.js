const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  minimize: () => ipcRenderer.send("window:minimize"),
  closeApp: () => ipcRenderer.send("window:close"),

  openExternal: (url) => ipcRenderer.send("open-external", url),

  openTelegram: () =>
    ipcRenderer.send("open-external", "http://t.me/cybecraft_uz"),
  openYoutube: () =>
    ipcRenderer.send("open-external", "http://www.youtube.com/@CyberCraft_UZ"),
  openDiscord: () =>
    ipcRenderer.send("open-external", "http://discord.gg/cybercraft"),

  saveUserData: (data) => ipcRenderer.invoke("save-user-data", data),
  getUserData: () => ipcRenderer.invoke("get-user-data"),
  logout: () => ipcRenderer.invoke("logout"),

  getMaxRAM: () => ipcRenderer.invoke("get-max-ram"),
  loadSettings: () => ipcRenderer.invoke("get-settings"),
  saveSettings: (settings) => ipcRenderer.invoke("save-settings", settings),
  selectGamePath: () => ipcRenderer.invoke("dialog:select-folder"),

  launchGame: (options) => ipcRenderer.invoke("launch-game", options),

  onGameLog: (callback) => {
    ipcRenderer.removeAllListeners("game-log");
    ipcRenderer.on("game-log", (_, message) => callback(message));
  },
});
