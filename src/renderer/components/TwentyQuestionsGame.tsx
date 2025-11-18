/**
 * TwentyQuestionsGame Component
 * Chess-themed 20 questions guessing game
 */

import React, { useState, useEffect, useCallback } from 'react';
import { GameItem, getRandomItem, QUESTIONS, GAME_ITEMS } from '../../shared/twentyQuestionsData';

type Answer = 'yes' | 'no' | 'maybe';

interface QuestionHistory {
  question: string;
  answer: Answer;
  questionNumber: number;
}

type GameState = 'selecting' | 'playing' | 'won' | 'lost';

export const TwentyQuestionsGame: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>('selecting');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [secretItem, setSecretItem] = useState<GameItem | null>(null);
  const [questionHistory, setQuestionHistory] = useState<QuestionHistory[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [possibleItems, setPossibleItems] = useState<GameItem[]>([...GAME_ITEMS]);
  const [questionsAsked, setQuestionsAsked] = useState(0);
  const [showInstructions, setShowInstructions] = useState(true);

  /**
   * Start a new game
   */
  const startGame = useCallback((selectedDifficulty: 'easy' | 'medium' | 'hard') => {
    const item = getRandomItem(selectedDifficulty);
    setSecretItem(item);
    setDifficulty(selectedDifficulty);
    setGameState('playing');
    setQuestionHistory([]);
    setCurrentQuestionIndex(0);
    setPossibleItems([...GAME_ITEMS]);
    setQuestionsAsked(0);
    setShowInstructions(false);
  }, []);

  /**
   * Filter possible items based on answer
   */
  const filterItems = useCallback(
    (propertyKey: string, answer: Answer) => {
      if (!secretItem) return;

      setPossibleItems((prev) => {
        return prev.filter((item) => {
          const propertyValue = item.properties[propertyKey];

          if (answer === 'yes') {
            return propertyValue === true;
          } else if (answer === 'no') {
            return propertyValue === false || propertyValue === undefined;
          } else {
            // 'maybe' - keep both
            return true;
          }
        });
      });
    },
    [secretItem]
  );

  /**
   * Handle answer to current question
   */
  const handleAnswer = useCallback(
    (answer: Answer) => {
      if (!secretItem || questionsAsked >= 20) return;

      const currentQuestion = QUESTIONS[currentQuestionIndex];
      const newHistory: QuestionHistory = {
        question: currentQuestion.question,
        answer,
        questionNumber: questionsAsked + 1,
      };

      setQuestionHistory((prev) => [...prev, newHistory]);
      filterItems(currentQuestion.property, answer);
      setQuestionsAsked((prev) => prev + 1);

      // Move to next question
      setCurrentQuestionIndex((prev) => (prev + 1) % QUESTIONS.length);

      // Check if we should make a guess
      if (questionsAsked + 1 >= 18 || possibleItems.length <= 3) {
        // Try to make a guess
        setTimeout(() => makeGuess(), 1000);
      }
    },
    [secretItem, questionsAsked, currentQuestionIndex, possibleItems.length, filterItems]
  );

  /**
   * Make a guess
   */
  const makeGuess = useCallback(() => {
    if (!secretItem) return;

    // Pick the most likely item from possibleItems
    const guess = possibleItems[0] || GAME_ITEMS[0];

    if (guess.id === secretItem.id) {
      setGameState('won');
    } else if (questionsAsked >= 20) {
      setGameState('lost');
    }
  }, [secretItem, possibleItems, questionsAsked]);

  /**
   * Force a guess (when player thinks AI is ready)
   */
  const forceGuess = useCallback(() => {
    makeGuess();
  }, [makeGuess]);

  /**
   * Reset game
   */
  const resetGame = useCallback(() => {
    setGameState('selecting');
    setSecretItem(null);
    setQuestionHistory([]);
    setCurrentQuestionIndex(0);
    setPossibleItems([...GAME_ITEMS]);
    setQuestionsAsked(0);
  }, []);

  /**
   * Get current guess
   */
  const getCurrentGuess = (): string => {
    if (possibleItems.length === 0) return 'Unknown';
    return possibleItems[0]?.name || 'Unknown';
  };

  return (
    <div className="p-6 pb-24 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          20 Questions ♟️
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Think of a chess piece, opening, player, or term. I'll try to guess it!
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
            <p>2. Think of something chess-related (piece, opening, player, or term)</p>
            <p>3. Answer my yes/no questions honestly</p>
            <p>4. I'll try to guess what you're thinking within 20 questions!</p>
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
            <div className="text-sm opacity-90">Basic pieces and terms</div>
          </button>
          <button
            onClick={() => startGame('medium')}
            className="bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl"
          >
            <div className="text-4xl mb-2">⚡</div>
            <div className="text-xl font-bold mb-1">Medium</div>
            <div className="text-sm opacity-90">Openings and famous players</div>
          </button>
          <button
            onClick={() => startGame('hard')}
            className="bg-gradient-to-br from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-xl p-6 transition-all shadow-lg hover:shadow-xl"
          >
            <div className="text-4xl mb-2">🔥</div>
            <div className="text-xl font-bold mb-1">Hard</div>
            <div className="text-sm opacity-90">Advanced tactics and history</div>
          </button>
        </div>
      )}

      {/* Game Play */}
      {gameState === 'playing' && secretItem && (
        <div className="space-y-6">
          {/* Progress */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Questions Asked: {questionsAsked} / 20
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Possibilities: {possibleItems.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${(questionsAsked / 20) * 100}%` }}
              />
            </div>
          </div>

          {/* Current Question */}
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl p-8 border border-purple-200 dark:border-purple-800 text-center">
            <div className="text-sm text-purple-700 dark:text-purple-300 mb-2">
              Question #{questionsAsked + 1}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              {QUESTIONS[currentQuestionIndex].question}
            </h2>

            <div className="flex gap-3 justify-center flex-wrap">
              <button
                onClick={() => handleAnswer('yes')}
                className="px-8 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-semibold transition-colors shadow-lg"
              >
                ✓ Yes
              </button>
              <button
                onClick={() => handleAnswer('no')}
                className="px-8 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-semibold transition-colors shadow-lg"
              >
                ✗ No
              </button>
              <button
                onClick={() => handleAnswer('maybe')}
                className="px-8 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-semibold transition-colors shadow-lg"
              >
                ? Not Sure
              </button>
            </div>
          </div>

          {/* Current Best Guess */}
          {possibleItems.length > 0 && possibleItems.length <= 5 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="text-sm font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                💡 I'm thinking it might be...
              </div>
              <div className="text-lg font-bold text-yellow-800 dark:text-yellow-300">
                {getCurrentGuess()}
              </div>
              <button
                onClick={forceGuess}
                className="mt-3 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Is this your guess?
              </button>
            </div>
          )}

          {/* Question History */}
          {questionHistory.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Previous Questions
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {questionHistory.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between text-sm p-2 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <span className="text-gray-700 dark:text-gray-300">
                      {item.questionNumber}. {item.question}
                    </span>
                    <span
                      className={`font-semibold ${
                        item.answer === 'yes'
                          ? 'text-green-600 dark:text-green-400'
                          : item.answer === 'no'
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-yellow-600 dark:text-yellow-400'
                      }`}
                    >
                      {item.answer === 'yes' ? '✓' : item.answer === 'no' ? '✗' : '?'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Game Won */}
      {gameState === 'won' && (
        <div className="text-center space-y-6">
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-12 border border-green-200 dark:border-green-800">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-3xl font-bold text-green-900 dark:text-green-200 mb-2">
              I Got It!
            </h2>
            <p className="text-xl text-green-800 dark:text-green-300 mb-4">
              You were thinking of: <span className="font-bold">{secretItem?.name}</span>
            </p>
            <p className="text-sm text-green-700 dark:text-green-400">
              I guessed it in {questionsAsked} questions!
            </p>
          </div>
          <button
            onClick={resetGame}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold transition-colors shadow-lg"
          >
            Play Again
          </button>
        </div>
      )}

      {/* Game Lost */}
      {gameState === 'lost' && (
        <div className="text-center space-y-6">
          <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 rounded-xl p-12 border border-red-200 dark:border-red-800">
            <div className="text-6xl mb-4">🤔</div>
            <h2 className="text-3xl font-bold text-red-900 dark:text-red-200 mb-2">
              You Stumped Me!
            </h2>
            <p className="text-xl text-red-800 dark:text-red-300 mb-4">
              I couldn't guess: <span className="font-bold">{secretItem?.name}</span>
            </p>
            <p className="text-sm text-red-700 dark:text-red-400">
              Great job! You really know your chess!
            </p>
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

export default TwentyQuestionsGame;
