/**
 * 全局轮询管理器 - 避免重复轮询同一个接口
 */

class PollingManager {
  private activePolls: Map<string, NodeJS.Timeout> = new Map();
  private pollCounts: Map<string, number> = new Map();

  /**
   * 开始轮询
   * @param key 轮询标识符
   * @param callback 轮询回调函数
   * @param interval 轮询间隔（毫秒）
   * @returns 是否成功开始轮询
   */
  startPolling(key: string, callback: () => void, interval: number = 5000): boolean {
    // 如果已经有相同的轮询在进行，增加计数但不重复创建
    if (this.activePolls.has(key)) {
      const currentCount = this.pollCounts.get(key) || 0;
      this.pollCounts.set(key, currentCount + 1);
      console.log(`⚠️ 轮询 ${key} 已存在，当前使用者数量: ${currentCount + 1}`);
      return false;
    }

    // 创建新的轮询
    const intervalId = setInterval(callback, interval);
    this.activePolls.set(key, intervalId);
    this.pollCounts.set(key, 1);
    
    console.log(`✅ 开始轮询 ${key}，间隔: ${interval}ms`);
    return true;
  }

  /**
   * 停止轮询
   * @param key 轮询标识符
   */
  stopPolling(key: string): void {
    const currentCount = this.pollCounts.get(key) || 0;
    
    if (currentCount > 1) {
      // 还有其他组件在使用，只减少计数
      this.pollCounts.set(key, currentCount - 1);
      console.log(`📉 轮询 ${key} 使用者减少，剩余: ${currentCount - 1}`);
      return;
    }

    // 最后一个使用者，真正停止轮询
    const intervalId = this.activePolls.get(key);
    if (intervalId) {
      clearInterval(intervalId);
      this.activePolls.delete(key);
      this.pollCounts.delete(key);
      console.log(`🛑 停止轮询 ${key}`);
    }
  }

  /**
   * 检查轮询是否活跃
   * @param key 轮询标识符
   */
  isPolling(key: string): boolean {
    return this.activePolls.has(key);
  }

  /**
   * 获取当前活跃的轮询列表
   */
  getActivePolls(): string[] {
    return Array.from(this.activePolls.keys());
  }

  /**
   * 清理所有轮询
   */
  clearAll(): void {
    this.activePolls.forEach((intervalId, key) => {
      clearInterval(intervalId);
      console.log(`🧹 清理轮询 ${key}`);
    });
    this.activePolls.clear();
    this.pollCounts.clear();
  }

  /**
   * 获取轮询统计信息
   */
  getStats(): { [key: string]: number } {
    const stats: { [key: string]: number } = {};
    this.pollCounts.forEach((count, key) => {
      stats[key] = count;
    });
    return stats;
  }
}

// 创建全局实例
export const pollingManager = new PollingManager();

// 页面卸载时清理所有轮询
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    pollingManager.clearAll();
  });
}

export default PollingManager;