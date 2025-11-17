/**
 * IPC Integration Test (Renderer Process)
 *
 * Tests IPC communication from renderer to main process
 * This can be run in the browser console or as a module
 */

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  duration: number;
}

class IPCIntegrationTest {
  private results: TestResult[] = [];

  /**
   * Run a single test
   */
  private async runTest(
    name: string,
    testFn: () => Promise<void>
  ): Promise<void> {
    console.log(`\n🧪 ${name}...`);
    const startTime = Date.now();

    try {
      await testFn();
      const duration = Date.now() - startTime;
      this.results.push({ name, passed: true, duration });
      console.log(`  ✓ Passed (${duration}ms)`);
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.results.push({ name, passed: false, error: errorMessage, duration });
      console.error(`  ✗ Failed: ${errorMessage} (${duration}ms)`);
    }
  }

  /**
   * Test backend status
   */
  private async testBackendStatus(): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke('backend-status');

    if (!result.success) {
      throw new Error(`Backend status failed: ${result.error}`);
    }

    const status = result.data;
    if (!status.running) {
      throw new Error('Backend is not running');
    }

    if (status.port !== 8000) {
      throw new Error(`Expected port 8000, got ${status.port}`);
    }
  }

  /**
   * Test backend health check
   */
  private async testBackendHealth(): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke('backend-health');

    if (!result.success) {
      throw new Error(`Backend health check failed: ${result.error}`);
    }

    if (!result.data.healthy) {
      throw new Error('Backend is not healthy');
    }
  }

  /**
   * Test start conversation
   */
  private async testStartConversation(): Promise<number> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke('start-conversation');

    if (!result.success) {
      throw new Error(`Start conversation failed: ${result.error}`);
    }

    const data = result.data;
    if (!data.conversation_id) {
      throw new Error('No conversation ID returned');
    }

    if (!data.greeting) {
      throw new Error('No greeting returned');
    }

    if (!data.personality) {
      throw new Error('No personality info returned');
    }

    return data.conversation_id;
  }

  /**
   * Test send message
   */
  private async testSendMessage(conversationId: number): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke(
      'send-message',
      conversationId,
      'Hello! This is a test message.'
    );

    if (!result.success) {
      throw new Error(`Send message failed: ${result.error}`);
    }

    const data = result.data;
    if (!data.content) {
      throw new Error('No response content returned');
    }

    if (typeof data.content !== 'string') {
      throw new Error('Response content is not a string');
    }

    if (!data.metadata) {
      throw new Error('No metadata returned');
    }
  }

  /**
   * Test end conversation
   */
  private async testEndConversation(conversationId: number): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke('end-conversation', conversationId);

    if (!result.success) {
      throw new Error(`End conversation failed: ${result.error}`);
    }
  }

  /**
   * Test get personality
   */
  private async testGetPersonality(): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke('get-personality');

    if (!result.success) {
      throw new Error(`Get personality failed: ${result.error}`);
    }

    const data = result.data;
    if (!data.name) {
      throw new Error('No personality name returned');
    }

    if (!data.traits) {
      throw new Error('No personality traits returned');
    }

    if (!data.mood) {
      throw new Error('No mood returned');
    }

    if (!data.friendship_level) {
      throw new Error('No friendship level returned');
    }
  }

  /**
   * Test get profile
   */
  private async testGetProfile(): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    const result = await window.electron.invoke('get-profile');

    if (!result.success) {
      throw new Error(`Get profile failed: ${result.error}`);
    }

    const data = result.data;
    if (!data.name) {
      throw new Error('No user name returned');
    }

    if (!data.favorites) {
      throw new Error('No favorites returned');
    }
  }

  /**
   * Test invalid channel (should fail)
   */
  private async testInvalidChannel(): Promise<void> {
    if (!window.electron) {
      throw new Error('Electron API not available');
    }

    try {
      // @ts-ignore - Intentionally testing invalid channel
      await window.electron.invoke('invalid-channel-name');
      throw new Error('Should have thrown error for invalid channel');
    } catch (error) {
      // Expected to fail - this is correct behavior
      if (error instanceof Error && error.message.includes('Invalid channel')) {
        return; // Test passed
      }
      throw error;
    }
  }

  /**
   * Run all tests
   */
  async runAll(): Promise<void> {
    console.log('╔══════════════════════════════════════════════════════════════╗');
    console.log('║   IPC Integration Test (Renderer → Main → Backend)          ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');

    const startTime = Date.now();
    let conversationId: number = 0;

    // Test 1: Backend status
    await this.runTest('Backend Status', async () => {
      await this.testBackendStatus();
    });

    // Test 2: Backend health
    await this.runTest('Backend Health Check', async () => {
      await this.testBackendHealth();
    });

    // Test 3: Get personality
    await this.runTest('Get Personality', async () => {
      await this.testGetPersonality();
    });

    // Test 4: Get profile
    await this.runTest('Get Profile', async () => {
      await this.testGetProfile();
    });

    // Test 5: Start conversation
    await this.runTest('Start Conversation', async () => {
      conversationId = await this.testStartConversation();
    });

    // Test 6: Send message
    await this.runTest('Send Message', async () => {
      await this.testSendMessage(conversationId);
    });

    // Test 7: Send follow-up message
    await this.runTest('Send Follow-up Message', async () => {
      await this.testSendMessage(conversationId);
    });

    // Test 8: End conversation
    await this.runTest('End Conversation', async () => {
      await this.testEndConversation(conversationId);
    });

    // Test 9: Invalid channel (error handling)
    await this.runTest('Invalid Channel (Error Handling)', async () => {
      await this.testInvalidChannel();
    });

    const totalDuration = Date.now() - startTime;
    this.printSummary(totalDuration);
  }

  /**
   * Print test summary
   */
  private printSummary(totalDuration: number): void {
    const passed = this.results.filter((r) => r.passed).length;
    const failed = this.results.filter((r) => !r.passed).length;
    const total = this.results.length;

    console.log('\n╔══════════════════════════════════════════════════════════════╗');
    console.log('║                      TEST SUMMARY                            ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');
    console.log(`\nTotal Tests:  ${total}`);
    console.log(`Passed:       ${passed} ✓`);
    console.log(`Failed:       ${failed} ✗`);
    console.log(`Duration:     ${(totalDuration / 1000).toFixed(2)}s`);
    console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);

    if (failed > 0) {
      console.log('\n❌ Failed Tests:');
      this.results
        .filter((r) => !r.passed)
        .forEach((r) => {
          console.log(`  - ${r.name}: ${r.error}`);
        });
    }

    if (failed === 0) {
      console.log('\n🎉 All IPC integration tests passed!\n');
    } else {
      console.log('\n❌ Some tests failed. Check details above.\n');
    }

    // Return results for programmatic access
    return this.results as any;
  }

  /**
   * Get test results
   */
  getResults(): TestResult[] {
    return this.results;
  }
}

// Export for use in console or as module
const testRunner = new IPCIntegrationTest();

// Make available in browser console
if (typeof window !== 'undefined') {
  (window as any).testIPC = () => testRunner.runAll();
  console.log('💡 IPC integration tests loaded!');
  console.log('   Run tests with: testIPC()');
}

export { IPCIntegrationTest, testRunner };
