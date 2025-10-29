#!/usr/bin/env python3
"""
情绪数据源管理模块
提供多市场情绪数据获取和管理功能
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from functools import wraps

# 导入日志管理器
from tradingagents.utils.logging_manager import get_logger
# 导入降级策略管理器
from tradingagents.agents.utils.fallback_strategy import FallbackStrategy

logger = get_logger('sentiment_data_sources')


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """数据获取重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # 指数退避
                        logger.warning(
                            f"数据获取失败 (尝试 {attempt + 1}/{max_retries}): {e}, "
                            f"等待 {wait_time}s 后重试..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"数据获取失败，已达最大重试次数: {e}")
            
            raise last_exception
        return wrapper
    return decorator


class SentimentDataSource(ABC):
    """情绪数据源基类"""
    
    def __init__(self, cache_manager=None, fallback_strategy=None):
        """
        初始化数据源
        
        Args:
            cache_manager: 缓存管理器实例（可选）
            fallback_strategy: 降级策略管理器实例（可选）
        """
        self.cache = cache_manager
        self.fallback_strategy = fallback_strategy
        self.source_name = self.__class__.__name__
        logger.info(f"初始化数据源: {self.source_name}")
    
    def get_data(self, ticker: str, date: str, **kwargs) -> Dict[str, Any]:
        """
        获取数据（带缓存和降级处理）
        
        Args:
            ticker: 股票代码
            date: 日期 (YYYY-MM-DD)
            **kwargs: 额外参数
            
        Returns:
            数据字典
        """
        # 使用数据源名称作为data_type
        data_type = self.source_name.lower().replace('datasource', '')
        
        # 尝试从缓存获取
        if self.cache:
            try:
                cached_data = self.cache.get(ticker, data_type, date, **kwargs)
                if cached_data is not None:
                    logger.info(f"✅ 缓存命中: {ticker}:{data_type}:{date}, 数据: {cached_data}")
                    return cached_data
            except Exception as cache_error:
                logger.warning(f"缓存读取失败: {cache_error}，继续获取新数据")
        
        # 缓存未命中，获取新数据（带降级处理）
        logger.info(f"⚠️  缓存未命中，获取新数据: {ticker}:{data_type}:{date}")
        try:
            data = self._fetch_data(ticker, date, **kwargs)
            
            # 存入缓存
            if self.cache and data:
                try:
                    ttl = self._get_cache_ttl()
                    self.cache.set(ticker, data_type, data, date, ttl=ttl, **kwargs)
                    logger.debug(f"数据已缓存: {ticker}:{data_type}:{date}, TTL={ttl}s")
                except Exception as cache_error:
                    logger.warning(f"缓存写入失败: {cache_error}，但数据获取成功")
            
            return data
            
        except Exception as e:
            logger.error(f"数据获取失败: {ticker}:{data_type}:{date}, 错误: {e}")
            
            # 如果有降级策略，使用降级数据
            if self.fallback_strategy:
                logger.warning(f"使用降级策略: {self.source_name}")
                self.fallback_strategy.record_failure(self.source_name, e)
                return self.fallback_strategy.get_fallback_data(self.source_name)
            
            # 没有降级策略，重新抛出异常
            raise
    
    def _generate_cache_key(self, ticker: str, date: str, **kwargs) -> str:
        """生成缓存键"""
        base_key = f"{self.source_name}:{ticker}:{date}"
        if kwargs:
            extra = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            return f"{base_key}:{extra}"
        return base_key
    
    def _get_cache_ttl(self) -> int:
        """获取缓存过期时间（秒），子类可覆盖"""
        return 300  # 默认5分钟
    
    @abstractmethod
    def _fetch_data(self, ticker: str, date: str, **kwargs) -> Dict[str, Any]:
        """
        实际获取数据（子类实现）
        
        Args:
            ticker: 股票代码
            date: 日期
            **kwargs: 额外参数
            
        Returns:
            数据字典
        """
        pass


class CoreSentimentDataSource(SentimentDataSource):
    """核心情绪数据源（三市场通用）"""
    
    def __init__(self, cache_manager=None, toolkit=None, fallback_strategy=None):
        """
        初始化核心情绪数据源
        
        Args:
            cache_manager: 缓存管理器
            toolkit: 工具包（包含新闻工具等）
            fallback_strategy: 降级策略管理器
        """
        super().__init__(cache_manager, fallback_strategy)
        self.toolkit = toolkit
        logger.info("核心情绪数据源初始化完成")
    
    def _fetch_data(self, ticker: str, date: str, **kwargs) -> Dict[str, Any]:
        """获取核心情绪数据"""
        logger.info(f"[CoreSentimentDataSource] 开始获取核心情绪数据: {ticker}, {date}")
        
        news_sentiment = self.get_news_sentiment(ticker, date)
        logger.info(f"[CoreSentimentDataSource] 新闻情绪: {news_sentiment:.3f}")
        
        price_momentum = self.get_price_momentum(ticker, date)
        logger.info(f"[CoreSentimentDataSource] 价格动量: {price_momentum:.3f}")
        
        volume_sentiment = self.get_volume_sentiment(ticker, date)
        logger.info(f"[CoreSentimentDataSource] 成交量情绪: {volume_sentiment:.3f}")
        
        result = {
            'news_sentiment': news_sentiment,
            'price_momentum': price_momentum,
            'volume_sentiment': volume_sentiment,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"[CoreSentimentDataSource] 核心数据获取完成: {result}")
        return result
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_news_sentiment(self, ticker: str, date: str) -> float:
        """
        获取新闻情绪评分（带降级处理）
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"获取新闻情绪: {ticker}")
        
        try:
            # 使用统一新闻工具
            if self.toolkit and hasattr(self.toolkit, 'get_stock_news_unified'):
                news_data = self.toolkit.get_stock_news_unified.invoke({
                    "ticker": ticker,
                    "curr_date": date
                })
                
                if news_data and len(news_data) > 100:
                    # 简单的情绪分析：基于关键词
                    positive_keywords = ['上涨', '增长', '盈利', '突破', '创新高', '利好', 
                                       'growth', 'profit', 'gain', 'surge', 'bullish']
                    negative_keywords = ['下跌', '亏损', '下滑', '风险', '警告', '利空',
                                       'loss', 'decline', 'fall', 'risk', 'bearish']
                    
                    positive_count = sum(1 for kw in positive_keywords if kw in news_data)
                    negative_count = sum(1 for kw in negative_keywords if kw in news_data)
                    
                    total = positive_count + negative_count
                    if total > 0:
                        score = (positive_count - negative_count) / total
                        logger.info(f"新闻情绪评分: {score:.2f} (正面:{positive_count}, 负面:{negative_count})")
                        return max(-1.0, min(1.0, score))
            
            logger.warning(f"无法获取新闻数据: {ticker}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('news_sentiment', Exception("新闻数据不可用"))
                fallback_data = self.fallback_strategy.get_fallback_data('news_sentiment')
                return fallback_data.get('score', 0.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"新闻情绪分析失败: {e}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('news_sentiment', e)
                fallback_data = self.fallback_strategy.get_fallback_data('news_sentiment')
                return fallback_data.get('score', 0.0)
            
            return 0.0
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_price_momentum(self, ticker: str, date: str) -> float:
        """
        获取价格动量评分（带降级处理）
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            动量评分 (-1.0 到 1.0)
        """
        logger.info(f"计算价格动量: {ticker}")
        
        try:
            # 导入数据获取工具
            from tradingagents.dataflows.interface import get_stock_data_by_market
            import re
            
            # 获取最近30天的价格数据
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=30)
            
            price_data_str = get_stock_data_by_market(
                symbol=ticker,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=date
            )
            
            # 解析字符串数据，提取涨跌幅信息
            if price_data_str and isinstance(price_data_str, str) and len(price_data_str) > 100:
                # 方法1: 尝试从摘要中提取 "涨跌幅: -2.02%"
                change_match = re.search(r'涨跌幅[：:]\s*([-+]?\d+\.?\d*)%', price_data_str)
                if change_match:
                    change_pct = float(change_match.group(1))
                    momentum = max(-1.0, min(1.0, change_pct / 10.0))
                    logger.info(f"✅ 价格动量评分: {momentum:.3f} (涨跌幅: {change_pct}%)")
                    return momentum
                
                # 方法2: 从表格数据中提取（最后一行的涨跌幅列）
                # 查找最后一行数据，格式: "2025-10-29 688256 1460.0 1448.67 ... 6.10 -2.02 -29.91 1.77"
                lines = price_data_str.strip().split('\n')
                for line in reversed(lines):
                    # 跳过表头和分隔线
                    if '日期' in line or '---' in line or '期间统计' in line:
                        continue
                    # 尝试提取数字（涨跌幅通常在倒数第3列）
                    parts = line.split()
                    if len(parts) >= 12:  # 确保有足够的列
                        try:
                            # 涨跌幅在倒数第3列（振幅、涨跌幅、涨跌额、换手率）
                            change_pct = float(parts[-3])
                            if -50 < change_pct < 50:  # 合理的涨跌幅范围
                                momentum = max(-1.0, min(1.0, change_pct / 10.0))
                                logger.info(f"✅ 价格动量评分(表格): {momentum:.3f} (涨跌幅: {change_pct}%)")
                                return momentum
                        except (ValueError, IndexError):
                            continue
                
                logger.warning(f"⚠️ 未找到涨跌幅字段，数据预览: {price_data_str[:200]}")
            else:
                logger.warning(f"⚠️ 价格数据格式异常: type={type(price_data_str)}, len={len(str(price_data_str)) if price_data_str else 0}")
            
            logger.warning(f"无法解析价格数据: {ticker}，返回中性评分")
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ 价格动量计算失败: {e}")
            return 0.0
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_volume_sentiment(self, ticker: str, date: str) -> float:
        """
        获取成交量情绪评分（带降级处理）
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            成交量情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"分析成交量情绪: {ticker}")
        
        try:
            # 导入数据获取工具
            from tradingagents.dataflows.interface import get_stock_data_by_market
            import re
            
            # 获取最近30天的成交量数据
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=30)
            
            volume_data_str = get_stock_data_by_market(
                symbol=ticker,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=date
            )
            
            # 解析字符串数据，提取成交量信息
            if volume_data_str and isinstance(volume_data_str, str) and len(volume_data_str) > 100:
                # 方法1: 尝试从摘要中提取 "换手率: X.XX"
                turnover_match = re.search(r'换手率[：:]\s*(\d+\.?\d*)', volume_data_str)
                
                if turnover_match:
                    turnover = float(turnover_match.group(1))
                else:
                    # 方法2: 从表格数据中提取（最后一行的换手率列）
                    # 查找最后一行数据，换手率在最后一列
                    lines = volume_data_str.strip().split('\n')
                    turnover = None
                    for line in reversed(lines):
                        # 跳过表头和分隔线
                        if '日期' in line or '---' in line or '期间统计' in line:
                            continue
                        # 尝试提取数字（换手率在最后一列）
                        parts = line.split()
                        if len(parts) >= 12:  # 确保有足够的列
                            try:
                                # 换手率在最后一列
                                turnover = float(parts[-1])
                                if 0 < turnover < 50:  # 合理的换手率范围
                                    break
                                else:
                                    turnover = None
                            except (ValueError, IndexError):
                                continue
                
                if turnover is not None:
                    # 换手率越高，市场越活跃
                    # 换手率 > 10%: 非常活跃 (0.7-1.0)
                    # 换手率 5-10%: 活跃 (0.3-0.7)
                    # 换手率 2-5%: 正常 (0-0.3)
                    # 换手率 < 2%: 低迷 (-0.3-0)
                    if turnover > 10:
                        sentiment = min(0.7 + (turnover - 10) / 20, 1.0)
                    elif turnover > 5:
                        sentiment = 0.3 + (turnover - 5) / 5 * 0.4
                    elif turnover > 2:
                        sentiment = (turnover - 2) / 3 * 0.3
                    else:
                        sentiment = -0.3 + turnover / 2 * 0.3
                    
                    logger.info(f"✅ 成交量情绪评分: {sentiment:.3f} (换手率: {turnover}%)")
                    return sentiment
                else:
                    logger.warning(f"⚠️ 未找到换手率字段，数据预览: {volume_data_str[:200]}")
            else:
                logger.warning(f"⚠️ 成交量数据格式异常: type={type(volume_data_str)}, len={len(str(volume_data_str)) if volume_data_str else 0}")
            
            logger.warning(f"无法解析成交量数据: {ticker}，返回中性评分")
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ 成交量情绪分析失败: {e}")
            return 0.0
    
    def _get_cache_ttl(self) -> int:
        """核心数据缓存30分钟"""
        return 1800



