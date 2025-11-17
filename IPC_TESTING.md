# IPC Communication Testing Guide

This document explains how to test the IPC (Inter-Process Communication) between the Electron renderer, main process, and Python backend.

## Test Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IPC Test Flow                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Renderer Process          Main Process         Backend    │
│  ┌──────────────┐         ┌──────────────┐    ┌─────────┐ │
│  │              │  IPC    │              │HTTP│         │ │
│  │ test-ipc-    │─invoke─→│ ipc-handlers │───→│ FastAPI │ │
│  │ integration  │         │              │    │         │ │
│  │              │←─result─│              │←───│         │ │
│  └──────────────┘         └──────────────┘    └─────────┘ │
│                                                             │
│  Direct Backend Test                                        │
│  ┌──────────────┐                            ┌─────────┐  │
│  │              │         HTTP                │         │  │
│  │  test-ipc.ts │────────────────────────────→│ FastAPI │  │
│  │              │                             │         │  │
│  └──────────────┘                             └─────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Available Tests

### 1. Backend Integration Test (Main Process)

**File:** `src/main/test-ipc.ts`

Tests the backend manager and direct HTTP communication with the Python backend.

**Test Coverage:**
- ✅ Backend startup and shutdown
- ✅ Health checks
- ✅ Conversation API (start, send, end)
- ✅ Personality API
- ✅ Profile API
- ✅ Error handling
- ✅ Request/response validation

**Run:**
```bash
# Ensure backend dependencies are installed
cd backend
pip install -r requirements.txt

# Run the test
npm run test:ipc
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════╗
║     IPC Communication End-to-End Test Suite                  ║
╚══════════════════════════════════════════════════════════════╝

📦 Testing Backend Manager...

Test 1: Backend Startup
  ✓ Backend started successfully
  ✓ Backend is marked as running

...

╔══════════════════════════════════════════════════════════════╗
║                      TEST SUMMARY                            ║
╚══════════════════════════════════════════════════════════════╝

Total Tests:  18
Passed:       18 ✓
Failed:       0 ✗
Duration:     12.34s
Success Rate: 100.0%

🎉 All tests passed!
```

### 2. IPC Integration Test (Renderer Process)

**File:** `src/renderer/test-ipc-integration.ts`

Tests the complete IPC flow from renderer through main process to backend.

**Test Coverage:**
- ✅ Backend status via IPC
- ✅ Backend health via IPC
- ✅ Conversation flow via IPC
- ✅ Personality retrieval via IPC
- ✅ Profile retrieval via IPC
- ✅ Error handling via IPC

**Run (in Browser Console):**

1. Start the Electron app:
   ```bash
   npm run dev
   ```

2. Open DevTools (should open automatically in dev mode)

3. In the console, run:
   ```javascript
   testIPC()
   ```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════╗
║   IPC Integration Test (Renderer → Main → Backend)          ║
╚══════════════════════════════════════════════════════════════╝

🧪 Backend Status...
  ✓ Passed (45ms)

🧪 Backend Health Check...
  ✓ Passed (123ms)

...

╔══════════════════════════════════════════════════════════════╗
║                      TEST SUMMARY                            ║
╚══════════════════════════════════════════════════════════════╝

Total Tests:  9
Passed:       9 ✓
Failed:       0 ✗
Duration:     3.45s
Success Rate: 100.0%

🎉 All IPC integration tests passed!
```

## Manual Testing

### Testing Individual IPC Channels

You can test individual IPC channels in the browser console:

```javascript
// Test backend status
await window.electron.invoke('backend-status')
// Expected: { success: true, data: { running: true, ... } }

// Test backend health
await window.electron.invoke('backend-health')
// Expected: { success: true, data: { healthy: true, ... } }

// Start a conversation
const result = await window.electron.invoke('start-conversation')
const conversationId = result.data.conversation_id
console.log('Conversation ID:', conversationId)

