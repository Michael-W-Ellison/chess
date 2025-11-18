/**
 * WordAssociationGame Component
 * Chess-themed word association game with timer and scoring
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  WordPrompt,
  getRandomPrompt,
  isValidAssociation,
  calculateFinalScore,
} from '../../shared/wordAssociationData';

type GameState = 'selecting' | 'playing' | 'finished';

interface WordEntry {
  word: string;
  points: number;
  timestamp: number;
}

export const WordAssociationGame: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>('selecting');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [currentPrompt, setCurrentPrompt] = useState<WordPrompt | null>(null);
  const [userInput, setUserInput] = useState('');
  const [usedWords, setUsedWords] = useState<string[]>([]);
  const [wordEntries, setWordEntries] = useState<WordEntry[]>([]);
  const [score, setScore] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [currentHintIndex, setCurrentHintIndex] = useState(0);
  const [feedback, setFeedback] = useState<string>('');
  const [showInstructions, setShowInstructions] = useState(true);

  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Start a new game
   */
  const startGame = useCallback((selectedDifficulty: 'easy' | 'medium' | 'hard') => {
    const prompt = getRandomPrompt(selectedDifficulty);
    setCurrentPrompt(prompt);
    setDifficulty(selectedDifficulty);
    setGameState('playing');
    setUserInput('');
    setUsedWords([]);
    setWordEntries([]);
    setScore(0);
    setTimeRemaining(prompt.timeLimit);
    setShowHint(false);
    setCurrentHintIndex(0);
    setFeedback('');
    setShowInstructions(false);

    // Focus input
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  /**
   * Timer countdown
   */
  useEffect(() => {
    if (gameState === 'playing' && timeRemaining > 0) {
      timerRef.current = setTimeout(() => {
        setTimeRemaining((prev) => prev - 1);
      }, 1000);
    } else if (gameState === 'playing' && timeRemaining === 0) {
      endGame();
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [gameState, timeRemaining]);

  /**
   * End the game
   */
  const endGame = useCallback(() => {
    setGameState('finished');
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
  }, []);

  /**
   * Handle word submission
   */
  const handleSubmit = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault();

      if (!currentPrompt || userInput.trim().length === 0) return;

      const result = isValidAssociation(currentPrompt, userInput, usedWords);

      if (result.valid) {
        const newWord = userInput.toLowerCase().trim();
        setUsedWords((prev) => [...prev, newWord]);
        setWordEntries((prev) => [
          ...prev,
          {
            word: userInput,
            points: result.points,
            timestamp: Date.now(),
          },
        ]);
        setScore((prev) => prev + result.points);
        setFeedback(result.message || 'Good!');
        setUserInput('');

        // Clear feedback after 1.5s
        setTimeout(() => setFeedback(''), 1500);
      } else {
        setFeedback(result.message || 'Try again!');
        setTimeout(() => setFeedback(''), 2000);
      }

      inputRef.current?.focus();
    },
    [currentPrompt, userInput, usedWords]
  );

  /**
   * Show next hint
   */
  const showNextHint = useCallback(() => {
    if (!currentPrompt) return;

    if (currentHintIndex < currentPrompt.hints.length) {
      setShowHint(true);
      setCurrentHintIndex((prev) => prev + 1);
    }
  }, [currentPrompt, currentHintIndex]);

  /**
   * Get time color based on remaining time
   */
  const getTimeColor = (): string => {
    if (!currentPrompt) return 'text-gray-500';

    const percentage = (timeRemaining / currentPrompt.timeLimit) * 100;
    if (percentage > 50) return 'text-green-600 dark:text-green-400';
    if (percentage > 25) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  /**
   * Reset game
   */
  const resetGame = useCallback(() => {
    setGameState('selecting');
    setCurrentPrompt(null);
    setUserInput('');
    setUsedWords([]);
    setWordEntries([]);
    setScore(0);
    setTimeRemaining(0);
    setShowHint(false);
    setCurrentHintIndex(0);
    setFeedback('');
  }, []);

  /**
   * Get final score
   */
  const getFinalScore = () => {
    if (!currentPrompt) return { baseScore: 0, timeBonus: 0, totalScore: 0 };
    return calculateFinalScore(score, timeRemaining, currentPrompt.timeLimit);
  };

  return (
    <div className="p-6 pb-24 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Word Association 🧠
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Type as many chess-related words as you can!
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
            <p>1. Choose a difficulty level</p>
            <p>2. You'll see a chess word or concept</p>
            <p>3. Type words related to it as fast as you can!</p>
            <p>4. Perfect matches: +10 points | Good words: +5 points</p>
            <p>5. Beat the clock for bonus points!</p>
          </div>
        </div>
      )}

      {/* Difficulty Selection */}
      {gameState === 'selecting' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => startGame('easy')}
            className="bg-gradient-to-br from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl"
          >
            <div className="text-4xl mb-2">🌱</div>
            <div className="text-xl font-bold mb-1">Easy</div>
            <div className="text-sm opacity-90">60 seconds</div>
            <div className="text-xs mt-2 opacity-75">Common pieces & concepts</div>
          </button>
          <button
            onClick={() => startGame('medium')}
            className="bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl"
          >
            <div className="text-4xl mb-2">⚡</div>
            <div className="text-xl font-bold mb-1">Medium</div>
            <div className="text-sm opacity-90">45 seconds</div>
            <div className="text-xs mt-2 opacity-75">Tactics & openings</div>
          </button>
          <button
            onClick={() => startGame('hard')}
            className="bg-gradient-to-br from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl"
          >
            <div className="text-4xl mb-2">🔥</div>
            <div className="text-xl font-bold mb-1">Hard</div>
            <div className="text-sm opacity-90">30 seconds</div>
            <div className="text-xs mt-2 opacity-75">Advanced concepts</div>
          </button>
        </div>
      )}

      {/* Game Play */}
      {gameState === 'playing' && currentPrompt && (
        <div className="space-y-6">
          {/* Stats Bar */}
          <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className={`text-3xl font-bold ${getTimeColor()}`}>{timeRemaining}s</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Time Left</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{score}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Score</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {usedWords.length}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Words</div>
              </div>
            </div>

            <button
              onClick={showNextHint}
              disabled={currentHintIndex >= currentPrompt.hints.length}
              className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors text-sm"
            >
              💡 Hint ({currentPrompt.hints.length - currentHintIndex} left)
            </button>
          </div>

          {/* Prompt Word */}
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl p-8 border border-purple-200 dark:border-purple-800 text-center">
            <div className="text-sm text-purple-700 dark:text-purple-300 mb-2">
              Find words related to...
            </div>
            <h2 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {currentPrompt.word}
            </h2>
            <div className="inline-block px-3 py-1 bg-purple-200 dark:bg-purple-800 rounded-full text-xs font-medium text-purple-800 dark:text-purple-200">
              {currentPrompt.category}
            </div>
          </div>

          {/* Hint Display */}
          {showHint && currentHintIndex > 0 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex items-center gap-2 text-yellow-900 dark:text-yellow-200">
                <span>💡</span>
                <span className="font-semibold">Hint:</span>
                <span>{currentPrompt.hints[currentHintIndex - 1]}</span>
              </div>
            </div>
          )}

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="relative">
            <input
              ref={inputRef}
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Type a related word..."
              className="w-full px-6 py-4 text-lg rounded-xl border-2 border-blue-300 dark:border-blue-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none shadow-lg"
              autoComplete="off"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
            >
              Submit
            </button>
          </form>

          {/* Feedback */}
          {feedback && (
            <div className="text-center">
              <div
                className={`inline-block px-4 py-2 rounded-lg font-semibold ${
                  feedback.includes('+')
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                    : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                }`}
              >
                {feedback}
              </div>
            </div>
          )}

          {/* Word History */}
          {wordEntries.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Your Words ({wordEntries.length})
              </h3>
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                {wordEntries
                  .slice()
                  .reverse()
                  .map((entry, index) => (
                    <div
                      key={index}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                        entry.points === 10
                          ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-300 dark:border-green-700'
                          : 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-700'
                      }`}
                    >
                      {entry.word} <span className="font-bold">+{entry.points}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Game Finished */}
      {gameState === 'finished' && (
        <div className="text-center space-y-6">
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-12 border border-green-200 dark:border-green-800">
            <div className="text-6xl mb-4">
              {getFinalScore().totalScore >= 100 ? '🏆' : getFinalScore().totalScore >= 50 ? '🎉' : '👏'}
            </div>
            <h2 className="text-3xl font-bold text-green-900 dark:text-green-200 mb-4">
              Time's Up!
            </h2>

            <div className="space-y-3 mb-6">
              <div className="text-xl text-green-800 dark:text-green-300">
                Base Score: <span className="font-bold">{getFinalScore().baseScore}</span>
              </div>
              <div className="text-xl text-green-800 dark:text-green-300">
                Time Bonus: <span className="font-bold">+{getFinalScore().timeBonus}</span>
              </div>
              <div className="text-3xl font-bold text-green-900 dark:text-green-200">
                Total: {getFinalScore().totalScore}
              </div>
            </div>

            <div className="text-sm text-green-700 dark:text-green-400 mb-4">
              You found {wordEntries.length} words for "{currentPrompt?.word}"!
            </div>

            {/* Performance Message */}
            <div className="text-lg font-semibold text-green-800 dark:text-green-300">
              {getFinalScore().totalScore >= 100 && '🌟 Outstanding! Chess Master!'}
              {getFinalScore().totalScore >= 50 &&
                getFinalScore().totalScore < 100 &&
                '💪 Great job! Keep it up!'}
              {getFinalScore().totalScore < 50 && '👍 Good effort! Try again!'}
            </div>
          </div>

          <button
            onClick={resetGame}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold transition-colors shadow-lg"
          >
            Play Again
          </button>
        </div>
      )}
    </div>
  );
};

export default WordAssociationGame;
