# Tamagotchi Chatbot Friend - TODO List

This TODO list is generated from the technical design document in `chatbot.txt`. The project is divided into phases following a 14-week implementation roadmap.

## Legend
- [ ] Pending
- [x] Completed
- [>] In Progress

---

## Phase 1: Foundation (Weeks 1-3)

### Project Setup
- [x] 1. Initialize Electron project with dependencies
- [x] 2. Create Electron main process setup (main.ts, window management)
- [x] 3. Set up React + TypeScript frontend structure
- [x] 4. Configure build tools (webpack/vite) for Electron + React
- [x] 5. Create shared TypeScript types and interfaces

### Backend Setup
- [x] 6. Initialize Python FastAPI project with dependencies
- [x] 7. Create FastAPI main.py with app initialization
- [x] 8. Set up Python project folder structure (routes, models, services)
- [x] 9. Create database.py for SQLAlchemy connection

### LLM Integration
- [x] 10. Install llama-cpp-python with appropriate backend (CPU/GPU/Metal)
- [x] 11. Download and configure LLM model (Llama 3.2 3B or Phi-3 Mini GGUF)
- [x] 12. Create LLM wrapper class for inference
- [x] 13. Test LLM integration with simple prompts — script `backend/test_llm.py`; requires a downloaded model to run

### Database Schema
- [x] 14. Create users table schema
- [x] 15. Create bot_personality table schema
- [x] 16. Create conversations table schema
- [x] 17. Create messages table schema
- [x] 18. Create user_profile table schema
- [x] 19. Create safety_flags table schema

### ORM Models
- [x] 20. Create User SQLAlchemy model
- [x] 21. Create BotPersonality SQLAlchemy model with JSON field helpers
- [x] 22. Create Conversation SQLAlchemy model
- [x] 23. Create Message SQLAlchemy model
- [x] 24. Create UserProfile SQLAlchemy model
- [x] 25. Create SafetyFlag SQLAlchemy model

### Basic Chat UI
- [x] 26. Create MessageBubble component
- [x] 27. Create InputArea component with send functionality
- [x] 28. Create ChatWindow component integrating MessageBubble and InputArea

### IPC Communication
- [x] 29. Set up Electron IPC handlers in main process
- [x] 30. Create backend-manager.ts for Python process lifecycle
- [x] 31. Create API client service in React for HTTP requests to FastAPI
- [x] 32. Test IPC communication end-to-end

### Prompt System
- [x] 33. Create base prompt template structure
- [x] 34. Implement personality traits injection into prompts
- [x] 35. Implement user profile context injection
- [x] 36. Implement conversation history formatting
- [x] 37. Add safety instructions to system prompt

### Basic Personality
- [x] 38. Create personality initialization logic with random trait values
- [x] 39. Implement personality trait storage and retrieval
- [x] 40. Create personality trait update logic

---

## Phase 2: Memory System (Weeks 4-5)

### User Profile Management
- [x] 41. Implement user profile creation and initialization
- [x] 42. Create profile update API endpoint
- [x] 43. Create profile retrieval API endpoint

### Memory Extraction
- [x] 44. Create memory extraction prompt for LLM
- [x] 45. Implement fact extraction from user messages
- [x] 46. Create memory storage logic with confidence scores
- [x] 47. Test memory extraction accuracy

### Short-term Memory
- [x] 48. Implement short-term memory context (last 3 conversations)

### Long-term Memory Categories
- [x] 49. Create favorites category storage
- [x] 50. Create dislikes category storage
- [x] 51. Create important people category storage
- [x] 52. Create goals category storage
- [x] 53. Create achievements category storage

### Memory Retrieval
- [x] 54. Implement keyword-based memory search
- [x] 55. Implement relevance ranking for memories
- [x] 56. Create context builder that assembles relevant memories

### Profile UI
- [x] 57. Add ProfilePanel UI component
- [x] 58. Test memory display in profile panel

---

## Phase 3: Personality Growth (Weeks 6-7)

