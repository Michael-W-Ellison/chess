/**
 * Twenty Questions Game Data
 * Diverse items for the guessing game
 */

export type GameCategory =
  | 'animal'
  | 'food'
  | 'sport'
  | 'movie'
  | 'place'
  | 'technology'
  | 'book'
  | 'music'
  | 'person'
  | 'other';

export interface GameItem {
  id: string;
  name: string;
  category: GameCategory;
  properties: {
    // General properties
    isAnimal?: boolean;
    isFood?: boolean;
    isSport?: boolean;
    isMovie?: boolean;
    isPlace?: boolean;
    isTechnology?: boolean;
    isBook?: boolean;
    isMusic?: boolean;
    isPerson?: boolean;

    // Animal properties
    hasFur?: boolean;
    hasFeathers?: boolean;
    hasScales?: boolean;
    canFly?: boolean;
    canSwim?: boolean;
    isPet?: boolean;
    isWild?: boolean;
    isDangerous?: boolean;

    // Food properties
    isFruit?: boolean;
    isVegetable?: boolean;
    isDessert?: boolean;
    isSweet?: boolean;
    isSavory?: boolean;
    isHealthy?: boolean;
    needsCooking?: boolean;

    // Sport properties
    usesBall?: boolean;
    isTeamSport?: boolean;
    isIndoorSport?: boolean;
    isOutdoorSport?: boolean;
    isOlympicSport?: boolean;

    // Entertainment properties
    isPopular?: boolean;
    isOld?: boolean;
    isNew?: boolean;
    isForKids?: boolean;

    // Place properties
    isCountry?: boolean;
    isCity?: boolean;
    isNaturalPlace?: boolean;
    isFamous?: boolean;

    // Technology properties
    hasScreen?: boolean;
    isPortable?: boolean;
    needsElectricity?: boolean;
    isForGaming?: boolean;

    // Person properties
    isMale?: boolean;
    isFemale?: boolean;
    isAthlete?: boolean;
    isActor?: boolean;
    isMusicArtist?: boolean;

    // Misc properties
    isExpensive?: boolean;
    isFun?: boolean;
    isCommon?: boolean;
  };
  hints?: string[];
  difficulty?: 'easy' | 'medium' | 'hard';
}

