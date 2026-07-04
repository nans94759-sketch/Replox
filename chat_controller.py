import pyautogui
import pyperclip
import time
import random
import math
import logger

# 设置 PyAutoGUI 的动作安全延时
pyautogui.PAUSE = 0.05

def move_to_curved(target_x, target_y):
    """
    使用 Bezier 曲线生成平滑自然的鼠标移动路径。
    """
    start_x, start_y = pyautogui.position()
    if start_x == target_x and start_y == target_y:
        return
        
    distance = math.hypot(target_x - start_x, target_y - start_y)
    if distance < 15:
        pyautogui.moveTo(target_x, target_y)
        return
        
    # 控制点的偏移幅度，随距离变大
    dev = distance * random.uniform(0.12, 0.22)
    
    # 垂直向量
    dx = target_x - start_x
    dy = target_y - start_y
    vx = -dy
    vy = dx
    length = math.hypot(vx, vy)
    vx /= length
    vy /= length
    
    # 随机左右偏离方向
    side = random.choice([-1, 1])
    
    # 第一个控制点 (偏离直线 35% 位置的垂直方向)
    mid_x1 = start_x + dx * 0.35
    mid_y1 = start_y + dy * 0.35
    ctrl_x1 = mid_x1 + vx * dev * side
    ctrl_y1 = mid_y1 + vy * dev * side
    
    # 第二个控制点 (偏离直线 65% 位置的垂直方向)
    mid_x2 = start_x + dx * 0.65
    mid_y2 = start_y + dy * 0.65
    ctrl_x2 = mid_x2 - vx * dev * side * 0.6  # 反向偏离，呈 S 型
    ctrl_y2 = mid_y2 - vy * dev * side * 0.6
    
    # 根据移动距离决定移动步数，使小距离快移动，大距离慢移动
    steps = random.randint(12, 25)
    if distance > 500:
        steps = random.randint(22, 35)
        
    points = []
    for i in range(steps + 1):
        t = i / steps
        # 三次贝塞尔曲线方程
        x = (1-t)**3 * start_x + 3*(1-t)**2 * t * ctrl_x1 + 3*(1-t) * t**2 * ctrl_x2 + t**3 * target_x
        y = (1-t)**3 * start_y + 3*(1-t)**2 * t * ctrl_y1 + 3*(1-t) * t**2 * ctrl_y2 + t**3 * target_y
        points.append((int(x), int(y)))
        
    # 沿着贝塞尔曲线平滑移动，头尾两端速度慢（启动/微调），中间快
    total_time = random.uniform(0.35, 0.6)
    step_delay = total_time / steps
    
    for idx, pt in enumerate(points):
        ratio = idx / steps
        # 变加速运动拟合 (正弦速度曲线)
        speed_factor = math.sin(ratio * math.pi)  # 0 -> 1 -> 0
        delay = step_delay * (1.5 - speed_factor)
        
        pyautogui.moveTo(pt[0], pt[1])
        time.sleep(delay)
        
    # 精准终点对齐
    pyautogui.moveTo(target_x, target_y)

def click_region(region):
    """
    模拟用户点击指定区域：
    1. 随机偏移点击位置；
    2. 平滑曲线路径移动鼠标；
    3. 模拟自然点击时延。
    """
    x, y, w, h = region
    
    # 施加随机偏移（中心区域）
    offset_x = random.randint(int(-w * 0.25), int(w * 0.25))
    offset_y = random.randint(int(-h * 0.25), int(h * 0.25))
    
    click_x = int(x + w / 2) + offset_x
    click_y = int(y + h / 2) + offset_y
    
    try:
        # 使用曲线轨迹移动
        move_to_curved(click_x, click_y)
        
        # 模拟按压延时 60-150 ms
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.06, 0.15))
        pyautogui.mouseUp()
        
    except pyautogui.FailSafeException:
        raise
        
    # 自然反应时间
    time.sleep(random.uniform(0.25, 0.45))

def click_navigation_item(list_item_region):
    """
    点击切换导航列表项
    """
    click_region(list_item_region)
    time.sleep(random.uniform(0.4, 0.7))

def send_text_input(text, input_box_region):
    """
    模拟用户操作输入文本：
    1. 贝塞尔轨迹点击输入框并短暂犹豫；
    2. Command+A, Backspace 清空；
    3. 模拟逐字/词组的分块输入效果；
    4. 输入完成前的短暂暂停；
    5. 回车发送。
    """
    if not text:
        return
        
    try:
        # 点击输入框
        click_region(input_box_region)
        time.sleep(random.uniform(0.25, 0.5))
        
        # 清空输入框
        pyautogui.hotkey("command", "a")
        time.sleep(random.uniform(0.08, 0.15))
        pyautogui.press("backspace")
        time.sleep(random.uniform(0.08, 0.15))
        
        # 模拟自然输入（逐词/字粘贴输入）
        i = 0
        while i < len(text):
            chunk_len = random.randint(1, 3)
            chunk = text[i:i+chunk_len]
            pyperclip.copy(chunk)
            time.sleep(0.02)  # 给剪贴板写入缓冲
            pyautogui.hotkey("command", "v")
            
            # 单字按键模拟延迟 (50ms - 130ms)
            delay = random.uniform(0.05, 0.13) * len(chunk)
            time.sleep(delay)
            i += chunk_len
            
        # 模拟发送前的短暂停顿
        time.sleep(random.uniform(0.6, 1.3))
        
        # 回车发送
        pyautogui.press("enter")
        time.sleep(random.uniform(0.2, 0.4))
        
    except pyautogui.FailSafeException:
        raise
    except Exception as e:
        logger.error(f"自动文本输入失败: {e}")
