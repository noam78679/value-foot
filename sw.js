// Value Foot : fonctionne hors ligne avec les dernières données chargées.
// Réseau d'abord (toujours la version la plus récente), cache si pas de connexion.
const C='value-foot-v3';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['./','index.html','manifest.json','icone-180.png','icone-192.png','icone-512.png'])));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;
  e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(C).then(c=>c.put(e.request.url.split('?')[0],cp))}return r})
    .catch(()=>caches.match(e.request.url.split('?')[0])));
});