export const GAME_ITEMS: GameItem[] = [
  // Animals - Easy
  {
    id: 'dog',
    name: 'Dog',
    category: 'animal',
    difficulty: 'easy',
    properties: {
      isAnimal: true,
      hasFur: true,
      isPet: true,
      isCommon: true,
    },
    hints: ["A popular pet", "Known as man's best friend"],
  },
  {
    id: 'cat',
    name: 'Cat',
    category: 'animal',
    difficulty: 'easy',
    properties: {
      isAnimal: true,
      hasFur: true,
      isPet: true,
      isCommon: true,
    },
    hints: ['Says meow', 'Likes to purr'],
  },
  {
    id: 'fish',
    name: 'Fish',
    category: 'animal',
    difficulty: 'easy',
    properties: {
      isAnimal: true,
      hasScales: true,
      canSwim: true,
      isPet: true,
    },
    hints: ['Lives in water', 'Can be kept in a tank'],
  },
  {
    id: 'bird',
    name: 'Bird',
    category: 'animal',
    difficulty: 'easy',
    properties: {
      isAnimal: true,
      hasFeathers: true,
      canFly: true,
    },
    hints: ['Has wings', 'Can sing'],
  },
  {
    id: 'elephant',
    name: 'Elephant',
    category: 'animal',
    difficulty: 'easy',
    properties: {
      isAnimal: true,
      isWild: true,
      isFamous: true,
    },
    hints: ['Has a trunk', 'Largest land animal'],
  },
  {
    id: 'dolphin',
    name: 'Dolphin',
    category: 'animal',
    difficulty: 'medium',
    properties: {
      isAnimal: true,
      canSwim: true,
      isWild: true,
      isFamous: true,
    },
    hints: ['Very intelligent', 'Lives in the ocean'],
  },
  {
    id: 'lion',
    name: 'Lion',
    category: 'animal',
    difficulty: 'medium',
    properties: {
      isAnimal: true,
      hasFur: true,
      isWild: true,
      isDangerous: true,
    },
    hints: ['King of the jungle', 'Has a mane'],
  },

  // Foods - Easy
  {
    id: 'pizza',
    name: 'Pizza',
    category: 'food',
    difficulty: 'easy',
    properties: {
      isFood: true,
      isSavory: true,
      needsCooking: true,
      isPopular: true,
    },
    hints: ['Comes in slices', 'Often has cheese and sauce'],
  },
  {
    id: 'apple',
    name: 'Apple',
    category: 'food',
    difficulty: 'easy',
    properties: {
      isFood: true,
      isFruit: true,
      isHealthy: true,
      isCommon: true,
    },
    hints: ['A day keeps the doctor away', 'Can be red, green, or yellow'],
  },
  {
    id: 'ice_cream',
    name: 'Ice Cream',
    category: 'food',
    difficulty: 'easy',
    properties: {
      isFood: true,
      isDessert: true,
      isSweet: true,
      isPopular: true,
    },
    hints: ['Cold and sweet', 'Melts in the sun'],
  },
  {
    id: 'banana',
    name: 'Banana',
    category: 'food',
    difficulty: 'easy',
    properties: {
      isFood: true,
      isFruit: true,
      isHealthy: true,
      isCommon: true,
    },
    hints: ['Yellow fruit', 'Monkeys love it'],
  },
  {
    id: 'chocolate',
    name: 'Chocolate',
    category: 'food',
    difficulty: 'easy',
    properties: {
      isFood: true,
      isDessert: true,
      isSweet: true,
      isPopular: true,
    },
    hints: ['Sweet treat', 'Can be dark, milk, or white'],
  },
  {
    id: 'carrot',
    name: 'Carrot',
    category: 'food',
    difficulty: 'easy',
    properties: {
      isFood: true,
      isVegetable: true,
      isHealthy: true,
    },
    hints: ['Orange vegetable', 'Good for your eyes'],
  },

  // Sports - Easy
  {
    id: 'soccer',
    name: 'Soccer',
    category: 'sport',
    difficulty: 'easy',
    properties: {
      isSport: true,
      usesBall: true,
      isTeamSport: true,
      isOutdoorSport: true,
      isOlympicSport: true,
      isPopular: true,
    },
    hints: ['Most popular sport in the world', 'Use your feet mainly'],
  },
  {
    id: 'basketball',
    name: 'Basketball',
    category: 'sport',
    difficulty: 'easy',
    properties: {
      isSport: true,
      usesBall: true,
      isTeamSport: true,
      isIndoorSport: true,
      isOlympicSport: true,
    },
    hints: ['Played with a hoop', 'Dribble and shoot'],
  },
  {
    id: 'swimming',
    name: 'Swimming',
    category: 'sport',
    difficulty: 'easy',
    properties: {
      isSport: true,
      isOlympicSport: true,
      isOutdoorSport: true,
      isIndoorSport: true,
    },
    hints: ['Done in water', 'Different strokes'],
  },
  {
    id: 'baseball',
    name: 'Baseball',
    category: 'sport',
    difficulty: 'easy',
    properties: {
      isSport: true,
      usesBall: true,
      isTeamSport: true,
      isOutdoorSport: true,
    },
    hints: ['Use a bat', 'Run the bases'],
  },
  {
    id: 'tennis',
    name: 'Tennis',
    category: 'sport',
    difficulty: 'medium',
    properties: {
      isSport: true,
      usesBall: true,
      isOlympicSport: true,
      isOutdoorSport: true,
    },
    hints: ['Played with a racket', 'Wimbledon is famous for this'],
  },

  // Movies/Shows - Easy
  {
    id: 'frozen',
    name: 'Frozen',
    category: 'movie',
    difficulty: 'easy',
    properties: {
      isMovie: true,
      isPopular: true,
      isForKids: true,
    },
    hints: ['Disney movie', '"Let It Go" is from this'],
  },
  {
    id: 'harry_potter',
    name: 'Harry Potter',
    category: 'movie',
    difficulty: 'easy',
    properties: {
      isMovie: true,
      isBook: true,
      isPopular: true,
      isFamous: true,
    },
    hints: ['Boy wizard', 'Hogwarts school'],
  },
  {
    id: 'toy_story',
    name: 'Toy Story',
    category: 'movie',
    difficulty: 'easy',
    properties: {
      isMovie: true,
      isPopular: true,
      isForKids: true,
    },
    hints: ['Woody and Buzz', 'Toys come to life'],
  },
  {
    id: 'minecraft',
    name: 'Minecraft',
    category: 'technology',
    difficulty: 'easy',
    properties: {
      isTechnology: true,
      isForGaming: true,
      isPopular: true,
      isFun: true,
    },
    hints: ['Build with blocks', 'Very popular game'],
  },

  // Places - Easy
  {
    id: 'paris',
    name: 'Paris',
    category: 'place',
    difficulty: 'medium',
    properties: {
      isPlace: true,
      isCity: true,
      isFamous: true,
    },
    hints: ['Eiffel Tower is here', 'Capital of France'],
  },
  {
    id: 'beach',
    name: 'Beach',
    category: 'place',
    difficulty: 'easy',
    properties: {
      isPlace: true,
      isNaturalPlace: true,
      isCommon: true,
    },
    hints: ['Has sand and water', 'People swim here'],
  },
  {
    id: 'mountain',
    name: 'Mountain',
    category: 'place',
    difficulty: 'easy',
    properties: {
      isPlace: true,
      isNaturalPlace: true,
    },
    hints: ['Very tall', 'People climb these'],
  },
  {
    id: 'disney_world',
    name: 'Disney World',
    category: 'place',
    difficulty: 'easy',
    properties: {
      isPlace: true,
      isFamous: true,
      isFun: true,
      isExpensive: true,
    },
    hints: ['Theme park', 'In Florida'],
  },

  // Technology - Easy
  {
    id: 'smartphone',
    name: 'Smartphone',
    category: 'technology',
    difficulty: 'easy',
    properties: {
      isTechnology: true,
      hasScreen: true,
      isPortable: true,
      needsElectricity: true,
      isCommon: true,
    },
    hints: ['Make calls and use apps', 'Most people have one'],
  },
  {
    id: 'computer',
    name: 'Computer',
    category: 'technology',
    difficulty: 'easy',
    properties: {
      isTechnology: true,
      hasScreen: true,
      needsElectricity: true,
      isCommon: true,
    },
    hints: ['Has a keyboard', 'For work and games'],
  },
  {
    id: 'tablet',
    name: 'Tablet',
    category: 'technology',
    difficulty: 'easy',
    properties: {
      isTechnology: true,
      hasScreen: true,
      isPortable: true,
      needsElectricity: true,
    },
    hints: ['Like a big phone', 'Touch screen'],
  },
  {
    id: 'video_game_console',
    name: 'Video Game Console',
    category: 'technology',
    difficulty: 'medium',
    properties: {
      isTechnology: true,
      isForGaming: true,
      needsElectricity: true,
      isFun: true,
    },
    hints: ['PlayStation or Xbox', 'For playing video games'],
  },

  // Music - Medium
  {
    id: 'piano',
    name: 'Piano',
    category: 'music',
    difficulty: 'easy',
    properties: {
      isMusic: true,
      isExpensive: true,
    },
    hints: ['Musical instrument', 'Has black and white keys'],
  },
  {
    id: 'guitar',
    name: 'Guitar',
    category: 'music',
    difficulty: 'easy',
    properties: {
      isMusic: true,
      isPopular: true,
    },
    hints: ['Has strings', 'Rock music uses this'],
  },
  {
    id: 'drums',
    name: 'Drums',
    category: 'music',
    difficulty: 'easy',
    properties: {
      isMusic: true,
    },
    hints: ['You hit them', 'Keep the beat'],
  },

  // Books/Characters - Medium
  {
    id: 'percy_jackson',
    name: 'Percy Jackson',
    category: 'book',
    difficulty: 'medium',
    properties: {
      isBook: true,
      isPerson: true,
      isPopular: true,
    },
    hints: ['Half-god character', 'Son of Poseidon'],
  },
  {
    id: 'diary_wimpy_kid',
    name: 'Diary of a Wimpy Kid',
    category: 'book',
    difficulty: 'easy',
    properties: {
      isBook: true,
      isPopular: true,
      isForKids: true,
    },
    hints: ['Funny book series', 'About Greg Heffley'],
  },

  // Famous People - Medium
  {
    id: 'taylor_swift',
    name: 'Taylor Swift',
    category: 'person',
    difficulty: 'easy',
    properties: {
      isPerson: true,
      isFemale: true,
      isMusicArtist: true,
      isPopular: true,
      isFamous: true,
    },
    hints: ['Pop singer', 'Writes her own songs'],
  },
  {
    id: 'lebron_james',
    name: 'LeBron James',
    category: 'person',
    difficulty: 'easy',
    properties: {
      isPerson: true,
      isMale: true,
      isAthlete: true,
      isFamous: true,
    },
    hints: ['Basketball player', 'Plays in the NBA'],
  },
  {
    id: 'serena_williams',
    name: 'Serena Williams',
    category: 'person',
    difficulty: 'medium',
    properties: {
      isPerson: true,
      isFemale: true,
      isAthlete: true,
      isFamous: true,
    },
    hints: ['Tennis champion', 'Won many Grand Slams'],
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
  // Category questions
  { question: 'Is it an animal?', property: 'isAnimal' },
  { question: 'Is it food?', property: 'isFood' },
  { question: 'Is it a sport?', property: 'isSport' },
  { question: 'Is it a movie or TV show?', property: 'isMovie' },
  { question: 'Is it a place?', property: 'isPlace' },
  { question: 'Is it technology?', property: 'isTechnology' },
  { question: 'Is it related to music?', property: 'isMusic' },
  { question: 'Is it a book or book character?', property: 'isBook' },
  { question: 'Is it a person?', property: 'isPerson' },

  // Animal questions
  { question: 'Does it have fur?', property: 'hasFur' },
  { question: 'Does it have feathers?', property: 'hasFeathers' },
  { question: 'Does it have scales?', property: 'hasScales' },
  { question: 'Can it fly?', property: 'canFly' },
  { question: 'Can it swim?', property: 'canSwim' },
  { question: 'Is it a pet?', property: 'isPet' },
  { question: 'Is it wild?', property: 'isWild' },
  { question: 'Is it dangerous?', property: 'isDangerous' },

  // Food questions
  { question: 'Is it a fruit?', property: 'isFruit' },
  { question: 'Is it a vegetable?', property: 'isVegetable' },
  { question: 'Is it a dessert?', property: 'isDessert' },
  { question: 'Is it sweet?', property: 'isSweet' },
  { question: 'Is it savory?', property: 'isSavory' },
  { question: 'Is it healthy?', property: 'isHealthy' },
  { question: 'Does it need cooking?', property: 'needsCooking' },

  // Sport questions
  { question: 'Does it use a ball?', property: 'usesBall' },
  { question: 'Is it a team sport?', property: 'isTeamSport' },
  { question: 'Is it an indoor sport?', property: 'isIndoorSport' },
  { question: 'Is it an outdoor sport?', property: 'isOutdoorSport' },
  { question: 'Is it an Olympic sport?', property: 'isOlympicSport' },

  // Entertainment questions
  { question: 'Is it popular?', property: 'isPopular' },
  { question: 'Is it old/classic?', property: 'isOld' },
  { question: 'Is it new/recent?', property: 'isNew' },
  { question: 'Is it for kids?', property: 'isForKids' },

  // Place questions
  { question: 'Is it a country?', property: 'isCountry' },
  { question: 'Is it a city?', property: 'isCity' },
  { question: 'Is it a natural place?', property: 'isNaturalPlace' },
  { question: 'Is it famous?', property: 'isFamous' },

  // Technology questions
  { question: 'Does it have a screen?', property: 'hasScreen' },
  { question: 'Is it portable?', property: 'isPortable' },
  { question: 'Does it need electricity?', property: 'needsElectricity' },
  { question: 'Is it for gaming?', property: 'isForGaming' },

  // Person questions
  { question: 'Is this person male?', property: 'isMale' },
  { question: 'Is this person female?', property: 'isFemale' },
  { question: 'Is this person an athlete?', property: 'isAthlete' },
  { question: 'Is this person an actor?', property: 'isActor' },
  { question: 'Is this person a music artist?', property: 'isMusicArtist' },

  // General questions
  { question: 'Is it expensive?', property: 'isExpensive' },
  { question: 'Is it fun?', property: 'isFun' },
  { question: 'Is it common?', property: 'isCommon' },
];
