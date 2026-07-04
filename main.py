import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import queue
import argparse
import sys
import os

import logger
import config as cfg_module
import screenshot_engine
import change_detector
import ocr_engine
import auto_replier
import chat_controller
from adaptive_timer import AdaptiveTimer

class CountdownDialog(tk.Toplevel):
    def __init__(self, parent, seconds, mode_desc):
        super().__init__(parent)
        self.seconds_left = seconds
        self.mode_desc = mode_desc
        
        self.title("准备截图")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#2d2d2d")
        
        # 居中定位 (420x200 像素)
        width, height = 420, 200
        parent.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        
        if pw > 100 and ph > 100:
            cx = px + (pw - width) // 2
            cy = py + (ph - height) // 2
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            cx = (screen_w - width) // 2
            cy = (screen_h - height) // 2
            
        self.geometry(f"{width}x{height}+{cx}+{cy}")
        
        # 绘制立体发光边框效果
        border_frame = tk.Frame(self, bg="#2d2d2d", highlightbackground="#00ff00", highlightthickness=2, bd=0)
        border_frame.pack(fill="both", expand=True)
        
        # 提示标题
        tk.Label(
            border_frame, text="📸 准备进行截图配置", 
            font=("PingFang SC", 12, "bold"), fg="#ff9500", bg="#2d2d2d"
        ).pack(pady=(15, 5))
        
        # 关键操作指引
        tk.Label(
            border_frame, 
            text="🚨 重要提示：请确保目标应用窗口完全显露在最上层！", 
            font=("PingFang SC", 10, "bold"), fg="#ff3b30", bg="#2d2d2d"
        ).pack(pady=2)
        
        tk.Label(
            border_frame, 
            text=f"配置步骤：{self.mode_desc}", 
            font=("PingFang SC", 9), fg="#cccccc", bg="#2d2d2d", wraplength=380
        ).pack(pady=2)
        
        # 巨大的倒计时数字标签
        self.lbl_num = tk.Label(
            border_frame, text=str(self.seconds_left), 
            font=("Impact", 44, "bold"), fg="#00ff00", bg="#2d2d2d"
        )
        self.lbl_num.pack(pady=(5, 10))
        
        self._tick()
        
    def _tick(self):
        if self.seconds_left > 0:
            self.lbl_num.config(text=str(self.seconds_left))
            if self.seconds_left == 1:
                self.lbl_num.config(fg="#ff3b30") # 最后一秒闪红提示
            self.seconds_left -= 1
            self.after(1000, self._tick)
        else:
            self.destroy()

class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent, name, incoming_text, reply, icon_img):
        super().__init__(parent)
        self.result = False
        
        self.title("安全模式 - 发送确认")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#2d2d2d")
        
        # 居中定位
        width, height = 400, 360
        parent.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        
        if pw > 100 and ph > 100:
            cx = px + (pw - width) // 2
            cy = py + (ph - height) // 2
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            cx = (screen_w - width) // 2
            cy = (screen_h - height) // 2
            
        self.geometry(f"{width}x{height}+{cx}+{cy}")
        
        # 立体高亮发光边框
        border_frame = tk.Frame(self, bg="#2d2d2d", highlightbackground="#007aff", highlightthickness=2, bd=0)
        border_frame.pack(fill="both", expand=True)
        
        # 顶部展示精美的 AI 机器人头像图片
        if icon_img:
            self.icon_label = tk.Label(border_frame, image=icon_img, bg="#2d2d2d")
            self.icon_label.pack(pady=(20, 10))
        else:
            tk.Label(border_frame, text="🤖", font=("PingFang SC", 32), bg="#2d2d2d", fg="#ff9500").pack(pady=(20, 10))
        
        # 标题提示
        tk.Label(
            border_frame, text="🔔 AI 助手为您生成了新回复，请审核：", 
            font=("PingFang SC", 11, "bold"), fg="#ffffff", bg="#2d2d2d"
        ).pack(pady=(5, 10))
        
        # 详情面板
        details_frame = tk.Frame(border_frame, bg="#202020", bd=1, relief="solid")
        details_frame.pack(fill="x", padx=25, pady=5, ipady=5)
        
        tk.Label(
            details_frame, text=f"👤 联系人: {name}", 
            font=("PingFang SC", 10, "bold"), fg="#00ff00", bg="#202020", anchor="w"
        ).pack(fill="x", padx=10, pady=2)
        
        tk.Label(
            details_frame, text=f"💬 收到消息: {incoming_text}", 
            font=("PingFang SC", 10), fg="#cccccc", bg="#202020", anchor="w", wraplength=330, justify="left"
        ).pack(fill="x", padx=10, pady=2)
        
        tk.Label(
            details_frame, text=f"🤖 AI 回复: {reply}", 
            font=("PingFang SC", 10, "bold"), fg="#ff9500", bg="#202020", anchor="w", wraplength=330, justify="left"
        ).pack(fill="x", padx=10, pady=2)
        
        # 提问句
        tk.Label(
            border_frame, text="是否确认执行物理模拟打字发送？", 
            font=("PingFang SC", 10, "bold"), fg="#ffffff", bg="#2d2d2d"
        ).pack(pady=(10, 10))
        
        # 底部按钮区 (Yes/No)
        btn_frame = tk.Frame(border_frame, bg="#2d2d2d")
        btn_frame.pack(fill="x", side="bottom", pady=(0, 20))
        
        self.btn_no = tk.Label(
            btn_frame, font=("PingFang SC", 10, "bold"), fg="white", bd=0, width=12, height=2, cursor="hand2"
        )
        self.btn_no.pack(side="left", padx=(50, 10))
        
        self.btn_yes = tk.Label(
            btn_frame, font=("PingFang SC", 10, "bold"), fg="white", bd=0, width=12, height=2, cursor="hand2"
        )
        self.btn_yes.pack(side="right", padx=(10, 50))
        
        # 绑定 hover 及事件
        self.set_button_state(self.btn_no, "❌ 取消 (No)", "#c0392b", self.on_no)
        self.set_button_state(self.btn_yes, "✅ 发送 (Yes)", "#27ae60", self.on_yes)
        
        self.bind("<Return>", lambda e: self.on_yes())
        self.bind("<Escape>", lambda e: self.on_no())
        
    def set_button_state(self, btn, text, bg, command):
        hover_colors = {
            "#27ae60": "#2ecc71",
            "#c0392b": "#e74c3c"
        }
        hover_bg = hover_colors.get(bg, bg)
        btn.config(text=text, bg=bg)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        
    def on_yes(self):
        self.result = True
        self.destroy()
        
    def on_no(self):
        self.result = False
        self.destroy()

def has_notification_badge(pil_img, config, scale=1.0):
    """
    分析列表项截图，检测是否包含未读通知标记（徽章）。
    """
    if pil_img is None:
        return False
        
    width, height = pil_img.size
    
    # 通知标记通常位于列表项的右上角附近
    # 限制只扫描前部区域 (逻辑像素 X: 0-70, Y: 0-50)
    scan_w = min(width, int(70 * scale))
    scan_h = min(height, int(50 * scale))
    
    rgb_img = pil_img.convert("RGB")
    
    r_min = config.get("badge_color_r_min", 210)
    g_max = config.get("badge_color_g_max", 110)
    b_max = config.get("badge_color_b_max", 110)
    
    matching_pixels = 0
    for x in range(scan_w):
        for y in range(scan_h):
            r, g, b = rgb_img.getpixel((x, y))
            # 通知标记的 RGB 色彩检测条件
            if r > r_min and g < g_max and b < b_max:
                if (r - g) > 100 and (r - b) > 100:
                    matching_pixels += 1
                    
    # 判定门槛：Retina 屏下比例折算，大于 12 个像素点判定为存在标记
    min_pixels = int(12 * (scale ** 2))
    return matching_pixels >= min_pixels