### Friendship Level System
- [x] 59. Create friendship level progression logic
- [x] 60. Implement conversation count tracking
- [x] 61. Create level-up event handling
- [x] 62. Implement feature unlocks for each friendship level

### Personality Drift
- [x] 63. Create personality drift calculation based on conversation metrics
- [x] 64. Implement trait adjustment with bounds (0.0-1.0)
- [x] 65. Add drift rate limiting (max change per conversation/month)

### Visual Friendship Meter
- [x] 66. Build FriendshipMeter component with progress bar
- [x] 67. Add heart icons visualization
- [x] 68. Add level labels and descriptions

### Quirks
- [x] 69. Implement uses_emojis quirk
- [x] 70. Implement tells_puns quirk
- [x] 71. Implement shares_facts quirk
- [ ] 72. Implement storyteller quirk — quirk is assigned at initialization (`personality_manager.py`) but never applied to responses
- [x] 73. Create quirk random assignment at initialization

### Catchphrases
- [x] 74. Generate catchphrase when reaching level 3
- [x] 75. Implement catchphrase injection into responses

### Mood System
- [x] 76. Create mood state management
- [x] 77. Implement mood detection from user messages
- [x] 78. Create mood-based response tone adjustment

### Feature Unlocks
- [x] 79. Create feature unlock registry
- [x] 80. Implement unlock checking logic

---

## Phase 4: Safety & Advice (Weeks 8-9)

### Content Safety Filter
- [x] 81. Create profanity word list
- [x] 82. Implement profanity detection filter
- [x] 83. Implement inappropriate request detection
- [x] 84. Create SafetyFilter class structure

### Crisis Detection
- [x] 85. Create crisis keyword lists (suicide, self-harm, abuse)
- [x] 86. Implement crisis keyword detection
- [x] 87. Implement bullying keyword detection
- [x] 88. Create severity scoring logic

### Crisis Response
- [x] 89. Create crisis response templates with resources
- [x] 90. Implement crisis response delivery
- [x] 91. Create mood change to 'concerned' on crisis

### Advice Template System
- [x] 92. Create advice category detection logic
- [x] 93. Create advice template database structure
- [x] 94. Implement template retrieval based on category and friendship level
- [x] 95. Implement template personalization with user data

### Advice Templates
- [x] 96. Create school_stress advice templates
- [x] 97. Create friend_conflict advice templates
- [x] 98. Create performance_anxiety advice templates
- [x] 99. Create family_issues advice templates
- [x] 100. Create self_confidence advice templates
- [x] 101. Seed advice templates into database

### Safety Logging
- [x] 102. Implement safety flag creation and storage
- [x] 103. Create safety flag retrieval for parent dashboard

### Parent Notification
- [x] 104. Implement email notification for critical flags
- [x] 105. Create parent notification preferences

---

## Phase 5: Parent Dashboard (Week 10)

### Dashboard UI
- [x] 106. Create ParentDashboard component layout
- [x] 107. Add conversation statistics display
- [x] 108. Add safety flags display section
- [x] 109. Add notification settings controls

### Conversation Summaries
- [x] 110. Implement conversation summary generation using LLM
- [x] 111. Store summaries on conversation end

### Safety Flag Viewer
- [x] 112. Create safety flags list view
- [x] 113. Add flag severity indicators

### Notification Settings
- [x] 114. Create notification preferences UI
- [x] 115. Implement preference storage

### Weekly Reports
- [x] 116. Create weekly report generation logic
- [x] 117. Implement email sending for weekly reports
- [x] 118. Create report template

### Password Protection
- [x] 119. Create password protection for parent dashboard access
- [x] 120. Implement password verification

---

## Phase 6: Polish & Features (Weeks 11-12)

### Visual Customization
- [x] 121. Create avatar selection UI
- [x] 122. Implement theme switching (light/dark modes)
- [x] 123. Create color customization options

### Achievement System
- [x] 124. Define achievement types and unlock conditions
- [x] 125. Implement achievement tracking logic
- [x] 126. Create achievement notification UI

