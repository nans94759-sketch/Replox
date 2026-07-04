import os
import datetime

# ANSI 颜色码
COLOR_RESET = "\033[0m"
COLOR_INFO = "\033[36m"     # 青色
COLOR_SUCCESS = "\033[32m"  # 绿色
COLOR_WARN = "\033[33m"     # 黄色
COLOR_ERROR = "\033[31m"    # 红色
COLOR_DEBUG = "\033[90m"    # 灰色
COLOR_MSG_IN = "\033[35m"   # 紫色 (收到的消息)
COLOR_MSG_OUT = "\033[34m"  # 蓝色 (发送的回复)

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "monitor.log")

def init_logger():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

_gui_log_callback = None

def register_gui_callback(callback):
    global _gui_log_callback
    _gui_log_callback = callback

def _log(level, msg, color):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {msg}"
    # 输出到终端（带颜色）
    print(f"{color}{formatted_msg}{COLOR_RESET}")
    
    # 同步输出到 GUI 控制台
    if _gui_log_callback:
        try:
            _gui_log_callback(formatted_msg + "\n")
        except Exception:
            pass
            
    # 写入文件（去颜色）
    try:
        init_logger()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted_msg + "\n")
    except Exception as e:
        print(f"写入日志文件失败: {e}")

def info(msg):
    _log("信息", msg, COLOR_INFO)

def success(msg):
    _log("成功", msg, COLOR_SUCCESS)

def warn(msg):
    _log("警告", msg, COLOR_WARN)

def error(msg):
    _log("错误", msg, COLOR_ERROR)

def debug(msg):
    _log("调试", msg, COLOR_DEBUG)

def message_in(sender, content):
    msg = f"检测到 [{sender}] 的新内容: {content}"
    _log("接收", msg, COLOR_MSG_IN)

def message_out(receiver, content):
    msg = f"已自动发送至 [{receiver}]: {content}"
    _log("发送", msg, COLOR_MSG_OUT)
