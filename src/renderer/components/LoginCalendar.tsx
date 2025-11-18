/**
 * LoginCalendar Component
 * Displays login activity in a calendar heatmap format
 */

import React, { useMemo } from 'react';
import { useLogin } from '../hooks/useLogin';

interface LoginCalendarProps {
  months?: number; // Number of months to display (default: 3)
  compact?: boolean; // Compact view without labels
}

export const LoginCalendar: React.FC<LoginCalendarProps> = ({ months = 3, compact = false }) => {
  const { getLoginHistory } = useLogin();

  // Get login data for the specified period
  const loginData = useMemo(() => {
    const days = months * 30;
    const history = getLoginHistory(days);
    const dataMap = new Map<string, number>();

    history.forEach((record) => {
      dataMap.set(record.date, record.sessionCount);
    });

    return dataMap;
  }, [getLoginHistory, months]);

  // Generate calendar grid (last N months)
  const calendarGrid = useMemo(() => {
    const grid: Array<{ date: string; sessionCount: number; dayOfWeek: number }> = [];
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - months * 30);

    for (let i = 0; i < months * 30; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + i);
      const dateStr = currentDate.toISOString().split('T')[0];
      const sessionCount = loginData.get(dateStr) || 0;

      grid.push({
        date: dateStr,
        sessionCount,
        dayOfWeek: currentDate.getDay(),
      });
    }

    return grid;
  }, [months, loginData]);

  // Get color intensity based on session count
  const getColorIntensity = (sessionCount: number): string => {
    if (sessionCount === 0) {
      return 'bg-gray-100 dark:bg-gray-800';
    } else if (sessionCount === 1) {
      return 'bg-green-200 dark:bg-green-900';
    } else if (sessionCount === 2) {
      return 'bg-green-400 dark:bg-green-700';
    } else if (sessionCount >= 3) {
      return 'bg-green-600 dark:bg-green-500';
    }
    return 'bg-gray-100 dark:bg-gray-800';
  };

  // Format date for tooltip
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (compact) {
    return (
      <div className="flex gap-1 flex-wrap">
        {calendarGrid.map((day) => (
          <div
            key={day.date}
            className={`w-3 h-3 rounded-sm ${getColorIntensity(day.sessionCount)} transition-colors`}
            title={`${formatDate(day.date)}: ${day.sessionCount} ${day.sessionCount === 1 ? 'login' : 'logins'}`}
          />
        ))}
      </div>
    );
  }

  // Group by weeks
  const weeks: Array<Array<{ date: string; sessionCount: number; dayOfWeek: number }>> = [];
  let currentWeek: Array<{ date: string; sessionCount: number; dayOfWeek: number }> = [];

  calendarGrid.forEach((day, index) => {
    if (index === 0 && day.dayOfWeek !== 0) {
      // Add empty cells for the start of the first week
      for (let i = 0; i < day.dayOfWeek; i++) {
        currentWeek.push({ date: '', sessionCount: 0, dayOfWeek: i });
      }
    }

    currentWeek.push(day);

    if (day.dayOfWeek === 6 || index === calendarGrid.length - 1) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });

  return (
    <div className="space-y-2">
      {/* Legend */}
      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
        <span>Less</span>
        <div className="flex gap-1">
          <div className="w-3 h-3 rounded-sm bg-gray-100 dark:bg-gray-800" />
          <div className="w-3 h-3 rounded-sm bg-green-200 dark:bg-green-900" />
          <div className="w-3 h-3 rounded-sm bg-green-400 dark:bg-green-700" />
          <div className="w-3 h-3 rounded-sm bg-green-600 dark:bg-green-500" />
        </div>
        <span>More</span>
      </div>

      {/* Calendar grid */}
      <div className="space-y-1">
        <div className="grid grid-cols-7 gap-1">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div
              key={day}
              className="text-xs text-center text-gray-500 dark:text-gray-400 font-medium"
            >
              {day[0]}
            </div>
          ))}
        </div>
        <div className="space-y-1">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-7 gap-1">
              {week.map((day, dayIndex) => (
                <div
                  key={`${weekIndex}-${dayIndex}`}
                  className={`w-8 h-8 rounded flex items-center justify-center ${
                    day.date
                      ? `${getColorIntensity(day.sessionCount)} cursor-pointer hover:ring-2 hover:ring-blue-400 dark:hover:ring-blue-600 transition-all`
                      : 'bg-transparent'
                  }`}
                  title={
                    day.date
                      ? `${formatDate(day.date)}: ${day.sessionCount} ${day.sessionCount === 1 ? 'login' : 'logins'}`
                      : ''
                  }
                >
                  {day.date && day.sessionCount > 0 && (
                    <span className="text-xs font-bold text-white dark:text-gray-100">
                      {day.sessionCount}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoginCalendar;
