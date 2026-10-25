import { app } from 'electron';
import * as path from 'path';
import { pathToFileURL } from 'url';

/**
 * Development mode: an unpackaged app started with --dev (npm run dev). An unpackaged app
 * started without it (npm start) loads the built files, like the packaged app.
 */
export const isDev = !app.isPackaged && process.argv.includes('--dev');

export const DEV_SERVER_URL = 'http://localhost:5173';

const RENDERER_DIR_URL = pathToFileURL(path.join(__dirname, '../renderer') + path.sep).href;

/**
 * Whether a URL is the app's own page: the Vite dev server in development, the built renderer
 * files otherwise. Compared by origin or path, not by prefix ("http://localhost.evil.com").
 */
export function isAppUrl(url: string | undefined): boolean {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    if (isDev) {
      return parsed.origin === new URL(DEV_SERVER_URL).origin;
    }
    return parsed.protocol === 'file:' && parsed.href.startsWith(RENDERER_DIR_URL);
  } catch {
    return false;
  }
}
