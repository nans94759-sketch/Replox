import requests
import json
import logger

# 本地规则备用回复词库
FALLBACK_RULES = {
    "在吗": "在的，请问有什么事吗？",
    "你好": "你好！有什么我可以帮你的？",
    "谢谢": "客气啦！",
    "哈哈": "😁",
}

def get_fallback_reply(latest_messages):
    """
    当 AI 接口不可用时的本地关键字兜底逻辑
    """
    last_text = "".join(latest_messages)
    for kw, reply in FALLBACK_RULES.items():
        if kw in last_text:
            return reply
    return "您好，我现在不方便看手机，稍后会回复您。[自动回复]"

def generate_reply(chat_history, config):
    """
    调用 AI 大模型生成自动回复内容。
    
    :param chat_history: 完整的内容历史记录列表，形如 [{"text": "xxx", "direction": "LEFT/RIGHT"}, ...]
    :param config: 全局配置字典
    :return: 生成的回复文本
    """
    if not config.get("reply_enabled", True):
        logger.warn("自动回复功能已在配置中禁用。")
        return None
        
    api_key = config.get("api_key")
    workspace_id = config.get("workspace_id")
    model = config.get("model", "qwen-plus")
    base_prompt = config.get("system_prompt", "")
    persona = config.get("persona", "")
    knowledge_base = config.get("knowledge_base", "")
    
    # 合成最终的 system prompt：基础行为规则 + 人设 + 知识库
    prompt_parts = []
    if base_prompt:
        prompt_parts.append(f"【基础行为规则】\n{base_prompt}")
    if persona:
        prompt_parts.append(f"【角色人设】\n{persona}")
    if knowledge_base:
        prompt_parts.append(f"【知识库参考资料】\n以下是你应当掌握的知识和信息，请在回复时参考：\n{knowledge_base}")
    
    final_system_prompt = "\n\n".join(prompt_parts) if prompt_parts else base_prompt
    
    # 构造兼容 OpenAI 接口标准的 DashScope 调用
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    # 注入百炼的工作空间 ID
    if workspace_id:
        headers["X-DashScope-WorkSpace"] = workspace_id
        
    # 转换对话历史为模型格式
    # 只取最近的 10 条，避免上下文过长
    recent_history = chat_history[-10:]
    messages = []
    
    if final_system_prompt:
        messages.append({"role": "system", "content": final_system_prompt})
        
    for msg in recent_history:
        role = "user" if msg["direction"] == "LEFT" else "assistant"
        messages.append({"role": role, "content": msg["text"]})
        
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        logger.info(f"正在请求通义千问 AI 生成回复 (模型: {model})...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        
        reply = res_data["choices"][0]["message"]["content"].strip()
        # 清洗可能带有的多余包围引号
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1].strip()
        if reply.startswith('“') and reply.endswith('”'):
            reply = reply[1:-1].strip()
            
        logger.success("AI 回复生成成功。")
        return reply
    except Exception as e:
        logger.error(f"AI 回复生成失败: {e}")
        # 降级到本地规则
        latest_incoming = [m["text"] for m in chat_history if m["direction"] == "LEFT"]
        fallback = get_fallback_reply(latest_incoming)
        logger.warn(f"已降级使用本地兜底回复: {fallback}")
        return fallback
