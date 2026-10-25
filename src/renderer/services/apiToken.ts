/**
 * The token the backend requires on every /api request when Electron started it (a new one
 * each launch, from the main process). Without Electron (the renderer in a plain browser
 * during development) there is none, and none is sent.
 */

let token: string | null = null;
let loading: Promise<void> | null = null;

export function loadApiToken(): Promise<void> {
  if (!loading) {
    loading = (async () => {
      try {
        const result = await window.electron?.invoke('get-api-token');
        if (result?.success && typeof result.data === 'string') {
          token = result.data;
        }
      } catch {
        // No main process to ask
      }
    })();
  }
  return loading;
}

/** The header carrying the token, once it is loaded */
export async function apiTokenHeaders(): Promise<Record<string, string>> {
  await loadApiToken();
  return cachedApiTokenHeaders();
}

/** The header without waiting, for requests sent while the window closes */
export function cachedApiTokenHeaders(): Record<string, string> {
  return token ? { 'X-API-Token': token } : {};
}
