import subprocess
import re
import json
import logger

def get_visible_windows():
    """
    使用 AppleScript 获取所有当前可见的主窗口信息。
    返回列表，每个元素为字典:
    {
        "app": "应用名称",
        "title": "窗口标题",
        "x": 100,
        "y": 100,
        "w": 800,
        "h": 600,
        "pid": 1234
    }
    """
    script = """
    tell application "System Events"
        set winList to {}
        set allProcesses to every application process whose visible is true
        repeat with proc in allProcesses
            set procName to name of proc
            try
                set allWindows to every window of proc
                repeat with win in allWindows
                    set winTitle to name of win
                    set winSize to size of win
                    set winPos to position of win
                    set end of winList to procName & "||" & winTitle & "||" & (item 1 of winPos) & "," & (item 2 of winPos) & "," & (item 1 of winSize) & "," & (item 2 of winSize) & "||" & (unix id of proc)
                end repeat
            end try
        end repeat
        return winList
    end tell
    """
    
    try:
        proc = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        if proc.returncode != 0:
            logger.error(f"获取窗口列表 AppleScript 失败: {proc.stderr}")
            return []
            
        output = proc.stdout.strip()
        if not output:
            return []
            
        windows = []
        # AppleScript 返回以逗号加空格分隔的列表项，例如 "item1, item2, item3"
        # 我们按 ", " 分割，注意有些标题包含逗号，这里作基础防御
        items = output.split(", ")
        for item in items:
            parts = item.split("||")
            if len(parts) == 4:
                app_name = parts[0]
                win_title = parts[1]
                rect_str = parts[2]
                pid_str = parts[3]
                
                rect_parts = rect_str.split(",")
                if len(rect_parts) == 4:
                    try:
                        windows.append({
                            "app": app_name,
                            "title": win_title,
                            "x": int(rect_parts[0]),
                            "y": int(rect_parts[1]),
                            "w": int(rect_parts[2]),
                            "h": int(rect_parts[3]),
                            "pid": int(pid_str)
                        })
                    except ValueError:
                        continue
        return windows
    except Exception as e:
        logger.error(f"获取窗口列表异常: {e}")
        return []

def find_target_window(app_keyword, title_keyword=""):
    """
    根据应用关键字（及可选的窗口标题关键字）搜索符合要求的窗口。
    支持模糊匹配。
    """
    windows = get_visible_windows()
    app_keyword_lower = app_keyword.lower()
    title_keyword_lower = title_keyword.lower()
    
    # 优先匹配 app 名字
    matched = []
    for win in windows:
        if app_keyword_lower in win["app"].lower():
            if title_keyword_lower:
                if title_keyword_lower in win["title"].lower():
                    matched.append(win)
            else:
                matched.append(win)
                
    if matched:
        # 如果有多个，默认返回第一个（最顶层或最先检测到的）
        return matched[0]
        
    return None

if __name__ == "__main__":
    # 测试运行
    print("当前可见窗口列表：")
    for w in get_visible_windows():
        print(f"PID: {w['pid']} | App: {w['app']} | Title: {w['title']} | Bounds: {w['x']},{w['y']},{w['w']},{w['h']}")
