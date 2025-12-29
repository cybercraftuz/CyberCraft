const { Client, Authenticator } = require("minecraft-launcher-core");
const path = require("path");
const os = require("os");
const fs = require("fs");

async function launchGame({ username, version }, sendLog) {
  const client = new Client();

  const rootDir = path.join(os.homedir(), ".cybercraft");
  const cacheDir = path.join(rootDir, "cache", "json");

  fs.mkdirSync(cacheDir, { recursive: true });

  const options = {
    authorization: Authenticator.getAuth(username),
    root: rootDir,
    version: {
      number: version,
      type: "release",
    },
    memory: {
      max: "2G",
      min: "1G",
    },
  };

  sendLog("Starting Minecraft...");
  client.launch(options);

  client.on("debug", (e) => sendLog("[DEBUG] " + e));
  client.on("data", (e) => sendLog(e.toString()));
}

module.exports = { launchGame };
