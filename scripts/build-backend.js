/**
 * Build the bundled backend (backend/dist/chatbot-backend/) with PyInstaller, using the
 * backend's virtual environment (backend/venv), or the Python in the PYTHON environment
 * variable. PyInstaller builds for the system it runs on: build on Windows for the Windows
 * installer, on macOS for the macOS one.
 *
 * Usage: npm run build:backend
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const backendDir = path.join(__dirname, '..', 'backend');
const venvPython = process.platform === 'win32'
  ? path.join(backendDir, 'venv', 'Scripts', 'python.exe')
  : path.join(backendDir, 'venv', 'bin', 'python');
const python = process.env.PYTHON || (fs.existsSync(venvPython) ? venvPython : 'python3');

console.log(`Building the backend with ${python}`);
const result = spawnSync(
  python,
  ['-m', 'PyInstaller', path.join('packaging', 'chatbot-backend.spec'), '--noconfirm',
    '--distpath', 'dist', '--workpath', 'build'],
  { cwd: backendDir, stdio: 'inherit' },
);
if (result.error) {
  console.error(`Could not run ${python}: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
