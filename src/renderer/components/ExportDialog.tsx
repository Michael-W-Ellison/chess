/**
 * ExportDialog Component
 * Reusable dialog for exporting data
 */

import React, { useState, useCallback } from 'react';
import { useChat } from '../hooks/useChat';
import { useAchievements } from '../hooks/useAchievements';
import { useLogin } from '../hooks/useLogin';
import { useMemory } from '../contexts/MemoryContext';
import { ACHIEVEMENTS } from '../../shared/achievements';
import {
  ExportFormat,
  exportConversationsToText,
  exportConversationsToMarkdown,
  exportAchievementsToText,
  exportAchievementsToMarkdown,
  exportLoginStatsToText,
  exportCompleteMemoryBook,
  downloadFile,
  generateExportFilename,
} from '../../shared/exportUtils';

type ExportType = 'conversations' | 'achievements' | 'stats' | 'memories' | 'complete';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  defaultType?: ExportType;
  defaultFormat?: ExportFormat;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  defaultType = 'complete',
  defaultFormat = 'markdown',
}) => {
  const { messages, personality } = useChat();
  const { unlockedAchievements } = useAchievements();
  const { stats } = useLogin();
  const { memories } = useMemory();

  const [selectedType, setSelectedType] = useState<ExportType>(defaultType);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(defaultFormat);
  const [exportStatus, setExportStatus] = useState<'idle' | 'exporting' | 'success' | 'error'>('idle');

  /**
   * Generate export content based on selections
   */
  const generateExportContent = useCallback((): string => {
    const personalityName = personality?.name || 'Chatbot Friend';

    switch (selectedType) {
      case 'conversations':
        return selectedFormat === 'markdown'
          ? exportConversationsToMarkdown(messages, personalityName)
          : exportConversationsToText(messages, personalityName);

      case 'achievements':
        return selectedFormat === 'markdown'
          ? exportAchievementsToMarkdown(ACHIEVEMENTS, unlockedAchievements)
          : exportAchievementsToText(ACHIEVEMENTS, unlockedAchievements);

      case 'stats':
        return exportLoginStatsToText(stats);

      case 'memories':
        // Simple memory export
        const memoryText = memories
          .map((m) => `${m.category}: ${m.key} = ${m.value}`)
          .join('\n');
        return `Memories Export\n================\n\n${memoryText}`;

      case 'complete':
        return exportCompleteMemoryBook({
          messages,
          personalityName,
          achievements: ACHIEVEMENTS,
          unlockedAchievements,
          loginStats: stats,
          format: selectedFormat,
        });

      default:
        return '';
    }
  }, [selectedType, selectedFormat, messages, personality, unlockedAchievements, stats, memories]);

  /**
   * Handle export/download
   */
  const handleExport = useCallback(() => {
    setExportStatus('exporting');

    try {
      const content = generateExportContent();
      const filename = generateExportFilename(selectedType, selectedFormat);
      const mimeType =
        selectedFormat === 'json'
          ? 'application/json'
          : selectedFormat === 'markdown'
          ? 'text/markdown'
          : 'text/plain';

      downloadFile(content, filename, mimeType);
      setExportStatus('success');

      // Auto-close after success
      setTimeout(() => {
        setExportStatus('idle');
        onClose();
      }, 2000);
    } catch (error) {
      console.error('Export failed:', error);
      setExportStatus('error');
      setTimeout(() => setExportStatus('idle'), 3000);
    }
  }, [generateExportContent, selectedType, selectedFormat, onClose]);

  /**
   * Get export type description
   */
  const getTypeDescription = (type: ExportType): string => {
    const descriptions = {
      conversations: `${messages.length} messages`,
      achievements: `${unlockedAchievements.length}/${ACHIEVEMENTS.length} unlocked`,
      stats: 'Login stats and streaks',
      memories: `${memories.length} memories`,
      complete: 'All data combined',
    };
    return descriptions[type];
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="modal-content bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <span>📥</span>
              <span>Export Data</span>
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Download your data in your preferred format
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-3xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Export Type Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              What would you like to export?
            </label>
            <div className="grid grid-cols-1 gap-3">
              {(['complete', 'conversations', 'achievements', 'stats', 'memories'] as ExportType[]).map(
                (type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedType === type
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {type === 'complete' && '📚'}
                        {type === 'conversations' && '💬'}
                        {type === 'achievements' && '🏆'}
                        {type === 'stats' && '📊'}
                        {type === 'memories' && '🧠'}
                      </span>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 dark:text-gray-100 capitalize">
                          {type === 'complete' ? 'Complete Memory Book' : type}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          {getTypeDescription(type)}
                        </div>
                      </div>
                    </div>
                  </button>
                )
              )}
            </div>
          </div>

          {/* Format Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Choose export format
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['markdown', 'text', 'json'] as ExportFormat[]).map((format) => (
                <button
                  key={format}
                  onClick={() => setSelectedFormat(format)}
                  disabled={selectedType === 'stats' && format !== 'text'}
                  className={`px-4 py-3 rounded-lg border-2 transition-all ${
                    selectedFormat === format
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                  } ${
                    selectedType === 'stats' && format !== 'text'
                      ? 'opacity-50 cursor-not-allowed'
                      : ''
                  }`}
                >
                  <div className="text-center">
                    <div className="text-lg font-bold text-gray-900 dark:text-gray-100 uppercase mb-1">
                      {format === 'markdown' && '.md'}
                      {format === 'text' && '.txt'}
                      {format === 'json' && '.json'}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {format === 'markdown' && 'Rich format'}
                      {format === 'text' && 'Plain text'}
                      {format === 'json' && 'Data format'}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Export Status */}
          {exportStatus === 'success' && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center gap-3">
              <span className="text-2xl">✅</span>
              <div className="flex-1">
                <div className="font-semibold text-green-700 dark:text-green-300">
                  Export successful!
                </div>
                <div className="text-sm text-green-600 dark:text-green-400">
                  Check your downloads folder
                </div>
              </div>
            </div>
          )}

          {exportStatus === 'error' && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
              <span className="text-2xl">❌</span>
              <div className="flex-1">
                <div className="font-semibold text-red-700 dark:text-red-300">Export failed</div>
                <div className="text-sm text-red-600 dark:text-red-400">
                  Please try again
                </div>
              </div>
            </div>
          )}

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <span className="text-xl">💡</span>
              <div className="text-sm text-blue-700 dark:text-blue-300">
                <p className="font-semibold mb-1">Quick Tips:</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Markdown (.md) files can be opened in any text editor</li>
                  <li>Use text (.txt) for printing or sharing</li>
                  <li>JSON (.json) is great for backups and data migration</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            disabled={exportStatus === 'exporting'}
            className="px-6 py-2 bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={exportStatus === 'exporting'}
            className="px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {exportStatus === 'exporting' ? (
              <>
                <span className="animate-spin">⏳</span>
                <span>Exporting...</span>
              </>
            ) : (
              <>
                <span>⬇️</span>
                <span>Export & Download</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportDialog;
