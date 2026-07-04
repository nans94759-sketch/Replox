from PIL import Image, ImageChops

def detect_change(img1, img2, threshold=0.005, diff_pixel_intensity=15):
    """
    对比两张图片，判断是否有显著变化。
    
    :param img1: 第一张 PIL 图像
    :param img2: 第二张 PIL 图像
    :param threshold: 变化像素占比阈值，例如 0.005 表示有超过 0.5% 的像素发生变化即判定为变化
    :param diff_pixel_intensity: 单像素灰度差异判定阈值 (0-255)，过滤微弱噪点
    :return: (has_changed, diff_ratio)
    """
    if img1 is None or img2 is None:
        return False, 0.0
        
    # 确保大小一致，如果不一致则缩放（防御性编程）
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)
        
    # 计算绝对差异图像
    diff = ImageChops.difference(img1, img2)
    # 转为灰度图以方便计算
    diff_gray = diff.convert("L")
    
    # 过滤微弱变化像素（低于阈值的设为 0）
    diff_data = diff_gray.tobytes()
    changed_pixels = sum(1 for pixel in diff_data if pixel > diff_pixel_intensity)
    total_pixels = img1.size[0] * img1.size[1]
    
    diff_ratio = changed_pixels / total_pixels
    has_changed = diff_ratio >= threshold
    
    return has_changed, diff_ratio
