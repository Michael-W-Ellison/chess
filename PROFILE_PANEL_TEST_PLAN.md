## Profile Panel Memory Display - Test Plan

## Overview

This document outlines the test plan for verifying that the ProfilePanel UI component correctly displays memory data from the backend database.

## Prerequisites

Before testing, ensure:

1. ✅ Backend server is running (`cd backend && python -m uvicorn main:app --reload`)
2. ✅ Frontend dev server is running (`npm run dev`)
3. ✅ Database is initialized with test data
4. ✅ Browser is open to the application

## Test Data Setup

### Step 1: Populate Test Data

Run the test data population script:

```bash
cd backend
python test_profile_panel.py
```

**Expected Output:**
```
✓ Created test user (ID: 1)
✓ Added 8 favorites
✓ Added 5 dislikes
✓ Added 7 people
✓ Added 7 goals
✓ Added 6 achievements
✓ Total memories: 33
```

### Step 2: Verify Backend API

Test the API endpoints directly:

```bash
# Get profile summary
curl http://localhost:8000/api/profile?user_id=1

# Get all memories
curl http://localhost:8000/api/profile/memories?user_id=1

# Get favorites only
curl http://localhost:8000/api/profile/favorites?user_id=1

# Get goals only
curl http://localhost:8000/api/profile/goals?user_id=1
```

**Expected:** All endpoints return JSON data with the test memories.

## UI Testing Checklist

### Tab 1: 🤖 Personality Tab

Navigate to Profile → Personality tab

#### Test Cases:

- [ ] **Friendship Meter Displays**
  - Visible friendship level indicator
  - Shows current level (e.g., "Friend", "Best Friend")
  - Stats display (conversations, messages, days)

- [ ] **Personality Traits Display**
  - [ ] Humor slider shows value (0-100)
  - [ ] Energy slider shows value (0-100)
  - [ ] Curiosity slider shows value (0-100)
  - [ ] Formality slider shows value (0-100)
  - [ ] Progress bars fill correctly
  - [ ] Colors match (yellow, orange, blue, purple)

- [ ] **Mood & Info Cards**
  - [ ] Current mood displays correctly
  - [ ] Bot name displays correctly
  - [ ] Cards styled properly

- [ ] **Quirks Section**
  - [ ] Quirks display as tags
  - [ ] Purple background styling
  - [ ] Underscores replaced with spaces

- [ ] **Interests Section**
  - [ ] Interests display as tags
  - [ ] Blue background styling
  - [ ] Underscores replaced with spaces

- [ ] **Catchphrase**
  - [ ] Displays in gradient box
  - [ ] Quotes around text
  - [ ] Italic styling

### Tab 2: 👤 Your Profile Tab

Navigate to Profile → Your Profile tab

#### Test Cases:

- [ ] **User Info Section**
  - [ ] Name displays correctly
  - [ ] Age displays correctly
  - [ ] Grade displays correctly
  - [ ] Section has border and padding

- [ ] **Favorites Section (⭐)**
  - [ ] Section header shows "⭐ Favorites"
  - [ ] All 8 favorites display
  - [ ] Key-value pairs correct:
    - [ ] color: blue
    - [ ] sport: soccer
    - [ ] food: pizza
    - [ ] animal: dog
    - [ ] subject: science
    - [ ] game: Minecraft
    - [ ] movie: Spider-Man
    - [ ] book: Harry Potter
  - [ ] Keys formatted (underscores → spaces, capitalized)
  - [ ] Items in gray background cards

- [ ] **Dislikes Section (👎)**
  - [ ] Section header shows "👎 Dislikes"
  - [ ] All 5 dislikes display
  - [ ] Key-value pairs correct:
    - [ ] vegetable: broccoli
    - [ ] weather: rain
    - [ ] subject: history
    - [ ] chore: cleaning room
    - [ ] food: mushrooms

