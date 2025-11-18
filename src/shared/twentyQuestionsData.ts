/**
 * Twenty Questions Game Data
 * Chess-themed items for the guessing game
 */

export type GameCategory = 'piece' | 'opening' | 'player' | 'term' | 'position';

export interface GameItem {
  id: string;
  name: string;
  category: GameCategory;
  properties: {
    // General properties
    isWhite?: boolean;
    isBlack?: boolean;
    isPiece?: boolean;
    isOpening?: boolean;
    isPerson?: boolean;
    isTerm?: boolean;
    isPosition?: boolean;

    // Piece properties
    canMoveForward?: boolean;
    canMoveBackward?: boolean;
    canMoveDiagonally?: boolean;
    canMoveHorizontally?: boolean;
    canMoveVertically?: boolean;
    canJump?: boolean;
    isRoyal?: boolean;
    isPawn?: boolean;

    // Opening properties
    isKingsideOpening?: boolean;
    isQueensideOpening?: boolean;
    isAggressive?: boolean;
    isDefensive?: boolean;
    isPopular?: boolean;

    // Player properties
    isWorldChampion?: boolean;
    isActive?: boolean;
    isMale?: boolean;
    isFemale?: boolean;
    isHistorical?: boolean;

    // Term properties
    isCheckmate?: boolean;
    isStalemate?: boolean;
    isTactic?: boolean;
    isEndgame?: boolean;

    // Position properties
    isWinning?: boolean;
    isDrawn?: boolean;
    isComplex?: boolean;
  };
  hints?: string[];
  difficulty?: 'easy' | 'medium' | 'hard';
}

export const GAME_ITEMS: GameItem[] = [
  // Chess Pieces
  {
    id: 'white_king',
    name: 'White King',
    category: 'piece',
    difficulty: 'easy',
    properties: {
      isWhite: true,
      isPiece: true,
      canMoveForward: true,
      canMoveBackward: true,
      canMoveDiagonally: true,
      canMoveHorizontally: true,
      canMoveVertically: true,
      isRoyal: true,
    },
    hints: ['The most important piece in chess', 'Must be protected at all costs'],
  },
  {
    id: 'black_queen',
    name: 'Black Queen',
    category: 'piece',
    difficulty: 'easy',
    properties: {
      isBlack: true,
      isPiece: true,
      canMoveForward: true,
      canMoveBackward: true,
      canMoveDiagonally: true,
      canMoveHorizontally: true,
      canMoveVertically: true,
    },
    hints: ['The most powerful piece', 'Can move in all directions'],
  },
  {
    id: 'knight',
    name: 'Knight',
    category: 'piece',
    difficulty: 'easy',
    properties: {
      isPiece: true,
      canJump: true,
    },
    hints: ['Moves in an L-shape', 'Can jump over other pieces'],
  },
  {
    id: 'rook',
    name: 'Rook',
    category: 'piece',
    difficulty: 'easy',
    properties: {
      isPiece: true,
      canMoveForward: true,
      canMoveBackward: true,
      canMoveHorizontally: true,
      canMoveVertically: true,
    },
    hints: ['Moves in straight lines', 'Important for castling'],
  },
  {
    id: 'bishop',
    name: 'Bishop',
    category: 'piece',
    difficulty: 'easy',
    properties: {
      isPiece: true,
      canMoveDiagonally: true,
    },
    hints: ['Moves diagonally', 'Always stays on the same color squares'],
  },
  {
    id: 'pawn',
    name: 'Pawn',
    category: 'piece',
    difficulty: 'easy',
    properties: {
      isPiece: true,
      canMoveForward: true,
      isPawn: true,
    },
    hints: ['The most numerous piece', 'Can promote when reaching the end'],
  },

  // Chess Openings
  {
    id: 'italian_game',
    name: 'Italian Game',
    category: 'opening',
    difficulty: 'medium',
    properties: {
      isOpening: true,
      isKingsideOpening: true,
      isPopular: true,
      isAggressive: true,
    },
    hints: ['One of the oldest openings', 'Starts with 1.e4 e5 2.Nf3 Nc6 3.Bc4'],
  },
  {
    id: 'sicilian_defense',
    name: 'Sicilian Defense',
    category: 'opening',
    difficulty: 'medium',
    properties: {
      isOpening: true,
      isPopular: true,
      isAggressive: true,
    },
    hints: ['Most popular response to 1.e4', 'Starts with 1.e4 c5'],
  },
  {
    id: 'queens_gambit',
    name: "Queen's Gambit",
    category: 'opening',
    difficulty: 'medium',
    properties: {
      isOpening: true,
      isQueensideOpening: true,
      isPopular: true,
    },
    hints: ['Famous Netflix series', 'Starts with 1.d4 d5 2.c4'],
  },
  {
    id: 'ruy_lopez',
    name: 'Ruy Lopez',
    category: 'opening',
    difficulty: 'medium',
    properties: {
      isOpening: true,
      isKingsideOpening: true,
      isPopular: true,
    },
    hints: ['Named after a Spanish priest', 'Starts with 1.e4 e5 2.Nf3 Nc6 3.Bb5'],
  },

  // Famous Players
  {
    id: 'magnus_carlsen',
    name: 'Magnus Carlsen',
    category: 'player',
    difficulty: 'easy',
    properties: {
      isPerson: true,
      isWorldChampion: true,
      isActive: true,
      isMale: true,
    },
    hints: ['Current world champion', 'From Norway'],
  },
  {
    id: 'garry_kasparov',
    name: 'Garry Kasparov',
    category: 'player',
    difficulty: 'medium',
    properties: {
      isPerson: true,
      isWorldChampion: true,
      isMale: true,
      isHistorical: true,
    },
    hints: ['Played against Deep Blue', 'World champion from 1985-2000'],
  },
  {
    id: 'bobby_fischer',
    name: 'Bobby Fischer',
    category: 'player',
    difficulty: 'medium',
    properties: {
      isPerson: true,
      isWorldChampion: true,
      isMale: true,
      isHistorical: true,
    },
    hints: ['American world champion', 'Won in 1972 against Spassky'],
  },
  {
    id: 'judit_polgar',
    name: 'Judit Polgar',
    category: 'player',
    difficulty: 'hard',
    properties: {
      isPerson: true,
      isFemale: true,
      isHistorical: true,
    },
    hints: ['Strongest female player ever', 'Beat Kasparov in 2002'],
  },

  // Chess Terms
  {
    id: 'checkmate',
    name: 'Checkmate',
    category: 'term',
    difficulty: 'easy',
    properties: {
      isTerm: true,
      isCheckmate: true,
    },
    hints: ['The goal of chess', 'King cannot escape attack'],
  },
  {
    id: 'stalemate',
    name: 'Stalemate',
    category: 'term',
    difficulty: 'medium',
    properties: {
      isTerm: true,
      isStalemate: true,
    },
    hints: ['A draw condition', 'No legal moves but not in check'],
  },
  {
    id: 'fork',
    name: 'Fork',
    category: 'term',
    difficulty: 'medium',
    properties: {
      isTerm: true,
      isTactic: true,
    },
    hints: ['A tactical motif', 'Attacking two pieces at once'],
  },
  {
    id: 'pin',
    name: 'Pin',
    category: 'term',
    difficulty: 'medium',
    properties: {
      isTerm: true,
      isTactic: true,
    },
    hints: ['A tactical motif', 'Piece cannot move without exposing a more valuable piece'],
  },
  {
    id: 'endgame',
    name: 'Endgame',
    category: 'term',
    difficulty: 'easy',
    properties: {
      isTerm: true,
      isEndgame: true,
    },
    hints: ['Final phase of the game', 'Few pieces remaining'],
  },
  {
    id: 'castling',
    name: 'Castling',
    category: 'term',
    difficulty: 'easy',
    properties: {
      isTerm: true,
    },
    hints: ['Special move involving king and rook', 'Can only be done once'],
  },
  {
    id: 'en_passant',
    name: 'En Passant',
    category: 'term',
    difficulty: 'hard',
    properties: {
      isTerm: true,
    },
    hints: ['Special pawn capture', 'French term meaning "in passing"'],
  },
];