class ScreenFlowApp:
    def __init__(self, root, args):
        self.root = root
        self.config = cfg_module.load_config()
        self.ui_queue = queue.Queue()
        
        # 运行与控制变量
        self.is_monitoring = False     # 是否处于监听循环
        self.reply_enabled = False     # 默认进入程序时关闭自动回复
        self.safety_mode = not args.auto_reply
        self.thread_active = True      # 后台轮询线程是否存活
        self.last_screenshots = {}
        self.first_check = {}          # 首次检查同步标记
        self.last_replied_sig = {}     # 已回复的监控项特征签名缓存
        
        # 定时器
        self.timer = AdaptiveTimer(
            base_interval=self.config.get("base_interval", 5.0),
            max_interval=self.config.get("max_interval", 60.0),
            multiplier=self.config.get("backoff_multiplier", 1.5)
        )
        
        # 加载并注册 App 精美图标
        self.app_icon_img = None
        self.app_icon_tk = None
        if os.path.exists("app_icon.png"):
            try:
                from PIL import Image, ImageTk
                self.app_icon_img = Image.open("app_icon.png")
                dialog_icon = self.app_icon_img.resize((70, 70), Image.Resampling.LANCZOS)
                self.app_icon_tk = ImageTk.PhotoImage(dialog_icon)
                
                # macOS Dock 栏图标设置
                try:
                    from AppKit import NSApplication, NSImage
                    abs_path = os.path.abspath("app_icon.png")
                    ns_image = NSImage.alloc().initWithContentsOfFile_(abs_path)
                    NSApplication.sharedApplication().setApplicationIconImage_(ns_image)
                    logger.info("🎉 已成功设置 macOS Dock 栏程序图标！")
                except Exception as ex:
                    logger.warn(f"无法设置 Dock 栏图标: {ex}")
            except Exception as e:
                logger.error(f"加载 app_icon.png 失败: {e}")

        # 设置窗口属性
        self.root.title("Replox 妙答AI聊天回复助手")
        self.root.geometry("820x650")
        self.root.configure(bg="#1e1e1e")
        
        # 将应用程序窗口图标也做设置（适用于多端）
        if self.app_icon_tk:
            try:
                self.root.iconphoto(False, self.app_icon_tk)
            except Exception:
                pass
                
        self.setup_styles()
        
        # 构建 Notebook 四标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_monitor = tk.Frame(self.notebook, bg="#1e1e1e")
        self.tab_config = tk.Frame(self.notebook, bg="#1e1e1e")
        self.tab_settings = tk.Frame(self.notebook, bg="#1e1e1e")
        self.tab_persona = tk.Frame(self.notebook, bg="#1e1e1e")
        
        self.notebook.add(self.tab_monitor, text="  🖥️ 实时监控与日志  ")
        self.notebook.add(self.tab_config, text="  📐 屏幕区域配置向导  ")
        self.notebook.add(self.tab_settings, text="  🔧 系统参数设置  ")
        self.notebook.add(self.tab_persona, text="  🎭 人设与知识库  ")
        
        # 初始化标签页视图
        self.setup_monitor_tab()
        self.setup_config_tab()
        self.setup_settings_tab()
        self.setup_persona_tab()
        
        # 注册日志回调
        logger.register_gui_callback(self.on_log_received)
        
        self.check_ui_queue()
        
        # 启动后台监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # 自动判定是否可以直接启动
        self.auto_start_if_configured()
        
        # 关闭安全退出
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        """配置暗黑风格界面"""
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#cccccc", padding=[15, 6], font=("PingFang SC", 10))
        style.map("TNotebook.Tab", background=[("selected", "#1e1e1e")], foreground=[("selected", "#00ff00")])
        style.configure("TSeparator", background="#333333")

    def create_scrollable_container(self, parent_frame):
        """
        创建一个通用的、可滚动的 Canvas + Scrollbar 容器，并返回内部的可放置组件的 Frame
        """
        canvas = tk.Canvas(parent_frame, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局 Canvas 和 Scrollbar
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # 创建内部的真实容器 Frame
        scroll_content_frame = tk.Frame(canvas, bg="#1e1e1e")
        canvas_window = canvas.create_window((0, 0), window=scroll_content_frame, anchor="nw")
        
        # 当内部 Frame 尺寸改变时，更新 Canvas 的滚动范围
        scroll_content_frame.bind(
            "<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 当 Canvas 宽度变化时，让内部 Frame 比 Canvas 窄 24 像素，留出边缘以防与右侧滚动条交错
        canvas.bind(
            "<Configure>", 
            lambda e: canvas.itemconfig(canvas_window, width=e.width - 24)
        )
        
        # 绑定鼠标滚轮滚动事件（只在鼠标悬停在当前 Canvas 或其子组件上时有效）
        def _on_mousewheel(event):
            widget = event.widget
            if widget and str(widget).startswith(str(canvas)):
                canvas.yview_scroll(-1 * int(event.delta), "units")
                
        self.root.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        
        return scroll_content_frame

    def set_button_state(self, btn, text, bg, command=None):
        """
        用于设置 flat 标签按钮的状态并赋予 hover 动态高亮动效
        """
        hover_colors = {
            "#27ae60": "#2ecc71", # 亮绿
            "#f5a623": "#ffb94b", # 亮橙
            "#007aff": "#5ac8fa", # 天蓝
            "#8e44ad": "#a29bfe", # 紫色
            "#c0392b": "#e74c3c", # 红色
            "#e67e22": "#f39c12", # 预览橙色
            "#9b59b6": "#af7ac5", # 浅紫一键配置
            "#af52de": "#c375e7", # 人设紫保存
            "#3a3a3a": "#4f4f4f"  # 模板灰色
        }
        hover_bg = hover_colors.get(bg, bg)
        
        btn.config(text=text, bg=bg)
        if command:
            btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))

    def setup_monitor_tab(self):
        """1. 监控日志标签页初始化"""
        self.tab_monitor.rowconfigure(0, weight=0)
        self.tab_monitor.rowconfigure(1, weight=3)
        self.tab_monitor.rowconfigure(2, weight=2)
        self.tab_monitor.columnconfigure(0, weight=1)
        
        # 顶部面板
        top_panel = tk.Frame(self.tab_monitor, bg="#2d2d2d")
        top_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.lbl_status = tk.Label(
            top_panel, text="监控状态: 🔴 未配置", 
            font=("PingFang SC", 12, "bold"), fg="#ff3b30", bg="#2d2d2d"
        )
        self.lbl_status.pack(side="left", padx=20, pady=15)
        
        self.lbl_interval = tk.Label(
            top_panel, text="轮询频率: 闲置中", 
            font=("PingFang SC", 12), fg="#bbbbbb", bg="#2d2d2d"
        )
        self.lbl_interval.pack(side="right", padx=20, pady=15)
        
        # 中部内容区 (左右网格结构，彻底杜绝控制台被挤扁的问题)
        mid_body = tk.Frame(self.tab_monitor, bg="#1e1e1e")
        mid_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        mid_body.columnconfigure(0, weight=1)
        mid_body.columnconfigure(1, weight=0)
        mid_body.rowconfigure(0, weight=1)
        
        # 左侧：列表与参数概览
        left_box = tk.LabelFrame(
            mid_body, text=" 监控信息概览 ", 
            font=("PingFang SC", 11, "bold"), fg="#00ff00", bg="#1e1e1e", bd=1
        )
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.info_text = tk.Text(
            left_box, bg="#151515", fg="#ffffff", font=("PingFang SC", 11),
            bd=0, highlightthickness=0, wrap="word", padx=10, pady=10
        )
        self.info_text.pack(fill="both", expand=True)
        self.update_info_display()
        
        # 右侧：快速控制面板
        right_box = tk.LabelFrame(
            mid_body, text=" 操作控制台 ", 
            font=("PingFang SC", 11, "bold"), fg="#00ff00", bg="#1e1e1e", bd=1,
            width=210
        )
        right_box.grid(row=0, column=1, sticky="nsew")
        right_box.grid_propagate(False)
        
        self.btn_run = tk.Label(
            right_box, font=("PingFang SC", 11, "bold"), fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_run.pack(fill="x", padx=15, pady=8)
        
        self.btn_reply = tk.Label(
            right_box, font=("PingFang SC", 11, "bold"), fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_reply.pack(fill="x", padx=15, pady=8)
        
        self.btn_safety = tk.Label(
            right_box, font=("PingFang SC", 11, "bold"), fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_safety.pack(fill="x", padx=15, pady=8)
        
        self.btn_exit = tk.Label(
            right_box, font=("PingFang SC", 11, "bold"), fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_exit.pack(fill="x", padx=15, pady=8)
        
        # 绑定初始状态、事件与 Hover 效果
        self.set_button_state(self.btn_run, "🚀 开启自动监控", "#27ae60", self.start_monitoring_action)
        self.set_button_state(self.btn_reply, "🤖 暂停自动回复" if self.reply_enabled else "🤖 开启自动回复", "#007aff", self.toggle_reply)
        self.set_button_state(self.btn_safety, "🛡️ 安全确认模式" if self.safety_mode else "🛡️ 自动回复模式", "#8e44ad", self.toggle_safety_mode)
        self.set_button_state(self.btn_exit, "🚪 退出整个程序", "#c0392b", self.on_close)
        
        # 底部：日志控制台
        log_box = tk.LabelFrame(
            self.tab_monitor, text=" 实时运行日志 ", 
            font=("PingFang SC", 11, "bold"), fg="#00ff00", bg="#1e1e1e", bd=1
        )
        log_box.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.log_widget = tk.Text(
            log_box, bg="#0c0c0c", fg="#00ff00", font=("Menlo", 10), 
            bd=0, highlightthickness=0, state="disabled"
        )
        self.log_widget.pack(fill="both", side="left", expand=True, padx=(10, 0), pady=10)
        
        scrollbar = tk.Scrollbar(log_box, bg="#1e1e1e", elementborderwidth=0)
        scrollbar.pack(fill="y", side="right", pady=10, padx=(0, 10))
        self.log_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_widget.yview)

    def setup_config_tab(self):
        """2. 配置向导标签页初始化"""
        guide_label = tk.Label(
            self.tab_config, 
            text="屏幕监控区域配置向导 — 拖拽框选，免去复杂的文本配置。",
            font=("PingFang SC", 12, "bold"), fg="#ffffff", bg="#1e1e1e", anchor="w"
        )
        guide_label.pack(fill="x", padx=15, pady=10)
        
        # 使用滚动容器包裹配置项
        scroll_container = tk.Frame(self.tab_config, bg="#1e1e1e")
        scroll_container.pack(fill="both", expand=True, padx=15)
        scroll_frame = self.create_scrollable_container(scroll_container)
        
        card_config = {"bg": "#2d2d2d", "bd": 1, "relief": "groove"}
        
        # ---------------- 🌟 智能一键配置 ----------------
        smart_box = tk.LabelFrame(
            scroll_frame, text=" 🌟 智能一键配置 (推荐) ", 
            font=("PingFang SC", 11, "bold"), fg="#00ff00", bg="#1e1e1e", bd=1
        )
        smart_box.pack(fill="x", pady=(0, 15), ipady=10)
        
        tk.Label(
            smart_box, text="只需框选整个目标应用窗口外框，系统将根据经典布局比例自动拆分导航区、内容展示区和输入框。",
            font=("PingFang SC", 10), fg="#bbbbbb", bg="#1e1e1e", wraplength=700, justify="left"
        ).pack(anchor="w", padx=15, pady=5)
        
        self.btn_smart_cal = tk.Label(
            smart_box, font=("PingFang SC", 11, "bold"), fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_smart_cal.pack(fill="x", padx=15, pady=(5, 5))
        self.set_button_state(self.btn_smart_cal, "📐 框选整个目标窗口，智能一键配置", "#9b59b6", lambda: self.start_region_calibration("smart"))
        
        # 分割线
        sep = ttk.Separator(scroll_frame, orient="horizontal")
        sep.pack(fill="x", pady=10)
        
        # ---------------- 🛠️ 手动分步微调 ----------------
        manual_box = tk.LabelFrame(
            scroll_frame, text=" 🛠️ 手动分步微调配置 (备用) ", 
            font=("PingFang SC", 11, "bold"), fg="#8e44ad", bg="#1e1e1e", bd=1
        )
        manual_box.pack(fill="both", expand=True, ipady=5)
        
        # 卡片 1: 导航列表区域
        card1 = tk.Frame(manual_box, **card_config)
        card1.pack(fill="x", pady=5, padx=10, ipady=5)
        self.lbl_status_nav_col = tk.Label(card1, text="步骤 1: 【导航列表区域】 (当前状态: ❌ 未配置)", font=("PingFang SC", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        self.lbl_status_nav_col.pack(side="left", padx=10)
        btn_list = tk.Label(card1, font=("PingFang SC", 9, "bold"), fg="white", bd=0, padx=10, pady=5, cursor="hand2")
        btn_list.pack(side="right", padx=10)
        self.set_button_state(btn_list, "📐 框选导航区", "#007aff", lambda: self.start_region_calibration("navigation"))
                  
        # 卡片 2: 内容展示区
        card2 = tk.Frame(manual_box, **card_config)
        card2.pack(fill="x", pady=5, padx=10, ipady=5)
        self.lbl_status_content = tk.Label(card2, text="步骤 2: 【内容展示区域】 (当前状态: ❌ 未配置)", font=("PingFang SC", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        self.lbl_status_content.pack(side="left", padx=10)
        btn_content = tk.Label(card2, font=("PingFang SC", 9, "bold"), fg="white", bd=0, padx=10, pady=5, cursor="hand2")
        btn_content.pack(side="right", padx=10)
        self.set_button_state(btn_content, "📐 框选内容区", "#27ae60", lambda: self.start_region_calibration("content"))
                  
        # 卡片 3: 打字输入框
        card3 = tk.Frame(manual_box, **card_config)
        card3.pack(fill="x", pady=5, padx=10, ipady=5)
        self.lbl_status_input = tk.Label(card3, text="步骤 3: 【输入框区域】 (当前状态: ❌ 未配置)", font=("PingFang SC", 10, "bold"), fg="#ffffff", bg="#2d2d2d")
        self.lbl_status_input.pack(side="left", padx=10)
        btn_input = tk.Label(card3, font=("PingFang SC", 9, "bold"), fg="white", bd=0, padx=10, pady=5, cursor="hand2")
        btn_input.pack(side="right", padx=10)
        self.set_button_state(btn_input, "📐 框选输入框", "#27ae60", lambda: self.start_region_calibration("input"))
                  
        # 下方提示区域
        self.lbl_wizard_tip = tk.Label(
            scroll_frame, 
            text="💡 经典比例：侧边栏 8%，导航列表 27%，内容区 65%，打字框 20% 高度。",
            font=("PingFang SC", 10), fg="#ff9500", bg="#1e1e1e", justify="center"
        )
        self.lbl_wizard_tip.pack(fill="x", pady=5)
        
        self.btn_preview_regions = tk.Label(
            scroll_frame, font=("PingFang SC", 11, "bold"), fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_preview_regions.pack(fill="x", padx=15, pady=5)
        self.set_button_state(self.btn_preview_regions, "👁️ 屏幕高亮预览校验当前选区", "#e67e22", self.show_regions_visualization)
        
        self.update_wizard_status()

    def setup_settings_tab(self):
        """3. 参数设置标签页初始化"""
        title_lbl = tk.Label(
            self.tab_settings, 
            text="🔧 系统高级参数配置中心 — 修改后直接写入配置文件并实时生效",
            font=("PingFang SC", 12, "bold"), fg="#ffffff", bg="#1e1e1e", anchor="w"
        )
        title_lbl.pack(fill="x", padx=15, pady=(10, 5))
        
        # 主框架容器
        main_container = tk.Frame(self.tab_settings, bg="#1e1e1e")
        main_container.pack(fill="both", expand=True, padx=15)
        
        lbl_cfg = {"font": ("PingFang SC", 10, "bold"), "fg": "#ffffff", "bg": "#1e1e1e", "anchor": "w"}
        ent_cfg = {"bg": "#151515", "fg": "#00ff00", "insertbackground": "white", "font": ("Menlo", 10), "bd": 1, "relief": "solid"}
        
        # ==== Section 1: 🔑 AI 凭证与目标配置 ====
        sec1 = tk.LabelFrame(
            main_container, text=" 🔑 AI 凭证与目标配置 ",
            font=("PingFang SC", 11, "bold"), fg="#ff9500", bg="#1e1e1e", bd=1
        )
        sec1.pack(fill="x", pady=5, ipady=5)
        sec1.columnconfigure(0, weight=1)
        sec1.columnconfigure(1, weight=3)
        
        # API Key
        tk.Label(sec1, text="AI 模型 API Key (DashScope Bearer Token):", **lbl_cfg).grid(row=0, column=0, sticky="w", pady=4, padx=10)
        self.ent_api_key = tk.Entry(sec1, **ent_cfg)
        self.ent_api_key.grid(row=0, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_api_key.insert(0, str(self.config.get("api_key", "")))
        
        # Workspace ID
        tk.Label(sec1, text="AI 工作空间 ID (DashScope Workspace ID, 可选):", **lbl_cfg).grid(row=1, column=0, sticky="w", pady=4, padx=10)
        self.ent_workspace_id = tk.Entry(sec1, **ent_cfg)
        self.ent_workspace_id.grid(row=1, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_workspace_id.insert(0, str(self.config.get("workspace_id", "")))
        
        # Target App Name
        tk.Label(sec1, text="目标应用名称/进程名 (如聊天软件应用名称，留空不限制):", **lbl_cfg).grid(row=2, column=0, sticky="w", pady=4, padx=10)
        self.ent_target_app = tk.Entry(sec1, **ent_cfg)
        self.ent_target_app.grid(row=2, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_target_app.insert(0, self.config.get("target_app_name", ""))
        
        # ==== Section 2: ⚙️ 监控与自适应轮询参数 ====
        sec2 = tk.LabelFrame(
            main_container, text=" ⚙️ 监控与自适应轮询参数 ",
            font=("PingFang SC", 11, "bold"), fg="#00ff00", bg="#1e1e1e", bd=1
        )
        sec2.pack(fill="x", pady=5, ipady=5)
        sec2.columnconfigure(0, weight=1)
        sec2.columnconfigure(1, weight=3)
        
        # 基础检测间隔
        tk.Label(sec2, text="基础检测间隔 (秒) - 聊天活跃时的轮询速度:", **lbl_cfg).grid(row=0, column=0, sticky="w", pady=4, padx=10)
        self.ent_base_int = tk.Entry(sec2, **ent_cfg)
        self.ent_base_int.grid(row=0, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_base_int.insert(0, str(self.config.get("base_interval", 5.0)))
        
        # 最大检测间隔
        tk.Label(sec2, text="最大检测间隔 (秒) - 长期闲置时的最大频率:", **lbl_cfg).grid(row=1, column=0, sticky="w", pady=4, padx=10)
        self.ent_max_int = tk.Entry(sec2, **ent_cfg)
        self.ent_max_int.grid(row=1, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_max_int.insert(0, str(self.config.get("max_interval", 60.0)))
        
        # 闲置退避系数
        tk.Label(sec2, text="闲置退避系数 - 没消息时每次延时累乘倍数:", **lbl_cfg).grid(row=2, column=0, sticky="w", pady=4, padx=10)
        self.ent_multiplier = tk.Entry(sec2, **ent_cfg)
        self.ent_multiplier.grid(row=2, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_multiplier.insert(0, str(self.config.get("backoff_multiplier", 1.5)))
        
        # 变化检测阈值
        tk.Label(sec2, text="通知标记检测敏感度 - 最小像素集范围点数:", **lbl_cfg).grid(row=3, column=0, sticky="w", pady=4, padx=10)
        self.ent_threshold = tk.Entry(sec2, **ent_cfg)
        self.ent_threshold.grid(row=3, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_threshold.insert(0, str(self.config.get("change_threshold", 0.005)))
        
        # ==== Section 3: 🛡️ 智能过滤与回复策略 ====
        sec3 = tk.LabelFrame(
            main_container, text=" 🛡️ 智能过滤与回复策略 ",
            font=("PingFang SC", 11, "bold"), fg="#007aff", bg="#1e1e1e", bd=1
        )
        sec3.pack(fill="both", expand=True, pady=5, ipady=5)
        sec3.columnconfigure(0, weight=1)
        sec3.columnconfigure(1, weight=3)
        sec3.rowconfigure(2, weight=1)
        
        # 回复过滤模式
        tk.Label(sec3, text="智能接管过滤模式:", **lbl_cfg).grid(row=0, column=0, sticky="w", pady=4, padx=10)
        self.filter_mode_var = tk.StringVar(value=self.config.get("filter_mode", "all"))
        radio_frame = tk.Frame(sec3, bg="#1e1e1e")
        radio_frame.grid(row=0, column=1, sticky="w", pady=4, padx=(0, 10))
        tk.Radiobutton(radio_frame, text="全部自动接管回复", variable=self.filter_mode_var, value="all", fg="#00ff00", bg="#1e1e1e", activeforeground="#00ff00", selectcolor="#2d2d2d").pack(side="left", padx=5)
        tk.Radiobutton(radio_frame, text="只回复名单中项目", variable=self.filter_mode_var, value="whitelist", fg="#007aff", bg="#1e1e1e", activeforeground="#007aff", selectcolor="#2d2d2d").pack(side="left", padx=5)
        tk.Radiobutton(radio_frame, text="排除名单中项目", variable=self.filter_mode_var, value="blacklist", fg="#ff3b30", bg="#1e1e1e", activeforeground="#ff3b30", selectcolor="#2d2d2d").pack(side="left", padx=5)
        
        # 过滤关键词
        tk.Label(sec3, text="过滤名单中的关键词 (空格或逗号分隔):", **lbl_cfg).grid(row=1, column=0, sticky="w", pady=4, padx=10)
        self.ent_filter_names = tk.Entry(sec3, **ent_cfg)
        self.ent_filter_names.grid(row=1, column=1, sticky="ew", pady=4, padx=(0, 10))
        self.ent_filter_names.insert(0, self.config.get("filter_keywords", ""))
        
        # AI 系统 Prompt
        tk.Label(sec3, text="AI 扮演角色与回复规则 Prompt:", **lbl_cfg).grid(row=2, column=0, sticky="nw", pady=4, padx=10)
        
        prompt_container = tk.Frame(sec3, bg="#1e1e1e")
        prompt_container.grid(row=2, column=1, sticky="nsew", pady=4, padx=(0, 10))
        
        self.txt_prompt = tk.Text(
            prompt_container, bg="#151515", fg="#ffffff", insertbackground="white",
            font=("PingFang SC", 10), bd=1, relief="solid", height=3
        )
        pr_scroll = ttk.Scrollbar(prompt_container, orient="vertical", command=self.txt_prompt.yview)
        self.txt_prompt.configure(yscrollcommand=pr_scroll.set)
        pr_scroll.pack(side="right", fill="y")
        self.txt_prompt.pack(side="left", fill="both", expand=True)
        self.txt_prompt.insert("1.0", self.config.get("system_prompt", ""))
        
        # 保存按钮
        self.btn_save_settings = tk.Label(
            self.tab_settings, font=("PingFang SC", 11, "bold"),
            fg="white", bd=0, height=2, cursor="hand2"
        )
        self.btn_save_settings.pack(fill="x", padx=15, pady=(5, 10))
        self.set_button_state(self.btn_save_settings, "💾 保存并应用参数配置", "#007aff", self.save_settings_action)

    def save_settings_action(self):
        """保存高级参数"""
        try:
            api_key = self.ent_api_key.get().strip()
            workspace_id = self.ent_workspace_id.get().strip()
            base_int = float(self.ent_base_int.get())
            max_int = float(self.ent_max_int.get())
            multiplier = float(self.ent_multiplier.get())
            threshold = float(self.ent_threshold.get())
            f_mode = self.filter_mode_var.get()
            f_names = self.ent_filter_names.get().strip()
            target_app = self.ent_target_app.get().strip()
            prompt = self.txt_prompt.get("1.0", tk.END).strip()
            
            if base_int <= 0 or max_int <= 0 or multiplier <= 1.0 or threshold <= 0:
                raise ValueError("数值格式或区间非法")
                
            self.config["api_key"] = api_key
            self.config["workspace_id"] = workspace_id
            self.config["base_interval"] = base_int
            self.config["max_interval"] = max_int
            self.config["backoff_multiplier"] = multiplier
            self.config["change_threshold"] = threshold
            self.config["filter_mode"] = f_mode
            self.config["filter_keywords"] = f_names
            self.config["target_app_name"] = target_app
            self.config["system_prompt"] = prompt
            
            cfg_module.save_config(self.config)
            
            # 实时调整定时器
            self.timer.base_interval = base_int
            self.timer.max_interval = max_int
            self.timer.multiplier = multiplier
            
            self.update_info_display()
            
            logger.success("✅ 系统参数设置已成功保存并实时应用！")
            messagebox.showinfo("配置成功", "系统运行参数已保存并实时应用更新！", parent=self.root)
            self.notebook.select(self.tab_monitor)
            
        except Exception as e:
            messagebox.showerror("配置错误", f"保存失败，请检查数据格式。原因: {e}", parent=self.root)

    # ==================== Tab 4: 人设与知识库 ====================
    
    PERSONA_PRESETS = {
        "温柔闺蜜": {
            "persona": "你是一个温柔体贴的闺蜜，说话甜美可爱，喜欢用语气词和颜文字。对朋友非常关心，总是以积极正面的态度鼓励对方。偶尔会撒娇卖萌，让人感到亲切温暖。",
            "knowledge_base": ""
        },
        "专业客服": {
            "persona": "你是一位专业、耐心的客服代表。回答问题时条理清晰、言简意赅。始终保持礼貌和专业态度，遇到无法回答的问题会诚实告知并提供替代方案。",
            "knowledge_base": "工作时间：周一至周五 9:00-18:00\n退换货政策：7天无理由退换\n客服热线：400-xxx-xxxx\n\n请根据以上信息回答客户问题。如不确定，建议客户联系人工客服。"
        },
        "幽默段子手": {
            "persona": "你是一个幽默风趣的段子手，说话诙谐逗趣，善于用比喻和反转制造笑点。喜欢用网络热梗和流行语，但不会过于低俗。聊天时总能让对方开心一笑。",
            "knowledge_base": ""
        },
        "商务精英": {
            "persona": "你是一位成熟稳重的商务人士。说话干练利落，注重效率。回复时措辞严谨得体，避免口语化表达。善于把控沟通节奏，推动事务进展。",
            "knowledge_base": ""
        },
        "知心大哥/大姐": {
            "persona": "你是一个年长几岁、阅历丰富的知心大哥（或大姐）。说话沉稳有分量，善于倾听和给建议。语气温和但不失坚定，让人感到可靠和安心。",
            "knowledge_base": ""
        },
    }
    
    def setup_persona_tab(self):
        """4. 人设与知识库标签页初始化"""
        lbl_cfg = {"font": ("PingFang SC", 10, "bold"), "fg": "#ffffff", "bg": "#1e1e1e", "anchor": "w"}
        
        # 顶部标题
        title_lbl = tk.Label(
            self.tab_persona,
            text="🎭 AI 人设与知识库配置 — 自定义回复的角色性格和专业知识",
            font=("PingFang SC", 12, "bold"), fg="#ffffff", bg="#1e1e1e", anchor="w"
        )
        title_lbl.pack(fill="x", padx=15, pady=(10, 5))
        
        # 主体容器
        body = tk.Frame(self.tab_persona, bg="#1e1e1e")
        body.pack(fill="both", expand=True, padx=15)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(2, weight=3) # 给输入框这一行高权重
        body.rowconfigure(4, weight=2) # 给预览框这一行中等权重
        
        # ---- 左上/右上：预设模板快捷选择 ----
        preset_frame = tk.Frame(body, bg="#2d2d2d", bd=1, relief="solid")
        preset_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        
        tk.Label(preset_frame, text="⚡ 一键预设模板:", font=("PingFang SC", 10, "bold"), fg="#ff9500", bg="#2d2d2d").pack(side="left", padx=8, pady=6)
        
        for name in self.PERSONA_PRESETS:
            btn_preset = tk.Label(
                preset_frame, font=("PingFang SC", 9), cursor="hand2",
                fg="#00ff00", bd=0, padx=8, pady=3
            )
            btn_preset.pack(side="left", padx=4, pady=6)
            self.set_button_state(btn_preset, name, "#3a3a3a", lambda n=name: self.apply_persona_preset(n))
        
        # ---- 左列：角色人设 ----
        tk.Label(body, text="🎭 角色人设（性格 · 语气 · 身份背景）:", **lbl_cfg).grid(row=1, column=0, sticky="sw", pady=(8, 2), padx=(0, 5))
        
        p_frame = tk.Frame(body, bg="#1e1e1e")
        p_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 8), padx=(0, 5))
        self.txt_persona = tk.Text(
            p_frame, bg="#151515", fg="#e0e0ff", insertbackground="white",
            font=("PingFang SC", 10), bd=1, relief="solid", wrap="word", height=6
        )
        p_scroll = ttk.Scrollbar(p_frame, orient="vertical", command=self.txt_persona.yview)
        self.txt_persona.configure(yscrollcommand=p_scroll.set)
        p_scroll.pack(side="right", fill="y")
        self.txt_persona.pack(side="left", fill="both", expand=True)
        self.txt_persona.insert("1.0", self.config.get("persona", ""))
        
        # 人设字数统计
        self.lbl_persona_count = tk.Label(body, text="0 字", font=("Menlo", 9), fg="#666666", bg="#1e1e1e", anchor="e")
        self.lbl_persona_count.grid(row=3, column=0, sticky="e", padx=(0, 5))
        self.txt_persona.bind("<KeyRelease>", lambda e: self._update_char_counts())
        
        # ---- 右列：知识库 ----
        tk.Label(body, text="📚 知识库（FAQ · 产品信息 · 专业知识）:", **lbl_cfg).grid(row=1, column=1, sticky="sw", pady=(8, 2), padx=(5, 0))
        
        k_frame = tk.Frame(body, bg="#1e1e1e")
        k_frame.grid(row=2, column=1, sticky="nsew", pady=(0, 8), padx=(5, 0))
        self.txt_knowledge = tk.Text(
            k_frame, bg="#151515", fg="#e0ffe0", insertbackground="white",
            font=("PingFang SC", 10), bd=1, relief="solid", wrap="word", height=6
        )
        k_scroll = ttk.Scrollbar(k_frame, orient="vertical", command=self.txt_knowledge.yview)
        self.txt_knowledge.configure(yscrollcommand=k_scroll.set)
        k_scroll.pack(side="right", fill="y")
        self.txt_knowledge.pack(side="left", fill="both", expand=True)
        self.txt_knowledge.insert("1.0", self.config.get("knowledge_base", ""))
        
        # 知识库字数统计
        self.lbl_kb_count = tk.Label(body, text="0 字", font=("Menlo", 9), fg="#666666", bg="#1e1e1e", anchor="e")
        self.lbl_kb_count.grid(row=3, column=1, sticky="e", padx=(5, 0))
        self.txt_knowledge.bind("<KeyRelease>", lambda e: self._update_char_counts())
        
        # ---- 底部：实时预览 + 保存 ----
        preview_frame = tk.LabelFrame(
            body, text=" 📋 最终合成 System Prompt 预览 ",
            font=("PingFang SC", 10, "bold"), fg="#ff9500", bg="#1e1e1e",
            bd=1, relief="solid", labelanchor="nw"
        )
        preview_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        
        self.txt_preview = tk.Text(
            preview_frame, bg="#0a0a0a", fg="#aaaaaa", insertbackground="white",
            font=("Menlo", 9), bd=0, relief="flat", wrap="word", height=3, state="disabled"
        )
        pr_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.txt_preview.yview)
        self.txt_preview.configure(yscrollcommand=pr_scroll.set)
        pr_scroll.pack(side="right", fill="y")
        self.txt_preview.pack(side="left", fill="both", expand=True)
        
        # 保存按钮
        btn_save = tk.Label(
            body, font=("PingFang SC", 11, "bold"),
            fg="white", bd=0, height=2, cursor="hand2"
        )
        btn_save.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 10))
        self.set_button_state(btn_save, "💾 保存人设与知识库", "#af52de", self.save_persona_action)
        
        # 初始化字数和预览
        self._update_char_counts()
        self._refresh_prompt_preview()
    
    def _update_char_counts(self):
        """更新人设和知识库的字数统计，并刷新预览"""
        p_len = len(self.txt_persona.get("1.0", tk.END).strip())
        k_len = len(self.txt_knowledge.get("1.0", tk.END).strip())
        self.lbl_persona_count.config(text=f"{p_len} 字")
        self.lbl_kb_count.config(text=f"{k_len} 字")
        self._refresh_prompt_preview()
    
    def _refresh_prompt_preview(self):
        """刷新最终合成的 system prompt 预览"""
        final = self.build_final_system_prompt(
            self.txt_persona.get("1.0", tk.END).strip(),
            self.txt_knowledge.get("1.0", tk.END).strip()
        )
        self.txt_preview.config(state="normal")
        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert("1.0", final)
        self.txt_preview.config(state="disabled")
    
    def build_final_system_prompt(self, persona_text, knowledge_text):
        """将基础行为规则 + 人设 + 知识库合成为最终的 system prompt"""
        base_prompt = self.config.get("system_prompt", "")
        parts = []
        
        if base_prompt:
            parts.append(f"【基础行为规则】\n{base_prompt}")
        
        if persona_text:
            parts.append(f"【角色人设】\n{persona_text}")
        
        if knowledge_text:
            parts.append(f"【知识库参考资料】\n以下是你应当掌握的知识和信息，请在回复时参考：\n{knowledge_text}")
        
        return "\n\n".join(parts) if parts else base_prompt
    
    def apply_persona_preset(self, preset_name):
        """应用预设人设模板"""
        preset = self.PERSONA_PRESETS.get(preset_name, {})
        
        self.txt_persona.delete("1.0", tk.END)
        self.txt_persona.insert("1.0", preset.get("persona", ""))
        
        if preset.get("knowledge_base"):
            self.txt_knowledge.delete("1.0", tk.END)
            self.txt_knowledge.insert("1.0", preset.get("knowledge_base", ""))
        
        self._update_char_counts()
        logger.info(f"已应用预设人设模板: 【{preset_name}】")
    
    def save_persona_action(self):
        """保存人设与知识库到配置文件"""
        persona = self.txt_persona.get("1.0", tk.END).strip()
        knowledge = self.txt_knowledge.get("1.0", tk.END).strip()
        
        self.config["persona"] = persona
        self.config["knowledge_base"] = knowledge
        
        cfg_module.save_config(self.config)
        
        self.update_info_display()
        logger.success(f"✅ 人设与知识库已保存！人设 {len(persona)} 字，知识库 {len(knowledge)} 字。")
        messagebox.showinfo("保存成功", f"人设与知识库配置已保存！\n\n人设: {len(persona)} 字\n知识库: {len(knowledge)} 字", parent=self.root)

    def get_navigation_region(self):
        """返回导航列表总栏坐标"""
        nav_col = self.config.get("navigation_region")
        if nav_col:
            return nav_col
            
        # 回退兼容
        items = self.config.get("monitored_items", [])
        if not items:
            return None
        xs = [c["list_item_region"][0] for c in items]
        ys = [c["list_item_region"][1] for c in items]
        ws = [c["list_item_region"][2] for c in items]
        hs = [c["list_item_region"][3] for c in items]
        
        x = min(xs)
        y = min(ys) - 100
        if y < 0: y = 0
        w = max(ws)
        return [x, y, w, h]

    def get_current_active_chat_name(self):
        """
        通过截取并 OCR 内容框上方区域，获取当前处于活动状态的监控项名称
        """
        content_r = self.config.get("content_region")
        if not content_r:
            return ""
            
        # 截取内容区上方的标题栏 (Y 轴往上移 50 像素，高度为 50 像素)
        title_region = [
            int(content_r[0]),
            max(0, int(content_r[1] - 50)),
            int(content_r[2]),
            50
        ]
        
        img = screenshot_engine.capture_region(title_region)
        if not img:
            return ""
            
        try:
            from ocrmac import ocrmac
            ocr = ocrmac.OCR(img, language_preference=self.config.get("ocr_languages", ["zh-Hans", "en-US"]))
            results = ocr.recognize(px=True)
            texts = [r[0].strip() for r in results if r[0].strip()]
            return " ".join(texts)
        except Exception as e:
            logger.error(f"识别当前窗口标题栏出错: {e}")
            return ""

    def init_baseline_screenshots(self):
        """用于向下兼容，清空首次同步记录"""
        logger.info("已清空状态，准备重构通知标记扫描任务...")
        self.last_screenshots.clear()
        self.first_check.clear()

    def clear_monitored_chats(self):
        """向下兼容清空名单"""
        if messagebox.askyesno("清空确认", "确定清空黑白名单监控列表吗？"):
            self.config["filter_keywords"] = ""
            self.ent_filter_names.delete(0, tk.END)
            cfg_module.save_config(self.config)
            self.update_info_display()
            logger.info("已清空名单列表。")

    def update_wizard_status(self):
        """刷新 Tab 2 各步骤框选状态"""
        list_col = self.config.get("navigation_region")
        content_r = self.config.get("content_region")
        input_r = self.config.get("input_region")
        
        if list_col:
            self.lbl_status_nav_col.config(text=f"步骤 1: 【导航列表区域】 (当前状态: 🟢 已配置 {list_col})", fg="#00ff00")
        else:
            self.lbl_status_nav_col.config(text="步骤 1: 【导航列表区域】 (当前状态: ❌ 未配置)", fg="#ffffff")
            
        if content_r:
            self.lbl_status_content.config(text=f"步骤 2: 【内容展示区域】 (当前状态: 🟢 已配置 {content_r})", fg="#00ff00")
        else:
            self.lbl_status_content.config(text="步骤 2: 【内容展示区域】 (当前状态: ❌ 未配置)", fg="#ffffff")
            
        if input_r:
            self.lbl_status_input.config(text=f"步骤 3: 【输入框区域】 (当前状态: 🟢 已配置 {input_r})", fg="#00ff00")
        else:
            self.lbl_status_input.config(text="步骤 3: 【输入框区域】 (当前状态: ❌ 未配置)", fg="#ffffff")

    def update_info_display(self):
        """刷新展示面板"""
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        
        self.info_text.insert(tk.END, "Replox 参数概览：\n", "title")
        self.info_text.insert(tk.END, "--------------------------------------------------\n")
        
        # 过滤模式
        f_mode = self.config.get("filter_mode", "all")
        mode_str = "全部自动接管"
        if f_mode == "whitelist":
            mode_str = "只处理指定名单项目"
        elif f_mode == "blacklist":
            mode_str = "排除指定名单项目"
            
        self.info_text.insert(tk.END, f"🛡️ 过滤模式: 【{mode_str}】\n", "section")
        self.info_text.insert(tk.END, f"👥 过滤名单关键词: {self.config.get('filter_keywords', '无')}\n")
        self.info_text.insert(tk.END, f"📱 目标应用窗口: {self.config.get('target_app_name', '不限')}\n\n")
        
        # 区域坐标
        self.info_text.insert(tk.END, "📐 系统核心选区坐标：\n", "section")
        self.info_text.insert(tk.END, f"   🔸 导航列表栏: {self.config.get('navigation_region', '❌ 暂未配置')}\n")
        self.info_text.insert(tk.END, f"   🔸 内容展示区: {self.config.get('content_region', '❌ 暂未配置')}\n")
        self.info_text.insert(tk.END, f"   🔸 文字输入框: {self.config.get('input_region', '❌ 暂未配置')}\n\n")
        
        # 参数
        self.info_text.insert(tk.END, "🤖 运行轮询参数：\n", "section")
        self.info_text.insert(tk.END, f"   💡 基础轮询频率: {self.config.get('base_interval', 5.0)} 秒\n")
        self.info_text.insert(tk.END, f"   ⏳ 最大轮询上限: {self.config.get('max_interval', 60.0)} 秒\n")
        self.info_text.insert(tk.END, f"   🧪 运行确认模式: {'🛡️ 安全审核模式 (人工确认)' if self.safety_mode else '🟢 自动发送模式 (无人值守)'}\n")
        
        self.info_text.tag_config("title", font=("PingFang SC", 12, "bold"), foreground="#00ff00")
        self.info_text.tag_config("section", font=("PingFang SC", 11, "bold"), foreground="#ffffff")
        self.info_text.config(state="disabled")

    def start_region_calibration(self, mode):
        """开始倒计时引导并执行框选"""
        if getattr(self, "calibrating", False):
            return
        self.calibrating = True
        
        instruction = "框选区域"
        mode_desc = ""
        if mode == "smart":
            instruction = "请用鼠标按住左键拖拽，框选整个【目标窗口外框】"
            mode_desc = "智能一键配置（框选整个目标窗口外框）"
        elif mode == "navigation":
            instruction = "请用鼠标按住左键拖拽，框选【整个导航列表区域】"
            mode_desc = "分步配置 - 步骤 1：导航列表区域"
        elif mode == "content":
            instruction = "请用鼠标按住左键拖拽，框选【内容展示区域】"
            mode_desc = "分步配置 - 步骤 2：内容展示区域"
        elif mode == "input":
            instruction = "请用鼠标按住左键拖拽，框选【输入框区域】"
            mode_desc = "分步配置 - 步骤 3：输入框区域"
            
        # 唤起醒目的居中倒计时弹窗
        dialog = CountdownDialog(self.root, 3, mode_desc)
        self.lbl_wizard_tip.config(text="⏱️ 倒计时准备中，请准备好窗口...", fg="#ff3b30")
        self.root.wait_window(dialog)
        
        # 倒计时结束，立即执行截图
        self.lbl_wizard_tip.config(text="📸 正在捕捉屏幕背景截图...", fg="#00ff00")
        self.root.update()
        time.sleep(0.3)
        
        import region_selector
        region = region_selector.select_region(instruction, self.root)
        self.lbl_wizard_tip.config(text="💡 经典比例：侧边栏 8%，导航列表 27%，内容区 65%，打字框 20% 高度。", fg="#ff9500", font=("PingFang SC", 10))
        
        self.calibrating = False # 释放锁
        
        if not region:
            logger.warn("选区配置已被取消")
            self.auto_start_if_configured()
            return
            
        self.handle_calibration_result(mode, region)

    def auto_start_if_configured(self):
        """配齐坐标后自动开启"""
        has_nav = self.config.get("navigation_region")
        has_content = self.config.get("content_region")
        has_input = self.config.get("input_region")
        
        if has_nav and has_content and has_input:
            self.lbl_status.config(text="监控状态: 🟢 运行中 (正在监听)", fg="#00ff00")
            self.set_button_state(self.btn_run, "⏸️ 暂停自动监控", "#f5a623")
            self.is_monitoring = True
        else:
            self.lbl_status.config(text="监控状态: 🔴 选区未配齐，请先配置", fg="#ff3b30")
            self.set_button_state(self.btn_run, "🚀 开启自动监控", "#27ae60")
            self.is_monitoring = False

    def show_regions_visualization(self):
        """
        在屏幕上以半透明有色图层形式高亮显示当前配置的三个核心选区，
        供用户直观校验校准。2.5 秒后自动关闭。
        """
        regions = {
            "navigation_region": ("👥 导航列表区域", "#ff3b30"),   # 红色
            "content_region": ("💬 内容展示区域", "#27ae60"),  # 绿色
            "input_region": ("⌨️ 输入框区域", "#007aff"),     # 蓝色
        }
        
        overlay_windows = []
        
        for key, (label_text, color) in regions.items():
            r = self.config.get(key)
            if not r:
                continue
            try:
                x, y, w, h = int(r[0]), int(r[1]), int(r[2]), int(r[3])
                
                # 创建无边框置顶半透明窗口
                win = tk.Toplevel(self.root)
                win.overrideredirect(True)
                win.attributes("-topmost", True)
                win.geometry(f"{w}x{h}+{x}+{y}")
                win.config(bg=color)
                win.attributes("-alpha", 0.28) # 28% 半透明度，既显眼又不遮挡底层应用
                
                # 在窗口上放一个居中的文字标签，提示区域名称
                lbl = tk.Label(
                    win, text=label_text, font=("PingFang SC", 12, "bold"),
                    fg="white", bg=color
                )
                lbl.pack(expand=True)
                
                overlay_windows.append(win)
            except Exception as e:
                logger.error(f"渲染选区高亮 [{key}] 出错: {e}")
                
        if overlay_windows:
            logger.info("💡 正在屏幕上展示当前三个选区的半透明高亮预览（持续 2.5 秒）...")
            self.root.after(2500, lambda: self.destroy_overlay_windows(overlay_windows))
            
    def destroy_overlay_windows(self, windows):
        for win in windows:
            try:
                win.destroy()
            except Exception:
                pass

    def start_monitoring_action(self):
        """手动开启/暂停监控"""
        has_list = self.config.get("navigation_region")
        has_content = self.config.get("content_region")
        has_input = self.config.get("input_region")
        
        if not (has_list and has_content and has_input):
            messagebox.showwarning("警告", "您尚未完成屏幕界面区域校准，请先在‘屏幕区域配置向导’中完成框选。", parent=self.root)
            self.notebook.select(self.tab_config)
            return
            
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.set_button_state(self.btn_run, "⏸️ 暂停自动监控", "#f5a623")
            self.lbl_status.config(text="监控状态: 🟢 运行中 (正在监听)", fg="#00ff00")
            logger.success("已恢复自动监控扫描。")
        else:
            self.set_button_state(self.btn_run, "🚀 开启自动监控", "#27ae60")
            self.lbl_status.config(text="监控状态: 🔴 已暂停", fg="#ff3b30")
            logger.warn("自动监控已暂停。")

    def toggle_reply(self):
        self.reply_enabled = not self.reply_enabled
        self.config["reply_enabled"] = self.reply_enabled
        cfg_module.save_config(self.config)
        self.update_info_display()
        if self.reply_enabled:
            self.set_button_state(self.btn_reply, "🤖 暂停自动回复", "#007aff")
            logger.success("自动回复功能已启用。")
        else:
            self.set_button_state(self.btn_reply, "🤖 开启自动回复", "#007aff")
            logger.warn("自动回复功能已暂停，系统仅扫描记录而不发信。")

    def toggle_safety_mode(self):
        self.safety_mode = not self.safety_mode
        self.update_info_display()
        if self.safety_mode:
            self.set_button_state(self.btn_safety, "🛡️ 安全确认模式", "#8e44ad")
            logger.warn("已切换到安全确认模式：AI 回复前会在屏幕上弹出对话框，由您人工审核确认后才模拟输入发送。")
        else:
            self.set_button_state(self.btn_safety, "🛡️ 自动回复模式", "#8e44ad")
            logger.success("已切换到自动回复模式：所有检测到的新消息将由 AI 自动输入发送，无需手动确认。")

    def on_log_received(self, message):
        self.ui_queue.put(lambda: self.append_log(message))

    def append_log(self, text):
        self.log_widget.config(state="normal")
        self.log_widget.insert(tk.END, text)
        self.log_widget.see(tk.END)
        self.log_widget.config(state="disabled")

    def check_ui_queue(self):
        try:
            while True:
                task = self.ui_queue.get_nowait()
                task()
                self.ui_queue.task_done()
        except queue.Empty:
            pass
        if self.thread_active:
            self.root.after(100, self.check_ui_queue)

    def on_failsafe_triggered(self):
        self.lbl_status.config(text="监控状态: ⚠️ 安全中止 (已暂停)", fg="#ff9500")
        self.set_button_state(self.btn_run, "🚀 开启自动监控", "#27ae60")

    def handle_calibration_result(self, mode, region):
        """处理框选结果并回显到 GUI 上"""
        if mode == "smart":
            X, Y, W, H = region
            logger.info(f"一键智能配置应用窗口外框: {region}。开始自动拆分功能区...")
            
            # 比例关系划分 (内容展示区与输入框)
            self.config["content_region"] = [
                int(X + W * 0.38),
                int(Y + 55),
                int(W * 0.62 - 15),
                int(H * 0.65)
            ]
            self.config["input_region"] = [
                int(X + W * 0.38 + 15),
                int(Y + H * 0.76),
                int(W * 0.62 - 30),
                int(H * 0.20)
            ]
            
            # 定位左侧导航列表区并保存
            list_col_x = int(X + W * 0.08)
            list_col_w = int(W * 0.28)
            list_col_y = int(Y + 60)
            list_col_h = int(H - 70)
            self.config["navigation_region"] = [list_col_x, list_col_y, list_col_w, list_col_h]
            
            # 获取用户输入的名字作为默认过滤名单
            friend_names = self.ent_filter_names.get().strip()
            self.config["filter_keywords"] = friend_names
            
            # 同步填充 monitored_items 作为旧版数据结构的向下兼容
            names = [n.strip() for n in friend_names.replace(",", " ").replace("，", " ").split() if n.strip()]
            monitored_items = []
            for idx, name in enumerate(names):
                est_y = list_col_y + 15 + idx * 64
                item_region = [int(list_col_x), int(est_y), int(W * 0.20), 64]
                monitored_items.append({
                    "name": name,
                    "list_item_region": item_region
                })
            self.config["monitored_items"] = monitored_items
            logger.success("智能一键拆分配置完成！导航列表区、内容展示区、输入框区均已自动校准。")
            
        elif mode == "navigation":
            self.config["navigation_region"] = region
            logger.success(f"导航列表栏坐标已更新: {region}")
            
        elif mode == "content":
            self.config["content_region"] = region
            logger.success(f"内容展示区坐标已更新: {region}")
            
        elif mode == "input":
            self.config["input_region"] = region
            logger.success(f"输入框区域坐标已更新: {region}")
            
        # 保存并刷新显示
        cfg_module.save_config(self.config)
        self.update_info_display()
        self.update_wizard_status()
        self.auto_start_if_configured()
        
        # 配置完后自动弹出高亮可视化预览，方便用户核对
        self.show_regions_visualization()

    def is_target_app_frontmost(self):
        """
        检测目标应用是否为当前 macOS 系统的最前台/焦点活动窗口
        """
        target_app = self.config.get("target_app_name", "").strip()
        if not target_app:
            return True # 如果未指定目标应用，默认不限制前台检测
        try:
            import subprocess
            cmd = ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            frontmost_app = result.stdout.strip()
            return frontmost_app.lower() == target_app.lower()
        except Exception:
            return True

    def monitor_loop(self):
        """
        后台通知标记扫描的自适应轮询子线程。
        """
        import pyautogui
        pyautogui.FAILSAFE = True
        
        while self.thread_active:
            if not self.is_monitoring:
                time.sleep(1.0)
                continue
                
            # 增加前台活跃窗口检测，防止目标应用在后台时乱点乱输
            if not self.is_target_app_frontmost():
                if not getattr(self, "_last_was_background", False):
                    logger.warn("⚠️ 检测到目标应用当前处于后台，暂停自动监控，切回后将自动恢复。")
                    self._last_was_background = True
                time.sleep(2.0)
                continue
            else:
                if getattr(self, "_last_was_background", False):
                    logger.success("🟢 目标应用已切回前台，恢复自动扫描。")
                    self._last_was_background = False
                
            try:
                any_chat_replied = False
                list_col = self.get_navigation_region()
                
                if not list_col:
                    time.sleep(2.0)
                    continue
                    
                # 1. 截取整个列表总栏
                list_img = screenshot_engine.capture_region(list_col)
                if not list_img:
                    time.sleep(1.0)
                    continue
                    
                # 2. 实时 OCR 获取当前可见的所有列表项名称与 Y 轴坐标
                try:
                    from ocrmac import ocrmac
                    ocr = ocrmac.OCR(list_img, language_preference=self.config.get("ocr_languages", ["zh-Hans", "en-US"]))
                    ocr_results = ocr.recognize(px=True)
                except Exception as e:
                    logger.error(f"扫描列表 OCR 出错: {e}")
                    time.sleep(1.0)
                    continue
                    
                scale = screenshot_engine.get_retina_scale()
                
                # 3. 限制 X 坐标并识别名称候选行 (屏蔽右侧时间戳等干扰)
                name_candidates = []
                for text, conf, bbox in ocr_results:
                    text = text.strip()
                    if len(text) < 1 or conf < 0.4:
                        continue
                        
                    lx, ly, lw, lh = bbox
                    lx_pt = lx / scale
                    ly_pt = ly / scale
                    lh_pt = lh / scale
                    
                    # 导航列表项的 X 坐标通常在左侧部分，根据宽度比例过滤
                    nav_width = list_col[2] if list_col else 200
                    if lx_pt <= nav_width * 0.7:
                        name_candidates.append({
                            "text": text,
                            "lx": lx_pt,
                            "ly": ly_pt,
                            "lh": lh_pt,
                            "bbox": bbox
                        })
                
                # 4. 根据纵向距离剔除下方的预览行 (两个候选文字块垂直距离小于 35 像素时，下方通常为预览文本)
                name_candidates.sort(key=lambda x: x["ly"])
                true_names = []
                for i, cand in enumerate(name_candidates):
                    is_preview = False
                    for prev in name_candidates[:i]:
                        if 0 < cand["ly"] - prev["ly"] < 35:
                            is_preview = True
                            break
                    if not is_preview:
                        true_names.append(cand)
                
                # 5. 过滤模式解析 (支持大小写敏感无关的名单匹配)
                f_mode = self.config.get("filter_mode", "all")
                f_names_str = self.config.get("filter_keywords", "")
                target_names = {n.strip().lower() for n in f_names_str.replace(",", " ").replace("，", " ").split() if n.strip()}
                
                visible_friends = []
                for cand in true_names:
                    name_lower = cand["text"].lower()
                    should_handle = False
                    
                    if f_mode == "all":
                        should_handle = True
                    elif f_mode == "whitelist":
                        should_handle = any(t_name in name_lower for t_name in target_names)
                    elif f_mode == "blacklist":
                        should_handle = not any(t_name in name_lower for t_name in target_names)
                        
                    if should_handle:
                        visible_friends.append({
                            "name": cand["text"],
                            "relative_y": cand["ly"],
                            "lh": cand["lh"],
                            "bbox": cand["bbox"]
                        })
                
                # 4. 对符合的列表行执行局部通知标记（未读徽章）图像提取与判断
                for friend in visible_friends:
                    if not self.thread_active or not self.is_monitoring:
                        break
                        
                    name = friend["name"]
                    ly_pt = friend["relative_y"]
                    lh_pt = friend["lh"]
                    
                    # 裁剪行切片 (高度 64)
                    name_center_y = ly_pt + lh_pt / 2
                    crop_y_local = name_center_y - 32
                    if crop_y_local < 0: crop_y_local = 0
                    
                    crop_y_px = int(crop_y_local * scale)
                    crop_h_px = int(64 * scale)
                    
                    img_w, img_h = list_img.size
                    if crop_y_px + crop_h_px > img_h:
                        crop_h_px = img_h - crop_y_px
                        
                    if crop_h_px <= 0:
                        continue
                        
                    item_img = list_img.crop((0, crop_y_px, img_w, crop_y_px + crop_h_px))
                    
                    # 检查是否有未读标记
                    has_unread = has_notification_badge(item_img, self.config, scale)
                    is_first = self.first_check.get(name, True)
                    
                    if has_unread or is_first:
                        self.first_check[name] = False
                        
                        if is_first:
                            logger.info(f"🔄 启动首次同步：检查「{name}」的窗口是否积压未读...")
                        else:
                            logger.success(f"🔴 发现新消息！检测到「{name}」带有通知标记")
                            
                        # 动态点击前校验：如果当前已经处于该项的内容窗口中，就不要重复点击
                        active_name = self.get_current_active_chat_name()
                        if not active_name or (name not in active_name and active_name not in name):
                            click_x = list_col[0] + list_col[2] * 0.45
                            click_y = list_col[1] + ly_pt + 10
                            chat_controller.click_region([click_x - 15, click_y - 15, 30, 30])
                            time.sleep(0.5)
                        else:
                            logger.info(f"当前已处于「{name}」对话窗口，跳过重复的点击动作。")
                            
                        # 检查内容区域
                        content_img = screenshot_engine.capture_region(self.config["content_region"])
                        if content_img:
                            has_new, incoming_msgs, full_history = ocr_engine.parse_content_region(
                                content_img,
                                languages=self.config.get("ocr_languages", ["zh-Hans", "en-US"])
                            )
                            
                            if has_new:
                                # 提取特征签名，防止重复回复
                                incoming_sig = "\n".join([m["text"] for m in full_history if m["direction"] == "LEFT"])
                                if incoming_sig == self.last_replied_sig.get(name):
                                    logger.debug(f"已处理过「{name}」的当前内容，跳过。")
                                    continue
 
                                any_chat_replied = True
                                incoming_text = " | ".join(incoming_msgs)
                                logger.message_in(name, incoming_text)
                                
                                # AI 生成
                                reply = auto_replier.generate_reply(full_history, self.config)
                                if reply:
                                    should_send = True
                                    if self.safety_mode:
                                        confirm_event = threading.Event()
                                        confirm_result = [False]
                                        
                                        def ask_user(n=name, it=incoming_text, r=reply):
                                            dialog = ConfirmDialog(self.root, n, it, r, self.app_icon_tk)
                                            self.root.wait_window(dialog)
                                            confirm_result[0] = dialog.result
                                            confirm_event.set()
                                            
                                        self.ui_queue.put(ask_user)
                                        confirm_event.wait()
                                        should_send = confirm_result[0]
                                        
                                    if should_send:
                                        if self.reply_enabled:
                                            # 二次校验：在真正物理输入的前一刻，再次检测当前窗口的标题，防范用户在确认期间切换了窗口
                                            active_chat_title = self.get_current_active_chat_name()
                                            if not active_chat_title or (name not in active_chat_title and active_chat_title not in name):
                                                logger.error(f"🚨 安全防发错拦截：检测到当前窗口已被手动切换至「{active_chat_title}」，与目标发送对象「{name}」不符！已自动终止。")
                                                continue
                                                
                                            chat_controller.send_text_input(reply, self.config["input_region"])
                                            logger.message_out(name, reply)
                                            self.last_replied_sig[name] = incoming_sig
                                            time.sleep(1.0)
                                        else:
                                            logger.info(f"[未开启回复] 模拟发送给 [{name}]: {reply}")
                                    else:
                                        logger.warn(f"❌ 用户取消并拒绝发送该回复给 [{name}]。")
                            else:
                                logger.debug(f"检查了「{name}」，但当前历史记录内并无新消息。")
                        else:
                            logger.error(f"读取「{name}」内容框失败。")
                
                # 5. 额外动作：检查当前活跃窗口（解决留在当前聊天，无红点的问题）
                if self.is_monitoring and self.thread_active:
                    content_img = screenshot_engine.capture_region(self.config["content_region"])
                    if content_img:
                        has_new, incoming_msgs, full_history = ocr_engine.parse_content_region(
                            content_img,
                            languages=self.config.get("ocr_languages", ["zh-Hans", "en-US"])
                        )
                        if has_new:
                            current_name = self.get_current_active_chat_name() or "当前活跃对话"
                            incoming_sig = "\n".join([m["text"] for m in full_history if m["direction"] == "LEFT"])
                            if incoming_sig == self.last_replied_sig.get(current_name):
                                continue
                                
                            any_chat_replied = True
                            incoming_text = " | ".join(incoming_msgs)
                            logger.message_in(current_name, incoming_text)
                            
                            reply = auto_replier.generate_reply(full_history, self.config)
                            if reply:
                                should_send = True
                                if self.safety_mode:
                                    confirm_event = threading.Event()
                                    confirm_result = [False]
                                    
                                    def ask_user(n=current_name, it=incoming_text, r=reply):
                                        dialog = ConfirmDialog(self.root, n, it, r, self.app_icon_tk)
                                        self.root.wait_window(dialog)
                                        confirm_result[0] = dialog.result
                                        confirm_event.set()
                                        
                                    self.ui_queue.put(ask_user)
                                    confirm_event.wait()
                                    should_send = confirm_result[0]
                                    
                                if should_send:
                                    if self.reply_enabled:
                                        # 二次校验：防范在弹窗审核期间用户手动切换了窗口
                                        active_chat_title = self.get_current_active_chat_name()
                                        if not active_chat_title or (current_name not in active_chat_title and active_chat_title not in current_name):
                                            logger.error(f"🚨 安全防发错拦截：当前活动窗口已由「{current_name}」切换为「{active_chat_title}」，已自动终止。")
                                            continue
                                            
                                        chat_controller.send_text_input(reply, self.config["input_region"])
                                        logger.message_out(current_name, reply)
                                        self.last_replied_sig[current_name] = incoming_sig
                                        time.sleep(1.0)
                                    else:
                                        logger.info(f"[未开启回复] 模拟发送给 [{current_name}]: {reply}")
                                else:
                                    logger.warn(f"❌ 用户取消并拒绝发送该回复给 [{current_name}]。")
                
                # 6. 自适应频率退避
                if any_chat_replied:
                    self.timer.reset()
                else:
                    self.timer.increase()
                    
                sleep_sec = self.timer.get_sleep_time()
                self.ui_queue.put(lambda sec=sleep_sec: self.lbl_interval.config(text=f"轮询频率: {sec:.1f} 秒一次"))
                
                # 分段休眠，以方便随时响应暂停
                slept = 0
                while slept < sleep_sec and self.thread_active and self.is_monitoring:
                    time.sleep(0.2)
                    slept += 0.2
                    
            except pyautogui.FailSafeException:
                self.is_monitoring = False
                self.ui_queue.put(self.on_failsafe_triggered)
                logger.error("[警告] 检测到鼠标移动至屏幕角落！触发安全防夺权机制，自动监控已紧急暂停。")
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"监听子线程中发生未捕获异常: {e}")
                time.sleep(2.0)

    def on_close(self):
        """关闭程序时，干净释放线程"""
        if messagebox.askyesno("确认退出", "确定退出 Replox 吗？", parent=self.root):
            self.thread_active = False
            try:
                self.root.withdraw()
            except Exception:
                pass
            time.sleep(0.3)
            try:
                self.root.destroy()
            except Exception:
                pass
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Replox 妙答AI聊天回复助手")
    parser.add_argument("--auto-reply", action="store_true", help="启动时直接自动回复而非安全模式")
    args = parser.parse_args()
    
    root = tk.Tk()
    app = ScreenFlowApp(root, args)
    root.mainloop()

if __name__ == "__main__":
    main()
