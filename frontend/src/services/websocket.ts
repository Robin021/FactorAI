import { useAnalysisStore } from '@/stores/analysisStore';
import { useNotificationStore } from '@/stores/notificationStore';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
}

export interface AnalysisProgressMessage {
  analysisId: string;
  progress: number;
  status: string;
  message?: string;
  currentStep?: string;
}

export interface NotificationMessage {
  title: string;
  message?: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  constructor() {
    this.connect();
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('auth_token');
    
    return `${protocol}//${host}/api/v1/ws?token=${token}`;
  }

  connect(): void {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isConnecting = true;
    
    try {
      this.ws = new WebSocket(this.getWebSocketUrl());
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private handleOpen(): void {
    console.log('WebSocket connected');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    // Subscribe to analysis progress updates
    this.subscribe('analysis_progress');
    this.subscribe('notifications');
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.processMessage(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnecting = false;
    
    if (event.code !== 1000) {
      // Abnormal closure, attempt to reconnect
      this.scheduleReconnect();
    }
  }

  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
    this.isConnecting = false;
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private processMessage(message: WebSocketMessage): void {
    const { type, data } = message;
    
    // Notify specific listeners
    const listeners = this.listeners.get(type);
    if (listeners) {
      listeners.forEach((listener) => listener(data));
    }

    // Handle built-in message types
    switch (type) {
      case 'analysis_progress':
        this.handleAnalysisProgress(data as AnalysisProgressMessage);
        break;
        
      case 'notification':
        this.handleNotification(data as NotificationMessage);
        break;
        
      default:
        console.log('Unhandled WebSocket message type:', type, data);
    }
  }

  private handleAnalysisProgress(data: AnalysisProgressMessage): void {
    const { updateAnalysisProgress } = useAnalysisStore.getState();
    updateAnalysisProgress(data.analysisId, data.progress, data.status);
    
    // Show notification for completed analysis
    if (data.status === 'completed') {
      const { success } = useNotificationStore.getState();
      success('分析完成', `股票分析已完成，进度: ${data.progress}%`);
    } else if (data.status === 'failed') {
      const { error } = useNotificationStore.getState();
      error('分析失败', data.message || '分析过程中发生错误');
    }
  }

  private handleNotification(data: NotificationMessage): void {
    const { addNotification } = useNotificationStore.getState();
    addNotification({
      type: data.type,
      title: data.title,
      message: data.message,
    });
  }

  // Public methods
  subscribe(messageType: string, listener?: (data: any) => void): void {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, new Set());
    }
    
    if (listener) {
      this.listeners.get(messageType)!.add(listener);
    }
    
    // Send subscription message to server
    this.send({
      type: 'subscribe',
      data: { messageType },
      timestamp: Date.now(),
    });
  }

  unsubscribe(messageType: string, listener?: (data: any) => void): void {
    if (listener) {
      const listeners = this.listeners.get(messageType);
      if (listeners) {
        listeners.delete(listener);
        if (listeners.size === 0) {
          this.listeners.delete(messageType);
        }
      }
    } else {
      this.listeners.delete(messageType);
    }
    
    // Send unsubscription message to server
    this.send({
      type: 'unsubscribe',
      data: { messageType },
      timestamp: Date.now(),
    });
  }

  send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected, message not sent:', message);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.listeners.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Subscribe to analysis progress for a specific analysis
  subscribeToAnalysis(analysisId: string, listener?: (data: AnalysisProgressMessage) => void): void {
    const messageType = `analysis_progress_${analysisId}`;
    this.subscribe(messageType, listener);
  }

  unsubscribeFromAnalysis(analysisId: string, listener?: (data: AnalysisProgressMessage) => void): void {
    const messageType = `analysis_progress_${analysisId}`;
    this.unsubscribe(messageType, listener);
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;