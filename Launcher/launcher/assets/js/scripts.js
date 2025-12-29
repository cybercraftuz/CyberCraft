let currentServer = null;

document.addEventListener("DOMContentLoaded", () => {
  showLoader(true);

  fetch("http://127.0.0.1:8000/api/servers/")
    .then((res) => res.json())
    .then((servers) => {
      showLoader(false);
      if (Array.isArray(servers) && servers.length > 0) {
        generateServerItems(servers);
        renderServerData(servers[0]);
      }
    })
    .catch((err) => {
      showLoader(false);
      console.error("API xatosi:", err);
    });
});

function showLoader(show) {
  document.getElementById("loader").style.display = show ? "flex" : "none";
}

function generateServerItems(servers) {
  const list = document.getElementById("serverList");
  list.innerHTML = "";
  servers.forEach((s) => {
    const li = document.createElement("li");
    li.classList.add("item");
    li.innerHTML = `<img src="${s.server_image}" class="item_img" />`;
    li.addEventListener("click", () => renderServerData(s));
    list.appendChild(li);
  });
}

function renderServerData(data) {
  currentServer = data;
  document.getElementById("serverHeader").innerHTML = `
    <div class="main_box">
      <div class="box_title">${data.name}</div>
      <div class="online_player">${data.online_player}</div>
    </div>
    <div class="play_box">
      <button class="play_btn" id="playNowBtn">O'ynash <i class="fa-solid fa-play"></i></button>
      <button class="mod_settings">Modlar</button>
    </div>`;
  document.getElementById("serverBody").innerHTML = `
    <div class="server_image a">
      ${(data.images || []).map((img) => `<img src="${img.image}" />`).join("")}
    </div>
    <div class="mod_list a">${(data.mods || []).join(" • ")}</div>
    <div class="social">
      <button onclick="window.electronAPI.openTelegram()"><i class="fa-brands fa-telegram" style="color: #21a1de;"></i></button>
      <button onclick="window.electronAPI.openYoutube()"><i class="fa-brands fa-youtube" style="color: #ff0000;"></i></button>
      <button onclick="window.electronAPI.openDiscord()"><i class="fa-brands fa-discord" style="color: #5865f2;"></i></button>
    </div>
    <div id="progressBox" style="color: limegreen; margin-top: 10px;"></div>
  `;

  document.getElementById("playNowBtn").addEventListener("click", () => {
    document.getElementById("progressBox").textContent = "Yuklash boshlandi...";
    window.electronAPI.playServer(currentServer);
  });
}
