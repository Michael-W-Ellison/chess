/**
 * Word Association Game Data
 * Chess-themed word associations for educational gameplay
 */

export interface WordPrompt {
  id: string;
  word: string;
  category: 'piece' | 'tactic' | 'opening' | 'endgame' | 'general';
  associations: string[];
  hints: string[];
  difficulty: 'easy' | 'medium' | 'hard';
  timeLimit: number; // seconds
}

export const WORD_PROMPTS: WordPrompt[] = [
  // Easy - Pieces
  {
    id: 'king',
    word: 'King',
    category: 'piece',
    difficulty: 'easy',
    timeLimit: 60,
    associations: [
      'royal',
      'castle',
      'castling',
      'checkmate',
      'protect',
      'defense',
      'center',
      'endgame',
      'safety',
      'throne',
      'crown',
      'majesty',
      'important',
      'valuable',
      'escape',
    ],
    hints: ['Most important piece', 'Must be protected', 'Can castle'],
  },
  {
    id: 'queen',
    word: 'Queen',
    category: 'piece',
    difficulty: 'easy',
    timeLimit: 60,
    associations: [
      'powerful',
      'strong',
      'attack',
      'diagonal',
      'straight',
      'move',
      'versatile',
      'sacrifice',
      'checkmate',
      'royal',
      'lady',
      'majesty',
      'nine',
      'points',
      'valuable',
    ],
    hints: ['Most powerful piece', 'Moves in all directions', 'Worth 9 points'],
  },
  {
    id: 'pawn',
    word: 'Pawn',
    category: 'piece',
    difficulty: 'easy',
    timeLimit: 60,
    associations: [
      'promote',
      'forward',
      'capture',
      'diagonal',
      'structure',
      'chain',
      'passed',
      'isolated',
      'doubled',
      'weak',
      'strong',
      'endgame',
      'soldier',
      'sacrifice',
      'advance',
    ],
    hints: ['Can promote', 'Moves forward', 'Most numerous'],
  },

  // Medium - Tactics
  {
    id: 'fork',
    word: 'Fork',
    category: 'tactic',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'knight',
      'attack',
      'double',
      'two',
      'pieces',
      'threat',
      'tactic',
      'win',
      'material',
      'family',
      'royal',
      'simultaneous',
      'branch',
      'split',
      'choose',
    ],
    hints: ['Attack two pieces at once', 'Common knight tactic', 'Forces a choice'],
  },
  {
    id: 'pin',
    word: 'Pin',
    category: 'tactic',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'bishop',
      'rook',
      'queen',
      'attack',
      'line',
      'trapped',
      'cannot',
      'move',
      'absolute',
      'relative',
      'king',
      'defend',
      'immobile',
      'stuck',
      'tactic',
    ],
    hints: ['Piece cannot move safely', 'Absolute or relative', 'Common with bishops'],
  },
  {
    id: 'skewer',
    word: 'Skewer',
    category: 'tactic',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'reverse',
      'pin',
      'attack',
      'line',
      'through',
      'valuable',
      'king',
      'queen',
      'bishop',
      'rook',
      'x-ray',
      'penetrate',
      'pierce',
      'tactic',
      'win',
    ],
    hints: ['Reverse pin', 'Attack through a piece', 'X-ray attack'],
  },

  // Medium - Openings
  {
    id: 'italian',
    word: 'Italian Game',
    category: 'opening',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'e4',
      'e5',
      'nf3',
      'nc6',
      'bc4',
      'bishop',
      'attack',
      'f7',
      'giuoco',
      'piano',
      'classical',
      'center',
      'development',
      'old',
      'popular',
    ],
    hints: ['1.e4 e5 2.Nf3 Nc6 3.Bc4', 'Oldest opening', 'Attacks f7'],
  },
  {
    id: 'sicilian',
    word: 'Sicilian Defense',
    category: 'opening',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'e4',
      'c5',
      'defense',
      'sharp',
      'complex',
      'dragon',
      'najdorf',
      'popular',
      'aggressive',
      'counterattack',
      'asymmetric',
      'dynamic',
      'fighting',
      'black',
      'winning',
    ],
    hints: ['1.e4 c5', 'Most popular defense', 'Sharp and complex'],
  },

  // Hard - Advanced Concepts
  {
    id: 'zugzwang',
    word: 'Zugzwang',
    category: 'endgame',
    difficulty: 'hard',
    timeLimit: 30,
    associations: [
      'endgame',
      'move',
      'worse',
      'position',
      'pawn',
      'king',
      'opposition',
      'German',
      'compulsion',
      'zugzwang',
      'disadvantage',
      'forced',
      'lose',
      'problem',
      'paradox',
    ],
    hints: ['German term', 'Any move worsens position', 'Common in endgames'],
  },
  {
    id: 'fianchetto',
    word: 'Fianchetto',
    category: 'opening',
    difficulty: 'hard',
    timeLimit: 30,
    associations: [
      'bishop',
      'diagonal',
      'g2',
      'b2',
      'g7',
      'b7',
      'long',
      'kingside',
      'queenside',
      'development',
      'flank',
      'italian',
      'setup',
      'defense',
      'control',
    ],
    hints: ['Bishop on long diagonal', 'Italian term', 'Usually g2 or b2'],
  },

  // Easy - General Chess
  {
    id: 'checkmate',
    word: 'Checkmate',
    category: 'general',
    difficulty: 'easy',
    timeLimit: 60,
    associations: [
      'win',
      'game',
      'over',
      'king',
      'attack',
      'escape',
      'cannot',
      'mate',
      'finish',
      'victory',
      'end',
      'goal',
      'check',
      'trapped',
      'final',
    ],
    hints: ['Goal of chess', 'King cannot escape', 'Game over'],
  },
  {
    id: 'castle',
    word: 'Castling',
    category: 'general',
    difficulty: 'easy',
    timeLimit: 60,
    associations: [
      'king',
      'rook',
      'safety',
      'kingside',
      'queenside',
      'special',
      'move',
      'once',
      'only',
      'connect',
      'rooks',
      'protect',
      'defense',
      'development',
      'corner',
    ],
    hints: ['Special move', 'King and rook', 'Only once per game'],
  },
  {
    id: 'develop',
    word: 'Development',
    category: 'general',
    difficulty: 'easy',
    timeLimit: 60,
    associations: [
      'opening',
      'pieces',
      'move',
      'active',
      'knights',
      'bishops',
      'center',
      'control',
      'quick',
      'early',
      'game',
      'mobilize',
      'activate',
      'squares',
      'tempo',
    ],
    hints: ['Opening principle', 'Activate pieces', 'Control center'],
  },

  // Medium - More Tactics
  {
    id: 'sacrifice',
    word: 'Sacrifice',
    category: 'tactic',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'give',
      'material',
      'attack',
      'advantage',
      'position',
      'compensation',
      'exchange',
      'piece',
      'pawn',
      'temporary',
      'gambit',
      'bold',
      'aggressive',
      'initiative',
      'winning',
    ],
    hints: ['Give up material', 'For compensation', 'Tactical decision'],
  },
  {
    id: 'discovered',
    word: 'Discovered Attack',
    category: 'tactic',
    difficulty: 'medium',
    timeLimit: 45,
    associations: [
      'move',
      'piece',
      'reveal',
      'attack',
      'behind',
      'line',
      'bishop',
      'rook',
      'queen',
      'double',
      'threat',
      'check',
      'powerful',
      'tactic',
      'uncover',
    ],
    hints: ['Move reveals attack', 'Piece behind attacks', 'Very powerful'],
  },
];

