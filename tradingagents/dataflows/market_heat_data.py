"""
市场热度数据获取模块

该模块负责获取用于计算市场热度的各项指标数据：
1. 市场整体成交量数据
2. 涨停/跌停家数统计
3. 市场宽度（上涨股票占比）
4. 市场平均换手率
5. 市场波动率
6. 资金流向数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


class MarketHeatDataSource:
    """市场热度数据源"""
    

    
    @staticmethod
    def get_market_overview(date: Optional[str] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        获取市场整体概况数据
        
        Args:
            date: 日期，格式 YYYY-MM-DD，默认为今天
            max_retries: 最大重试次数
        
        Returns:
            {
                'volume_ratio': float,      # 成交量放大倍数
                'limit_up_ratio': float,    # 涨停家数占比
                'turnover_rate': float,     # 平均换手率
                'market_breadth': float,    # 市场宽度（上涨占比）
                'volatility': float,        # 市场波动率
                'money_flow': float,        # 资金流向
                'date': str                 # 数据日期
            }
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        else:
            date = date.replace("-", "")
        
        logger.info(f"📊 开始获取市场概况数据，日期: {date}")
        
        # 尝试多次获取数据
        last_error = None
        for attempt in range(max_retries):
            try:
                # 添加延迟避免频繁请求
                if attempt > 0:
                    wait_time = min(attempt * 2, 5)  # 最多等待5秒
                    logger.info(f"   等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                
                # 使用 stock_zh_a_spot (测试显示这个接口可用)
                logger.info(f"📊 尝试获取市场数据 (第{attempt + 1}次尝试)")
                df = ak.stock_zh_a_spot()
                
                if df is None or df.empty:
                    raise Exception("返回的数据为空")
                
                logger.info(f"✅ 成功获取 {len(df)} 只股票的数据")
                
                # 计算各项指标
                total_stocks = len(df)
                
                # 确保涨跌幅列存在且为数值类型
                if '涨跌幅' not in df.columns:
                    raise Exception("数据中缺少'涨跌幅'列")
                
                # 转换涨跌幅为数值类型（可能是字符串）
                df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
                
                # 1. 涨停家数占比
                # 涨停判断：涨跌幅 >= 9.8%（考虑误差）
                limit_up_count = len(df[df['涨跌幅'] >= 9.8])
                limit_up_ratio = limit_up_count / total_stocks if total_stocks > 0 else 0.0
                
                # 2. 市场宽度（上涨股票占比）
                up_count = len(df[df['涨跌幅'] > 0])
                market_breadth = up_count / total_stocks if total_stocks > 0 else 0.5
                
                # 3. 平均换手率
                if '换手率' in df.columns:
                    df['换手率'] = pd.to_numeric(df['换手率'], errors='coerce')
                    avg_turnover = df['换手率'].mean()
                else:
                    # stock_zh_a_spot 没有换手率列，使用市场平均值
                    avg_turnover = 8.0  # A股市场平均换手率约8%
                
                # 4. 成交量放大倍数（需要历史数据对比）
                volume_ratio = MarketHeatDataSource._calculate_volume_ratio(df, date)
                
                # 5. 市场波动率（用涨跌幅标准差近似）
                volatility = df['涨跌幅'].std()
                
                # 6. 资金流向（用主力净流入占比近似）
                money_flow = MarketHeatDataSource._calculate_money_flow(df)
                
                logger.info(
                    f"✅ 市场概况获取成功: "
                    f"涨停={limit_up_count}家({limit_up_ratio:.2%}), "
                    f"上涨={up_count}家({market_breadth:.2%}), "
                    f"换手率={avg_turnover:.2f}%, "
                    f"波动率={volatility:.2f}%"
                )
                
                return {
                    'volume_ratio': volume_ratio,
                    'limit_up_ratio': limit_up_ratio,
                    'turnover_rate': avg_turnover,
                    'market_breadth': market_breadth,
                    'volatility': volatility,
                    'money_flow': money_flow,
                    'date': date,
                    'stats': {
                        'total_stocks': total_stocks,
                        'limit_up_count': limit_up_count,
                        'up_count': up_count,
                        'down_count': len(df[df['涨跌幅'] < 0]),
                        'flat_count': len(df[df['涨跌幅'] == 0])
                    }
                }
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ 获取市场数据失败 (第{attempt + 1}次尝试): {e}")
                    continue
        
        # 所有尝试都失败了，尝试使用指数数据作为后备
        if last_error:
            logger.error(f"❌ 获取市场概况数据失败 (已重试{max_retries}次): {last_error}")
            logger.info("📊 尝试使用指数数据作为后备方案...")
            
            try:
                index_data = MarketHeatDataSource._get_data_from_index(date)
                if index_data:
                    logger.info("✅ 成功从指数数据获取市场概况")
                    return index_data
            except Exception as index_error:
                logger.warning(f"⚠️ 指数数据获取也失败: {index_error}")
            
            # 判断失败原因并提供建议
            error_msg = str(last_error)
            error_lower = error_msg.lower()
            if "decode" in error_lower and "<" in error_msg:
                reason = "数据源返回HTML而非数据（可能是访问限制或服务器错误）"
                suggestion = "等待几分钟后重试，或检查是否需要代理访问"
            elif "connection" in error_lower or "timeout" in error_lower:
                reason = "网络连接失败或超时"
                suggestion = "检查网络连接，或稍后重试"
            elif "remote end closed" in error_lower:
                reason = "数据源服务器主动断开连接（可能是访问频率限制）"
                suggestion = "等待几分钟后重试"
            elif "date" in error_lower or date > datetime.now().strftime("%Y%m%d"):
                reason = f"日期无效或为未来日期（{date}）"
                suggestion = "检查系统日期设置"
            else:
                reason = "数据源不可用或返回错误"
                suggestion = "检查akshare版本或数据源状态"
                
                logger.warning(
                    f"⚠️ 使用默认市场热度数据（假设正常市场，热度=50分）\n"
                    f"   原因：{reason}\n"
                    f"   影响：将使用标准风险控制策略（1轮辩论，标准仓位）\n"
                    f"   建议：{suggestion}"
                )
                return MarketHeatDataSource._get_default_data(date)
    
    @staticmethod
    def _calculate_volume_ratio(df: pd.DataFrame, date: str) -> float:
        """
        计算成交量放大倍数
        
        通过对比当日总成交量与历史平均成交量
        """
        try:
            # 当日总成交量（亿元）
            # stock_zh_a_spot 可能有 '成交额' 或 '成交量' 列
            volume_col = None
            if '成交额' in df.columns:
                volume_col = '成交额'
            elif '成交量' in df.columns:
                volume_col = '成交量'
            else:
                logger.debug("数据中没有成交额/成交量列，使用默认值")
                return 1.0
            
            df[volume_col] = pd.to_numeric(df[volume_col], errors='coerce')
            today_volume = df[volume_col].sum() / 100000000  # 转换为亿元
            
            # 获取历史20日平均成交量
            try:
                # 获取上证指数历史数据作为市场整体参考
                end_date = datetime.strptime(date, "%Y%m%d")
                start_date = end_date - timedelta(days=30)
                
                hist_df = ak.stock_zh_index_daily(symbol="sh000001")
                hist_df['日期'] = pd.to_datetime(hist_df['日期'])
                
                # 筛选最近20个交易日
                hist_df = hist_df[
                    (hist_df['日期'] >= start_date) & 
                    (hist_df['日期'] <= end_date)
                ].tail(20)
                
                if len(hist_df) > 0 and '成交额' in hist_df.columns:
                    avg_volume = hist_df['成交额'].mean() / 100000000
                    if avg_volume > 0:
                        ratio = today_volume / avg_volume
                        return min(5.0, max(0.1, ratio))  # 限制在0.1-5.0范围
                
            except Exception as e:
                logger.debug(f"获取历史成交量失败: {e}")
            
            # 如果无法获取历史数据，返回默认值
            return 1.0
            
        except Exception as e:
            logger.debug(f"计算成交量放大倍数失败: {e}")
            return 1.0
    
    @staticmethod
    def _calculate_money_flow(df: pd.DataFrame) -> float:
        """
        计算资金流向
        
        使用主力净流入占总成交额的比例
        返回值范围：-1.0 到 1.0
        """
        try:
            # stock_zh_a_spot 通常没有主力净流入数据
            # 直接用涨跌家数比例近似资金流向
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            total = up_count + down_count
            
            if total > 0:
                flow_ratio = (up_count - down_count) / total
                return flow_ratio
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"计算资金流向失败: {e}")
            return 0.0
    
    @staticmethod
    def _get_data_from_index(date: str) -> Optional[Dict[str, Any]]:
        """
        从指数数据估算市场热度（后备方案）
        
        使用上证、深证、创业板指数的数据来估算市场整体情况
        """
        try:
            # 获取三大指数的最新数据
            indices = {
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指'
            }
            
            index_data = []
            for symbol, name in indices.items():
                try:
                    df = ak.stock_zh_index_daily(symbol=symbol)
                    if not df.empty:
                        latest = df.iloc[-1]
                        
                        # 计算涨跌幅：(close - open) / open * 100
                        if 'close' in latest.index and 'open' in latest.index:
                            close_price = float(latest['close'])
                            open_price = float(latest['open'])
                            if open_price > 0:
                                change_pct = (close_price - open_price) / open_price * 100
                                index_data.append(change_pct)
                                logger.info(f"✅ {name}: 涨跌幅={change_pct:.2f}%")
                            else:
                                logger.warning(f"⚠️ {name}: 开盘价为0")
                        else:
                            logger.warning(f"⚠️ {name}: 缺少收盘价或开盘价")
                except Exception as e:
                    logger.warning(f"❌ 获取{name}失败: {e}")
                    continue
            
            if not index_data:
                logger.debug("无法从指数数据获取涨跌幅")
                return None
            
            # 从指数数据估算市场指标
            # 1. 市场宽度：根据上涨指数占比
            up_indices = sum(1 for change in index_data if change > 0)
            market_breadth = up_indices / len(index_data) if index_data else 0.5
            
            # 2. 市场波动率：指数涨跌幅的标准差
            volatility = pd.Series(index_data).std() if index_data else 3.0
            
            # 3. 资金流向：根据指数涨跌
            avg_change = sum(index_data) / len(index_data) if index_data else 0
            money_flow = max(-1.0, min(1.0, avg_change / 5.0))  # 归一化
            
            # 4. 其他指标使用默认值
            logger.info(f"📊 从指数数据估算: 市场宽度={market_breadth:.2%}, 波动率={volatility:.2f}%")
            
            return {
                'volume_ratio': 1.5,  # 使用默认值
                'limit_up_ratio': 0.03,  # 使用默认值
                'turnover_rate': 10.0,  # 使用默认值
                'market_breadth': market_breadth,
                'volatility': abs(volatility),
                'money_flow': money_flow,
                'date': date,
                'stats': {
                    'total_stocks': 0,
                    'limit_up_count': 0,
                    'up_count': 0,
                    'down_count': 0,
                    'flat_count': 0
                },
                'data_source': 'index_estimation'
            }
            
        except Exception as e:
            logger.debug(f"从指数数据估算失败: {e}")
            return None
    
    @staticmethod
    def _get_default_data(date: str) -> Dict[str, Any]:
        """
        返回默认数据（当无法获取实时数据时）
        
        ⚠️ 重要：默认值代表"正常"市场状态（热度评分=50分）
        
        设计理念：
        - 在无法获取实时数据时，假设市场处于正常状态
        - 避免过于保守（错失机会）或过于激进（增加风险）
        - 使用标准的1轮风险辩论和标准仓位配置
        
        参数说明：
        - volume_ratio=1.8: 成交量放大1.8倍（正常偏活跃）
        - limit_up_ratio=0.04: 4%涨停（正常活跃市场）
        - turnover_rate=11.0: 11%换手率（活跃）
        - market_breadth=0.6: 60%上涨（偏多方）
        - volatility=3.0: 3%波动（正常）
        - money_flow=0.2: 资金净流入（正常）
        
        这组参数经过优化，确保热度评分=50分（正常市场）
        """
        return {
            'volume_ratio': 1.8,
            'limit_up_ratio': 0.04,
            'turnover_rate': 11.0,
            'market_breadth': 0.6,
            'volatility': 3.0,
            'money_flow': 0.2,
            'date': date,
            'stats': {
                'total_stocks': 0,
                'limit_up_count': 0,
                'up_count': 0,
                'down_count': 0,
                'flat_count': 0
            }
        }
    
    @staticmethod
    def get_market_heat_summary(date: Optional[str] = None) -> str:
        """
        获取市场热度摘要（文本格式）
        
        Args:
            date: 日期，格式 YYYY-MM-DD
        
        Returns:
            市场热度摘要文本
        """
        data = MarketHeatDataSource.get_market_overview(date)
        
        summary = f"""
