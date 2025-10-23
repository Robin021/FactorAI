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
  private enabled = false;
  private supportChecked = false;

  constructor() {
    // 延迟检查后端是否支持WebSocket，避免在不支持时反复403重连
    this.checkSupportAndConnect();
  }

  private async checkSupportAndConnect(): Promise<void> {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/v1/ws/stats', {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      this.supportChecked = true;
      if (res.ok) {
        this.enabled = true;
        this.connect();
      } else {
        console.info('WebSocket not enabled on backend, using polling only');
        this.enabled = false;
      }
    } catch (_) {
      // 后端不支持或网络失败，退回轮询
      this.supportChecked = true;
      this.enabled = false;
      console.info('WebSocket probe failed, fallback to polling');
    }
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('auth_token');
    
    return `${protocol}//${host}/api/v1/ws?token=${token}`;
  }

  connect(): void {
    if (!this.supportChecked) {
      // 尚未完成支持探测，等探测完成后再连接
      return;
    }
    if (!this.enabled) {
      // 后端不支持，跳过连接
      return;
    }
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
    
    // Subscribe to notifications channel (server expects explicit message type)
    this.send({
      type: 'subscribe_notifications',
      data: {},
      timestamp: Date.now(),
    });
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
    const { updateAnalysisProgress, getAnalysisResult } = useAnalysisStore.getState();
    updateAnalysisProgress(data.analysisId, data.progress, data.status);
    
    // Show notification for completed analysis
    if (data.status === 'completed') {
      const { success } = useNotificationStore.getState();
      success('分析完成', `股票分析已完成，进度: ${data.progress}%`);
      
      // 自动获取分析结果
      console.log('🎉 分析完成，自动获取结果数据:', data.analysisId);
      getAnalysisResult(data.analysisId).catch(err => {
        console.error('❌ 自动获取分析结果失败:', err);
      });
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
  // Generic local listener registry (client side only)
  subscribeLocal(messageType: string, listener: (data: any) => void): void {
    if (!this.listeners.has(messageType)) this.listeners.set(messageType, new Set());
    this.listeners.get(messageType)!.add(listener);
  }

  unsubscribeLocal(messageType: string, listener?: (data: any) => void): void {
    if (!listener) {
      this.listeners.delete(messageType);
      return;
    }
    const set = this.listeners.get(messageType);
    if (!set) return;
    set.delete(listener);
    if (set.size === 0) this.listeners.delete(messageType);
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
    // Register local listener for progress events
    if (listener) this.subscribeLocal('analysis_progress', listener as any);
    // Tell server to subscribe this connection to the analysis
    this.send({
      type: 'subscribe_analysis',
      data: { analysis_id: analysisId },
      timestamp: Date.now(),
    });
  }

  unsubscribeFromAnalysis(analysisId: string, listener?: (data: AnalysisProgressMessage) => void): void {
    if (listener) this.unsubscribeLocal('analysis_progress', listener as any);
    this.send({
      type: 'unsubscribe_analysis',
      data: { analysis_id: analysisId },
      timestamp: Date.now(),
    });
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;
