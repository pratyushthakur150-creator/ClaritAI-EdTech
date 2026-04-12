export const getStyles = (theme) => `
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  .widget-container {
    position: fixed;
    ${theme.position === 'bottom-right' ? 'bottom: 20px; right: 20px;' : ''}
    ${theme.position === 'bottom-left' ? 'bottom: 20px; left: 20px;' : ''}
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  }

  .chat-bubble {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: ${theme.primaryColor};
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s, box-shadow 0.2s;
    color: white;
  }

  .chat-bubble:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  }

  .chat-bubble svg {
    width: 28px;
    height: 28px;
  }

  .chat-window {
    position: fixed;
    ${theme.position === 'bottom-right' ? 'bottom: 90px; right: 20px;' : ''}
    ${theme.position === 'bottom-left' ? 'bottom: 90px; left: 20px;' : ''}
    width: 380px;
    height: 550px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    display: none;
    flex-direction: column;
    overflow: hidden;
    animation: slideUp 0.3s ease-out;
  }

  .chat-window.open {
    display: flex;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .chat-header {
    background: ${theme.primaryColor};
    color: white;
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .chat-title {
    font-size: 18px;
    font-weight: 600;
  }

  .close-button {
    background: transparent;
    border: none;
    color: white;
    font-size: 28px;
    cursor: pointer;
    line-height: 1;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: background 0.2s;
  }

  .close-button:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: #f9fafb;
  }

  .message {
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    max-width: 80%;
  }

  .message.user {
    align-self: flex-end;
    align-items: flex-end;
  }

  .message.assistant {
    align-self: flex-start;
  }

  .message-content {
    padding: 10px 14px;
    border-radius: 12px;
    word-wrap: break-word;
  }

  .message.user .message-content {
    background: ${theme.primaryColor};
    color: white;
  }

  .message.assistant .message-content {
    background: white;
    color: #1f2937;
    border: 1px solid #e5e7eb;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 12px;
    background: white;
    border-radius: 12px;
    width: fit-content;
    border: 1px solid #e5e7eb;
  }

  .typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #9ca3af;
    animation: bounce 1.4s infinite ease-in-out;
  }

  .typing-dot:nth-child(1) {
    animation-delay: -0.32s;
  }

  .typing-dot:nth-child(2) {
    animation-delay: -0.16s;
  }

  @keyframes bounce {
    0%, 80%, 100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }

  .input-container {
    display: flex;
    padding: 16px;
    gap: 8px;
    background: white;
    border-top: 1px solid #e5e7eb;
  }

  .message-input {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }

  .message-input:focus {
    border-color: ${theme.primaryColor};
  }

  .send-button {
    background: ${theme.primaryColor};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .send-button:hover:not(:disabled) {
    opacity: 0.9;
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .lead-form {
    padding: 16px;
    background: white;
    border-top: 1px solid #e5e7eb;
  }

  .lead-form h3 {
    font-size: 16px;
    margin-bottom: 12px;
    color: #1f2937;
  }

  .lead-form input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 8px;
  }

  .lead-form-buttons {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }

  .lead-form-buttons button {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .lead-form-buttons button:first-child {
    background: ${theme.primaryColor};
    color: white;
  }

  .lead-form-buttons button:last-child {
    background: #f3f4f6;
    color: #6b7280;
  }

  .lead-form-buttons button:hover {
    opacity: 0.9;
  }

  @media (max-width: 480px) {
    .chat-window {
      width: calc(100vw - 20px);
      height: calc(100vh - 100px);
      left: 10px !important;
      right: 10px !important;
    }
  }
`;