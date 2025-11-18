/**
 * Sound Effects Utility
 * Uses Web Audio API to generate sound effects without requiring audio files
 */

// Sound preferences stored in localStorage
const SOUND_ENABLED_KEY = 'soundEffectsEnabled';

export function isSoundEnabled(): boolean {
  const stored = localStorage.getItem(SOUND_ENABLED_KEY);
  return stored === null ? true : stored === 'true';
}

export function setSoundEnabled(enabled: boolean): void {
  localStorage.setItem(SOUND_ENABLED_KEY, enabled.toString());
}

/**
 * Play a message send sound effect
 * Creates a pleasant "swoosh" or "pop" sound
 */
export function playMessageSendSound(): void {
  if (!isSoundEnabled()) return;

  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

    // Create oscillator for the main tone
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Configure the sound - rising pitch "swoosh"
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(1200, audioContext.currentTime + 0.1);

    // Configure volume envelope - quick fade out
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);

    // Play the sound
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.15);

    // Clean up
    setTimeout(() => {
      audioContext.close();
    }, 200);
  } catch (error) {
    console.warn('Failed to play send sound:', error);
  }
}

/**
 * Play a message receive sound effect
 * Creates a gentle notification sound
 */
export function playMessageReceiveSound(): void {
  if (!isSoundEnabled()) return;

  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

    // Create oscillator for the main tone
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Configure the sound - descending pitch "ding"
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(1000, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(800, audioContext.currentTime + 0.1);

    // Configure volume envelope
    gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

    // Play the sound
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.2);

    // Clean up
    setTimeout(() => {
      audioContext.close();
    }, 250);
  } catch (error) {
    console.warn('Failed to play receive sound:', error);
  }
}

/**
 * Play an achievement unlock sound effect
 * Creates an exciting "success" sound
 */
export function playAchievementSound(): void {
  if (!isSoundEnabled()) return;

  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

    // Create multiple oscillators for a richer sound
    const osc1 = audioContext.createOscillator();
    const osc2 = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    osc1.connect(gainNode);
    osc2.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Configure the sound - rising chord
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
    osc1.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
    osc1.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5

    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(261.63, audioContext.currentTime); // C4
    osc2.frequency.setValueAtTime(329.63, audioContext.currentTime + 0.1); // E4
    osc2.frequency.setValueAtTime(392.00, audioContext.currentTime + 0.2); // G4

    // Configure volume envelope
    gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);

    // Play the sound
    osc1.start(audioContext.currentTime);
    osc2.start(audioContext.currentTime);
    osc1.stop(audioContext.currentTime + 0.4);
    osc2.stop(audioContext.currentTime + 0.4);

    // Clean up
    setTimeout(() => {
      audioContext.close();
    }, 500);
  } catch (error) {
    console.warn('Failed to play achievement sound:', error);
  }
}

/**
 * Play a button click sound effect
 * Creates a subtle "tap" sound
 */
export function playClickSound(): void {
  if (!isSoundEnabled()) return;

  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Configure the sound - very short click
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(1200, audioContext.currentTime);

    // Very short and quiet
    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.05);

    // Play the sound
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.05);

    // Clean up
    setTimeout(() => {
      audioContext.close();
    }, 100);
  } catch (error) {
    console.warn('Failed to play click sound:', error);
  }
}
