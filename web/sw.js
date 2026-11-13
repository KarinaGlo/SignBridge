/**
 * web/sw.js
 * Service Worker untuk dukungan luring (Offline PWA) SignBridge ASEAN.
 * Menyimpan aset statis (HTML, CSS, JS) dan model ONNX di Cache Storage.
 */

const CACHE_NAME = "signbridge-asean-v8";
const CORE_ASSETS = [
  "./",
  "./index.html",
  "./css/style.css",
  "./manifest.webmanifest",
  "./js/config.js",
  "./js/icons.js",
  "./js/features.js",
  "./js/handcrop.js",
  "./js/sentence.js",
  "./js/speech.js",
  "./js/vision.js",
  "./js/recognizer.js",
  "./js/fingerspell.js",
  "./js/fingerspell_mlp.js",
  "./js/room.js",
  "./js/recorder.js",
  "./js/app.js",
  "./model/labels.json",
  "./model/fingerspell.json",
  "./model/fingerspell_mlp.json",
  "./model/student.onnx",
  "./model/fingerspell.onnx"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).catch(() => { })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