- [ ] **Goals Section (🎯)**
  - [ ] Section header shows "🎯 Goals"
  - [ ] All 7 goals display
  - [ ] Key-value pairs correct:
    - [ ] academic: get all A's this semester
    - [ ] sports: make the varsity soccer team
    - [ ] personal: read 30 books this year
    - [ ] fitness: run a 5k race
    - [ ] creative: learn to play guitar
    - [ ] social: make 3 new friends
    - [ ] skill: learn Python programming

- [ ] **People Section (👥)**
  - [ ] Section header shows "👥 People"
  - [ ] All 7 people display
  - [ ] Key-value pairs correct:
    - [ ] friend_emma: best friend who loves soccer
    - [ ] friend_jake: friend from school who plays Minecraft
    - [ ] teacher_smith: favorite math teacher
    - [ ] mom: helps with homework and bakes cookies
    - [ ] dad: teaches me science experiments
    - [ ] sister_lily: younger sister who likes art
    - [ ] coach_martinez: soccer coach

- [ ] **Achievements Section (🏆)**
  - [ ] Section header shows "🏆 Achievements"
  - [ ] All 6 achievements display
  - [ ] Key-value pairs correct:
    - [ ] academic: made honor roll last semester
    - [ ] sports: won soccer championship
    - [ ] personal: read 25 books last year
    - [ ] creative: won school art contest
    - [ ] community: volunteered 50 hours
    - [ ] skill: built my first robot

- [ ] **Empty State**
  - [ ] Not shown when data exists
  - [ ] Would show helpful message if no data

### Tab 3: 🧠 Memories Tab

Navigate to Profile → Memories tab

#### Test Cases:

- [ ] **Memory Count Badge**
  - [ ] Tab shows "🧠 Memories (33)" with correct count
  - [ ] Updates if memories change

- [ ] **Grouped Display**
  - [ ] Memories grouped by category
  - [ ] Each category has its own card
  - [ ] Category names capitalized

- [ ] **Memory Details**
  - [ ] Each memory shows key (formatted)
  - [ ] Each memory shows value
  - [ ] Mention count shown when > 1
  - [ ] Examples to verify:
    - [ ] Soccer favorite shows "×15"
    - [ ] Pizza favorite shows "×8"
    - [ ] Emma shows "×12"

- [ ] **Last Mentioned Dates**
  - [ ] Dates display at bottom of memory cards
  - [ ] Format: "Last mentioned: MM/DD/YYYY"
  - [ ] Recent dates for updated memories

- [ ] **Category Organization**
  - [ ] All 5 categories present:
    - [ ] Favorites
    - [ ] Dislikes
    - [ ] People (or Person)
    - [ ] Goals
    - [ ] Achievements
  - [ ] Memories correctly grouped

- [ ] **Empty State**
  - [ ] Not shown when data exists
  - [ ] Would show brain emoji and message if no memories

## Visual & UX Testing

### Layout & Styling

- [ ] **Header**
  - [ ] "Profile" title displays
  - [ ] Subtitle text present
  - [ ] Border at bottom

- [ ] **Tabs**
  - [ ] Three tabs visible
  - [ ] Active tab highlighted in blue
  - [ ] Inactive tabs gray
  - [ ] Blue underline on active tab
  - [ ] Hover effects work

- [ ] **Content Area**
  - [ ] Scrollable when content overflows
  - [ ] Padding around content
  - [ ] Gray background color

- [ ] **Cards**
  - [ ] White background
  - [ ] Border styling
  - [ ] Rounded corners
  - [ ] Proper spacing between cards

- [ ] **Bottom Navigation**
  - [ ] Fixed at bottom
  - [ ] Doesn't overlap content
  - [ ] Profile button highlights when active

### Responsiveness

- [ ] **Desktop View**
  - [ ] Content centered and readable
  - [ ] Appropriate card widths
  - [ ] No overflow issues

- [ ] **Mobile View** (if applicable)
  - [ ] Content stacks properly
  - [ ] Touch targets large enough
  - [ ] Scrolling smooth

### Loading States

- [ ] **Initial Load**
  - [ ] Loading spinner shows while fetching
  - [ ] "Loading..." text appears
  - [ ] Spinner animated

