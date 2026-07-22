import subprocess
import json
import os
import logger

CUA_BINARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "cua-driver")
SESSION_ID = "bg_automation"


def run_cua_call(tool_name, args):
    """
    通过 CLI 执行 cua-driver call <tool_name> <json_args>
    """
    if not os.path.exists(CUA_BINARY):
        logger.error(f"找不到 cua-driver 二进制文件: {CUA_BINARY}")
        return None
        
    cmd = [CUA_BINARY, "call", tool_name, json.dumps(args)]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        if proc.returncode != 0:
            logger.error(f"执行 cua-driver call {tool_name} 失败. Code: {proc.returncode}, Stderr: {proc.stderr.strip()}")
            return None
            
        output = proc.stdout.strip()
        if not output:
            return {}
            
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            logger.error(f"解析 CuaDriver 返回值失败，原始输出: {output}")
            return None
    except Exception as e:
        logger.error(f"执行 cua-driver 异常: {e}")
        return None

def init_cursor_style(color="#007AFF", size=20, opacity=0.6, label="生图助手"):
    """
    初始化和定制虚拟鼠标样式 (半透明蓝色光斑，尾迹，自定义标签)
    """
    # 启动/激活后台会话以防止 TTL 超时
    run_cua_call("start_session", {"session": SESSION_ID})
    
    logger.info(f"正在配置虚拟副鼠标样式: 颜色={color}, 大小={size}, 透明度={opacity}, 标签={label}")
    
    # 1. 基础运动参数 (Bezier 曲线，Spring 弹性振动过度效果)
    motion_args = {
        "cursor_id": SESSION_ID,
        "cursor_color": color,
        "cursor_size": size,
        "cursor_opacity": opacity,
        "cursor_label": label,
        "cursor_icon": "teardrop", # 精美的泪滴形/圆点外观
        "spring": 0.65,            # 让滑行带一点自然的惯性回弹，极富科技感
        "start_handle": 0.4,
        "end_handle": 0.4,
        "arc_size": 0.15,
        "dwell_after_click_ms": 150 # 涟漪动画驻留时间
    }
    
    # 2. 定制高级光圈/光环色彩
    style_args = {
        "cursor_id": SESSION_ID,
        "bloom_color": color, # 科技感的发光光环
        "gradient_colors": [color, "#00FFFF"] # 蓝到青色的渐变色尾迹
    }
    
    res1 = run_cua_call("set_agent_cursor_motion", motion_args)
    res2 = run_cua_call("set_agent_cursor_style", style_args)
    
    if res1 and res2:
        logger.success("虚拟副鼠标样式配置完成！")
        return True
    return False

def bg_click(pid, x, y, window_id=None):
    """
    物理后台点击 (使用虚拟鼠标滑行至 x, y 并点击，不影响主鼠标)
    """
    args = {
        "pid": pid,
        "x": x,
        "y": y,
        "session": SESSION_ID,
        "delivery_mode": "foreground"
    }
    if window_id:
        args["window_id"] = window_id
        
    logger.info(f"模拟后台点击: PID={pid}, 坐标=({x}, {y})")
    return run_cua_call("click", args)

def bg_type(pid, text, x, y, window_id=None):
    """
    模拟后台点击输入文本 (使用虚拟鼠标移动到输入框，点击激活焦点并打字，不干扰物理键盘输入)
    """
    args = {
        "pid": pid,
        "text": text,
        "x": x,
        "y": y,
        "session": SESSION_ID,
        "delivery_mode": "foreground",
        "delay_ms": 15 # 字符间的毫秒间隔
    }
    if window_id:
        args["window_id"] = window_id
        
    logger.info(f"模拟后台输入文本 (长 {len(text)} 字) 并移动焦点至 ({x}, {y})...")
    return run_cua_call("type_text", args)

def bg_press_key(pid, key, modifiers=None):
    """
    模拟后台键盘单键物理触发 (例如回车发送)
    """
    args = {
        "pid": pid,
        "key": key,
        "session": SESSION_ID,
        "delivery_mode": "foreground"
    }
    if modifiers:
        args["modifiers"] = modifiers
    logger.info(f"模拟后台按键: {key} (修饰符: {modifiers})")
    return run_cua_call("press_key", args)

def bg_move_cursor(x, y):
    """
    模拟后台将虚拟鼠标悬停到目标点 (x, y 为绝对物理像素坐标)
    """
    args = {
        "x": x,
        "y": y,
        "session": SESSION_ID
    }
    logger.info(f"模拟后台移动悬停至坐标: ({x}, {y})")
    return run_cua_call("move_cursor", args)

def bg_scroll(pid, direction, amount=3, window_id=None, x=None, y=None):
    """
    模拟后台鼠标滚轮滚动 (支持向特定窗口坐标投递滚轮事件)
    """
    args = {
        "pid": pid,
        "direction": direction,
        "amount": amount,
        "session": SESSION_ID,
        "delivery_mode": "foreground"
    }
    if window_id:
        args["window_id"] = window_id
    if x is not None and y is not None:
        args["x"] = x
        args["y"] = y
    logger.info(f"模拟后台滚动: PID={pid}, 方向={direction}, 数量={amount}, 坐标=({x}, {y})")
    return run_cua_call("scroll", args)

if __name__ == "__main__":
    # 简易自检
    init_cursor_style()
