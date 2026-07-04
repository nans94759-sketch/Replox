import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    # AI 大模型 API 配置
    "api_key": "",
    "workspace_id": "",
    "base_url": "https://dashscope.aliyuncs.com",
    "model": "qwen-plus",
    
    # 轮询时间配置（秒）
    "base_interval": 5.0,
    "max_interval": 60.0,
    "backoff_multiplier": 1.5,
    
    # 变化检测阈值 (0.005 表示 0.5% 的像素发生变化即认为有新内容)
    "change_threshold": 0.005,
    
    # 自动回复开关
    "reply_enabled": True,
    
    # AI 系统提示词
    "system_prompt": (
        "你是一个智能消息回复助手。你需要阅读对方发送的消息，并以友好、自然、得体且简短的中文进行回复。\n"
        "要求：\n"
        "1. 回复要像一个真实的人在交流，口吻亲切、自然。\n"
        "2. 回复尽量简明扼要，控制在 1-2 句话以内。\n"
        "3. 不要使用多余的格式，直接输出你要回复的文本即可。"
    ),
    
    # OCR 语言设置
    "ocr_languages": ["zh-Hans", "en-US"],
    
    # 屏幕操作区域 [x, y, w, h]，如果为 None 需要在运行前框选
    "navigation_region": None,
    "content_region": None,
    "input_region": None,
    
    # 目标应用名称（如 WeChat, Slack, 钉钉 等，留空则不检测前台）
    "target_app_name": "",
    
    # 通知标记颜色检测阈值 (RGB)
    "badge_color_r_min": 210,
    "badge_color_g_max": 110,
    "badge_color_b_max": 110,
    
    # 智能过滤控制：'all' (全部接管), 'whitelist' (只回复), 'blacklist' (不回复)
    "filter_mode": "all",
    "filter_keywords": "",
    
    # AI 人设与知识库
    "persona": "",
    "knowledge_base": "",
    
    # 被监控的列表项配置 (兼容性保留，列表红点扫描以它为白/黑名单参考)
    "monitored_items": []
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 补充可能缺失的默认字段
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception as e:
            print(f"加载配置文件失败: {e}，将使用默认配置。")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False