- [ ] **Data Loaded**
  - [ ] Loading spinner disappears
  - [ ] Content appears smoothly
  - [ ] No flash of wrong content

### Error Handling

To test error states (if backend is stopped):

- [ ] **Backend Offline**
  - [ ] Error message displays
  - [ ] Helpful error text
  - [ ] No crash or blank screen

## Functional Testing

### Data Accuracy

- [ ] **All Data Present**
  - [ ] No missing memories
  - [ ] Counts match database
  - [ ] Values display correctly

- [ ] **Data Freshness**
  - [ ] Recent changes reflected
  - [ ] Refresh updates data
  - [ ] No stale data shown

### Interactions

- [ ] **Tab Switching**
  - [ ] Clicking tabs switches content
  - [ ] Smooth transitions
  - [ ] No data loss on switch

- [ ] **Scrolling**
  - [ ] Long lists scroll smoothly
  - [ ] Header stays visible
  - [ ] Bottom nav stays fixed

### Performance

- [ ] **Load Time**
  - [ ] Profile loads in < 2 seconds
  - [ ] No significant delay
  - [ ] Responsive to clicks

- [ ] **Memory Usage**
  - [ ] No memory leaks
  - [ ] Efficient rendering
  - [ ] Smooth animations

## Backend Integration Testing

### API Calls

Monitor network requests (DevTools → Network):

- [ ] **Profile Tab Load**
  - [ ] GET `/api/personality?user_id=1`
  - [ ] GET `/api/profile?user_id=1`
  - [ ] GET `/api/profile/memories?user_id=1`

- [ ] **Response Format**
  - [ ] Personality response has traits, mood, name
  - [ ] Profile response has favorites, goals, etc.
  - [ ] Memories response has array of memory objects

- [ ] **Status Codes**
  - [ ] All requests return 200 OK
  - [ ] No 404 or 500 errors

### Data Transformation

- [ ] **Frontend Processing**
  - [ ] Data correctly parsed
  - [ ] Categories properly grouped
  - [ ] Formatting applied correctly

## Test Results Documentation

### Test Environment

- **Date:** [Fill in]
- **Tester:** [Fill in]
- **Backend Version:** [Fill in]
- **Frontend Version:** [Fill in]
- **Browser:** [Fill in]
- **OS:** [Fill in]

### Results Summary

| Category | Tests Passed | Tests Failed | Notes |
|----------|-------------|--------------|-------|
| Personality Tab | /15 | /15 | |
| Your Profile Tab | /30 | /30 | |
| Memories Tab | /15 | /15 | |
| Visual & UX | /20 | /20 | |
| Functional | /10 | /10 | |
| Integration | /10 | /10 | |
| **TOTAL** | **/100** | **/100** | |

### Issues Found

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| 1 | | | |
| 2 | | | |

### Screenshots

Attach screenshots of:
1. Personality tab with full data
2. Your Profile tab showing all categories
3. Memories tab with grouped memories
4. Any errors or issues found

## Automation Potential

Future automated tests could include:

1. **E2E Tests (Playwright/Cypress)**
   ```typescript
   test('displays all memory categories', async () => {
     await page.goto('/');
     await page.click('[data-testid="profile-tab"]');
     await expect(page.locator('.favorites')).toBeVisible();
     await expect(page.locator('.goals')).toBeVisible();
     // ...
   });
   ```

2. **API Tests**
   ```python
   def test_profile_endpoint():
       response = client.get('/api/profile?user_id=1')
       assert response.status_code == 200
       assert 'favorites' in response.json()
   ```

3. **Component Tests (React Testing Library)**
   ```typescript
   test('renders memories grouped by category', () => {
     render(<ProfilePanel />);
     expect(screen.getByText('Favorites')).toBeInTheDocument();
     expect(screen.getByText('soccer')).toBeInTheDocument();
   });
   ```

## Sign-Off

- [ ] All critical tests passed
- [ ] No blocking issues found
- [ ] Ready for production

**Tester Signature:** ___________________ **Date:** ___________

**Reviewer Signature:** _________________ **Date:** ___________
