// Bump this whenever the shell caching strategy changes so existing installs
// discard a potentially stale HTML/JavaScript shell on their next update.
const CACHE_NAME = "dondoo-pwa-v4";
const APP_SHELL = ["/", "/manifest.webmanifest", "/icons/icon-192.png", "/icons/icon-512.png", "/brand/dondoo-mark.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || !event.request.url.startsWith(self.location.origin)) {
    return;
  }

  const requestUrl = new URL(event.request.url);

  // API requests must always reach the server. Returning a cached response or
  // Response.error() here makes a healthy login endpoint look like a browser
  // network failure.
  if (requestUrl.pathname.startsWith("/api/")) {
    return;
  }

  // Keep the document network-first. Cached HTML can point at a JavaScript
  // bundle that has been removed by a later deployment.
  if (event.request.mode === "navigate" || requestUrl.pathname === "/" || requestUrl.pathname === "/index.html") {
    event.respondWith(
      fetch(event.request).catch(() => caches.match("/"))
    );
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (!response.ok) {
          return response;
        }

        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        return response;
      })
      .catch(() =>
        caches.match(event.request).then((cached) => {
          if (cached) {
            return cached;
          }

          if (event.request.mode === "navigate") {
            return caches.match("/");
          }

          return Response.error();
        })
      )
  );
});
