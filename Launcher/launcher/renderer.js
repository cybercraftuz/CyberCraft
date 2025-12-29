let currentServer = null;

document.addEventListener("DOMContentLoaded", async () => {
  const loginBox = document.getElementById("login_box");
  const profileSection = document.getElementById("profileSection");
  const serverMainSection = document.getElementById("serverMainSection");
  const profileWrapper = document.querySelector(".profile_info-item");
  const signInBtn = document.getElementById("signInBtn");
  const ramSlider = document.getElementById("ramSlider");
  const ramValue = document.getElementById("ramValue");
  const gamePathInput = document.getElementById("gamePathInput");
  const browseBtn = document.getElementById("browseBtn");
  const saveSettingsBtn = document.getElementById("saveSettings");
  const settingsModal = document.getElementById("settingsModal");

  const loader = document.getElementById("loader");
  const serverList = document.getElementById("serverList");
  const serverHeader = document.getElementById("serverHeader");
  const serverBody = document.getElementById("serverBody");
  const bottom_bar = document.querySelector(".bottom_bar");
  const registerBox = document.getElementById("register_box");

  function showLoader(show) {
    if (loader) loader.style.display = show ? "flex" : "none";
  }

  const renderProfileButton = (username, avatar_url) => {
    const avatar = avatar_url
      ? `<img src="${avatar_url}" alt="avatar" class="logo"/>`
      : `<i class="fa fa-user"></i>`;

    profileWrapper.innerHTML = `
      <button id="profileToggleBtn">
        ${avatar}
        <span class="profile_name">${username}</span>
      </button>`;
  };

  const renderLoginButton = () => {
    profileWrapper.innerHTML = `
      <button id="openLoginBtn">
        <i class="fa fa-sign-in-alt"></i> Login
      </button>`;
  };

  async function autoLogin(username, password) {
    showLoader(true);
    try {
      const res = await fetch(
        "http://127.0.0.1:8000/api/auth/launcher/login/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        }
      );

      if (!res.ok) throw new Error("Auto-login failed");

      const data = await res.json();

      await window.electronAPI.saveUserData({
        username,
        password,
        avatar_url: data.user?.avatar_url || null,
      });

      renderProfileButton(username, data.user?.avatar_url);
      loginBox.style.display = "none";
      serverMainSection.style.display = "block";
      bottom_bar.style.display = "flex";
    } catch (e) {
      console.warn("Auto-login ishlamadi");
      renderLoginButton();
    } finally {
      showLoader(false);
    }
  }

  async function initUser() {
    const user = await window.electronAPI.getUserData();

    if (user?.username && user?.password) {
      await autoLogin(user.username, user.password);
    } else {
      renderLoginButton();
    }
  }

  document.addEventListener("click", async (e) => {
    if (e.target.closest("#login-button")) {
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value.trim();

      if (!username || !password) {
        alert("Username va password kiriting");
        return;
      }

      showLoader(true);
      const res = await fetch(
        "http://127.0.0.1:8000/api/auth/launcher/login/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        }
      );
      showLoader(false);

      if (!res.ok) return alert("Login xato!");

      const data = await res.json();

      await window.electronAPI.saveUserData({
        username,
        password,
        avatar_url: data.user?.avatar_url || null,
      });

      renderProfileButton(username, data.user?.avatar_url);
      loginBox.style.display = "none";
      serverMainSection.style.display = "block";
      bottom_bar.style.display = "flex";
    }

    if (e.target.closest("#openLoginBtn")) {
      loginBox.style.display = "flex";
      serverMainSection.style.display = "none";
      profileSection.style.display = "none";
      bottom_bar.style.display = "none";
      settingsModal.style.display = "none";
      registerBox.style.display = "none";
    }

    if (e.target.closest("#logoutBtn")) {
      await window.electronAPI.logout();
      location.reload();
    }
  });

  async function loadServers() {
    showLoader(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/servers/");
      const servers = await res.json();
      if (Array.isArray(servers) && servers.length > 0) {
        generateServerItems(servers);
        renderServerData(servers[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      showLoader(false);
    }
  }

  function generateServerItems(servers) {
    serverList.innerHTML = "";
    servers.forEach((s) => {
      const li = document.createElement("li");
      li.classList.add("item");
      li.innerHTML = `<img src="${s.server_image}" class="item_img" />`;
      li.addEventListener("click", () => renderServerData(s));
      serverList.appendChild(li);
    });
  }

  function renderServerData(data) {
    currentServer = data;
    serverHeader.innerHTML = `
      <div class="main_box">
        <div class="box_title">${data.name}</div>
        <div class="online_player">${data.online_player}</div>
      </div>
      <div class="play_box">
        <button class="play_btn" id="playNowBtn">
          O'ynash <i class="fa-solid fa-play"></i>
        </button>
      </div>`;
  }

  async function initSettings() {
    const maxRAM = await window.electronAPI.getMaxRAM();
    ramSlider.min = 2;
    ramSlider.max = Math.max(2, maxRAM - 1);
    ramSlider.value = 2;
    ramValue.textContent = "2 GB";

    ramSlider.addEventListener("input", () => {
      ramValue.textContent = `${ramSlider.value} GB`;
    });

    const settings = await window.electronAPI.loadSettings();
    if (settings?.ram) {
      ramSlider.value = settings.ram;
      ramValue.textContent = `${settings.ram} GB`;
    }
  }

  await initUser();
  await initSettings();
  await loadServers();
});
