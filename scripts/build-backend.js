/**
 * Build the bundled backend (backend/dist/chatbot-backend/) with PyInstaller, and, with
 * BUNDLE_MODEL=1, put the language model next to it (backend/dist/models/, see bundleModel
 * below). The app runs without a language model by default. PyInstaller uses the
 * backend's virtual environment (backend/venv), or the Python in the PYTHON environment
 * variable. PyInstaller builds for the system it runs on: build on Windows for the Windows
 * app, on macOS for the macOS one.
 *
 * Usage: npm run build:backend                  (no language model)
 *        BUNDLE_MODEL=1 npm run build:backend   (with the language model)
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
if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

bundleModel().catch((error) => {
  console.error(error.message);
  process.exit(1);
});

/**
 * With BUNDLE_MODEL=1, the language model and its license, in backend/dist/models/
 * (package.json "extraResources" copies it into the app). Even then the model writes no
 * replies until a parent turns it on in the parent dashboard. The model comes from, in order: the file in LLM_MODEL_FILE, the one
 * download_model.sh saves (backend/models/llama-3.2-3b-instruct.gguf), or a download from
 * LLM_MODEL_URL (default: Llama 3.2 3B Instruct, Q4_K_M). The Llama 3.2 license must go with
 * the model: LLM_MODEL_LICENSE_FILE, backend/models/LLAMA_3.2_LICENSE.txt, or a download from
 * LLM_MODEL_LICENSE_URL (default: Meta's model page, which needs a Hugging Face token with
 * access to it in HF_TOKEN). Without BUNDLE_MODEL=1 the folder is left empty.
 */
async function bundleModel() {
  const MODEL_NAME = 'llama-3.2-3b-instruct.gguf';
  const LICENSE_NAME = 'LLAMA_3.2_LICENSE.txt';
  const modelsOut = path.join(backendDir, 'dist', 'models');
  if (process.env.BUNDLE_MODEL !== '1') {
    // Emptied, so a model from an earlier BUNDLE_MODEL=1 build is not packaged
    fs.rmSync(modelsOut, { recursive: true, force: true });
    fs.mkdirSync(modelsOut, { recursive: true });
    console.log('Building without the language model (set BUNDLE_MODEL=1 to include it)');
    return;
  }
  fs.mkdirSync(modelsOut, { recursive: true });
  const modelTarget = path.join(modelsOut, MODEL_NAME);
  await provide(modelTarget, [process.env.LLM_MODEL_FILE, path.join(backendDir, 'models', MODEL_NAME)],
    process.env.LLM_MODEL_URL
      || 'https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf');
  const magic = Buffer.alloc(4);
  const fd = fs.openSync(modelTarget, 'r');
  fs.readSync(fd, magic, 0, 4, 0);
  fs.closeSync(fd);
  if (magic.toString('latin1') !== 'GGUF') {
    fs.rmSync(modelTarget);
    throw new Error(`${modelTarget} is not a GGUF model file; removed it`);
  }
  await provide(path.join(modelsOut, LICENSE_NAME),
    [process.env.LLM_MODEL_LICENSE_FILE, path.join(backendDir, 'models', LICENSE_NAME)],
    process.env.LLM_MODEL_LICENSE_URL
      || 'https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct/resolve/main/LICENSE.txt',
    'The Llama 3.2 license must be shipped with the model. Put it at backend/models/' + LICENSE_NAME
      + ', or set LLM_MODEL_LICENSE_FILE, or HF_TOKEN for a Hugging Face account with access to Llama 3.2.');
  console.log(`Bundled ${MODEL_NAME} and ${LICENSE_NAME} in ${modelsOut}`);
}

/** Copy the first existing file of `sources` to `target`, else download `url` (unless `target` is already there) */
async function provide(target, sources, url, hint = '') {
  const source = sources.find((file) => file && fs.existsSync(file));
  if (source) {
    if (!fs.existsSync(target) || fs.statSync(target).size !== fs.statSync(source).size) {
      console.log(`Copying ${source}`);
      fs.copyFileSync(source, target);
    }
    return;
  }
  if (fs.existsSync(target)) {
    return;
  }
  console.log(`Downloading ${url}`);
  const headers = process.env.HF_TOKEN ? { Authorization: `Bearer ${process.env.HF_TOKEN}` } : {};
  const response = await fetch(url, { headers });
  if (!response.ok || !response.body) {
    throw new Error(`Download failed (${response.status} ${response.statusText}): ${url}\n${hint}`);
  }
  const partial = `${target}.part`;
  const out = fs.createWriteStream(partial);
  let received = 0;
  let reported = 0;
  for await (const chunk of response.body) {
    out.write(chunk);
    received += chunk.length;
    if (received - reported >= 200 * 1024 * 1024) {
      reported = received;
      console.log(`  ${Math.round(received / 1024 / 1024)} MB`);
    }
  }
  await new Promise((resolve, reject) => out.end((error) => (error ? reject(error) : resolve())));
  fs.renameSync(partial, target);
}
