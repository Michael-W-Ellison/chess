#!/usr/bin/env node
/**
 * IPC Communication End-to-End Test
 *
 * Tests the complete IPC flow:
 * 1. Backend Manager starts Python process
 * 2. IPC handlers communicate with backend
 * 3. Responses are properly formatted
 *
 * Run with: ts-node src/main/test-ipc.ts
 * Or: node dist/main/test-ipc.js (after build)
 */

import { backendManager } from './backend-manager';

// Test results tracking
let testsRun = 0;
let testsPassed = 0;
let testsFailed = 0;

/**
 * Test assertion helper
 */
function assert(condition: boolean, message: string): void {
  testsRun++;
  if (condition) {
    testsPassed++;
    console.log(`  ✓ ${message}`);
  } else {
    testsFailed++;
    console.error(`  ✗ ${message}`);
  }
}

/**
 * Test backend manager functionality
 */
async function testBackendManager(): Promise<void> {
  console.log('\n📦 Testing Backend Manager...\n');

  // Test 1: Backend starts successfully
  console.log('Test 1: Backend Startup');
  try {
    await backendManager.start();
    assert(true, 'Backend started successfully');
    assert(backendManager.isBackendRunning(), 'Backend is marked as running');
  } catch (error) {
    assert(false, `Backend startup failed: ${error}`);
    throw error; // Can't continue without backend
  }

  // Test 2: Backend status
  console.log('\nTest 2: Backend Status');
  const status = backendManager.getStatus();
  assert(status.running === true, 'Status shows backend running');
  assert(status.host === '127.0.0.1', 'Host is 127.0.0.1');
  assert(status.port === 8000, 'Port is 8000');
  assert(status.baseUrl === 'http://127.0.0.1:8000', 'Base URL is correct');

  // Test 3: Health check
  console.log('\nTest 3: Health Check');
  try {
    const healthy = await backendManager.checkHealth();
    assert(healthy === true, 'Backend health check passes');
  } catch (error) {
    assert(false, `Health check failed: ${error}`);
  }

  // Test 4: Root endpoint
  console.log('\nTest 4: Root Endpoint');
  try {
    const response = await backendManager.request('GET', '/');
    assert(response.status === 'running', 'Root endpoint returns running status');
    assert(response.version !== undefined, 'Root endpoint returns version');
  } catch (error) {
    assert(false, `Root endpoint failed: ${error}`);
  }

  // Test 5: Health endpoint (detailed)
  console.log('\nTest 5: Health Endpoint Details');
  try {
    const health = await backendManager.request('GET', '/health');
    assert(health.status === 'healthy', 'Health endpoint returns healthy status');
    assert(health.database !== undefined, 'Health includes database status');
    assert(health.llm !== undefined, 'Health includes LLM status');
  } catch (error) {
    assert(false, `Health endpoint failed: ${error}`);
  }
}

/**
 * Test conversation API endpoints
 */
async function testConversationAPI(): Promise<void> {
  console.log('\n💬 Testing Conversation API...\n');

  let conversationId: number | null = null;

  // Test 6: Start conversation
  console.log('Test 6: Start Conversation');
  try {
    const response = await backendManager.request('POST', '/api/conversation/start?user_id=1');
    conversationId = response.conversation_id;

    assert(conversationId !== undefined, 'Conversation ID is returned');
    assert(response.greeting !== undefined, 'Greeting message is returned');
    assert(response.personality !== undefined, 'Personality info is returned');
    assert(response.personality.name !== undefined, 'Bot name is included');
    assert(response.personality.mood !== undefined, 'Bot mood is included');
    assert(response.personality.friendship_level !== undefined, 'Friendship level is included');
  } catch (error) {
    assert(false, `Start conversation failed: ${error}`);
    return; // Can't continue without conversation
  }

  // Test 7: Send message
  console.log('\nTest 7: Send Message');
  try {
    const response = await backendManager.request('POST', '/api/message', {
      user_message: 'Hello! How are you?',
      conversation_id: conversationId,
      user_id: 1,
    });

    assert(response.content !== undefined, 'Response content is returned');
    assert(typeof response.content === 'string', 'Response content is a string');
    assert(response.content.length > 0, 'Response content is not empty');
    assert(response.metadata !== undefined, 'Response metadata is included');
  } catch (error) {
    assert(false, `Send message failed: ${error}`);
  }

  // Test 8: Send another message (conversation history)
  console.log('\nTest 8: Send Follow-up Message');
  try {
    const response = await backendManager.request('POST', '/api/message', {
      user_message: 'What are your interests?',
      conversation_id: conversationId,
      user_id: 1,
    });

    assert(response.content !== undefined, 'Follow-up response received');
    assert(response.content.length > 0, 'Follow-up response has content');
  } catch (error) {
    assert(false, `Follow-up message failed: ${error}`);
  }

  // Test 9: End conversation
  console.log('\nTest 9: End Conversation');
  try {
    await backendManager.request('POST', `/api/conversation/end/${conversationId}`);
    assert(true, 'Conversation ended successfully');
  } catch (error) {
    assert(false, `End conversation failed: ${error}`);
  }
}

/**
 * Test personality API endpoints
 */
