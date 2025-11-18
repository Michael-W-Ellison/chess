/**
 * StoryCollaborationGame Component
 * Turn-based collaborative storytelling with AI
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  StoryPrompt,
  StoryTheme,
  StoryDifficulty,
  getRandomStoryPrompt,
  validateContribution,
  generateAIContribution,
} from '../../shared/storyCollaborationData';

type GameState = 'selecting' | 'playing' | 'finished';
type Turn = 'user' | 'ai';

interface StorySegment {
  text: string;
  author: 'user' | 'ai' | 'starter';
  timestamp: number;
}

export const StoryCollaborationGame: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>('selecting');
  const [selectedPrompt, setSelectedPrompt] = useState<StoryPrompt | null>(null);
  const [storySegments, setStorySegments] = useState<StorySegment[]>([]);
  const [currentTurn, setCurrentTurn] = useState<Turn>('user');
  const [userInput, setUserInput] = useState('');
  const [turnCount, setTurnCount] = useState(0);
  const [feedback, setFeedback] = useState<string>('');
  const [isAIThinking, setIsAIThinking] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const storyContainerRef = useRef<HTMLDivElement>(null);

  /**
   * Start a new story with selected prompt
   */
  const startStory = useCallback((difficulty: StoryDifficulty, theme?: StoryTheme) => {
    const prompt = getRandomStoryPrompt(difficulty, theme);
    setSelectedPrompt(prompt);
    setStorySegments([
      {
        text: prompt.starter,
        author: 'starter',
        timestamp: Date.now(),
      },
    ]);
    setGameState('playing');
    setCurrentTurn('user');
    setTurnCount(0);
    setUserInput('');
    setFeedback('');
    setShowInstructions(false);

    // Focus input after a short delay
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  /**
   * Scroll to bottom of story
   */
  useEffect(() => {
    if (storyContainerRef.current) {
      storyContainerRef.current.scrollTop = storyContainerRef.current.scrollHeight;
    }
  }, [storySegments, isAIThinking]);

  /**
   * Handle user submission
   */
  const handleUserSubmit = useCallback(() => {
    if (!selectedPrompt || currentTurn !== 'user') return;

    const validation = validateContribution(userInput);

    if (!validation.valid) {
      setFeedback(validation.message || 'Invalid contribution');
      setTimeout(() => setFeedback(''), 3000);
      return;
    }

    // Add user's contribution
    const newSegment: StorySegment = {
      text: userInput.trim(),
      author: 'user',
      timestamp: Date.now(),
    };

    setStorySegments((prev) => [...prev, newSegment]);
    setUserInput('');
    setTurnCount((prev) => prev + 1);

    // Check if story should end
    const newTurnCount = turnCount + 1;
    if (newTurnCount >= selectedPrompt.maxTurns) {
      setGameState('finished');
      return;
    }

    // Switch to AI turn
    setCurrentTurn('ai');
    setIsAIThinking(true);

    // Simulate AI thinking and response
    setTimeout(() => {
      const fullStory = [...storySegments, newSegment].map((s) => s.text).join(' ');
      const aiResponse = generateAIContribution(selectedPrompt, fullStory, newTurnCount + 1);

      setStorySegments((prev) => [
        ...prev,
        {
          text: aiResponse,
          author: 'ai',
          timestamp: Date.now(),
        },
      ]);

      setTurnCount((prev) => prev + 1);
      setIsAIThinking(false);

      // Check if story should end after AI turn
      if (newTurnCount + 1 >= selectedPrompt.maxTurns) {
        setGameState('finished');
      } else {
        setCurrentTurn('user');
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    }, 2000 + Math.random() * 1000); // Random delay 2-3 seconds
  }, [selectedPrompt, currentTurn, userInput, turnCount, storySegments]);

  /**
   * Reset to story selection
   */
  const resetGame = useCallback(() => {
    setGameState('selecting');
    setSelectedPrompt(null);
    setStorySegments([]);
    setCurrentTurn('user');
    setUserInput('');
    setTurnCount(0);
    setFeedback('');
    setIsAIThinking(false);
  }, []);

  /**
   * Get full story text
   */
  const getFullStory = useCallback(() => {
    return storySegments.map((s) => s.text).join(' ');
  }, [storySegments]);

  /**
   * Get theme emoji
   */
  const getThemeEmoji = (theme: StoryTheme): string => {
    const emojis = {
      adventure: '🗺️',
      mystery: '🔍',
      historical: '📜',
      fantasy: '✨',
      comedy: '😂',
    };
    return emojis[theme];
  };

  /**
   * Get difficulty color
   */
  const getDifficultyColor = (difficulty: StoryDifficulty): string => {
    const colors = {
      easy: 'from-green-500 to-green-600',
      medium: 'from-blue-500 to-blue-600',
      hard: 'from-purple-500 to-purple-600',
    };
    return colors[difficulty];
  };

  return (
    <div className="p-6 pb-24 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Story Collaboration 📖
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Create amazing chess stories together, one turn at a time!
        </p>
      </div>

      {/* Instructions */}
      {showInstructions && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 dark:text-blue-200 mb-3 flex items-center gap-2">
            <span>📖</span>
            <span>How to Play</span>
          </h2>
          <div className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
            <p>1. Choose a story theme and difficulty</p>
            <p>2. Read the story starter carefully</p>
            <p>3. Take turns with AI adding to the story</p>
            <p>4. Each contribution should be 10-500 characters</p>
            <p>5. Build an exciting chess-themed narrative together!</p>
          </div>
        </div>
      )}

      {/* Story Selection */}
      {gameState === 'selecting' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Choose Your Adventure
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Easy */}
              <button
                onClick={() => startStory('easy')}
                className={`bg-gradient-to-br ${getDifficultyColor('easy')} hover:from-green-600 hover:to-green-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl text-left`}
              >
                <div className="text-4xl mb-2">🌱</div>
                <div className="text-xl font-bold mb-1">Easy Stories</div>
                <div className="text-sm opacity-90">4-8 turns</div>
                <div className="text-xs mt-2 opacity-75">
                  Simple, fun adventures perfect for beginners
                </div>
              </button>

              {/* Medium */}
              <button
                onClick={() => startStory('medium')}
                className={`bg-gradient-to-br ${getDifficultyColor('medium')} hover:from-blue-600 hover:to-blue-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl text-left`}
              >
                <div className="text-4xl mb-2">⚡</div>
                <div className="text-xl font-bold mb-1">Medium Stories</div>
                <div className="text-sm opacity-90">6-10 turns</div>
                <div className="text-xs mt-2 opacity-75">
                  Engaging plots with more complexity
                </div>
              </button>

              {/* Hard */}
              <button
                onClick={() => startStory('hard')}
                className={`bg-gradient-to-br ${getDifficultyColor('hard')} hover:from-purple-600 hover:to-purple-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl text-left`}
              >
                <div className="text-4xl mb-2">🔥</div>
                <div className="text-xl font-bold mb-1">Hard Stories</div>
                <div className="text-sm opacity-90">8-12 turns</div>
                <div className="text-xs mt-2 opacity-75">
                  Epic tales with deep narratives
                </div>
              </button>
            </div>
          </div>

          {/* Theme Examples */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Story Themes
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
              <div className="text-center">
                <div className="text-2xl mb-1">🗺️</div>
                <div className="text-gray-700 dark:text-gray-300">Adventure</div>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-1">🔍</div>
                <div className="text-gray-700 dark:text-gray-300">Mystery</div>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-1">📜</div>
                <div className="text-gray-700 dark:text-gray-300">Historical</div>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-1">✨</div>
                <div className="text-gray-700 dark:text-gray-300">Fantasy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-1">😂</div>
                <div className="text-gray-700 dark:text-gray-300">Comedy</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Story Playing */}
      {gameState === 'playing' && selectedPrompt && (
        <div className="space-y-6">
          {/* Story Info */}
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getThemeEmoji(selectedPrompt.theme)}</span>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {selectedPrompt.title}
                </h2>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <div className="text-purple-700 dark:text-purple-300">
                  Turn: <span className="font-bold">{turnCount + 1}/{selectedPrompt.maxTurns}</span>
                </div>
                <div className="px-3 py-1 bg-purple-200 dark:bg-purple-800 rounded-full text-xs font-medium text-purple-800 dark:text-purple-200">
                  {selectedPrompt.theme}
                </div>
              </div>
            </div>
            <p className="text-sm text-purple-700 dark:text-purple-300">
              {selectedPrompt.context}
            </p>
          </div>

          {/* Story Display */}
          <div
            ref={storyContainerRef}
            className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto space-y-4"
          >
            {storySegments.map((segment, index) => (
              <div
                key={index}
                className={`${
                  segment.author === 'starter'
                    ? 'bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/30 dark:to-blue-900/30 border-l-4 border-purple-500'
                    : segment.author === 'user'
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500'
                    : 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500'
                } p-4 rounded-r-lg`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase">
                    {segment.author === 'starter'
                      ? '📖 Story Start'
                      : segment.author === 'user'
                      ? '✍️ You'
                      : '🤖 AI Partner'}
                  </span>
                </div>
                <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                  {segment.text}
                </p>
              </div>
            ))}

            {/* AI Thinking Indicator */}
            {isAIThinking && (
              <div className="bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 p-4 rounded-r-lg">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="animate-bounce delay-0">●</span>
                    <span className="animate-bounce delay-75">●</span>
                    <span className="animate-bounce delay-150">●</span>
                  </div>
                  <span className="text-sm text-green-700 dark:text-green-300 italic">
                    AI is writing...
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Suggestions */}
          {selectedPrompt.suggestions.length > 0 && turnCount < selectedPrompt.suggestions.length && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex items-center gap-2 text-yellow-900 dark:text-yellow-200">
                <span>💡</span>
                <span className="font-semibold">Suggestion:</span>
                <span className="text-sm">{selectedPrompt.suggestions[turnCount]}</span>
              </div>
            </div>
          )}

          {/* Input Area */}
          {currentTurn === 'user' && !isAIThinking && (
            <div className="space-y-3">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                <label className="block text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
                  Your Turn - Add to the Story:
                </label>
                <textarea
                  ref={inputRef}
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="Continue the story... (10-500 characters)"
                  className="w-full px-4 py-3 rounded-lg border-2 border-blue-300 dark:border-blue-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none resize-none"
                  rows={4}
                  maxLength={500}
                />
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {userInput.length}/500 characters
                  </span>
                  <button
                    onClick={handleUserSubmit}
                    disabled={userInput.trim().length === 0}
                    className="px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                  >
                    Submit Turn
                  </button>
                </div>
              </div>

              {/* Feedback */}
              {feedback && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
                  ⚠️ {feedback}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Story Finished */}
      {gameState === 'finished' && (
        <div className="text-center space-y-6">
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-12 border border-green-200 dark:border-green-800">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-3xl font-bold text-green-900 dark:text-green-200 mb-4">
              Story Complete!
            </h2>

            {selectedPrompt && (
              <div className="mb-6">
                <p className="text-xl text-green-800 dark:text-green-300 mb-2">
                  "{selectedPrompt.title}"
                </p>
                <p className="text-sm text-green-700 dark:text-green-400">
                  {storySegments.length} segments • {getFullStory().split(' ').length} words
                </p>
              </div>
            )}

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-h-96 overflow-y-auto text-left mb-6">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Your Completed Story:
              </h3>
              <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                {getFullStory()}
              </p>
            </div>

            <div className="text-lg font-semibold text-green-800 dark:text-green-300">
              🌟 Great collaboration! You've created something unique!
            </div>
          </div>

          <button
            onClick={resetGame}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold transition-colors shadow-lg"
          >
            Create Another Story
          </button>
        </div>
      )}
    </div>
  );
};

export default StoryCollaborationGame;
