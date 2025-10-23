"""
Result formatter for analysis results
"""
from typing import Dict, Any
import logging
logger = logging.getLogger('backend.result_formatter')


def format_analysis_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format analysis results for display
    """
    if not results.get('success', False):
        return {
            'error': results.get('error', 'Unknown error'),
            'success': False
        }
    
    state = results.get('state', {})
    decision = results.get('decision', {})
    
    # Format decision
    if isinstance(decision, str):
        # Convert string decision to structured format
        action_translation = {
            'BUY': '买入',
            'SELL': '卖出', 
            'HOLD': '持有',
            'buy': '买入',
            'sell': '卖出',
            'hold': '持有'
        }
        action = action_translation.get(decision.strip(), decision.strip())
        
        formatted_decision = {
            'action': action,
            'confidence': 0.7,
            'risk_score': 0.3,
            'target_price': None,
            'reasoning': f'基于AI分析，建议{decision.strip().upper()}'
        }
    elif isinstance(decision, dict):
        # Handle target price
        target_price = decision.get('target_price')
        if target_price is not None and target_price != 'N/A':
            try:
                if isinstance(target_price, str):
                    clean_price = target_price.replace('$', '').replace('¥', '').replace('￥', '').strip()
                    target_price = float(clean_price) if clean_price and clean_price != 'None' else None
                elif isinstance(target_price, (int, float)):
                    target_price = float(target_price)
                else:
                    target_price = None
            except (ValueError, TypeError):
                target_price = None
        else:
            target_price = None
        
        # Translate action to Chinese
        action_translation = {
            'BUY': '买入',
            'SELL': '卖出',
            'HOLD': '持有',
            'buy': '买入',
            'sell': '卖出',
            'hold': '持有'
        }
        action = decision.get('action', '持有')
        chinese_action = action_translation.get(action, action)
        
        formatted_decision = {
            'action': chinese_action,
            'confidence': decision.get('confidence', 0.5),
            'risk_score': decision.get('risk_score', 0.3),
            'target_price': target_price,
            'reasoning': decision.get('reasoning', '暂无分析推理')
        }
    else:
        formatted_decision = {
            'action': '持有',
            'confidence': 0.5,
            'risk_score': 0.3,
            'target_price': None,
            'reasoning': f'分析结果: {str(decision)}'
        }
    
    # Format state information
    formatted_state = {}
    analysis_keys = [
        'market_report',
        'fundamentals_report', 
        'sentiment_report',
        'news_report',
        'risk_assessment',
        'investment_plan',
        'investment_debate_state',
        'trader_investment_plan',
        'risk_debate_state',
        'final_trade_decision'
    ]
    
    for key in analysis_keys:
        if key in state:
            formatted_state[key] = state[key]
            try:
                val = state[key]
                length = len(val) if isinstance(val, str) else (len(str(val)) if val is not None else 0)
                logger.debug(f"[ResultFormatter] 包含字段: {key}, 长度: {length}")
            except Exception:
                pass
    
    result_payload = {
        'stock_symbol': results.get('stock_symbol'),
        'stock_name': results.get('stock_name'),  # 添加股票名称
        'decision': formatted_decision,
        'state': formatted_state,
        'success': True,
        'analysis_date': results.get('analysis_date'),
        'analysts': results.get('analysts'),
        'research_depth': results.get('research_depth'),
        'llm_provider': results.get('llm_provider', 'dashscope'),
        'llm_model': results.get('llm_model'),
        'metadata': {
            'analysis_date': results.get('analysis_date'),
            'analysts': results.get('analysts'),
            'research_depth': results.get('research_depth'),
            'llm_provider': results.get('llm_provider', 'dashscope'),
            'llm_model': results.get('llm_model')
        }
    }
    try:
        fr_len = len(formatted_state.get('fundamentals_report', '') or '')
        logger.info(f"[ResultFormatter] 基本面报告长度: {fr_len}")
    except Exception:
        pass
    return result_payload
