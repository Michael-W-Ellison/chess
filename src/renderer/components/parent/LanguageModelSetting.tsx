/**
 * LanguageModelSetting Component
 * Turns the language model on or off. It is off by default; turning it on shows a warning that
 * the model's replies might exceed the safety mechanisms, which the parent must confirm.
 */

import React, { useState } from 'react';
import { useLanguageModelSetting } from '../../hooks/useLanguageModelSetting';

export const LanguageModelSetting: React.FC = () => {
  const { status, isLoading, isSaving, error, setEnabled } = useLanguageModelSetting();
  const [showWarning, setShowWarning] = useState(false);
  const [accepted, setAccepted] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading setting...</p>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading the language model setting: {error}</p>
        </div>
      </div>
    );
  }

  const turnOn = async () => {
    if (await setEnabled(true, true)) {
      setShowWarning(false);
      setAccepted(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-2">Language Model</h3>
        <p className="text-sm text-gray-600">
          By default the chatbot replies with responses written in advance, chosen by rules. A language model
          can be turned on to write replies instead. It is off unless you turn it on here.
        </p>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg mt-4">
          <div>
            <div className="font-medium text-gray-800">
              Language model: {status.enabled || status.enabled_by_config ? 'On' : 'Off'}
            </div>
            {status.enabled && status.warning_accepted_at && (
              <p className="text-sm text-gray-600 mt-1">
                Turned on after the warning was accepted on {new Date(status.warning_accepted_at).toLocaleString()}
              </p>
            )}
            {status.enabled_by_config && (
              <p className="text-sm text-gray-600 mt-1">
                Turned on by USE_LLM=true in the backend configuration; this switch cannot turn it off.
              </p>
            )}
          </div>
          {status.enabled ? (
            <button
              onClick={() => setEnabled(false)}
              disabled={isSaving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Turn off
            </button>
          ) : (
            !showWarning && (
              <button
                onClick={() => setShowWarning(true)}
                disabled={isSaving}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Turn on...
              </button>
            )
          )}
        </div>

        {(status.enabled || status.enabled_by_config) && !status.model_available && (
          <p className="text-sm text-gray-700 mt-4">
            No model file was found ({status.model_file}), so replies still come from the rules. See the
            documentation for where to put a model file.
          </p>
        )}

        {status.bundled_model && <p className="text-xs text-gray-500 mt-4">Built with Llama.</p>}
      </div>

      {showWarning && !status.enabled && (
        <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-6" role="alert">
          <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Warning</h3>
          <p className="text-sm text-yellow-900">{status.warning}</p>
          <label className="flex items-start gap-2 mt-4 text-sm text-yellow-900">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="mt-0.5"
            />
            <span>I have read this warning and understand that the model's replies might exceed the safety mechanisms.</span>
          </label>
          <div className="flex gap-2 mt-4">
            <button
              onClick={turnOn}
              disabled={!accepted || isSaving}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Turn on the language model
            </button>
            <button
              onClick={() => {
                setShowWarning(false);
                setAccepted(false);
              }}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}
    </div>
  );
};
