// Web Push via the OneSignal v16 browser SDK (loaded on demand).
const APP_ID = import.meta.env.VITE_ONESIGNAL_APP_ID;
let initPromise = null;

function loadSdk() {
  return new Promise((resolve, reject) => {
    if (window.OneSignalDeferred) return resolve();
    window.OneSignalDeferred = [];
    const s = document.createElement("script");
    s.src = "https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js";
    s.defer = true;
    s.onload = resolve;
    s.onerror = () => reject(new Error("Could not load the OneSignal SDK"));
    document.head.appendChild(s);
  });
}

function withOneSignal(fn) {
  return new Promise((resolve, reject) => {
    window.OneSignalDeferred.push(async (OneSignal) => {
      try { resolve(await fn(OneSignal)); } catch (e) { reject(e); }
    });
  });
}

export function pushConfigured() {
  return Boolean(APP_ID);
}

async function init() {
  if (!APP_ID) throw new Error("VITE_ONESIGNAL_APP_ID is not set");
  if (!initPromise) {
    initPromise = loadSdk().then(() =>
      withOneSignal((OneSignal) =>
        // allowLocalhostAsSecureOrigin lets http://localhost work during development.
        OneSignal.init({ appId: APP_ID, allowLocalhostAsSecureOrigin: true, serviceWorkerPath: "OneSignalSDKWorker.js" })
      )
    );
  }
  return initPromise;
}

/** Ask for permission, subscribe and return the OneSignal subscription id. */
export async function subscribeToPush() {
  await init();
  return withOneSignal(async (OneSignal) => {
    await OneSignal.Notifications.requestPermission();
    await OneSignal.User.PushSubscription.optIn();
    // The id can take a moment to appear after opt-in.
    for (let i = 0; i < 20; i++) {
      const id = OneSignal.User.PushSubscription.id;
      if (id) return id;
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error("Subscription id not available - check that notifications are allowed in the browser");
  });
}