// Send a message
await window.electron.invoke('send-message', conversationId, 'Hello!')

// Get personality
await window.electron.invoke('get-personality')

// Get profile
await window.electron.invoke('get-profile')

// End conversation
await window.electron.invoke('end-conversation', conversationId)
```

### Testing Backend Directly

You can test the backend API directly using curl:

```bash
# Health check
curl http://localhost:8000/health

# Start conversation
curl -X POST http://localhost:8000/api/conversation/start?user_id=1

# Send message
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Hello!",
    "conversation_id": 1,
    "user_id": 1
  }'

# Get personality
curl http://localhost:8000/api/personality?user_id=1

# Get profile
curl http://localhost:8000/api/profile?user_id=1
```

## Troubleshooting

### Backend Won't Start

**Problem:** Backend fails to start during tests

**Solutions:**
1. Ensure Python virtual environment is set up:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. Check if port 8000 is already in use:
   ```bash
   lsof -i :8000  # macOS/Linux
   netstat -ano | findstr :8000  # Windows
   ```

3. Run backend manually to see errors:
   ```bash
   cd backend
   python main.py
   ```

### IPC Tests Fail

**Problem:** IPC integration tests fail in renderer

**Solutions:**
1. Ensure backend is running (check console for backend startup logs)
2. Check DevTools console for errors
3. Verify `window.electron` API is available
4. Check Network tab for failed HTTP requests

### Tests Timeout

**Problem:** Tests timeout waiting for backend

**Solutions:**
1. Increase timeout in `backend-manager.ts` (default: 30s)
2. Check if LLM model is trying to load (can be slow)
3. Ensure backend/main.py exists and is executable
4. Check backend logs for startup errors

### Health Checks Fail

**Problem:** Health endpoint returns unhealthy

**Solutions:**
1. Check if database can be created
2. Verify all dependencies are installed
3. Check backend logs for errors
4. Ensure backend/data/ directory is writable

## Test Coverage

### Backend Manager Tests (18 tests)

1. ✅ Backend starts successfully
2. ✅ Backend status is correct
3. ✅ Health check passes
4. ✅ Root endpoint responds
5. ✅ Health endpoint details
6. ✅ Start conversation
7. ✅ Send message
8. ✅ Send follow-up message
9. ✅ End conversation
10. ✅ Get personality
11. ✅ Get personality description
12. ✅ Get profile
13. ✅ Get memories
14. ✅ Invalid endpoint error handling
15. ✅ Invalid method error handling
16. ✅ Missing parameters error handling
17. ✅ Backend shutdown
18. ✅ Requests fail after shutdown

### IPC Integration Tests (9 tests)

1. ✅ Backend status via IPC
2. ✅ Backend health via IPC
3. ✅ Get personality via IPC
4. ✅ Get profile via IPC
5. ✅ Start conversation via IPC
6. ✅ Send message via IPC
7. ✅ Send follow-up message via IPC
8. ✅ End conversation via IPC
9. ✅ Invalid channel error handling

## Continuous Integration

To run tests in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Install Python Dependencies
  run: |
    cd backend
    pip install -r requirements.txt

- name: Run IPC Tests
  run: npm run test:ipc
```

## Performance Benchmarks

Expected test duration:
- Backend startup: ~2-5 seconds
- Single API call: ~100-500ms
- Full test suite: ~10-15 seconds
- IPC integration tests: ~3-5 seconds

## Next Steps

After verifying IPC communication works:

1. ✅ Add tests to CI/CD pipeline
2. ✅ Monitor test performance over time
3. ✅ Add more edge case tests
4. ✅ Test with production build
5. ✅ Test on different platforms (Windows, macOS, Linux)

## Resources

- [Electron IPC Documentation](https://www.electronjs.org/docs/latest/api/ipc-main)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Backend Manager Documentation](src/main/BACKEND_MANAGER.md)
