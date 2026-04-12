import { h } from 'preact';

const TypingIndicator = () => {
  return h('div', {
    className: 'typing-indicator',
    'aria-label': 'Assistant is typing'
  }, [
    h('span', { className: 'typing-dot' }),
    h('span', { className: 'typing-dot' }),
    h('span', { className: 'typing-dot' })
  ]);
};

export default TypingIndicator;