/**
 * Get a random word prompt
 */
export function getRandomPrompt(difficulty?: 'easy' | 'medium' | 'hard'): WordPrompt {
  let prompts = WORD_PROMPTS;

  if (difficulty) {
    prompts = prompts.filter((p) => p.difficulty === difficulty);
  }

  const randomIndex = Math.floor(Math.random() * prompts.length);
  return prompts[randomIndex];
}

/**
 * Check if a word is a valid association
 */
export function isValidAssociation(
  prompt: WordPrompt,
  userWord: string,
  usedWords: string[]
): {
  valid: boolean;
  points: number;
  message?: string;
} {
  const normalized = userWord.toLowerCase().trim();

  // Check if already used
  if (usedWords.includes(normalized)) {
    return {
      valid: false,
      points: 0,
      message: 'Already used!',
    };
  }

  // Check if too short
  if (normalized.length < 3) {
    return {
      valid: false,
      points: 0,
      message: 'Too short!',
    };
  }

  // Check if it's the prompt word itself
  if (normalized === prompt.word.toLowerCase()) {
    return {
      valid: false,
      points: 0,
      message: "Can't use the prompt word!",
    };
  }

  // Check if it's in the predefined associations (bonus points)
  const isInList = prompt.associations.some((a) => a.toLowerCase() === normalized);
  if (isInList) {
    return {
      valid: true,
      points: 10,
      message: 'Perfect match! +10',
    };
  }

  // Accept any reasonable chess-related word (fewer points)
  const chessWords = [
    'chess',
    'board',
    'square',
    'rank',
    'file',
    'white',
    'black',
    'piece',
    'move',
    'capture',
    'strategy',
    'tactic',
    'game',
    'play',
    'player',
    'tournament',
    'match',
    'win',
    'lose',
    'draw',
  ];

  const isChessRelated = chessWords.some((w) => normalized.includes(w) || w.includes(normalized));
  if (isChessRelated || normalized.length >= 4) {
    return {
      valid: true,
      points: 5,
      message: 'Good! +5',
    };
  }

  return {
    valid: false,
    points: 0,
    message: 'Not related enough',
  };
}

/**
 * Calculate final score with bonus
 */
export function calculateFinalScore(
  baseScore: number,
  timeRemaining: number,
  totalTime: number
): {
  baseScore: number;
  timeBonus: number;
  totalScore: number;
} {
  const timeBonus = Math.floor((timeRemaining / totalTime) * 50);

  return {
    baseScore,
    timeBonus,
    totalScore: baseScore + timeBonus,
  };
}
