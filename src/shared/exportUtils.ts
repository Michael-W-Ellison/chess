/**
 * Export Utilities
 * Functions to export conversation history, achievements, and stats
 */

import { Message } from './types';
import { Achievement } from './achievements';

export type ExportFormat = 'text' | 'markdown' | 'json';

/**
 * Export conversations to text format
 */
export function exportConversationsToText(
  messages: Message[],
  personalityName: string = 'Chess Tutor'
): string {
  const header = `
================================================================================
  CHESS TUTOR - CONVERSATION HISTORY
================================================================================

Date Exported: ${new Date().toLocaleString()}
Tutor Name: ${personalityName}
Total Messages: ${messages.length}

================================================================================
`;

  const messageText = messages
    .map((msg) => {
      const timestamp = msg.timestamp instanceof Date
        ? msg.timestamp.toLocaleString()
        : new Date(msg.timestamp).toLocaleString();
      const sender = msg.role === 'user' ? 'You' : personalityName;
      const divider = '-'.repeat(80);

      return `
${divider}
[${timestamp}] ${sender}:
${divider}

${msg.content}
`;
    })
    .join('\n');

  const footer = `
================================================================================
  END OF CONVERSATION
================================================================================
`;

  return header + messageText + footer;
}

/**
 * Export conversations to markdown format
 */
export function exportConversationsToMarkdown(
  messages: Message[],
  personalityName: string = 'Chess Tutor'
): string {
  const header = `# Chess Tutor - Conversation History

**Date Exported:** ${new Date().toLocaleString()}
**Tutor Name:** ${personalityName}
**Total Messages:** ${messages.length}

---

`;

  const messageText = messages
    .map((msg) => {
      const timestamp = msg.timestamp instanceof Date
        ? msg.timestamp.toLocaleString()
        : new Date(msg.timestamp).toLocaleString();
      const sender = msg.role === 'user' ? '👤 You' : `🤖 ${personalityName}`;

      return `### ${sender}
*${timestamp}*

${msg.content}

---
`;
    })
    .join('\n');

  return header + messageText;
}

/**
 * Export achievements to text format
 */
export function exportAchievementsToText(
  achievements: Achievement[],
  unlockedAchievements: string[]
): string {
  const header = `
================================================================================
  CHESS TUTOR - ACHIEVEMENTS
================================================================================

Date Exported: ${new Date().toLocaleString()}
Total Achievements: ${achievements.length}
Unlocked: ${unlockedAchievements.length}
Progress: ${Math.round((unlockedAchievements.length / achievements.length) * 100)}%

================================================================================
`;

  const achievementsByCategory = achievements.reduce((acc, achievement) => {
    if (!acc[achievement.category]) {
      acc[achievement.category] = [];
    }
    acc[achievement.category].push(achievement);
    return acc;
  }, {} as Record<string, Achievement[]>);

  let achievementText = '';

  Object.entries(achievementsByCategory).forEach(([category, items]) => {
    achievementText += `\n${category.toUpperCase()}\n${'='.repeat(80)}\n`;

    items.forEach((achievement) => {
      const unlocked = unlockedAchievements.includes(achievement.id);
      const status = unlocked ? '✓ UNLOCKED' : '○ Locked';

      achievementText += `
${status} - ${achievement.name}
${achievement.description}
Points: ${achievement.points}
`;

      if (achievement.rarity) {
        achievementText += `Rarity: ${achievement.rarity}\n`;
      }

      achievementText += '\n';
    });
  });

  const footer = `
================================================================================
  END OF ACHIEVEMENTS
================================================================================
`;

  return header + achievementText + footer;
}

/**
 * Export achievements to markdown format
 */
