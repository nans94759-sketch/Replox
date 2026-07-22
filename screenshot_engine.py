import mss
import pyautogui
from PIL import Image
import os
import datetime

_scale_factor = None

def get_retina_scale():
    """获取 Retina 缩放比例 (mss 物理像素 / pyautogui 逻辑坐标)"""
    global _scale_factor
    if _scale_factor is not None:
        return _scale_factor
        
    try:
        with mss.MSS() as sct:
            monitor = sct.monitors[1]  # 主显示器
            mss_width = monitor["width"]
        screen_width = pyautogui.size().width
        _scale_factor = mss_width / screen_width
    except Exception:
        _scale_factor = 1.0
    return _scale_factor

def capture_region(region, save_debug=False, debug_name="capture", scale=None):
    """
    截取指定区域 [x, y, w, h] (坐标为 pyautogui 逻辑点坐标)
    """
    if scale is None:
        scale = get_retina_scale()
    x, y, w, h = region
    
    # 转换为 mss 物理像素坐标
    monitor = {
        "top": int(y * scale),
        "left": int(x * scale),
        "width": int(w * scale),
        "height": int(h * scale)
    }
    
    try:
        with mss.MSS() as sct:
            sct_img = sct.grab(monitor)
            # mss 返回 bgra 格式，转换为 PIL RGB 格式
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            if save_debug:
                debug_dir = "screenshots_debug"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                img.save(os.path.join(debug_dir, f"{debug_name}_{timestamp}.png"))
                
            return img
    except Exception as e:
        print(f"截屏失败: {e}")
        return None