### Daily Streak Tracker
- [x] 127. Implement daily login tracking
- [x] 128. Create streak calculation logic
- [x] 129. Add streak display UI component

### Text Games
- [x] 130. Implement 20 questions game
- [x] 131. Implement word association game
- [x] 132. Implement story collaboration game

### Memory Book Export
- [x] 133. Create memory export format (PDF or text)
- [x] 134. Implement memory collection and formatting
- [x] 135. Add export button and file save dialog

### UI/UX Improvements
- [x] 136. Add CSS animations for message appearances
- [x] 137. Add transitions for component changes
- [x] 138. Add typing indicator animation

### Sound Effects
- [x] 139. Add message send sound effect
- [x] 140. Add message receive sound effect
- [x] 141. Add level-up celebration sound

### Performance Optimization
- [x] 142. Optimize LLM model loading time
- [x] 143. Implement response caching where appropriate
- [x] 144. Optimize database queries with indexing
- [x] 145. Profile and reduce memory usage

---

## Core Systems Implementation

### Backend API Endpoints
- [x] 146. Create POST /api/conversation/start endpoint
- [x] 147. Create POST /api/message endpoint
- [x] 148. Create GET /api/personality endpoint
- [x] 149. Create GET /api/profile endpoint
- [x] 150. Create GET /api/parent/dashboard endpoint
- [x] 151. Create POST /api/conversation/end endpoint

### Conversation Manager
- [x] 152. Create ConversationManager class with conversation lifecycle methods
- [x] 153. Implement message processing pipeline
- [x] 154. Implement conversation end handling

### Memory Manager
- [x] 155. Create MemoryManager class structure
- [x] 156. Implement extract_and_store_memories method
- [x] 157. Implement get_relevant_memories method

### Safety System
- [x] 158. Finalize SafetyFilter class with all check methods
- [x] 159. Test safety filter with various inputs

### React Hooks
- [x] 160. Create useChat hook with sendMessage and state management
- [x] 161. Create usePersonality hook
- [x] 162. Create useProfile hook

### Settings
- [x] 163. Create SettingsPanel component with app configuration options
- [x] 164. Implement settings persistence
- [x] 165. Install and configure electron-store
- [x] 166. Create settings schema and defaults

---

## Phase 7: Testing & Refinement (Weeks 13-14)

### User Testing
- [ ] 167. Recruit preteen testers with parental consent
- [ ] 168. Conduct supervised testing sessions
- [ ] 169. Gather and analyze user feedback

### Safety Testing
- [ ] 170. Attempt to bypass safety filters
- [ ] 171. Test crisis detection with various phrasings
- [ ] 172. Verify all inappropriate content is blocked

### Performance Testing
- [ ] 173. Test on low-end hardware (minimum requirements)
- [ ] 174. Test on Mac, Windows, and Linux
- [ ] 175. Measure startup time and response latency

### Bug Fixes
- [ ] 176. Fix bugs from testing phase
- [ ] 177. Address user feedback issues

### Documentation
- [x] 178. Write developer setup documentation
- [ ] 179. Document API endpoints — partial: `backend/README.md` lists core endpoints; parent endpoints are not documented
- [x] 180. Create architecture diagram — ASCII diagram in `README.md` (Architecture section)

### User Guide
- [ ] 181. Write parent user guide explaining features
- [ ] 182. Document safety features for parents
- [ ] 183. Create FAQ section

---

## Follow-up Items (found during code review, 2026-10-19)

These are not in the original 183-task plan; they were found while evaluating and testing the code.