export function exportAchievementsToMarkdown(
  achievements: Achievement[],
  unlockedAchievements: string[]
): string {
  const header = `# Chess Tutor - Achievements

**Date Exported:** ${new Date().toLocaleString()}
**Total Achievements:** ${achievements.length}
**Unlocked:** ${unlockedAchievements.length}
**Progress:** ${Math.round((unlockedAchievements.length / achievements.length) * 100)}%

---

`;

  const achievementsByCategory = achievements.reduce((acc, achievement) => {
    if (!acc[achievement.category]) {
      acc[achievement.category] = [];
    }
    acc[achievement.category].push(achievement);
    return acc;
  }, {} as Record<string, Achievement[]>);

  let achievementText = '';

  Object.entries(achievementsByCategory).forEach(([category, items]) => {
    achievementText += `## ${category}\n\n`;

    items.forEach((achievement) => {
      const unlocked = unlockedAchievements.includes(achievement.id);
      const status = unlocked ? '✅' : '⬜';

      achievementText += `### ${status} ${achievement.name}\n\n`;
      achievementText += `${achievement.description}\n\n`;
      achievementText += `**Points:** ${achievement.points}`;

      if (achievement.rarity) {
        achievementText += ` | **Rarity:** ${achievement.rarity}`;
      }

      achievementText += '\n\n';
    });
  });

  return header + achievementText;
}

/**
 * Export login stats to text format
 */
export function exportLoginStatsToText(stats: {
  totalLogins: number;
  currentStreak: number;
  longestStreak: number;
  weeklyLogins: number;
  monthlyLogins: number;
}): string {
  return `
================================================================================
  CHESS TUTOR - LOGIN STATISTICS
================================================================================

Date Exported: ${new Date().toLocaleString()}

Current Streak: ${stats.currentStreak} days
Longest Streak: ${stats.longestStreak} days
Total Logins: ${stats.totalLogins}
This Week: ${stats.weeklyLogins} logins
This Month: ${stats.monthlyLogins} logins

================================================================================
`;
}

/**
 * Export complete memory book (all data)
 */
export function exportCompleteMemoryBook(data: {
  messages: Message[];
  personalityName: string;
  achievements: Achievement[];
  unlockedAchievements: string[];
  loginStats: {
    totalLogins: number;
    currentStreak: number;
    longestStreak: number;
    weeklyLogins: number;
    monthlyLogins: number;
  };
  format: ExportFormat;
}): string {
  const { messages, personalityName, achievements, unlockedAchievements, loginStats, format } = data;

  if (format === 'json') {
    return JSON.stringify(
      {
        exportDate: new Date().toISOString(),
        personalityName,
        loginStats,
        achievements: achievements.map((a) => ({
          ...a,
          unlocked: unlockedAchievements.includes(a.id),
        })),
        messages: messages.map((m) => ({
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
        })),
      },
      null,
      2
    );
  }

  if (format === 'markdown') {
    const header = `# Chess Tutor - Complete Memory Book

**Date Exported:** ${new Date().toLocaleString()}
**Tutor Name:** ${personalityName}

---

`;

    const statsSection = `## Statistics

- **Current Streak:** ${loginStats.currentStreak} days
- **Longest Streak:** ${loginStats.longestStreak} days
- **Total Logins:** ${loginStats.totalLogins}
- **This Week:** ${loginStats.weeklyLogins} logins
- **This Month:** ${loginStats.monthlyLogins} logins

---

`;

    const achievementsSection = exportAchievementsToMarkdown(achievements, unlockedAchievements);
    const conversationsSection = `\n---\n\n` + exportConversationsToMarkdown(messages, personalityName);

    return header + statsSection + achievementsSection + conversationsSection;
  }

  // Text format
  const statsSection = exportLoginStatsToText(loginStats);
  const achievementsSection = exportAchievementsToText(achievements, unlockedAchievements);
  const conversationsSection = exportConversationsToText(messages, personalityName);

  return statsSection + '\n' + achievementsSection + '\n' + conversationsSection;
}

/**
 * Download a file with the given content
 */
export function downloadFile(content: string, filename: string, mimeType: string = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Generate filename for export
 */
export function generateExportFilename(type: string, format: ExportFormat): string {
  const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const extension = format === 'json' ? 'json' : format === 'markdown' ? 'md' : 'txt';
  return `chess-tutor-${type}-${date}.${extension}`;
}
