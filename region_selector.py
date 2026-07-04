import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
import mss

class SelectionOverlay:
    """
    截图蒙版选择器 (Tkinter Toplevel 悬浮顶层窗口)
    """
    def __init__(self, instruction, bg_image, dark_image, mx, my, screen_w, screen_h, scale, parent):
        self.instruction = instruction
        self.bg_image = bg_image
        self.dark_image = dark_image
        self.mx = mx
        self.my = my
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.scale = scale
        self.parent = parent
        
        self.win = tk.Toplevel(self.parent)
        self.win.title("屏幕区域选择")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{self.screen_w}x{self.screen_h}+{self.mx}+{self.my}")
        self.win.config(cursor="cross")
        
        # 画布
        self.canvas = tk.Canvas(self.win, width=self.screen_w, height=self.screen_h,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        
        # 变暗的截图做背景
        self.dark_tk = ImageTk.PhotoImage(self.dark_image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.dark_tk, tags="bg")
        
        # 高亮图像引用
        self.highlight_img_ref = None
        self.highlight_item = None
        
        # 顶部 UI 栏 (进一步增加高度并下移文本与按钮，确保绝对不会被刘海屏和顶栏遮挡)
        banner_h = 130
        self.canvas.create_rectangle(0, 0, self.screen_w, banner_h, fill="black", outline="", tags="ui")
        self.canvas.create_text(
            self.screen_w // 2, 52,
            text=instruction,
            font=("PingFang SC", 15, "bold"),
            fill="#00ff00", tags="ui"
        )
        self.canvas.create_text(
            self.screen_w // 2, 90,
            text="用鼠标按住左键拖拽框选，松开鼠标自动完成确认",
            font=("PingFang SC", 11),
            fill="#cccccc", tags="ui"
        )
        
        # 右上角取消退出按钮 (继续下移按钮防止遮挡)
        btn_w, btn_h = 100, 30
        btn_x = self.screen_w - btn_w - 20
        btn_y = 50
        self.canvas.create_rectangle(
            btn_x, btn_y, btn_x + btn_w, btn_y + btn_h,
            fill="#cc0000", outline="#ff3333", width=1, tags="cancel_btn"
        )
        self.canvas.create_text(
            btn_x + btn_w // 2, btn_y + btn_h // 2,
            text="❌ 取消退出", font=("PingFang SC", 11, "bold"),
            fill="white", tags="cancel_btn"
        )
        self.canvas.tag_bind("cancel_btn", "<Button-1>", self.cancel_selection)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.selected_region = None
        
        # 绑定鼠标
        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # 绑定键盘 Esc 键作为取消
        self.win.bind("<Escape>", self.cancel_selection)
        self.win.focus_force()

    def on_button_press(self, event):
        if event.y < 60:
            return
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        if self.highlight_item:
            self.canvas.delete(self.highlight_item)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#00ff00", width=2, tags="sel_rect"
        )

    def on_move_press(self, event):
        if self.start_x is None:
            return
        event_x, event_y = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, event_x, event_y)
        
        x1, y1 = min(self.start_x, event_x), min(self.start_y, event_y)
        x2, y2 = max(self.start_x, event_x), max(self.start_y, event_y)
        
        if x2 - x1 > 5 and y2 - y1 > 5:
            cropped = self.bg_image.crop((x1, y1, x2, y2))
            self.highlight_img_ref = ImageTk.PhotoImage(cropped)
            if self.highlight_item:
                self.canvas.delete(self.highlight_item)
            self.highlight_item = self.canvas.create_image(x1, y1, anchor="nw",
                                                            image=self.highlight_img_ref,
                                                            tags="highlight")
            self.canvas.tag_raise("sel_rect")
            self.canvas.tag_raise("ui")
            self.canvas.tag_raise("cancel_btn")

    def on_button_release(self, event):
        if self.start_x is None:
            return
        end_x, end_y = event.x, event.y
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        
        width = x2 - x1
        height = y2 - y1
        
        if width > 10 and height > 10:
            # 返回屏幕绝对坐标：叠加当前显示器偏移量，确保多显示器完美对接
            self.selected_region = (x1 + self.mx, y1 + self.my, width, height)
            self.canvas.itemconfig(self.rect, outline="#00ff00", width=3)
            self.win.after(250, self._close)
        else:
            self.start_x = None
            if self.rect:
                self.canvas.delete(self.rect)
            if self.highlight_item:
                self.canvas.delete(self.highlight_item)

    def _close(self):
        self.win.destroy()

    def cancel_selection(self, event=None):
        self.selected_region = None
        self.win.destroy()

    def get_region(self):
        self.parent.wait_window(self.win)
        return self.selected_region

def capture_screen(px, py):
    """
    抓取当前主程序所在显示器的全屏截图，生成原版和变暗版。
    """
    with mss.MSS() as sct:
        target_monitor = sct.monitors[1] # 默认主显示器
        for monitor in sct.monitors[1:]:
            left = monitor["left"]
            top = monitor["top"]
            right = left + monitor["width"]
            bottom = top + monitor["height"]
            if left <= px <= right and top <= py <= bottom:
                target_monitor = monitor
                break
                
        sct_img = sct.grab(target_monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        # 提取高精度的逻辑参数 (mss 自动匹配多屏 Retina 比例)
        mx = target_monitor["left"]
        my = target_monitor["top"]
        mw = target_monitor["width"]
        mh = target_monitor["height"]
        
        scale = sct_img.size[0] / mw
        img_resized = img.resize((mw, mh), Image.LANCZOS)
        
        enhancer = ImageEnhance.Brightness(img_resized)
        dark = enhancer.enhance(0.35)
        
        return img_resized, dark, mx, my, mw, mh, scale

def select_region(instruction, parent_root):
    """
    便捷框选函数，直接在传入 parent_root 上创建顶层选区
    """
    # 1. 在隐藏窗口前，获取主窗口在屏幕上的绝对坐标位置，防止隐藏后 winfo 坐标变为无效值
    parent_root.update_idletasks()
    px = parent_root.winfo_x()
    py = parent_root.winfo_y()
    
    # 2. 隐藏主窗口以截取干净的屏幕背景
    parent_root.withdraw()
    parent_root.update()
    
    # 3. 截图
    bg_image, dark_image, mx, my, screen_w, screen_h, scale = capture_screen(px, py)
    
    # 3. 截图完成后立即恢复并置底主窗口，防范 Tkinter 对话框挂起死锁
    parent_root.deiconify()
    parent_root.lower()
    parent_root.update()
    
    overlay = SelectionOverlay(instruction, bg_image, dark_image, mx, my, screen_w, screen_h, scale, parent_root)
    return overlay.get_region()