### Frontend
- [ ] F1. Add a parent login step to the frontend: call `POST /api/parent/auth/login`, store the token, and send `Authorization: Bearer <token>` on all `/api/parent/*` requests (these endpoints now require authentication)
- [ ] F2. Fix the remaining renderer TypeScript errors (`npx tsc --noEmit -p tsconfig.json`: 78 errors, e.g. `MessageBubble.tsx` uses snake_case metadata fields, `ExportDialog.tsx`/`MemoryExport.tsx` type mismatches)
- [x] F3. Fix the Electron main-process TypeScript errors (`npx tsc --noEmit -p tsconfig.main.json`: 37 errors), which block `npm run build:main` and `npm run dev`
- [x] F4. Fix the end-conversation call: frontend calls `POST /api/conversation/end/{id}`, backend expects `POST /api/conversation/end` with the ID in the body (backend now accepts both; the app also ends the conversation when the window closes)
- [ ] F5. Chat header shows "Level" without the friendship level number (renderer reads a field name that does not match the API response; part of F2)
- [ ] F6. In development, React StrictMode mounts the app twice, so each launch starts two conversations (the first is never ended) and counts two sessions; production builds are not affected
- [ ] F7. Several Electron IPC handlers are stubs: `get-parent-dashboard` returns mock data and `update-settings` does not save (`src/main/ipc-handlers.ts`)

### Backend
- [x] B1. Move `GET /api/conversation/stats`, `/recent` and `/streak` above `GET /api/conversation/{conversation_id}` in `routes/conversation.py`; they returned 422
- [ ] B2. Parent endpoints return 500 (not 401/503) when password protection is required but no password is configured
- [ ] B3. Advice templates (`advice_template_service`) are not called from the conversation pipeline; detected advice requests only add a category hint to the LLM prompt, so the stored templates are never used (and with no model loaded, advice requests get the generic fallback reply)

### Rule-Based Engine (no-LLM mode, prototype added 2026-10-20)
- [x] R1. Parse messages into dependency trees (spaCy) and match structural rules from `backend/knowledge/conversation_rules.json` for replies, memory extraction and mood (`services/response_engine.py`)
- [x] R2. Expand rule coverage: school events, questions about the child's day, multi-sentence messages, and word order in reflections ("your mom and you" should be "you and your mom")
- [x] R6. Further coverage: sentences about other people's feelings ("my friend is sad"), requests ("can you tell me a joke?"), comparisons, and messages over 15 words that match no rule (currently get a topic or generic reply)
- [x] R3. Track the last-mentioned person and topic across turns so follow-ups like "she said no" can be understood
- [x] R7. Reference limits: "it"/"that" are only resolved as the subject of "was fun/hard/..." or the object of like/love/hate; references to what the bot said, and to whole events ("that" = "going to the zoo"), are not resolved; when two unfamiliar people are mentioned together, "she"/"he" goes to the most recent one until the child's own usage shows otherwise
- [x] R4. Learn from engagement: favor reply types the child responds to (longer answers, returning to a topic)
- [ ] R10. Remaining reference limits: events are only recorded for the child's own actions ("I/we ..."), not other people's ("my dad got mad"); the bot's own answers are only referable for its favorites and picks, jokes and facts, and nouns it introduced; an ambiguous "she"/"he" is only detected for people mentioned in the same turn
- [x] R8. Engagement limits: scoring uses only the text of the next message (not response time or the child leaving); rules with two templates still alternate, so template preferences only apply to rules with three or more; with the LLM enabled, only pun/fact choices are learned
- [x] R5. The quirk filter appended puns, facts and the catchphrase after the bot's closing question; they now go before it
- [ ] R11. Engagement timing thresholds (2 minutes = slow, 15 minutes = left) are estimates; tune them with real usage data
- [ ] R9. Remaining quirk-filter issues: emoji choice ignores the words and emojis are inserted mid-sentence ("orange 💜", "game 🎯?"); a fact and a pun can both be added to one reply (more often at high humor since R4 scales their probability up to 1.5x); transition phrases produce "By the way, What..." and double spaces

### Tests
- [ ] T1. `tests/test_emoji_quirk.py::TestMoodBasedEmojis::test_happy_mood_emojis` fails about half the time (random emoji choice checked against a narrower set)

---

## Progress Summary

**Total Tasks:** 183
**Completed:** 167
**In Progress:** 0
**Pending:** 16 (task 72, tasks 167-177, 179, 181-183)

**Follow-up Items:** 11 pending, 11 completed

**Current Phase:** Phase 7 - Testing & Refinement
