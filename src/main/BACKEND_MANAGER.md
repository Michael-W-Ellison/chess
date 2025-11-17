# Backend Manager

The Backend Manager handles the Python FastAPI backend process lifecycle in the Electron main process.

## Features

- **Automatic Python Detection**: Finds Python in virtual environment or falls back to system Python
- **Process Lifecycle Management**: Start, stop, and monitor the backend process
- **Health Checks**: Periodic health monitoring to detect backend crashes
- **Graceful Shutdown**: Ensures backend shuts down cleanly on app exit
- **HTTP Request Interface**: Simple API for making requests to the backend

## Architecture

```
Electron Main Process
  ├── main.ts (starts/stops backend on app lifecycle)
  ├── backend-manager.ts (manages Python process)
  └── ipc-handlers.ts (uses backend manager for API calls)
```

## Usage

### Starting the Backend

The backend is automatically started when the Electron app is ready:

```typescript
// main.ts
app.whenReady().then(async () => {
  await backendManager.start();
  // ... create windows, etc.
});
```

### Stopping the Backend

The backend is automatically stopped when the app quits:

```typescript
// main.ts
app.on('before-quit', async (event) => {
  await backendManager.stop();
});
```

### Making Requests

IPC handlers use the backend manager to make HTTP requests:

```typescript
// ipc-handlers.ts
const response = await backendManager.request('POST', '/api/conversation/start', {
  user_id: 1
});
```

### Checking Status

```typescript
// Get backend status
const status = backendManager.getStatus();
// Returns: { running: boolean, host: string, port: number, baseUrl: string }

// Check if running
const isRunning = backendManager.isBackendRunning();

// Health check
const healthy = await backendManager.checkHealth();
```

## Configuration

The backend manager can be configured with custom settings:

```typescript
import { BackendManager } from './backend-manager';

const customBackend = new BackendManager({
  host: '127.0.0.1',
  port: 8080,
  pythonPath: '/custom/path/to/python',
  backendPath: '/custom/path/to/backend',
  maxStartupTime: 30000,
  healthCheckInterval: 5000,
});
```

## Backend Detection

The manager automatically detects the backend location:

- **Development**: `<project-root>/backend`
- **Production**: `<resources>/backend`

Python executable detection:

- **Windows**: `backend/venv/Scripts/python.exe`
- **Unix**: `backend/venv/bin/python`

## Health Monitoring

The backend manager performs periodic health checks:

1. Every 5 seconds (configurable)
2. Makes HTTP GET request to `/health`
3. Marks backend as unhealthy if check fails
4. Logs warnings if backend crashes

## Error Handling

The backend manager handles various error scenarios:

- **Startup Timeout**: Backend fails to start within 30 seconds
- **Process Crash**: Backend process exits unexpectedly
- **Health Check Failure**: Backend stops responding to health checks
- **Shutdown Timeout**: Backend doesn't stop within 5 seconds (force kill)

## IPC Handlers

Two IPC handlers provide backend status to the renderer:

### `backend-status`

Returns current backend status:

```typescript
const result = await window.electron.invoke('backend-status');
// result.data = { running: true, host: '127.0.0.1', port: 8000, baseUrl: 'http://127.0.0.1:8000' }
```

### `backend-health`

Performs a health check:

```typescript
const result = await window.electron.invoke('backend-health');
// result.data = { healthy: true, message: 'Backend is healthy' }
```

## Logging

The backend manager logs all important events:

- Backend process stdout/stderr
- Startup progress
- Health check failures
- Shutdown events
- Errors

All logs are prefixed with `[Backend]` or `[Backend Error]`.

## Development vs Production

### Development Mode
- Backend path: `<project-root>/backend`
- Uses virtual environment: `backend/venv/bin/python`
- Backend runs as separate process

### Production Mode (Packaged App)
- Backend path: `<resources>/backend`
- Backend bundled with app
- Uses packaged Python environment

## Troubleshooting

### Backend won't start

1. Check Python is installed in virtual environment
2. Verify `backend/main.py` exists
3. Check logs for specific error messages
4. Ensure port 8000 is not already in use

### Health checks failing

1. Verify backend is running (`ps aux | grep python`)
2. Check backend logs for errors
3. Test health endpoint manually: `curl http://localhost:8000/health`

### Backend crashes on startup

1. Check backend dependencies are installed
2. Verify database can be created
3. Check model file exists (if using LLM)
4. Review backend error logs

## API Reference

### `BackendManager` Class

#### Methods

- `start(): Promise<void>` - Start the backend process
- `stop(): Promise<void>` - Stop the backend process
- `checkHealth(): Promise<boolean>` - Perform health check
- `request<T>(method, path, body?, headers?): Promise<T>` - Make HTTP request
- `getStatus()` - Get current status
- `isBackendRunning(): boolean` - Check if running

#### Configuration Options

- `host: string` - Backend host (default: '127.0.0.1')
- `port: number` - Backend port (default: 8000)
- `pythonPath?: string` - Custom Python path
- `backendPath?: string` - Custom backend directory
- `maxStartupTime: number` - Startup timeout in ms (default: 30000)
- `healthCheckInterval: number` - Health check interval in ms (default: 5000)