class USEnhancedDataSource(SentimentDataSource):
    """美股增强数据源"""
    
    def __init__(self, cache_manager=None, toolkit=None, fallback_strategy=None):
        """
        初始化美股增强数据源
        
        Args:
            cache_manager: 缓存管理器
            toolkit: 工具包
            fallback_strategy: 降级策略管理器
        """
        super().__init__(cache_manager, fallback_strategy)
        self.toolkit = toolkit
        logger.info("美股增强数据源初始化完成")
    
    def _fetch_data(self, ticker: str, date: str, **kwargs) -> Dict[str, Any]:
        """获取美股增强数据"""
        return {
            'vix_sentiment': self.get_vix_sentiment(),
            'reddit_sentiment': self.get_reddit_sentiment(ticker, date),
            'timestamp': datetime.now().isoformat()
        }
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_vix_sentiment(self) -> float:
        """
        获取VIX恐慌指数情绪评分
        
        Returns:
            情绪评分 (-1.0 到 1.0)，VIX越高情绪越负面
        """
        logger.info("获取VIX恐慌指数")
        
        try:
            # 尝试导入yfinance
            try:
                import yfinance as yf
            except ImportError:
                logger.warning("yfinance未安装，无法获取VIX数据")
                return 0.0
            
            # 获取VIX指数
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1d")
            
            if not vix_data.empty:
                current_vix = vix_data['Close'].iloc[-1]
                logger.info(f"当前VIX指数: {current_vix:.2f}")
                
                # VIX情绪映射
                # VIX < 15: 低恐慌 (乐观) -> 0.5 到 1.0
                # VIX 15-25: 正常 -> -0.2 到 0.5
                # VIX > 25: 高恐慌 (悲观) -> -1.0 到-0.2
                if current_vix < 15:
                    sentiment = 0.5 + (15 - current_vix) / 30  # 0.5 到 1.0
                elif current_vix <= 25:
                    sentiment = 0.5 - (current_vix - 15) / 15  # -0.2 到 0.5
                else:
                    sentiment = -0.2 - min((current_vix - 25) / 30, 0.8)  # -1.0 到 -0.2
                
                sentiment = max(-1.0, min(1.0, sentiment))
                logger.info(f"VIX情绪评分: {sentiment:.2f}")
                return sentiment
            
            logger.warning("无法获取VIX数据")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('vix_sentiment', Exception("VIX数据不可用"))
                fallback_data = self.fallback_strategy.get_fallback_data('vix_sentiment')
                return fallback_data.get('score', 0.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"VIX情绪分析失败: {e}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('vix_sentiment', e)
                fallback_data = self.fallback_strategy.get_fallback_data('vix_sentiment')
                return fallback_data.get('score', 0.0)
            
            return 0.0
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_reddit_sentiment(self, ticker: str, date: str) -> float:
        """
        获取Reddit社交媒体情绪评分
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"获取Reddit情绪: {ticker}")
        
        try:
            # 使用现有的reddit_utils
            from tradingagents.dataflows.reddit_utils import fetch_top_from_category
            import os
            
            # 获取Reddit数据
            posts = fetch_top_from_category(
                category="company_news",
                date=date,
                max_limit=20,
                query=ticker,
                data_path=os.path.join("data", "reddit_data")
            )
            
            if posts and len(posts) > 0:
                # 基于upvotes和内容分析情绪
                total_sentiment = 0
                for post in posts:
                    # 简单的关键词分析
                    text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
                    
                    positive_keywords = ['bullish', 'buy', 'moon', 'gain', 'profit', 'up']
                    negative_keywords = ['bearish', 'sell', 'crash', 'loss', 'down', 'risk']
                    
                    pos_count = sum(1 for kw in positive_keywords if kw in text)
                    neg_count = sum(1 for kw in negative_keywords if kw in text)
                    
                    if pos_count + neg_count > 0:
                        post_sentiment = (pos_count - neg_count) / (pos_count + neg_count)
                        # 根据upvotes加权
                        weight = min(post.get('upvotes', 1) / 100, 1.0)
                        total_sentiment += post_sentiment * weight
                
                avg_sentiment = total_sentiment / len(posts) if posts else 0
                avg_sentiment = max(-1.0, min(1.0, avg_sentiment))
                
                logger.info(f"Reddit情绪评分: {avg_sentiment:.2f} (基于{len(posts)}条帖子)")
                return avg_sentiment
            
            logger.warning(f"未找到Reddit数据: {ticker}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('reddit_sentiment', Exception("Reddit数据不可用"))
                fallback_data = self.fallback_strategy.get_fallback_data('reddit_sentiment')
                return fallback_data.get('score', 0.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Reddit情绪分析失败: {e}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('reddit_sentiment', e)
                fallback_data = self.fallback_strategy.get_fallback_data('reddit_sentiment')
                return fallback_data.get('score', 0.0)
            
            return 0.0
    
    def _get_cache_ttl(self) -> int:
        """VIX数据缓存5分钟"""
        return 300


class CNEnhancedDataSource(SentimentDataSource):
    """A股增强数据源"""
    
    def __init__(self, cache_manager=None, toolkit=None, tushare_token: Optional[str] = None, fallback_strategy=None):
        """
        初始化A股增强数据源
        
        Args:
            cache_manager: 缓存管理器
            toolkit: 工具包（保留兼容性，暂未使用）
            tushare_token: TuShare API Token
            fallback_strategy: 降级策略管理器
        """
        super().__init__(cache_manager, fallback_strategy)
        self.toolkit = toolkit
        self.tushare_token = tushare_token
        self._validate_tushare_token()
        logger.info("A股增强数据源初始化完成")
    
    def _validate_tushare_token(self):
        """验证TuShare Token"""
        if self.tushare_token:
            try:
                import tushare as ts
                pro = ts.pro_api(self.tushare_token)
                # 简单测试
                logger.info("TuShare Token验证成功")
                self.tushare_available = True
            except Exception as e:
                logger.warning(f"TuShare Token验证失败: {e}")
                self.tushare_available = False
        else:
            logger.warning("未提供TuShare Token，融资融券数据将不可用")
            self.tushare_available = False
    
    def _fetch_data(self, ticker: str, date: str, **kwargs) -> Dict[str, Any]:
        """获取A股增强数据"""
        return {
            'northbound_flow': self.get_northbound_flow(ticker, date),
            'margin_trading': self.get_margin_trading(ticker, date),
            'volatility_sentiment': self.get_volatility_sentiment(ticker, date),
            'timestamp': datetime.now().isoformat()
        }
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_northbound_flow(self, ticker: str, date: str) -> float:
        """
        获取北向资金流向情绪评分
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"获取北向资金流向: {ticker}")
        
        try:
            import akshare as ak
            
            # 科创板股票(688开头)不在沪深港通标的范围内
            if ticker.startswith('688'):
                logger.info(f"⚠️ 科创板股票 {ticker} 不支持北向资金，返回中性评分")
                return 0.0
            
            # 获取个股北向资金数据
            df = ak.stock_hsgt_individual_em(symbol=ticker)
            
            if df is not None and not df.empty:
                # 获取最近的净流入数据
                recent_flow = df['净流入'].iloc[-1] if '净流入' in df.columns else 0
                
                # 归一化评分
                # 净流入 > 10亿: 强烈看多 (0.7-1.0)
                # 净流入 0-10亿: 温和看多 (0-0.7)
                # 净流出 0-10亿: 温和看空 (-0.7-0)
                # 净流出 > 10亿: 强烈看空 (-1.0--0.7)
                
                if recent_flow > 0:
                    sentiment = min(recent_flow / 1000000000 * 0.7, 1.0)  # 转换为亿元
                else:
                    sentiment = max(recent_flow / 1000000000 * 0.7, -1.0)
                
                logger.info(f"✅ 北向资金情绪评分: {sentiment:.3f} (净流入: {recent_flow/100000000:.2f}亿)")
                return sentiment
            
            logger.warning(f"⚠️ 无法获取北向资金数据: {ticker}，可能不在沪深港通标的范围内")
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ 北向资金分析失败: {e}，返回中性评分")
            return 0.0
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_margin_trading(self, ticker: str, date: str) -> float:
        """
        获取融资融券情绪评分
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"获取融资融券数据: {ticker}")
        
        # 如果TuShare不可用，使用降级方案
        if not self.tushare_available:
            logger.warning("TuShare不可用，使用AKShare市场整体数据")
            return self._get_margin_trading_fallback(date)
        
        try:
            import tushare as ts
            pro = ts.pro_api(self.tushare_token)
            
            # 转换股票代码格式
            ts_code = self._convert_to_tushare_code(ticker)
            
            # 获取融资融券数据
            df = pro.margin_detail(
                ts_code=ts_code,
                start_date=date.replace('-', ''),
                end_date=date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                # 计算融资融券比例变化
                rzye = df['rzye'].iloc[-1] if 'rzye' in df.columns else 0  # 融资余额
                rqye = df['rqye'].iloc[-1] if 'rqye' in df.columns else 0  # 融券余额
                
                # 融资余额增长表示看多，融券余额增长表示看空
                if rzye > 0:
                    sentiment = min(rzye / 1000000000 * 0.5, 1.0)
                else:
                    sentiment = 0.0
                
                logger.info(f"融资融券情绪评分: {sentiment:.2f}")
                return sentiment
            
            logger.warning(f"无法获取融资融券数据: {ticker}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('margin_trading', Exception("融资融券数据不可用"))
                fallback_data = self.fallback_strategy.get_fallback_data('margin_trading')
                return fallback_data.get('score', 0.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"融资融券分析失败: {e}，使用降级方案")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('margin_trading', e)
                fallback_data = self.fallback_strategy.get_fallback_data('margin_trading')
                return fallback_data.get('score', 0.0)
            
            return self._get_margin_trading_fallback(date)
    
    def _get_margin_trading_fallback(self, date: str) -> float:
        """
        融资融券数据降级方案
        
        使用 AKShare 获取市场整体融资融券数据作为参考
        注意：这是市场整体数据，不是个股数据
        """
        try:
            import akshare as ak
            
            # 尝试获取沪深两市融资融券汇总数据
            try:
                # 获取最近的融资融券汇总
                df = ak.stock_margin_sse(start_date=date.replace('-', ''))
                
                if df is not None and not df.empty:
                    # 获取最新一天的数据
                    latest = df.iloc[-1]
                    
                    # 融资余额和融券余额
                    rzye = latest.get('融资余额(元)', 0)
                    rqye = latest.get('融券余额(元)', 0)
                    
                    # 计算融资融券比例变化（相对于前一天）
                    if len(df) > 1:
                        prev = df.iloc[-2]
                        prev_rzye = prev.get('融资余额(元)', rzye)
                        
                        if prev_rzye > 0:
                            # 融资余额增长率
                            growth_rate = (rzye - prev_rzye) / prev_rzye
                            
                            # 转换为情绪评分
                            # 增长 > 2%: 强烈看多 (0.5-1.0)
                            # 增长 0-2%: 温和看多 (0-0.5)
                            # 下降 0-2%: 温和看空 (-0.5-0)
                            # 下降 > 2%: 强烈看空 (-1.0--0.5)
                            sentiment = max(-1.0, min(1.0, growth_rate * 25))
                            
                            logger.info(
                                f"✅ 使用市场整体融资融券数据（降级）: "
                                f"融资余额={rzye/100000000:.2f}亿, "
                                f"增长率={growth_rate*100:.2f}%, "
                                f"情绪评分={sentiment:.3f}"
                            )
                            return sentiment
                    
                    # 如果没有历史数据，返回中性
                    logger.info("使用市场整体融资融券数据（降级），无历史对比，返回中性")
                    return 0.0
                    
            except Exception as e:
                logger.warning(f"获取上交所融资融券数据失败: {e}，尝试深交所数据")
                
                # 尝试深交所数据 (注意：深交所API不支持start_date参数)
                df = ak.stock_margin_szse(date=date.replace('-', ''))
                
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    rzye = latest.get('融资余额(元)', 0)
                    
                    if len(df) > 1:
                        prev = df.iloc[-2]
                        prev_rzye = prev.get('融资余额(元)', rzye)
                        
                        if prev_rzye > 0:
                            growth_rate = (rzye - prev_rzye) / prev_rzye
                            sentiment = max(-1.0, min(1.0, growth_rate * 25))
                            
                            logger.info(
                                f"✅ 使用深交所融资融券数据（降级）: "
                                f"增长率={growth_rate*100:.2f}%, "
                                f"情绪评分={sentiment:.3f}"
                            )
                            return sentiment
                    
                    logger.info("使用深交所融资融券数据（降级），无历史对比，返回中性")
                    return 0.0
            
            logger.warning("无法获取融资融券数据，返回中性评分")
            return 0.0
            
        except Exception as e:
            logger.error(f"融资融券降级方案失败: {e}")
            return 0.0
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_volatility_sentiment(self, ticker: str, date: str) -> float:
        """
        获取波动率情绪评分（基于振幅）
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"计算波动率情绪: {ticker}")
        
        try:
            from tradingagents.dataflows.interface import get_stock_data_by_market
            import re
            
            # 获取最近30天的价格数据
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=30)
            
            price_data_str = get_stock_data_by_market(
                symbol=ticker,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=date
            )
            
            # 从字符串中提取振幅信息
            if price_data_str and isinstance(price_data_str, str) and len(price_data_str) > 100:
                # 方法1: 查找 "振幅: X.XX"
                amplitude_match = re.search(r'振幅[：:]\s*(\d+\.?\d*)', price_data_str)
                
                if amplitude_match:
                    amplitude = float(amplitude_match.group(1))
                else:
                    # 方法2: 从表格数据中提取（振幅在倒数第4列）
                    lines = price_data_str.strip().split('\n')
                    amplitude = None
                    for line in reversed(lines):
                        # 跳过表头和分隔线
                        if '日期' in line or '---' in line or '期间统计' in line:
                            continue
                        # 尝试提取数字（振幅在倒数第4列）
                        parts = line.split()
                        if len(parts) >= 12:  # 确保有足够的列
                            try:
                                # 振幅在倒数第4列（振幅、涨跌幅、涨跌额、换手率）
                                amplitude = float(parts[-4])
                                if 0 < amplitude < 50:  # 合理的振幅范围
                                    break
                                else:
                                    amplitude = None
                            except (ValueError, IndexError):
                                continue
                
                if amplitude is not None:
                    # 振幅映射到情绪
                    # 振幅 > 8%: 高波动（恐慌）-> -0.5 到 -1.0
                    # 振幅 4-8%: 正常波动 -> -0.2 到 0.2
                    # 振幅 < 4%: 低波动（平静）-> 0.2 到 0.5
                    
                    if amplitude > 8:
                        sentiment = -0.5 - min((amplitude - 8) / 10, 0.5)
                    elif amplitude > 4:
                        sentiment = 0.2 - (amplitude - 4) / 4 * 0.4
                    else:
                        sentiment = 0.2 + (4 - amplitude) / 4 * 0.3
                    
                    sentiment = max(-1.0, min(1.0, sentiment))
                    logger.info(f"✅ 波动率情绪评分: {sentiment:.3f} (振幅: {amplitude}%)")
                    return sentiment
                else:
                    logger.warning(f"⚠️ 未找到振幅字段，数据预览: {price_data_str[:200]}")
            else:
                logger.warning(f"⚠️ 价格数据格式异常")
            
            logger.warning(f"无法计算波动率: {ticker}，返回中性评分")
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ 波动率情绪分析失败: {e}")
            return 0.0
    
    def _convert_to_tushare_code(self, ticker: str) -> str:
        """转换股票代码为TuShare格式"""
        ticker = ticker.upper().strip()
        
        if '.' in ticker:
            return ticker
        
        # 6位数字代码
        if len(ticker) == 6 and ticker.isdigit():
            if ticker.startswith('6'):
                return f"{ticker}.SH"
            else:
                return f"{ticker}.SZ"
        
        return ticker
    
    def _get_cache_ttl(self) -> int:
        """A股数据缓存1小时"""
        return 3600


