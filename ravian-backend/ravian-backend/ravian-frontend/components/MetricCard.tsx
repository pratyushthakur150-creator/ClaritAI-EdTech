'use client'

import React, { useEffect, useState, useRef } from 'react';

/** Props for brand-colored icon background mapping */
const iconColors: Record<string, { bg: string; text: string }> = {
  blue: { bg: 'bg-blue-50', text: 'text-blue-600' },
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-600' },
  green: { bg: 'bg-emerald-50', text: 'text-emerald-600' },
  purple: { bg: 'bg-purple-50', text: 'text-purple-600' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-600' },
  red: { bg: 'bg-red-50', text: 'text-red-600' },
  default: { bg: 'bg-slate-100', text: 'text-slate-500' },
};

export interface MetricCardProps {
  title: string;
  value: number | string;
  trend?: number;
  icon: React.ReactNode;
  trendInverted?: boolean;
  /** Brand color for the icon container */
  iconColor?: keyof typeof iconColors;
  /** Animation stagger index (0-based) for entry animation */
  index?: number;
}

/** Animated count-up hook for numeric values */
function useCountUp(target: number, duration: number = 800): number {
  const [current, setCurrent] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (target === 0) { setCurrent(0); return; }
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(target * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return current;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  trend,
  icon,
  trendInverted = false,
  iconColor = 'default',
  index = 0,
}) => {
  const isNumeric = typeof value === 'number';
  const animatedValue = useCountUp(isNumeric ? value : 0);

  const formatValue = (val: number | string): string => {
    if (typeof val === 'number') return val.toLocaleString();
    return val;
  };

  const getTrendColor = (trendValue: number): string => {
    if (trendValue > 0) return trendInverted ? 'text-red-600 bg-red-50' : 'text-emerald-600 bg-emerald-50';
    if (trendValue < 0) return trendInverted ? 'text-emerald-600 bg-emerald-50' : 'text-red-600 bg-red-50';
    return 'text-slate-500 bg-slate-50';
  };

  const getTrendArrow = (trendValue: number): string => {
    return trendValue >= 0 ? '↑' : '↓';
  };

  const colors = iconColors[iconColor] || iconColors.default;

  return (
    <div
      className="metric-card animate-fade-in-up"
      style={{ animationDelay: `${index * 0.06}s` }}
    >
      {/* Top row: title (left) and icon (right) */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="metric-label">{title}</h3>
        <div className={`w-9 h-9 rounded-xl ${colors.bg} ${colors.text} flex items-center justify-center`}>
          {icon}
        </div>
      </div>

      {/* Large value display with count-up animation */}
      <div className="mb-2">
        <p className="metric-value">
          {isNumeric ? animatedValue.toLocaleString() : formatValue(value)}
        </p>
      </div>

      {/* Optional trend indicator */}
      {trend !== undefined && (
        <div className="flex items-center gap-1.5">
          <span className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${getTrendColor(trend)}`}>
            {getTrendArrow(trend)} {Math.abs(trend).toFixed(1)}%
          </span>
          <span className="text-xs text-slate-400">
            vs last period
          </span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
