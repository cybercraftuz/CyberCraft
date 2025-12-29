const { app, BrowserWindow, ipcMain, shell, dialog } = require("electron");
const path = require("path");
const fs = require("fs");
const os = require("os");

const { launchGame } = require("../game/launch");

let mainWindow;

function getUserDataPath(file) {
  return path.join(app.getPath("userData"), file);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 600,
    resizable: false,
    frame: false,
    transparent: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "index.html"));

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

ipcMain.on("window:minimize", () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on("window:close", () => {
  app.quit();
});

ipcMain.on("open-external", (_, url) => {
  shell.openExternal(url);
});

ipcMain.handle("get-user-data", () => {
  const p = getUserDataPath("user.json");
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, "utf-8"));
});

ipcMain.handle("save-user-data", (_, data) => {
  fs.writeFileSync(
    getUserDataPath("user.json"),
    JSON.stringify(data, null, 2),
    "utf-8"
  );
  return { ok: true };
});

ipcMain.handle("logout", () => {
  const p = getUserDataPath("user.json");
  if (fs.existsSync(p)) fs.unlinkSync(p);
  return { ok: true };
});

ipcMain.handle("get-settings", () => {
  const p = getUserDataPath("settings.json");
  if (!fs.existsSync(p)) {
    return {
      ram: Math.min(
        4,
        Math.max(2, Math.floor(os.totalmem() / 1024 / 1024 / 1024) - 1)
      ),
      gamePath: path.join(app.getPath("userData"), "CyberCraft"),
    };
  }
  return JSON.parse(fs.readFileSync(p, "utf-8"));
});

ipcMain.handle("save-settings", (_, settings) => {
  fs.writeFileSync(
    getUserDataPath("settings.json"),
    JSON.stringify(settings, null, 2),
    "utf-8"
  );
  return { ok: true };
});

ipcMain.handle("get-max-ram", () => {
  return Math.floor(os.totalmem() / 1024 / 1024 / 1024);
});

ipcMain.handle("dialog:select-folder", async () => {
  const res = await dialog.showOpenDialog({
    properties: ["openDirectory"],
  });
  return res.canceled ? null : res.filePaths[0];
});

ipcMain.handle("launch-game", async (_, options) => {
  try {
    await launchGame(options, (log) => {
      if (mainWindow) {
        mainWindow.webContents.send("game-log", log);
      }
    });
    return { ok: true };
  } catch (err) {
    if (mainWindow) {
      mainWindow.webContents.send("game-log", `❌ ${err.message}`);
    }
    return { ok: false, error: err.message };
  }
});

app.commandLine.appendSwitch("disable-features", "OutOfBlinkCors");
app.commandLine.appendSwitch("disable-site-isolation-trials");
app.commandLine.appendSwitch("allow-insecure-localhost");
