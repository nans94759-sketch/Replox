import logger

class AdaptiveTimer:
    def __init__(self, base_interval=5.0, max_interval=60.0, multiplier=1.5):
        self.base_interval = base_interval
        self.current_interval = base_interval
        
    def reset(self):
        """
        当检测到活动时，无需特别重置，因为间隔已为固定值
        """
        pass
        
    def increase(self):
        """
        闲置时不再增加轮询间隔，直接使用固定的检测间隔，防止响应过度迟钝
        """
        pass
        
    def get_sleep_time(self):
        return self.base_interval
