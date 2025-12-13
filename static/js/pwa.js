// Register service worker and handle add-to-home prompt
(function() {
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/js/sw.js").catch((err) => console.warn("SW registration failed", err));
  });

  let deferredPrompt;
  const installBanner = document.getElementById("pwa-install");
  const installBtn = document.getElementById("pwa-install-btn");
  const installClose = document.getElementById("pwa-install-close");

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBanner) installBanner.classList.add("show");
  });

  if (installBtn) {
    installBtn.addEventListener("click", async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      installBanner.classList.remove("show");
    });
  }

  if (installClose) {
    installClose.addEventListener("click", () => {
      if (installBanner) installBanner.classList.remove("show");
    });
  }
})();