## 市场热度概况 ({data['date']})

### 📊 核心指标
- **成交量放大倍数**: {data['volume_ratio']:.2f}x
- **涨停家数占比**: {data['limit_up_ratio']:.2%} ({data['stats']['limit_up_count']}家)
- **平均换手率**: {data['turnover_rate']:.2f}%
- **市场宽度**: {data['market_breadth']:.2%} (上涨{data['stats']['up_count']}家 / 总计{data['stats']['total_stocks']}家)
- **市场波动率**: {data['volatility']:.2f}%
- **资金流向**: {data['money_flow']:.2f} ({'流入' if data['money_flow'] > 0 else '流出'})

### 📈 涨跌分布
- 上涨: {data['stats']['up_count']}家
- 下跌: {data['stats']['down_count']}家
- 平盘: {data['stats']['flat_count']}家
"""
        
        return summary.strip()


def get_market_heat_for_analysis(date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取用于分析的市场热度数据（便捷函数）
    
    Args:
        date: 日期，格式 YYYY-MM-DD
    
    Returns:
        市场热度数据字典
    """
    return MarketHeatDataSource.get_market_overview(date)


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("测试市场热度数据获取")
    print("=" * 80)
    
    # 获取今日市场数据
    data = MarketHeatDataSource.get_market_overview()
    
    print("\n📊 市场数据:")
    for key, value in data.items():
        if key != 'stats':
            print(f"   {key}: {value}")
    
    print("\n📈 统计信息:")
    for key, value in data['stats'].items():
        print(f"   {key}: {value}")
    
    # 获取摘要
    print("\n" + "=" * 80)
    summary = MarketHeatDataSource.get_market_heat_summary()
    print(summary)
    print("=" * 80)
