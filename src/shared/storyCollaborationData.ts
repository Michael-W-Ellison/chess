/**
 * Story Collaboration Game Data
 * Chess-themed collaborative storytelling prompts and scenarios
 */

export type StoryTheme = 'adventure' | 'mystery' | 'historical' | 'fantasy' | 'comedy';
export type StoryDifficulty = 'easy' | 'medium' | 'hard';

export interface StoryPrompt {
  id: string;
  title: string;
  theme: StoryTheme;
  difficulty: StoryDifficulty;
  starter: string;
  context: string;
  minTurns: number;
  maxTurns: number;
  suggestions: string[];
}

export const STORY_PROMPTS: StoryPrompt[] = [
  // Easy - Adventure
  {
    id: 'lost_queen',
    title: 'The Lost Queen',
    theme: 'adventure',
    difficulty: 'easy',
    starter: 'In the middle of an important chess tournament, the white queen piece suddenly went missing from the board.',
    context: 'A fun mystery about finding a missing chess piece during a tournament.',
    minTurns: 4,
    maxTurns: 8,
    suggestions: [
      'Describe who discovers the missing piece',
      'Add a suspicious character',
      'Include a clue',
      'Resolve the mystery',
    ],
  },
  {
    id: 'first_tournament',
    title: 'First Tournament',
    theme: 'adventure',
    difficulty: 'easy',
    starter: 'Maya nervously approached the chess board for her very first tournament game. Her hands trembled as she reached for the white pawn.',
    context: 'A heartwarming story about a beginner\'s first chess tournament experience.',
    minTurns: 4,
    maxTurns: 8,
    suggestions: [
      'Describe Maya\'s opponent',
      'Show an important game moment',
      'Include a learning experience',
      'End with growth or achievement',
    ],
  },

  // Easy - Comedy
  {
    id: 'talking_pieces',
    title: 'The Talking Pieces',
    theme: 'comedy',
    difficulty: 'easy',
    starter: 'One morning, Alex sat down to play chess and heard a tiny voice say, "Not the King\'s Gambit again!" The pieces had come to life!',
    context: 'A humorous story where chess pieces can talk and have opinions about moves.',
    minTurns: 4,
    maxTurns: 8,
    suggestions: [
      'Give pieces funny personalities',
      'Show them arguing about strategy',
      'Include a comedic game moment',
      'Add a twist ending',
    ],
  },

  // Medium - Mystery
  {
    id: 'grandmaster_secret',
    title: 'The Grandmaster\'s Secret',
    theme: 'mystery',
    difficulty: 'medium',
    starter: 'Detective Romano studied the chess board left behind in the famous grandmaster\'s study. Each piece was positioned deliberately - this was a message.',
    context: 'A mystery where a chess position holds the key to solving a puzzle.',
    minTurns: 6,
    maxTurns: 10,
    suggestions: [
      'Describe the mysterious chess position',
      'Introduce suspects or clues',
      'Show the detective\'s deduction process',
      'Build tension',
      'Reveal the solution',
    ],
  },
  {
    id: 'cursed_opening',
    title: 'The Cursed Opening',
    theme: 'mystery',
    difficulty: 'medium',
    starter: 'Legends say that anyone who plays the Immortal Opening at the old Chess Club at midnight will face a mysterious opponent from the past.',
    context: 'A spooky mystery about a legendary chess opening and its consequences.',
    minTurns: 6,
    maxTurns: 10,
    suggestions: [
      'Set the spooky atmosphere',
      'Introduce the brave player',
      'Describe the mysterious opponent',
      'Add supernatural elements',
      'Resolve the curse',
    ],
  },

  // Medium - Historical
  {
    id: 'fischer_spassky',
    title: 'Reykjavik 1972',
    theme: 'historical',
    difficulty: 'medium',
    starter: 'The tension in Reykjavik was electric. Bobby Fischer and Boris Spassky faced each other across the board in what would become the most famous chess match of the Cold War.',
    context: 'A historical fiction piece about the legendary 1972 World Championship match.',
    minTurns: 6,
    maxTurns: 10,
    suggestions: [
      'Capture the Cold War atmosphere',
      'Show the personalities of the players',
      'Describe a crucial game moment',
      'Include historical details',
      'Build to the climax',
    ],
  },

  // Hard - Fantasy
  {
    id: 'kingdom_chess',
    title: 'The Kingdom of 64 Squares',
    theme: 'fantasy',
    difficulty: 'hard',
    starter: 'In the realm of Chessaria, the eternal war between the White Kingdom and the Black Kingdom was not fought with swords, but with strategy and sacrifice on the sacred 64 squares.',
    context: 'An epic fantasy where chess pieces are living warriors in a magical realm.',
    minTurns: 8,
    maxTurns: 12,
    suggestions: [
      'Build the fantasy world',
      'Develop character relationships',
      'Show political intrigue',
      'Include magical elements',
      'Create battle scenes',
      'Add emotional depth',
    ],
  },
  {
    id: 'time_knight',
    title: 'The Time-Traveling Knight',
    theme: 'fantasy',
    difficulty: 'hard',
    starter: 'When the ancient knight piece was moved to g5, it activated a long-forgotten spell. Suddenly, Elena found herself transported to a medieval kingdom where chess moves controlled reality itself.',
    context: 'A fantasy adventure where chess moves have magical consequences across time.',
    minTurns: 8,
    maxTurns: 12,
    suggestions: [
      'Describe the magical chess system',
      'Show Elena learning the rules',
      'Introduce allies and antagonists',
      'Create high-stakes chess challenges',
      'Build towards resolution',
      'Add character growth',
    ],
  },

  // Hard - Mystery
  {
    id: 'impossible_game',
    title: 'The Impossible Game',
    theme: 'mystery',
    difficulty: 'hard',
    starter: 'The chess match was perfect. Too perfect. Every move by both players was flawless, as if they were following a pre-written script. But no such game had ever been recorded in history.',
    context: 'A complex mystery about an impossibly perfect chess game and its implications.',
    minTurns: 8,
    maxTurns: 12,
    suggestions: [
      'Establish the impossibility',
      'Introduce expert investigators',
      'Layer multiple theories',
      'Add red herrings',
      'Build complexity',
      'Deliver a satisfying revelation',
    ],
  },

  // Medium - Adventure
  {
    id: 'chess_olympiad',
    title: 'Quest for the Chess Olympiad',
    theme: 'adventure',
    difficulty: 'medium',
    starter: 'Twelve-year-old Raj had trained for years, dreaming of representing his country at the Chess Olympiad. Now, standing at the airport with his team, the adventure was about to begin.',
    context: 'An adventure story about a young player competing on the world stage.',
    minTurns: 6,
    maxTurns: 10,
    suggestions: [
      'Show the team dynamics',
      'Describe cultural experiences',
      'Include challenging matches',
      'Add obstacles to overcome',
      'Celebrate achievements',
    ],
  },
];

