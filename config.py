# 智能课程表配置文件

# ===== 软件基本信息 =====
# 软件版本信息
VERSION = "1.2"

# 发布日期
RELEASE_DATE = "2025年10月10日"

# 软件名称
APP_NAME = "智能课程表"

# 作者信息
AUTHOR = "hjcba"

# ===== 课程表设置 =====
# 每周上课天数（1-7，周一到周日）
WEEKLY_CLASS_DAYS = 5  # 周一到周五

# 每天最大课时数
MAX_DAILY_SECTIONS = 12

# 每节课时长（分钟）
SECTION_DURATION = 45

# 课间休息时长（分钟）
BREAK_DURATION = 10

# 起始周（第几周开始）
START_WEEK = 1

# 总周数
TOTAL_WEEKS = 18

# ===== 界面设置 =====
# 主题颜色
PRIMARY_COLOR = "#4CAF50"  #主色调（绿色）
SECONDARY_COLOR = "#2196F3"  # 辅助色（蓝色）
BACKGROUND_COLOR = "#f5f5f5"  # 背景色
TEXT_COLOR = "#333333"  # 文本颜色

# 字体设置
DEFAULT_FONT = "SimHei"
FONT_SIZE = 10
HEADER_FONT_SIZE = 12
TITLE_FONT_SIZE = 24

# 窗口设置
MAIN_WINDOW_WIDTH = 1000
MAIN_WINDOW_HEIGHT = 700
SPLASH_SCREEN_WIDTH = 400
SPLASH_SCREEN_HEIGHT = 200
FLOATING_WINDOW_WIDTH = 600
FLOATING_WINDOW_HEIGHT = 300

# ===== 提醒设置 =====
# 默认提前提醒时间（分钟）
DEFAULT_REMINDER_MINUTES = 10

# 是否启用声音提醒
ENABLE_SOUND_REMINDER = True

# 是否启用弹窗提醒
ENABLE_POPUP_REMINDER = True

# ===== 文件路径设置 =====
# 课程表数据文件路径
SCHEDULE_FILE_PATH = "schedule.json"

# 示例课程表文件路径
EXAMPLE_SCHEDULE_FILE_PATH = "example_schedule.json"

# 日志文件路径
LOG_FILE_PATH = "classtable.log"


# ===== 更新日志 =====
# 更新日志信息，格式为：版本号 -> 更新内容
UPDATE_LOGS = {
    
    "1.2": {
        "date": "2025年8月30日",
        "content": """
        1. 新增课程表打印功能，支持打印预览和直接打印
        2. 添加课程表统计功能，显示课程数量、总学时、平均学分、总学分等信息
        3. 优化课程搜索功能，支持按课程名称、教师名称、教室名称搜索
        4. 添加课程表导入/导出功能，支持导入/导出为JSON文件
        """
    },
    
    "1.1": {
        "date": "2025年8月30日",
        "content": """
        1. 新增课程表打印功能，支持打印预览和直接打印
        2. 打印时保留课程颜色和跨节课程显示
        3. 优化打印文档布局，添加页面边距和内容区域
        4. 修复打印预览中文本错位问题
        5. 改进打印标题和日期显示位置
        """
    },
    "1.0": {
        "date": "2025年8月30日",
        "content": """
        1. 全新界面设计，更加美观和现代化
        2. 新增课程表导入/导出功能
        3. 添加考试日历功能
        4. 优化课程提醒系统
        5. 修复已知bug
        """
    },
    "0.9": {
        "date": "2025年7月15日",
        "content": """
        1. 添加浮动窗口功能
        2. 优化移动设备兼容性
        3. 改进课程表打印功能
        4. 修复部分显示问题
        """
    },
    "0.8": {
        "date": "2025年6月1日",
        "content": """
        1. 新增自定义背景功能
        2. 优化课程搜索功能
        3. 添加课程表统计功能
        4. 修复部分性能问题
        """
    },
    "0.7": {
        "date": "2025年5月10日",
        "content": """
        1. 初始版本发布
        2. 基本课程表功能
        3. 课程提醒功能
        """
    }
}