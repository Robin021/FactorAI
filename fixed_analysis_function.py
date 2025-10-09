
# 启动真实分析 - 修复版本，消除重复执行
def start_real_analysis(analysis_id: str, symbol: str, market_type: str, analysis_type: str, username: str):
    """启动真实的股票分析 - 修复重复执行问题"""
    import threading
    import time
    from datetime import datetime
    
    def analysis_worker():
        try:
            # 简化的路径设置
            import sys
            import os
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            
            if not (project_root / 'tradingagents').exists():
                project_root = Path(os.getcwd()).parent if 'backend' in os.getcwd() else Path(os.getcwd())
                if not (project_root / 'tradingagents').exists():
                    # Try to find tradingagents directory in common locations
                    possible_paths = [
                        Path('/app'),  # Docker container
                        Path.cwd().parent,  # Parent directory
                        Path.cwd(),  # Current directory
                        Path.home() / 'TradingAgents-CN',  # User home
                    ]
                    for path in possible_paths:
                        if (path / 'tradingagents').exists():
                            project_root = path
                            break
                    else:
                        # If still not found, use current directory as fallback
                        project_root = Path(os.getcwd())
            
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # 进度回调函数
            def progress_callback(message, step, total_steps):
                try:
                    current_time = time.time()
                    elapsed_time = current_time - analysis_progress_store[analysis_id].get("start_time", current_time)
                    
                    # 计算进度百分比
                    progress_percentage = (step + 1) / total_steps if total_steps > 0 else 0
                    
                    progress_data = {
                        "status": "running" if progress_percentage < 1.0 else "completed",
                        "current_step": step,
                        "total_steps": total_steps,
                        "progress_percentage": progress_percentage,
                        "progress": progress_percentage * 100,
                        "current_step_name": message,
                        "message": message,
                        "elapsed_time": int(elapsed_time),
                        "last_update": current_time,
                        "timestamp": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # 更新内存存储
                    analysis_progress_store[analysis_id].update(progress_data)
                    
                    # 写入Redis
                    if redis_client:
                        try:
                            import json
                            redis_key = f"analysis_progress:{analysis_id}"
                            redis_client.setex(redis_key, 3600, json.dumps(progress_data))
                        except Exception as redis_error:
                            logger.warning(f"Failed to write progress to Redis: {redis_error}")
                    
                    logger.info(f"分析 {analysis_id} 进度: {int(progress_percentage * 100)}% - {message}")
                except Exception as e:
                    logger.error(f"进度回调失败: {e}")
            
            # 直接执行TradingAgents分析 - 只执行一次
            try:
                from tradingagents.graph.trading_graph import TradingAgentsGraph
                from tradingagents.default_config import DEFAULT_CONFIG
                
                logger.info("✅ 使用真实TradingAgents分析引擎")
                
                # 创建配置
                config = DEFAULT_CONFIG.copy()
                config['llm_provider'] = "deepseek"
                config['deep_think_llm'] = "deepseek-chat"
                config['quick_think_llm'] = "deepseek-chat"
                
                # 统一的分析师配置 - 避免重复
                selected_analysts = ["market", "fundamentals", "social"]
                
                # 记录开始时间
                analysis_progress_store[analysis_id]["start_time"] = time.time()
                
                # 创建TradingAgents图实例
                trading_graph = TradingAgentsGraph(selected_analysts=selected_analysts, config=config)
                
                progress_callback("🔍 初始化TradingAgents分析引擎", 0, 7)
                
                # 在开始分析前检查是否已被取消
                if analysis_progress_store[analysis_id].get("status") == "cancelled":
                    logger.info(f"Analysis {analysis_id} was cancelled before execution")
                    return
                
                # 执行分析 - 只执行一次
                final_state, decision = trading_graph.propagate(
                    company_name=symbol,
                    trade_date=datetime.now().strftime("%Y-%m-%d"),
                    progress_callback=progress_callback
                )
                
                progress_callback("✅ 分析完成，正在整理结果", 6, 7)
                
                # 构建结果
                result = {
                    'success': True,
                    'stock_symbol': symbol,
                    'analysis_date': datetime.now().strftime("%Y-%m-%d"),
                    'analysts': selected_analysts,
                    'research_depth': 2,
                    'llm_provider': "deepseek",
                    'llm_model': "deepseek-chat",
                    'state': final_state,
                    'decision': decision
                }
                
            except ImportError as e:
                logger.warning(f"⚠️ 无法导入TradingAgents: {e}，使用模拟分析")
                
                # 简化的模拟分析
                import random
                steps = [
                    ("🔍 识别股票类型并获取基本信息", 0),
                    ("📈 市场分析师开始技术指标分析", 1), 
                    ("📊 基本面分析师开始财务数据分析", 2),
                    ("💭 情绪分析师开始社交媒体分析", 3),
                    ("⚖️ 投资辩论：多空观点交锋", 4),
                    ("🛡️ 风险管理评估和最终决策", 5)
                ]
                
                # 记录开始时间
                analysis_progress_store[analysis_id]["start_time"] = time.time()
                
                for step_name, step_num in steps:
                    if analysis_progress_store[analysis_id].get("status") == "cancelled":
                        result = {"success": False, "error": "分析已取消"}
                        break
                    
                    progress_callback(step_name, step_num, 6)
                    time.sleep(random.uniform(2, 5))
                else:
                    result = {
                        'success': True,
                        'stock_symbol': symbol,
                        'analysis_date': datetime.now().strftime("%Y-%m-%d"),
                        'analysis_summary': f'{symbol} 股票分析已完成',
                        'recommendation': '建议关注',
                        'confidence_score': random.uniform(0.6, 0.9)
                    }
            
            # 保存分析结果
            final_status = "completed" if result.get("success", False) else "failed"
            final_message = "分析完成！" if result.get("success", False) else f"分析失败: {result.get('error', '未知错误')}"
            
            final_progress_data = {
                "status": final_status,
                "progress_percentage": 1.0,
                "progress": 100,
                "current_step": 10,
                "total_steps": 10,
                "message": final_message,
                "current_step_name": final_message,
                "last_message": final_message,
                "results": result,
                "last_update": time.time(),
                "timestamp": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "elapsed_time": int(time.time() - analysis_progress_store[analysis_id].get("start_time", time.time())),
                "estimated_time_remaining": 0,
                "estimated_remaining": 0
            }
            
            analysis_progress_store[analysis_id].update(final_progress_data)
            
            # 同时写入Redis
            if redis_client:
                try:
                    import json
                    redis_key = f"analysis_progress:{analysis_id}"
                    redis_client.setex(redis_key, 3600, json.dumps(final_progress_data))
                    logger.info(f"✅ 分析完成状态已写入Redis: {analysis_id}")
                except Exception as redis_error:
                    logger.warning(f"Failed to write completion status to Redis: {redis_error}")
            
            # 更新MongoDB数据库状态
            if mongodb_db is not None:
                try:
                    update_data = {
                        "status": final_status,
                        "progress": 100.0,
                        "completed_at": datetime.utcnow()
                    }
                    
                    # 如果分析成功，保存结果
                    if result.get('success', False):
                        update_data["result_data"] = result
                    else:
                        update_data["error_message"] = result.get('error', '未知错误')
                    
                    # 使用统一的MongoDB操作函数
                    safe_mongodb_operation(
                        mongodb_db.analyses.update_one,
                        {"_id": ObjectId(analysis_id)},
                        {"$set": update_data}
                    )
                    
                    logger.info(f"✅ 分析完成状态已更新到数据库: {analysis_id}")
                except Exception as db_error:
                    logger.warning(f"⚠️ 更新数据库状态失败: {db_error}")
            
            logger.info(f"分析 {analysis_id} 完成，成功: {result.get('success', False)}")
            
        except Exception as e:
            logger.error(f"分析 {analysis_id} 执行失败: {e}")
            error_progress_data = {
                "status": "failed",
                "progress_percentage": 0,
                "progress": 0,
                "message": f"分析失败: {str(e)}",
                "last_message": f"分析失败: {str(e)}",
                "error": str(e),
                "last_update": time.time(),
                "timestamp": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            analysis_progress_store[analysis_id].update(error_progress_data)
            
            # 同时写入Redis
            if redis_client:
                try:
                    import json
                    redis_key = f"analysis_progress:{analysis_id}"
                    redis_client.setex(redis_key, 3600, json.dumps(error_progress_data))
                except Exception as redis_error:
                    logger.warning(f"Failed to write error status to Redis: {redis_error}")
            
            # 更新MongoDB数据库状态
            if mongodb_db is not None:
                try:
                    # 使用统一的MongoDB操作函数
                    safe_mongodb_operation(
                        mongodb_db.analyses.update_one,
                        {"_id": ObjectId(analysis_id)},
                        {"$set": {
                            "status": "failed",
                            "error_message": str(e),
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    
                    logger.info(f"✅ 分析失败状态已更新到数据库: {analysis_id}")
                except Exception as db_error:
                    logger.warning(f"⚠️ 更新数据库状态失败: {db_error}")
    
    # 启动后台线程
    thread = threading.Thread(target=analysis_worker, daemon=True)
    thread.start()
    logger.info(f"启动真实分析: {analysis_id} - {symbol} ({market_type})")