/**
 * Get a random story prompt
 */
export function getRandomStoryPrompt(
  difficulty?: StoryDifficulty,
  theme?: StoryTheme
): StoryPrompt {
  let prompts = STORY_PROMPTS;

  if (difficulty) {
    prompts = prompts.filter((p) => p.difficulty === difficulty);
  }

  if (theme) {
    prompts = prompts.filter((p) => p.theme === theme);
  }

  const randomIndex = Math.floor(Math.random() * prompts.length);
  return prompts[randomIndex];
}

/**
 * Get story prompts by theme
 */
export function getStoryPromptsByTheme(theme: StoryTheme): StoryPrompt[] {
  return STORY_PROMPTS.filter((p) => p.theme === theme);
}

/**
 * Get story prompts by difficulty
 */
export function getStoryPromptsByDifficulty(difficulty: StoryDifficulty): StoryPrompt[] {
  return STORY_PROMPTS.filter((p) => p.difficulty === difficulty);
}

/**
 * Validate story contribution (basic checks)
 */
export function validateContribution(text: string): {
  valid: boolean;
  message?: string;
} {
  const trimmed = text.trim();

  if (trimmed.length === 0) {
    return { valid: false, message: 'Please write something to continue the story!' };
  }

  if (trimmed.length < 10) {
    return { valid: false, message: 'Try to add at least 10 characters to move the story forward.' };
  }

  if (trimmed.length > 500) {
    return { valid: false, message: 'Keep your contribution under 500 characters to give others a turn!' };
  }

  // Check for at least some letters (not just punctuation/numbers)
  if (!/[a-zA-Z]{3,}/.test(trimmed)) {
    return { valid: false, message: 'Please write actual words to continue the story.' };
  }

  return { valid: true };
}

/**
 * Generate AI story contribution (placeholder - would use actual AI in production)
 */
export function generateAIContribution(
  prompt: StoryPrompt,
  storyText: string,
  turnNumber: number
): string {
  // In a real implementation, this would call an AI API
  // For now, we'll return contextual responses based on turn number

  const responses = [
    `The room fell silent as everyone turned to look. Something unexpected was about to happen.`,
    `With a determined look, the protagonist took a deep breath and made their next move.`,
    `"Wait!" a voice called out from the back. "There's something you should know about that position."`,
    `The clock was ticking down. Time was running out to make a decision.`,
    `Little did they know, this moment would change everything they thought they knew about chess.`,
    `An old master once said, "In chess, as in life, opportunity comes to those who prepare." This was one of those moments.`,
    `The pattern on the board began to reveal itself, like a secret message waiting to be discovered.`,
    `As the pieces moved across the board, it became clear this was no ordinary game.`,
    `The crowd gasped. No one had seen that combination coming.`,
    `And then, in a flash of inspiration, the answer became perfectly clear.`,
  ];

  // Return a contextually appropriate response based on turn number
  const index = Math.min(turnNumber - 1, responses.length - 1);
  return responses[index];
}
