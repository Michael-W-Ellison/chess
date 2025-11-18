/**
 * MemoryExport Component
 * Export conversation history, achievements, and stats
 */

import React, { useState, useCallback } from 'react';
import { useChat } from '../hooks/useChat';
import { useAchievements } from '../hooks/useAchievements';
import { useLogin } from '../hooks/useLogin';
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

type ExportType = 'conversations' | 'achievements' | 'stats' | 'complete';

export const MemoryExport: React.FC = () => {
  const { messages, personality } = useChat();
  const { unlockedAchievements } = useAchievements();
  const { stats } = useLogin();

  const [selectedType, setSelectedType] = useState<ExportType>('complete');
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('markdown');
  const [showPreview, setShowPreview] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [exportStatus, setExportStatus] = useState<'idle' | 'success' | 'error'>('idle');

  /**
   * Generate export content based on selections
   */
  const generateExportContent = useCallback((): string => {
    const personalityName = personality?.name || 'Chess Tutor';

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
  }, [selectedType, selectedFormat, messages, personality, unlockedAchievements, stats]);

  /**
   * Handle preview
   */
  const handlePreview = useCallback(() => {
    const content = generateExportContent();
    setPreviewContent(content);
    setShowPreview(true);
  }, [generateExportContent]);

  /**
   * Handle export/download
   */
  const handleExport = useCallback(() => {
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
      setTimeout(() => setExportStatus('idle'), 3000);
    } catch (error) {
      console.error('Export failed:', error);
      setExportStatus('error');
      setTimeout(() => setExportStatus('idle'), 3000);
    }
  }, [generateExportContent, selectedType, selectedFormat]);

  /**
   * Get export type description
   */
  const getTypeDescription = (type: ExportType): string => {
    const descriptions = {
      conversations: `Export ${messages.length} conversation messages`,
      achievements: `Export ${unlockedAchievements.length}/${ACHIEVEMENTS.length} achievements`,
      stats: 'Export login statistics and streaks',
      complete: 'Export everything (conversations, achievements, stats)',
    };
    return descriptions[type];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          📥 Memory Book Export
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Export your conversations, achievements, and progress to keep your memories safe.
        </p>
      </div>

      {/* Export Type Selection */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          What would you like to export?
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(['complete', 'conversations', 'achievements', 'stats'] as ExportType[]).map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`p-4 rounded-lg border-2 transition-all text-left ${
                selectedType === type
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">
                  {type === 'complete' && '📚'}
                  {type === 'conversations' && '💬'}
                  {type === 'achievements' && '🏆'}
                  {type === 'stats' && '📊'}
                </span>
                <span className="font-semibold text-gray-900 dark:text-gray-100 capitalize">
                  {type === 'complete' ? 'Complete Memory Book' : type}
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {getTypeDescription(type)}
              </p>
            </button>
          ))}
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
              className={`px-4 py-3 rounded-lg border-2 transition-all ${
                selectedFormat === format
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
              }`}
            >
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900 dark:text-gray-100 uppercase mb-1">
                  {format === 'markdown' && '.md'}
                  {format === 'text' && '.txt'}
                  {format === 'json' && '.json'}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {format === 'markdown' && 'Rich formatting'}
                  {format === 'text' && 'Plain text'}
                  {format === 'json' && 'Data format'}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={handlePreview}
          className="flex-1 px-4 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          <span>👁️</span>
          <span>Preview</span>
        </button>
        <button
          onClick={handleExport}
          className="flex-1 px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          <span>⬇️</span>
          <span>Export & Download</span>
        </button>
      </div>

      {/* Export Status */}
      {exportStatus === 'success' && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center gap-2">
          <span className="text-green-700 dark:text-green-300">✅</span>
          <span className="text-sm text-green-700 dark:text-green-300 font-medium">
            Export successful! Check your downloads folder.
          </span>
        </div>
      )}

      {exportStatus === 'error' && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-2">
          <span className="text-red-700 dark:text-red-300">❌</span>
          <span className="text-sm text-red-700 dark:text-red-300 font-medium">
            Export failed. Please try again.
          </span>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <span className="text-blue-700 dark:text-blue-300">💡</span>
          <div className="text-sm text-blue-700 dark:text-blue-300">
            <p className="font-semibold mb-1">Why export your memories?</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Keep a permanent record of your learning journey</li>
              <li>Share your progress with parents or teachers</li>
              <li>Create a portfolio of your chess achievements</li>
              <li>Print and add to a scrapbook or journal</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Export Preview
              </h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
              >
                ×
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <pre className="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                {previewContent}
              </pre>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleExport();
                  setShowPreview(false);
                }}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
              >
                Export This
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryExport;
