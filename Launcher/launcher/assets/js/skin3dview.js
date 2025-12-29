async function loadSkinViewer() {
  const user = await window.electronAPI.getUserData();
  const username = user.username;

  if (!username) {
    console.error("Foydalanuvchi topilmadi!");
    return;
  }

  const checkCanvas = () =>
    new Promise((resolve) => {
      const interval = setInterval(() => {
        const canvas = document.getElementById("skinCanvas");
        if (canvas) {
          clearInterval(interval);
          resolve(canvas);
        }
      }, 100);
    });

  const canvas = await checkCanvas();

  const apiUrl = `http://127.0.0.1:8000/api/accounts/profile/?username=${username}`;
  try {
    const res = await fetch(apiUrl);
    if (!res.ok) throw new Error("API so‘rovida xatolik");

    const data = await res.json();
    const skinUrl = data.skin_url;

    if (!skinUrl) throw new Error("Skin URL mavjud emas");

    const viewer = new skinview3d.SkinViewer({
      canvas: canvas,
      width: 300,
      height: 400,
      skin: skinUrl,
    });

    viewer.zoom = 0.9;
    viewer.animation = new skinview3d.WalkingAnimation();
  } catch (error) {
    console.error("Skinni yuklashda xatolik:", error);
  }
}

document.addEventListener("click", async (e) => {
  if (e.target.closest("#profileToggleBtn")) {
    await loadSkinViewer();
  }
});
