import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

const colorMap = {
  blue:   { bg: 'bg-blue-50',   icon: 'bg-blue-100',   text: 'text-blue-600' },
  green:  { bg: 'bg-green-50',  icon: 'bg-green-100',  text: 'text-green-600' },
  red:    { bg: 'bg-red-50',    icon: 'bg-red-100',    text: 'text-red-600' },
  yellow: { bg: 'bg-yellow-50', icon: 'bg-yellow-100', text: 'text-yellow-600' },
  purple: { bg: 'bg-purple-50', icon: 'bg-purple-100', text: 'text-purple-600' },
  indigo: { bg: 'bg-indigo-50', icon: 'bg-indigo-100', text: 'text-indigo-600' },
};

export default function StatsCard({ title, value, icon: Icon, color = 'blue', trend, trendValue, subtitle }) {
  const c = colorMap[color] || colorMap.blue;
  const isUp = trend === 'up';
  const isDown = trend === 'down';
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900 tabular-nums">{value ?? '—'}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
          {trendValue !== undefined && (
            <div className={`mt-2 flex items-center gap-1 text-xs font-medium ${isUp ? 'text-green-600' : isDown ? 'text-red-500' : 'text-gray-400'}`}>
              {isUp && <TrendingUp className="w-3.5 h-3.5" />}
              {isDown && <TrendingDown className="w-3.5 h-3.5" />}
              <span>{trendValue}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`flex-shrink-0 w-12 h-12 rounded-xl ${c.icon} flex items-center justify-center`}>
            <Icon className={`w-6 h-6 ${c.text}`} />
          </div>
        )}
      </div>
    </div>
  );
}
