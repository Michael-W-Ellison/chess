/**
 * Backend Manager
 * Manages the Python FastAPI backend process lifecycle
 */

import { spawn, ChildProcess } from 'child_process';
import { randomBytes } from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import * as http from 'http';
import { app } from 'electron';

interface BackendConfig {
  host: string;
  port: number;
  pythonPath?: string;
  backendPath?: string;
  maxStartupTime: number; // milliseconds
  healthCheckInterval: number; // milliseconds
}

const defaultConfig: BackendConfig = {
  host: '127.0.0.1',
  port: 8000,
  maxStartupTime: 30000, // 30 seconds
  healthCheckInterval: 5000, // 5 seconds
};

export class BackendManager {
  private process: ChildProcess | null = null;
  private config: BackendConfig;
  // Required by the backend on every /api request (API_TOKEN), new for each launch, so web
  // pages and other programs can't use the API
  readonly apiToken: string = randomBytes(32).toString('hex');
  private isRunning: boolean = false;
  private startupPromise: Promise<void> | null = null;
  private healthCheckTimer: NodeJS.Timeout | null = null;
  // Why the backend process could not start, or exited while starting (no waiting for the
  // whole startup time then)
  private startFailure: Error | null = null;

  constructor(config?: Partial<BackendConfig>) {
    this.config = { ...defaultConfig, ...config };
  }

  /**
   * Get the Python executable path
   * Checks for virtual environment first, then falls back to system python
   */
  private getPythonPath(): string {
    if (this.config.pythonPath) {
      return this.config.pythonPath;
    }

    const backendDir = this.getBackendPath();

    // Try virtual environment first
    if (process.platform === 'win32') {
      return path.join(backendDir, 'venv', 'Scripts', 'python.exe');
    } else {
      return path.join(backendDir, 'venv', 'bin', 'python');
    }
  }

  /**
   * Get the backend directory path
   */
  private getBackendPath(): string {
    if (this.config.backendPath) {
      return this.config.backendPath;
    }

    if (!app.isPackaged) {
      // Development: app.getAppPath() is the project root (where package.json is),
      // and the backend directory sits directly inside it
      return path.join(app.getAppPath(), 'backend');
    } else {
      // Production: backend is packaged with app
      return path.join(process.resourcesPath, 'backend');
    }
  }

  /**
   * How to run the backend. Unpackaged: python main.py in the backend folder. Packaged: the
   * bundled backend (npm run build:backend, copied into the app's resources), run in a
   * "backend" folder in the user's app data, where it keeps its .env, data/ (the database),
   * logs/ and models/; the app's own files can't be written to.
   */
  private getLaunchCommand(pythonPath: string, mainScript: string, backendPath: string):
    { command: string; args: string[]; cwd: string } {
    if (!app.isPackaged || this.config.pythonPath) {
      return { command: pythonPath, args: [mainScript], cwd: backendPath };
    }
    const dataDir = path.join(app.getPath('userData'), 'backend');
    for (const dir of ['data', 'logs', 'models']) {
      fs.mkdirSync(path.join(dataDir, dir), { recursive: true });
    }
    const executable = process.platform === 'win32' ? 'chatbot-backend.exe' : 'chatbot-backend';
    return { command: path.join(backendPath, executable), args: [], cwd: dataDir };
  }

  /**
   * The language model that comes with the packaged app (npm run build:backend puts it in the
   * app's resources); the backend uses it unless the user put a model in its models/ folder
   */
  private bundledModelEnv(): Record<string, string> {
    if (!app.isPackaged) {
      return {};
    }
    return { BUNDLED_MODEL_PATH: path.join(process.resourcesPath, 'models', 'llama-3.2-3b-instruct.gguf') };
  }

