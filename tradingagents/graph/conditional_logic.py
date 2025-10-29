# TradingAgents/graph/conditional_logic.py

from tradingagents.agents.utils.agent_states import AgentState

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1, enable_dynamic_risk_rounds=True):
        """
        Initialize with configuration parameters.
        
        Args:
            max_debate_rounds: 投资辩论最大轮次
            max_risk_discuss_rounds: 风险辩论基础轮次（当禁用动态调整时使用）
            enable_dynamic_risk_rounds: 是否启用基于市场热度的动态风险辩论轮次
        """
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds
        self.enable_dynamic_risk_rounds = enable_dynamic_risk_rounds
        
        logger.info(
            f"🔧 ConditionalLogic初始化: "
            f"投资辩论={max_debate_rounds}轮, "
            f"风险辩论基础={max_risk_discuss_rounds}轮, "
            f"动态调整={'启用' if enable_dynamic_risk_rounds else '禁用'}"
        )

    def should_continue_market(self, state: AgentState):
        """Determine if market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_social"
        return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"

    def should_continue_technical(self, state: AgentState):
        """Determine if technical analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_technical"
        return "Msg Clear Technical"

    def should_continue_sentiment(self, state: AgentState):
        """Determine if sentiment analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_sentiment"
        return "Msg Clear Sentiment"

    def should_continue_market_sentiment(self, state: AgentState):
        """Determine if market sentiment analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_market_sentiment"
        return "Msg Clear Market_sentiment"

    def should_continue_risk(self, state: AgentState):
        """Determine if risk analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]

        # 只有AIMessage才有tool_calls属性
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_risk"
        return "Msg Clear Risk"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""

        if (
            state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds
        ):  # 3 rounds of back-and-forth between 2 agents
            return "Research Manager"
        if state["investment_debate_state"]["current_response"].startswith("Bull"):
            return "Bear Researcher"
        return "Bull Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """
        Determine if risk analysis should continue.
        
        根据市场热度动态调整风险辩论轮次：
        - 市场热度 >= 60: 2轮辩论（充分讨论机会）
        - 市场热度 < 60: 1轮辩论（快速决策）
        """
        # 获取动态风险辩论轮次
        if self.enable_dynamic_risk_rounds and "market_heat_score" in state:
            heat_score = state.get("market_heat_score", 50.0)
            
            # 根据市场热度动态调整轮次
            if heat_score >= 60:
                # 市场火热或沸腾：2轮辩论
                max_rounds = 2
                logger.debug(
                    f"🌡️ 市场热度{heat_score:.1f}（火热），"
                    f"风险辩论轮次: 2轮（充分讨论）"
                )
            else:
                # 市场正常、冷淡或极冷：1轮辩论
                max_rounds = 1
                logger.debug(
                    f"🌡️ 市场热度{heat_score:.1f}（冷淡），"
                    f"风险辩论轮次: 1轮（快速决策）"
                )
        else:
            # 未启用动态调整或无市场热度数据，使用基础轮次
            max_rounds = self.max_risk_discuss_rounds
            if self.enable_dynamic_risk_rounds:
                logger.warning(
                    "⚠️ 动态风险辩论已启用但未找到市场热度数据，"
                    f"使用基础轮次: {max_rounds}轮"
                )
        
        # 判断是否继续辩论（3个分析师轮流发言，所以是 3 * max_rounds）
        current_count = state["risk_debate_state"]["count"]
        if current_count >= 3 * max_rounds:
            logger.info(
                f"✅ 风险辩论完成: {current_count}次发言 "
                f"(目标: {3 * max_rounds}次, {max_rounds}轮)"
            )
            return "Risk Judge"
        
        # 确定下一个发言者
        if state["risk_debate_state"]["latest_speaker"].startswith("Risky"):
            return "Safe Analyst"
        if state["risk_debate_state"]["latest_speaker"].startswith("Safe"):
            return "Neutral Analyst"
        return "Risky Analyst"
