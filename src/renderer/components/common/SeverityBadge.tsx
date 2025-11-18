/**
 * SeverityBadge Component
 * Reusable badge component for displaying safety flag severity levels
 */

import React from 'react';

interface SeverityBadgeProps {
  severity: 'critical' | 'high' | 'medium' | 'low';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  size = 'md',
  showIcon = true,
  className = '',
}) => {
  const severityConfig = {
    critical: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      border: 'border-red-300',
      icon: '🚨',
      label: 'CRITICAL',
      description: 'Immediate attention required',
    },
    high: {
      bg: 'bg-orange-100',
      text: 'text-orange-800',
      border: 'border-orange-300',
      icon: '⚠️',
      label: 'HIGH',
      description: 'Should be addressed soon',
    },
    medium: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      border: 'border-yellow-300',
      icon: '⚡',
      label: 'MEDIUM',
      description: 'Moderate concern',
    },
    low: {
      bg: 'bg-blue-100',
      text: 'text-blue-800',
      border: 'border-blue-300',
      icon: 'ℹ️',
      label: 'LOW',
      description: 'Minor issue',
    },
  };

  const sizeConfig = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const config = severityConfig[severity.toLowerCase() as keyof typeof severityConfig] || severityConfig.low;
  const sizeClass = sizeConfig[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${config.bg} ${config.text} ${config.border} ${sizeClass} ${className}`}
      title={config.description}
    >
      {showIcon && <span className={size === 'sm' ? 'text-xs' : ''}>{config.icon}</span>}
      <span>{config.label}</span>
    </span>
  );
};
