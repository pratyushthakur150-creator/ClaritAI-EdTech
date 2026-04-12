import { storage } from './helpers.js';

class APIService {
  constructor(config) {
    this.config = config;
    this.retryAttempts = 3;
    this.retryDelay = 1000;
  }

  async makeRequest(endpoint, data, attempt = 1) {
    const url = `${this.config.apiBaseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`,
          'X-Tenant-ID': this.config.tenantId
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed (attempt ${attempt}):`, error);
      
      if (attempt < this.retryAttempts) {
        await this.delay(this.retryDelay * attempt);
        return this.makeRequest(endpoint, data, attempt + 1);
      }
      
      throw error;
    }
  }

  async sendMessage(message, sessionId, metadata) {
    return this.makeRequest('/api/v1/chatbot', {
      message,
      sessionId,
      metadata
    });
  }

  async submitLead(leadData, sessionId) {
    return this.makeRequest('/api/v1/leads', {
      ...leadData,
      sessionId
    });
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export default APIService;