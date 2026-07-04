from ocrmac import ocrmac
from PIL import Image
import os
import logger

def parse_content_region(pil_image, languages=['zh-Hans', 'en-US']):
    """
    解析内容区域截图，提取并分类文本块。
    返回: (has_new_incoming, incoming_messages, full_history)
    - has_new_incoming: 布尔值，是否存在新的待处理内容（LEFT 侧有新内容且尚未被 RIGHT 侧响应）
    - incoming_messages: 列表，LEFT 侧最新的未响应内容
    - full_history: 列表，解析出的所有内容历史记录（用于提供给 AI 作为上下文）
    """
    if pil_image is None:
        return False, [], []
        
    width, height = pil_image.size
    
    try:
        # 使用 ocrmac 识别文本，px=True 返回像素坐标 (x1, y1, x2, y2)
        ocr = ocrmac.OCR(pil_image, language_preference=languages)
        annotations = ocr.recognize(px=True)
    except Exception as e:
        logger.error(f"OCR 识别出错: {e}")
        return False, [], []
        
    # 按照 y1 (从上到下) 排序，使内容按时间顺序排列
    # annotations 格式为: [(text, confidence, (x1, y1, x2, y2)), ...]
    sorted_blocks = sorted(annotations, key=lambda b: b[2][1])
    parsed_messages = []
    
    for text, conf, bbox in sorted_blocks:
        x1, y1, x2, y2 = bbox
        
        # 过滤掉置信度极低或长度过短的杂质噪声字符
        text = text.strip()
        if not text or conf < 0.3:
            continue
            
        # 计算水平中心位置比例，确定文本块的水平位置归属
        center_x = (x1 + x2) / (2 * width)
        
        # 判定文本块方向
        if center_x < 0.48:
            direction = "LEFT"   # 左侧内容
        elif center_x > 0.52:
            direction = "RIGHT"  # 右侧内容
        else:
            direction = "CENTER" # 系统信息/时间戳等
            
        parsed_messages.append({
            "text": text,
            "direction": direction,
            "bbox": bbox,
            "center_x": center_x
        })
        
    if not parsed_messages:
        return False, [], []
        
    # 过滤出有意义的历史记录（过滤掉 CENTER 类型的系统信息，仅保留 LEFT 和 RIGHT 内容）
    chat_history = [m for m in parsed_messages if m["direction"] in ("LEFT", "RIGHT")]
    
    if not chat_history:
        return False, [], []
        
    # 判断最新的一条内容来自哪一侧
    last_msg = chat_history[-1]
    
    if last_msg["direction"] == "RIGHT":
        # 最新一条内容来自 RIGHT 侧，说明已经响应过了
        return False, [], chat_history
        
    # 最新一条内容来自 LEFT 侧，说明有新内容待处理
    # 向前追溯，找出所有连续的 LEFT 侧新内容
    new_incoming = []
    for msg in reversed(chat_history):
        if msg["direction"] == "LEFT":
            new_incoming.insert(0, msg["text"])
        else:
            break
            
    return True, new_incoming, chat_history
