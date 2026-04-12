import { v4 as uuidv4 } from 'uuid';

export const generateSessionId = () => uuidv4();

export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePhone = (phone) => {
  const phoneRegex = /^[\+]?[1-9]?\d{9,15}$/;
  return phoneRegex.test(phone.replace(/\s+/g, ''));
};

export const getDeviceType = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  if (/mobile|iphone|ipod|android|blackberry|opera|mini|windows\sce|palm|smartphone|iemobile/i.test(userAgent)) {
    return 'mobile';
  } else if (/tablet|ipad|playbook|silk/i.test(userAgent)) {
    return 'tablet';
  }
  return 'desktop';
};

export const getMetadata = () => ({
  url: window.location.href,
  referrer: document.referrer,
  deviceType: getDeviceType(),
  timestamp: new Date().toISOString(),
  userAgent: navigator.userAgent,
  language: navigator.language
});

export const storage = {
  get: (key) => {
    try {
      const item = sessionStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  set: (key, value) => {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Silent fail if storage is not available
    }
  },
  remove: (key) => {
    try {
      sessionStorage.removeItem(key);
    } catch {
      // Silent fail
    }
  }
};