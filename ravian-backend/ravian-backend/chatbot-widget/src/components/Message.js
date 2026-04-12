import { h } from 'preact';

const Message = ({ message, type, avatar }) => {
  return h('div', {
    className: `message ${type}`,
    role: 'listitem',
    'aria-label': `${type === 'user' ? 'You' : 'Assistant'}: ${message}`
  }, [
    type === 'assistant' && avatar && h('img', {
      src: avatar,
      alt: 'Assistant avatar',
      style: { width: '20px', height: '20px', borderRadius: '50%', marginRight: '8px' }
    }),
    message
  ]);
};

export default Message;