/**
 * Get a random item for the game
 */
export function getRandomItem(difficulty?: 'easy' | 'medium' | 'hard'): GameItem {
  let items = GAME_ITEMS;

  if (difficulty) {
    items = items.filter((item) => item.difficulty === difficulty);
  }

  const randomIndex = Math.floor(Math.random() * items.length);
  return items[randomIndex];
}

/**
 * Get all available questions
 */
export const QUESTIONS = [
  { question: 'Is it a chess piece?', property: 'isPiece' },
  { question: 'Is it white?', property: 'isWhite' },
  { question: 'Is it black?', property: 'isBlack' },
  { question: 'Can it move diagonally?', property: 'canMoveDiagonally' },
  { question: 'Can it move horizontally?', property: 'canMoveHorizontally' },
  { question: 'Can it move vertically?', property: 'canMoveVertically' },
  { question: 'Can it jump over other pieces?', property: 'canJump' },
  { question: 'Is it a royal piece?', property: 'isRoyal' },
  { question: 'Is it a pawn?', property: 'isPawn' },
  { question: 'Is it an opening?', property: 'isOpening' },
  { question: 'Is it a kingside opening?', property: 'isKingsideOpening' },
  { question: 'Is it a queenside opening?', property: 'isQueensideOpening' },
  { question: 'Is it aggressive?', property: 'isAggressive' },
  { question: 'Is it popular?', property: 'isPopular' },
  { question: 'Is it a person?', property: 'isPerson' },
  { question: 'Is it a world champion?', property: 'isWorldChampion' },
  { question: 'Is this person active today?', property: 'isActive' },
  { question: 'Is this person male?', property: 'isMale' },
  { question: 'Is this person female?', property: 'isFemale' },
  { question: 'Is it a chess term?', property: 'isTerm' },
  { question: 'Is it checkmate?', property: 'isCheckmate' },
  { question: 'Is it a tactic?', property: 'isTactic' },
  { question: 'Is it related to the endgame?', property: 'isEndgame' },
];