async function testPersonalityAPI(): Promise<void> {
  console.log('\n🤖 Testing Personality API...\n');

  // Test 10: Get personality
  console.log('Test 10: Get Personality');
  try {
    const response = await backendManager.request('GET', '/api/personality?user_id=1');

    assert(response.name !== undefined, 'Personality name is returned');
    assert(response.traits !== undefined, 'Personality traits are returned');
    assert(response.traits.humor !== undefined, 'Humor trait exists');
    assert(response.traits.energy !== undefined, 'Energy trait exists');
    assert(response.traits.curiosity !== undefined, 'Curiosity trait exists');
    assert(response.traits.formality !== undefined, 'Formality trait exists');
    assert(response.friendship_level !== undefined, 'Friendship level exists');
    assert(response.mood !== undefined, 'Mood exists');
    assert(response.interests !== undefined, 'Interests list exists');
    assert(response.quirks !== undefined, 'Quirks list exists');
  } catch (error) {
    assert(false, `Get personality failed: ${error}`);
  }

  // Test 11: Get personality description
  console.log('\nTest 11: Get Personality Description');
  try {
    const response = await backendManager.request('GET', '/api/personality/description?user_id=1');

    assert(response.humor !== undefined, 'Humor description exists');
    assert(response.energy !== undefined, 'Energy description exists');
    assert(response.curiosity !== undefined, 'Curiosity description exists');
    assert(response.formality !== undefined, 'Formality description exists');
  } catch (error) {
    assert(false, `Get personality description failed: ${error}`);
  }
}

/**
 * Test profile API endpoints
 */
async function testProfileAPI(): Promise<void> {
  console.log('\n👤 Testing Profile API...\n');

  // Test 12: Get profile
  console.log('Test 12: Get Profile');
  try {
    const response = await backendManager.request('GET', '/api/profile?user_id=1');

    assert(response.name !== undefined, 'User name exists');
    assert(response.favorites !== undefined, 'Favorites object exists');
    assert(response.important_people !== undefined, 'Important people list exists');
    assert(response.goals !== undefined, 'Goals list exists');
  } catch (error) {
    assert(false, `Get profile failed: ${error}`);
  }

  // Test 13: Get memories
  console.log('\nTest 13: Get Memories');
  try {
    const response = await backendManager.request('GET', '/api/profile/memories?user_id=1');

    assert(response.memories !== undefined, 'Memories list exists');
    assert(Array.isArray(response.memories), 'Memories is an array');
  } catch (error) {
    assert(false, `Get memories failed: ${error}`);
  }
}

/**
 * Test error handling
 */
async function testErrorHandling(): Promise<void> {
  console.log('\n⚠️  Testing Error Handling...\n');

  // Test 14: Invalid endpoint
  console.log('Test 14: Invalid Endpoint');
  try {
    await backendManager.request('GET', '/api/nonexistent');
    assert(false, 'Should have thrown error for invalid endpoint');
  } catch (error) {
    assert(true, 'Correctly throws error for invalid endpoint');
  }

  // Test 15: Invalid method
  console.log('\nTest 15: Invalid Method');
  try {
    await backendManager.request('DELETE', '/api/conversation/start');
    assert(false, 'Should have thrown error for invalid method');
  } catch (error) {
    assert(true, 'Correctly throws error for invalid method');
  }

  // Test 16: Missing required parameters
  console.log('\nTest 16: Missing Parameters');
  try {
    await backendManager.request('POST', '/api/message', {
      // Missing required fields
      user_id: 1,
    });
    assert(false, 'Should have thrown error for missing parameters');
  } catch (error) {
    assert(true, 'Correctly throws error for missing parameters');
  }
}

/**
 * Test backend shutdown
 */
async function testBackendShutdown(): Promise<void> {
  console.log('\n🛑 Testing Backend Shutdown...\n');

  // Test 17: Backend stops successfully
  console.log('Test 17: Backend Shutdown');
  try {
    await backendManager.stop();
    assert(true, 'Backend stopped successfully');
    assert(!backendManager.isBackendRunning(), 'Backend is marked as not running');
  } catch (error) {
    assert(false, `Backend shutdown failed: ${error}`);
  }

  // Test 18: Requests fail after shutdown
  console.log('\nTest 18: Requests After Shutdown');
  try {
    await backendManager.request('GET', '/health');
    assert(false, 'Should have thrown error after shutdown');
  } catch (error) {
    assert(true, 'Correctly throws error when backend is not running');
  }
}

/**
 * Main test runner
 */
async function runTests(): Promise<void> {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║     IPC Communication End-to-End Test Suite                  ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');

  const startTime = Date.now();

  try {
    // Run all test suites
    await testBackendManager();
    await testConversationAPI();
    await testPersonalityAPI();
    await testProfileAPI();
    await testErrorHandling();
    await testBackendShutdown();

  } catch (error) {
    console.error('\n❌ Test suite failed with critical error:', error);
    process.exit(1);
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  // Print summary
  console.log('\n╔══════════════════════════════════════════════════════════════╗');
  console.log('║                      TEST SUMMARY                            ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log(`\nTotal Tests:  ${testsRun}`);
  console.log(`Passed:       ${testsPassed} ✓`);
  console.log(`Failed:       ${testsFailed} ✗`);
  console.log(`Duration:     ${duration}s`);
  console.log(`Success Rate: ${((testsPassed / testsRun) * 100).toFixed(1)}%`);

  if (testsFailed === 0) {
    console.log('\n🎉 All tests passed!\n');
    process.exit(0);
  } else {
    console.log('\n❌ Some tests failed. See details above.\n');
    process.exit(1);
  }
}

// Run tests if executed directly
if (require.main === module) {
  runTests().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { runTests };
