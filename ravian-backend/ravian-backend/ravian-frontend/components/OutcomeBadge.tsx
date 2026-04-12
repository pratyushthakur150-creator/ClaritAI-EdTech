import React from 'react';

type CallOutcome = 
  | 'demo_booked'
  | 'callback'
  | 'not_interested'
  | 'voicemail'
  | 'no_answer'
  | 'information_provided';

interface OutcomeBadgeProps {
  outcome: CallOutcome | string;
}

export const OutcomeBadge: React.FC<OutcomeBadgeProps> = ({ outcome }) => {
  const getOutcomeConfig = (outcome: string) => {
    switch (outcome) {
      case 'demo_booked':
        return {
          label: 'Demo Booked',
          className: 'bg-green-100 text-green-800 border-green-200'
        };
      case 'callback':
        return {
          label: 'Callback',
          className: 'bg-amber-100 text-amber-800 border-amber-200'
        };
      case 'not_interested':
        return {
          label: 'Not Interested',
          className: 'bg-red-100 text-red-800 border-red-200'
        };
      case 'voicemail':
        return {
          label: 'Voicemail',
          className: 'bg-gray-100 text-gray-800 border-gray-200'
        };
      case 'no_answer':
        return {
          label: 'No Answer',
          className: 'bg-gray-100 text-gray-800 border-gray-200'
        };
      case 'information_provided':
        return {
          label: 'Info Provided',
          className: 'bg-blue-100 text-blue-800 border-blue-200'
        };
      default:
        return {
          label: 'Unknown',
          className: 'bg-gray-100 text-gray-500 border-gray-200'
        };
    }
  };

  const config = getOutcomeConfig(outcome);

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.className}`}>
      {config.label}
    </span>
  );
};