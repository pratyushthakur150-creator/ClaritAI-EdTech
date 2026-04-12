import React from 'react';

type Sentiment = 'positive' | 'neutral' | 'negative';

interface SentimentEmojiProps {
  sentiment: Sentiment;
}

export const SentimentEmoji: React.FC<SentimentEmojiProps> = ({ sentiment }) => {
  const getSentimentEmoji = (sentiment: Sentiment) => {
    switch (sentiment) {
      case 'positive':
        return '😊';
      case 'neutral':
        return '😐';
      case 'negative':
        return '😞';
      default:
        return '😐'; // Default to neutral for unknown sentiment
    }
  };

  return (
    <span className="text-lg select-none" title={`${sentiment} sentiment`}>
      {getSentimentEmoji(sentiment)}
    </span>
  );
};