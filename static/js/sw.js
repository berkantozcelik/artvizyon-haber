// Basic service worker for PWA shell + future push hooks
const CACHE_NAME = "av-static-v1";
const OFFLINE_URLS = ["/", "/manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
    .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).catch(() => caches.match("/")))
  );
});

// Push placeholder (extend when backend sends pushes)
self.addEventListener("push", (event) => {
  if (!event.data) return;
  const data = event.data.json ? event.data.json() : { title: "Artvizyon Haber", body: event.data.text() };
  event.waitUntil(
    self.registration.showNotification(data.title || "Artvizyon Haber", {
      body: data.body || "",
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/icon-192.png",
      data: data.url || "/"
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data || "/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientsArr) => {
      const matching = clientsArr.find((c) => c.url.includes(new URL(url, self.location.origin).pathname));
      if (matching) return matching.focus();
      return clients.openWindow(url);
    })
  );
});
