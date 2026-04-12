import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import Message from './Message.js';
import TypingIndicator from './TypingIndicator.js';
import LeadForm from './LeadForm.js';
import APIService from '../utils/api.js';
import { generateSessionId, debounce, getMetadata, storage } from '../utils/helpers.js';

const ChatWidget = ({ config }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [isSubmittingLead, setIsSubmittingLead] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const apiService = useRef(null);

  useEffect(() => {
    const storedSessionId = storage.get('chatbot_session_id');
    const storedMessages = storage.get('chatbot_messages');
    
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
      storage.set('chatbot_session_id', newSessionId);
    }
    
    if (storedMessages) {
      setMessages(storedMessages);
    } else if (config.theme.greeting) {
      const greetingMessage = {
        id: 'greeting',
        type: 'assistant',
        message: config.theme.greeting,
        timestamp: new Date().toISOString()
      };
      setMessages([greetingMessage]);
      storage.set('chatbot_messages', [greetingMessage]);
    }
    
    apiService.current = new APIService(config);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);
  const addMessage = (message) => {
    setMessages(prev => {
      const updated = [...prev, message];
      storage.set('chatbot_messages', updated);
      return updated;
    });
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      message: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    addMessage(userMessage);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await apiService.current.sendMessage(
        userMessage.message,
        sessionId,
        getMetadata()
      );

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        message: response.response || 'I apologize, but I cannot process your request right now.',
        timestamp: new Date().toISOString()
      };

      addMessage(assistantMessage);

      if (response.leadCaptured && config.features.leadCapture) {
        setShowLeadForm(true);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        message: 'Sorry, I am having trouble connecting. Please try again later.',
        timestamp: new Date().toISOString()
      };
      addMessage(errorMessage);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmitLead = async (leadData) => {
    setIsSubmittingLead(true);
    try {
      await apiService.current.submitLead(leadData, sessionId);
      setShowLeadForm(false);
      
      const successMessage = {
        id: Date.now(),
        type: 'assistant',
        message: 'Thank you! We will be in touch soon to help you get started.',
        timestamp: new Date().toISOString()
      };
      addMessage(successMessage);
    } catch (error) {
      console.error('Failed to submit lead:', error);
      const errorMessage = {
        id: Date.now(),
        type: 'assistant',
        message: 'Sorry, there was an error submitting your information. Please try again.',
        timestamp: new Date().toISOString()
      };
      addMessage(errorMessage);
    } finally {
      setIsSubmittingLead(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const debouncedInputChange = debounce((value) => {
    setInputValue(value);
  }, 50);
  return h('div', { className: 'widget-container' }, [
    h('button', {
      className: 'chat-bubble',
      onClick: () => setIsOpen(!isOpen),
      'aria-label': isOpen ? 'Close chat' : 'Open chat',
      'aria-expanded': isOpen
    }, [
      h('svg', {
        viewBox: '0 0 24 24',
        fill: 'currentColor'
      }, [
        h('path', {
          d: 'M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z'
        })
      ])
    ]),
    
    h('div', {
      className: `chat-window ${isOpen ? 'open' : ''}`,
      role: 'dialog',
      'aria-label': 'Chat conversation',
      'aria-hidden': !isOpen
    }, [
      h('div', { className: 'chat-header' }, [
        h('h2', { className: 'chat-title' }, 'Need Help?'),
        h('button', {
          className: 'close-button',
          onClick: () => setIsOpen(false),
          'aria-label': 'Close chat'
        }, '×')
      ]),
      
      h('div', {
        className: 'messages-container',
        role: 'log',
        'aria-label': 'Chat messages',
        'aria-live': 'polite'
      }, [
        ...messages.map(msg => 
          h(Message, {
            key: msg.id,
            message: msg.message,
            type: msg.type,
            avatar: msg.type === 'assistant' ? config.theme.avatar : null
          })
        ),
        
        isTyping && h(TypingIndicator),
        h('div', { ref: messagesEndRef })
      ]),
      
      showLeadForm && h(LeadForm, {
        onSubmit: handleSubmitLead,
        onCancel: () => setShowLeadForm(false),
        isSubmitting: isSubmittingLead
      }),
      
      !showLeadForm && h('div', { className: 'input-container' }, [
        h('input', {
          ref: inputRef,
          type: 'text',
          className: 'message-input',
          placeholder: 'Type your message...',
          value: inputValue,
          onInput: (e) => debouncedInputChange(e.target.value),
          onKeyPress: handleKeyPress,
          disabled: isTyping,
          'aria-label': 'Type your message'
        }),
        h('button', {
          className: 'send-button',
          onClick: sendMessage,
          disabled: !inputValue.trim() || isTyping,
          'aria-label': 'Send message'
        }, [
          h('svg', {
            width: '20',
            height: '20',
            viewBox: '0 0 24 24',
            fill: 'currentColor'
          }, [
            h('path', {
              d: 'M2.01 21L23 12 2.01 3 2 10l15 2-15 2z'
            })
          ])
        ])
      ])
    ])
  ]);
};

export default ChatWidget;