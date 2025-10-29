"""
市场情绪分析师 - Market Sentiment Analyst
通过整合多维度数据源，提供量化的市场情绪评估

需求: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from datetime import datetime

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
# 导入分析模块日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

logger = get_logger("analysts.sentiment")


def _get_company_name(ticker: str, market_info: dict) -> str:
    """
    根据股票代码获取公司名称
    
    Args:
        ticker: 股票代码
        market_info: 市场信息字典
    
    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)
            
            # 解析股票名称
            if "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.debug(f"从统一接口获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                logger.warning(f"无法从统一接口解析股票名称: {ticker}")
                return f"股票代码{ticker}"
                
        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.improved_hk_utils import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"改进港股工具获取名称失败: {e}")
                # 降级方案：生成友好的默认名称
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"
                
        elif market_info['is_us']:
            # 美股：使用简单映射或返回代码
            us_stock_names = {
                'AAPL': '苹果公司',
                'TSLA': '特斯拉',
                'NVDA': '英伟达',
                'MSFT': '微软',
                'GOOGL': '谷歌',
                'AMZN': '亚马逊',
                'META': 'Meta',
                'NFLX': '奈飞'
            }
            
            company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
            logger.debug(f"美股名称映射: {ticker} -> {company_name}")
            return company_name
            
        else:
            return f"股票{ticker}"
            
    except Exception as e:
        logger.error(f"获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_market_sentiment_analyst(llm, toolkit, progress_callback=None):
    """
    创建市场情绪分析师智能体
    
    Args:
        llm: LLM实例
        toolkit: 工具集
        progress_callback: 进度回调函数
    
    Returns:
        市场情绪分析师节点函数
    
    需求: 1.1, 1.2, 1.3, 1.4
    """
    
    @log_analyst_module("sentiment")
    def market_sentiment_analyst_node(state):
        """
        市场情绪分析师节点
        
        需求: 1.5, 10.5
        """
        start_time = datetime.now()
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        logger.info(f"[市场情绪分析师] 开始分析 {ticker} 的市场情绪，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[市场情绪分析师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 从状态中获取进度回调（优先）或使用传入的回调
        callback = state.get("progress_callback") or progress_callback
        
        # 通知进度回调 - 需求 10.5
        if callback:
            callback(f"📊 市场情绪分析师开始分析 {ticker}", 4)
        
        # 获取市场信息 - 需求 1.2
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[市场情绪分析师] 股票类型: {market_info['market_name']}")
        
        # 获取公司名称
        company_name = _get_company_name(ticker, market_info)
        logger.info(f"[市场情绪分析师] 公司名称: {company_name}")
        
        # 创建情绪分析工具 - 需求 11.3
        from tradingagents.tools.sentiment_tools import create_sentiment_analysis_tool
        sentiment_tool = create_sentiment_analysis_tool(toolkit, market_info)
        
        tools = [sentiment_tool]
        logger.info(f"[市场情绪分析师] 已加载情绪分析工具")
        
        # 系统提示词 - 需求 11.1, 11.2
        system_message = f"""你是一位专业的市场情绪分析师，负责量化和分析市场整体情绪。

你的主要职责：
1. 分析{company_name}（股票代码：{ticker}，{market_info['market_name']}）的市场情绪
2. 整合多维度数据源（新闻、资金流向、波动率、技术动量、社交媒体）
3. 提供0-100的综合情绪评分和情绪等级
4. 生成详细的中文分析报告

🔴 强制要求：
- 你必须调用 get_market_sentiment_data 工具获取真实的情绪数据
- 参数：ticker='{ticker}', date='{current_date}', market_type='{market_info['market_name']}'
- 不允许假设或编造任何数据

📊 分析要求：
- 基于工具返回的真实数据进行分析
- 提供综合情绪评分（0-100）和情绪等级
- 分析各情绪组件的贡献度
- 包含具体的数据点和专业分析
- 当情绪达到极端值时，提供反向指标警告

🌍 语言和格式要求：
- 所有分析内容必须使用中文
- 使用Markdown格式
- 包含表格总结关键指标
- 货币单位使用：{market_info['currency_name']}（{market_info['currency_symbol']}）

现在立即开始调用工具！"""

        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "你是一位专业的市场情绪分析师。"
             "\n🚨 绝对强制要求："
             "\n- 你必须调用 get_market_sentiment_data 工具获取真实数据"
             "\n- 不允许假设或编造任何数据"
             "\n- 必须基于工具返回的数据进行分析"
             "\n"
             "\n可用工具：{tool_names}"
             "\n{system_message}"
             "\n当前日期：{current_date}"
             "\n分析目标：{company_name}（股票代码：{ticker}）"
             "\n请用中文撰写所有分析内容。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(company_name=company_name)
        
        logger.info(f"[市场情绪分析师] 准备调用LLM进行情绪分析")
        
        # 创建LLM链
        chain = prompt | llm.bind_tools(tools)
        
        # 调用LLM
        llm_start_time = datetime.now()
        result = chain.invoke(state["messages"])
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[市场情绪分析师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")
        
        # 使用统一的Google工具调用处理器 - 需求 11.5
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"[市场情绪分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="市场情绪分析",
                specific_requirements="重点关注市场情绪评分、情绪等级、各组件贡献度、极端情绪警告等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="市场情绪分析师"
            )
            
            # 提取情绪评分（从报告中解析或使用默认值）
            sentiment_score = _extract_sentiment_score(report)
            
            # 通知进度回调完成 - 需求 10.5
            if callback:
                preview = report[:500] + "..." if len(report) > 500 else report
                callback(f"✅ 市场情绪分析师完成分析: {ticker}", 4, 7, preview, "市场情绪分析师")
            
            # 返回清洁的AIMessage，避免工具调用循环
            clean_message = AIMessage(content=report)
            
            return {
                "messages": [clean_message],
                "sentiment_report": report,
                "sentiment_score": sentiment_score
            }
        
        else:
            # 非Google模型的处理逻辑
            logger.info(f"[市场情绪分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            
            # 检查工具调用情况
            tool_call_count = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
            logger.info(f"[市场情绪分析师] LLM调用了 {tool_call_count} 个工具")
            
            # 如果有工具调用，需要执行工具并获取结果
            if tool_call_count > 0:
                logger.info(f"[市场情绪分析师] 🔧 执行工具调用...")
                
                try:
                    # 执行工具调用
                    tool_messages = []
                    for tool_call in result.tool_calls:
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                        
                        logger.info(f"[市场情绪分析师] 执行工具: {tool_name}, 原始参数: {tool_args}")
                        
                        # 处理阿里百炼的特殊参数格式
                        # 阿里百炼可能会把参数包装成 {'__arg1': "{'key': 'value'}"}
                        if '__arg1' in tool_args and isinstance(tool_args['__arg1'], str):
                            try:
                                import json
                                import ast
                                # 尝试解析字符串参数
                                arg_str = tool_args['__arg1']
                                # 先尝试JSON解析
                                try:
                                    parsed_args = json.loads(arg_str)
                                except:
                                    # 如果JSON失败，尝试ast.literal_eval
                                    parsed_args = ast.literal_eval(arg_str)
                                
                                tool_args = parsed_args
                                logger.info(f"[市场情绪分析师] 🔧 解析后的参数: {tool_args}")
                            except Exception as e:
                                logger.warning(f"[市场情绪分析师] ⚠️ 参数解析失败: {e}，使用原始参数")
                        
                        # 找到对应的工具并执行
                        for tool in tools:
                            if tool.name == tool_name:
                                tool_result = tool.invoke(tool_args)
                                tool_messages.append(tool_result)
                                logger.info(f"[市场情绪分析师] ✅ 工具执行成功，结果长度: {len(str(tool_result))} 字符")
                                break
                    
                    # 使用工具结果作为报告
                    if tool_messages:
                        report = str(tool_messages[0])
                        logger.info(f"[市场情绪分析师] ✅ 使用工具输出作为报告，长度: {len(report)} 字符")
                    else:
                        # 如果工具执行失败，使用LLM的原始输出
                        report = result.content if hasattr(result, 'content') else str(result)
                        logger.warning(f"[市场情绪分析师] ⚠️ 工具执行失败，使用LLM原始输出")
                        
                except Exception as e:
                    logger.error(f"[市场情绪分析师] ❌ 工具执行失败: {e}")
                    report = result.content if hasattr(result, 'content') else str(result)
                    
            elif tool_call_count == 0:
                logger.warning(f"[市场情绪分析师] ⚠️ {llm.__class__.__name__} 没有调用任何工具，启动补救机制...")
                
                try:
                    # 强制调用情绪分析工具
                    logger.info(f"[市场情绪分析师] 🔧 强制调用情绪分析工具...")
                    sentiment_data = sentiment_tool.invoke({
                        'ticker': ticker,
                        'date': current_date,
                        'market_type': market_info['market_name']
                    })
                    
                    if sentiment_data and len(str(sentiment_data)) > 100:
                        logger.info(f"[市场情绪分析师] ✅ 强制获取情绪数据成功: {len(str(sentiment_data))} 字符")
                        
                        # 基于真实情绪数据重新生成分析
                        forced_prompt = f"""
你是一位专业的市场情绪分析师。请基于以下最新获取的情绪数据，对股票 {ticker} 进行详细的情绪分析：

=== 市场情绪数据 ===
{sentiment_data}

=== 分析要求 ===
{system_message}

请基于上述真实情绪数据撰写详细的中文分析报告。
"""
                        
                        logger.info(f"[市场情绪分析师] 🔄 基于强制获取的情绪数据重新生成完整分析...")
                        forced_result = llm.invoke([{"role": "user", "content": forced_prompt}])
                        
                        if hasattr(forced_result, 'content') and forced_result.content:
                            report = forced_result.content
                            logger.info(f"[市场情绪分析师] ✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                        else:
                            logger.warning(f"[市场情绪分析师] ⚠️ 强制补救失败，使用原始结果")
                            report = result.content if hasattr(result, 'content') else str(result)
                    else:
                        logger.warning(f"[市场情绪分析师] ⚠️ 情绪分析工具获取失败，使用原始结果")
                        report = result.content if hasattr(result, 'content') else str(result)
                        
                except Exception as e:
                    logger.error(f"[市场情绪分析师] ❌ 强制补救过程失败: {e}")
                    report = result.content if hasattr(result, 'content') else str(result)
            else:
                # 有工具调用，直接使用结果
                report = result.content if hasattr(result, 'content') else str(result)
            
            # 提取情绪评分
            sentiment_score = _extract_sentiment_score(report)
            
            total_time_taken = (datetime.now() - start_time).total_seconds()
            logger.info(f"[市场情绪分析师] 情绪分析完成，总耗时: {total_time_taken:.2f}秒")
            
            # 返回清洁的AIMessage，避免工具调用循环
            clean_message = AIMessage(content=report)
            
            # 通知进度回调完成 - 需求 10.5
            if callback:
                preview = report[:500] + "..." if len(report) > 500 else report
                callback(f"✅ 市场情绪分析师完成分析: {ticker}", 4, 7, preview, "市场情绪分析师")
            
            return {
                "messages": [clean_message],
                "sentiment_report": report,
                "sentiment_score": sentiment_score
            }
    
    return market_sentiment_analyst_node


def _extract_sentiment_score(report: str) -> float:
    """
    从报告中提取情绪评分
    
    Args:
        report: 情绪分析报告
    
    Returns:
        情绪评分（0-100），如果无法提取则返回50（中性）
    """
    try:
        import re
        
        # 尝试匹配各种可能的评分格式
        patterns = [
            # 中文格式
            r'综合情绪评分[：:]\s*(\d+\.?\d*)\s*/?\s*100',  # 综合情绪评分: 65.5 / 100
            r'综合情绪评分[：:]\s*(\d+\.?\d*)',              # 综合情绪评分: 65.5
            r'情绪评分[：:]\s*(\d+\.?\d*)\s*/?\s*100',      # 情绪评分: 65.5 / 100
            r'情绪评分[：:]\s*(\d+\.?\d*)',                  # 情绪评分: 65.5
            r'市场情绪[：:]\s*(\d+\.?\d*)',                  # 市场情绪: 65.5
            r'评分[：:]\s*(\d+\.?\d*)\s*/?\s*100',          # 评分: 65.5 / 100
            r'评分[：:]\s*(\d+\.?\d*)',                      # 评分: 65.5
            # 英文格式
            r'sentiment\s+score[：:]\s*(\d+\.?\d*)',        # sentiment score: 65.5
            r'score[：:]\s*(\d+\.?\d*)\s*/?\s*100',         # score: 65.5 / 100
            # 数字后跟"分"
            r'(\d+\.?\d*)\s*分',                            # 65.5分
            # Markdown表格格式
            r'\*\*综合情绪评分\*\*[：:]\s*(\d+\.?\d*)',     # **综合情绪评分**: 65.5
            r'\*\*情绪评分\*\*[：:]\s*(\d+\.?\d*)',         # **情绪评分**: 65.5
        ]
        
        for pattern in patterns:
            match = re.search(pattern, report, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                # 确保评分在有效范围内
                if 0 <= score <= 100:
                    logger.info(f"✅ 从报告中提取情绪评分: {score}")
                    return score
        
        # 尝试查找报告中的任何0-100之间的数字（作为最后的备选）
        all_numbers = re.findall(r'\b(\d+\.?\d*)\b', report)
        for num_str in all_numbers:
            num = float(num_str)
            if 0 <= num <= 100 and num != 50:  # 排除50，因为那是默认值
                logger.info(f"⚠️ 使用报告中找到的数字作为情绪评分: {num}")
                return num
        
        # 如果无法提取，返回中性评分
        logger.warning("⚠️ 无法从报告中提取情绪评分，返回中性评分50")
        return 50.0
        
    except Exception as e:
        logger.error(f"❌ 提取情绪评分失败: {e}")
        return 50.0