  /**
   * Start the Python backend process
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.log('Backend already running');
      return;
    }

    if (this.startupPromise) {
      return this.startupPromise;
    }

    this.startupPromise = this._startBackend();
    return this.startupPromise;
  }

  private async _startBackend(): Promise<void> {
    const pythonPath = this.getPythonPath();
    const backendPath = this.getBackendPath();
    const mainScript = path.join(backendPath, 'main.py');
    const launch = this.getLaunchCommand(pythonPath, mainScript, backendPath);

    console.log('Starting Python backend...');
    console.log('  Command:', launch.command, ...launch.args);
    console.log('  Working directory:', launch.cwd);

    // Environment variables for backend
    const env = {
      ...process.env,
      HOST: this.config.host,
      PORT: this.config.port.toString(),
      PYTHONUNBUFFERED: '1', // Disable Python output buffering
      API_TOKEN: this.apiToken,
      CHILD_USER_ID: '1', // The app's one child profile: the child API serves no other user
      ...this.bundledModelEnv(),
    };

    // Spawn Python process
    this.startFailure = null;
    try {
      this.process = spawn(launch.command, launch.args, {
        cwd: launch.cwd,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      // Handle stdout
      this.process.stdout?.on('data', (data) => {
        const output = data.toString().trim();
        if (output) {
          console.log('[Backend]', output);
        }
      });

      // Handle stderr
      this.process.stderr?.on('data', (data) => {
        const output = data.toString().trim();
        if (output) {
          console.error('[Backend Error]', output);
        }
      });

      // Handle process exit
      this.process.on('exit', (code, signal) => {
        console.log(`Backend process exited with code ${code}, signal ${signal}`);
        this.startFailure ??= new Error(`Backend exited with code ${code}, signal ${signal}`);
        this.isRunning = false;
        this.process = null;
        this.stopHealthCheck();
      });

      // Handle process errors
      this.process.on('error', (error) => {
        console.error('Backend process error:', error);
        this.startFailure ??= error;
        this.isRunning = false;
        this.process = null;
        this.stopHealthCheck();
      });

      // Wait for backend to be ready
      await this.waitForBackendReady();

      this.isRunning = true;
      this.startHealthCheck();

      console.log('✓ Backend started successfully');
    } catch (error) {
      this.isRunning = false;
      this.process = null;
      throw error;
    } finally {
      this.startupPromise = null;
    }
  }

  /**
   * Wait for backend to be ready (health check passes)
   */
  private async waitForBackendReady(): Promise<void> {
    const startTime = Date.now();
    const maxWaitTime = this.config.maxStartupTime;

    while (Date.now() - startTime < maxWaitTime) {
      // The process could not be started or already exited: no point waiting
      if (this.startFailure) {
        throw new Error(`Backend failed to start: ${this.startFailure.message}`);
      }
      try {
        const healthy = await this.checkHealth();
        if (healthy) {
          return;
        }
      } catch (error) {
        // Backend not ready yet, continue waiting
      }

      // Wait 500ms before next check
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    throw new Error('Backend failed to start within timeout period');
  }

  /**
   * Check if backend is healthy
   */
  async checkHealth(): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.get(
        {
          hostname: this.config.host,
          port: this.config.port,
          path: '/health',
          timeout: 5000,
        },
        (res) => {
          resolve(res.statusCode === 200);
        }
      );

      req.on('error', () => {
        resolve(false);
      });

      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  /**
   * Start periodic health checks
   */
  private startHealthCheck(): void {
    this.healthCheckTimer = setInterval(async () => {
      const healthy = await this.checkHealth();
      if (!healthy && this.isRunning) {
        console.warn('Backend health check failed - backend may have crashed');
        this.isRunning = false;
      }
    }, this.config.healthCheckInterval);
  }

  /**
   * Stop periodic health checks
   */
  private stopHealthCheck(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
  }

  /**
   * Stop the Python backend process
   */
  async stop(): Promise<void> {
    if (!this.process) {
      console.log('Backend not running');
      return;
    }

    console.log('Stopping Python backend...');

    this.stopHealthCheck();

    return new Promise((resolve) => {
      if (!this.process) {
        resolve();
        return;
      }

      // Give the process 5 seconds to shut down gracefully
      const timeout = setTimeout(() => {
        if (this.process && !this.process.killed) {
          console.warn('Backend did not shut down gracefully, forcing kill');
          this.process.kill('SIGKILL');
        }
      }, 5000);

      this.process.on('exit', () => {
        clearTimeout(timeout);
        this.isRunning = false;
        this.process = null;
        console.log('✓ Backend stopped');
        resolve();
      });

      // Send SIGTERM for graceful shutdown
      this.process.kill('SIGTERM');
    });
  }

  /**
   * Make an HTTP request to the backend
   */
  async request<T = any>(
    method: string,
    path: string,
    body?: any,
    headers?: Record<string, string>
  ): Promise<T> {
    if (!this.isRunning) {
      throw new Error('Backend is not running');
    }

    const url = `http://${this.config.host}:${this.config.port}${path}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Token': this.apiToken,
        ...headers,
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend request failed: ${response.status} ${errorText}`);
    }

    return (await response.json()) as T;
  }

  /**
   * Get backend status
   */
  getStatus(): {
    running: boolean;
    host: string;
    port: number;
    baseUrl: string;
  } {
    return {
      running: this.isRunning,
      host: this.config.host,
      port: this.config.port,
      baseUrl: `http://${this.config.host}:${this.config.port}`,
    };
  }

  /**
   * Check if backend is running
   */
  isBackendRunning(): boolean {
    return this.isRunning;
  }
}

// Global singleton instance
export const backendManager = new BackendManager();
