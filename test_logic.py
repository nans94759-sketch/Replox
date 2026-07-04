import unittest
from PIL import Image, ImageDraw
import os
import sys

# 添加当前路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from change_detector import detect_change
from adaptive_timer import AdaptiveTimer

class TestLogic(unittest.TestCase):
    def setUp(self):
        # 创建两张测试图片
        self.img1 = Image.new("RGB", (100, 100), color="white")
        
        self.img2 = Image.new("RGB", (100, 100), color="white")
        draw = ImageDraw.Draw(self.img2)
        # 在第二张图上画一个小黑块（模拟通知标记）
        draw.rectangle([40, 40, 60, 60], fill="black")
        
    def test_change_detection(self):
        # 1. 相同的图应该判定没有变化
        has_changed, ratio = detect_change(self.img1, self.img1, threshold=0.01)
        self.assertFalse(has_changed)
        self.assertEqual(ratio, 0.0)
        
        # 2. 不同的图应该判定有变化 (400 像素变化占 10000 像素的 4%)
        has_changed, ratio = detect_change(self.img1, self.img2, threshold=0.01)
        self.assertTrue(has_changed)
        self.assertAlmostEqual(ratio, 0.04, places=2)
        
        # 3. 如果把阈值调得非常高，应该判定无变化
        has_changed, ratio = detect_change(self.img1, self.img2, threshold=0.10)
        self.assertFalse(has_changed)
        
    def test_adaptive_timer(self):
        timer = AdaptiveTimer(base_interval=5.0, max_interval=20.0, multiplier=1.5)
        
        # 初始值
        self.assertEqual(timer.get_sleep_time(), 5.0)
        
        # 闲置不退避延时，保持固定检测间隔
        timer.increase()
        self.assertEqual(timer.get_sleep_time(), 5.0)
        
        timer.increase()
        self.assertEqual(timer.get_sleep_time(), 5.0)
        
        # 重置
        timer.reset()
        self.assertEqual(timer.get_sleep_time(), 5.0)

if __name__ == "__main__":
    unittest.main()