class HKEnhancedDataSource(SentimentDataSource):
    """港股增强数据源"""
    
    def __init__(self, cache_manager=None, toolkit=None, fallback_strategy=None):
        """
        初始化港股增强数据源
        
        Args:
            cache_manager: 缓存管理器
            toolkit: 工具包（保留兼容性，暂未使用）
            fallback_strategy: 降级策略管理器
        """
        super().__init__(cache_manager, fallback_strategy)
        self.toolkit = toolkit
        logger.info("港股增强数据源初始化完成")
    
    def _fetch_data(self, ticker: str, date: str, **kwargs) -> Dict[str, Any]:
        """获取港股增强数据"""
        return {
            'southbound_flow': self.get_southbound_flow(ticker, date),
            'timestamp': datetime.now().isoformat()
        }
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_southbound_flow(self, ticker: str, date: str) -> float:
        """
        获取南向资金流向情绪评分
        
        Args:
            ticker: 股票代码
            date: 日期
            
        Returns:
            情绪评分 (-1.0 到 1.0)
        """
        logger.info(f"获取南向资金流向: {ticker}")
        
        try:
            import akshare as ak
            
            # 获取港股通（沪）数据
            try:
                df_sh = ak.stock_hsgt_hist_em(symbol="港股通（沪）")
                df_sz = ak.stock_hsgt_hist_em(symbol="港股通（深）")
                
                if df_sh is not None and not df_sh.empty:
                    # 获取最近的净流入数据
                    recent_flow_sh = df_sh['当日资金流入'].iloc[-1] if '当日资金流入' in df_sh.columns else 0
                    recent_flow_sz = df_sz['当日资金流入'].iloc[-1] if '当日资金流入' in df_sz.columns else 0
                    
                    total_flow = recent_flow_sh + recent_flow_sz
                    
                    # 归一化评分（单位：亿港元）
                    # 净流入 > 5亿: 内地资金看多 (0.5-1.0)
                    # 净流入 0-5亿: 温和流入 (0-0.5)
                    # 净流出 0-5亿: 温和流出 (-0.5-0)
                    # 净流出 > 5亿: 内地资金看空 (-1.0--0.5)
                    
                    if total_flow > 0:
                        sentiment = min(total_flow / 500000000 * 0.5, 1.0)
                    else:
                        sentiment = max(total_flow / 500000000 * 0.5, -1.0)
                    
                    logger.info(f"南向资金情绪评分: {sentiment:.2f} (净流入: {total_flow/100000000:.2f}亿港元)")
                    return sentiment
                
            except Exception as e:
                logger.warning(f"获取南向资金数据失败: {e}，使用降级方案")
                return self._get_southbound_flow_fallback()
            
            logger.warning(f"无法获取南向资金数据: {ticker}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('southbound_flow', Exception("南向资金数据不可用"))
                fallback_data = self.fallback_strategy.get_fallback_data('southbound_flow')
                return fallback_data.get('score', 0.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"南向资金分析失败: {e}")
            
            # 使用降级策略
            if self.fallback_strategy:
                self.fallback_strategy.record_failure('southbound_flow', e)
                fallback_data = self.fallback_strategy.get_fallback_data('southbound_flow')
                return fallback_data.get('score', 0.0)
            
            return self._get_southbound_flow_fallback()
    
    def _get_southbound_flow_fallback(self) -> float:
        """南向资金数据降级方案"""
        logger.info("使用南向资金降级方案：返回中性评分")
        return 0.0
    
    def _get_cache_ttl(self) -> int:
        """港股数据缓存1小时"""
        return 3600
