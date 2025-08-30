import sys
import json
import os
import random
import string
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,QLabel, QPushButton, QDialog, QLineEdit, QComboBox, QSpinBox, QColorDialog,QMessageBox, QCalendarWidget, QTabWidget, QInputDialog, QListWidget, QListWidgetItem,QMenu, QAction, QToolBar, QStatusBar, QSystemTrayIcon, QScrollArea, QGroupBox, QFileDialog
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QBrush, QPixmap, QTextDocument, QTextOption
from PyQt5.QtCore import Qt, QDate, QTime, QTimer, pyqtSignal, QRectF, QSizeF
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

# 导入配置信息
import config

# 悬浮课程表窗口类
class FloatingScheduleWindow(QWidget):
    closed = pyqtSignal()  # 定义关闭信号
    
    def __init__(self, courses, day_names, parent=None):
        """初始化悬浮课程表窗口。"""
        super().__init__(parent)
        self.courses = courses
        self.day_names = day_names
        self.setWindowTitle("悬浮课程表")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(config.FLOATING_WINDOW_WIDTH, config.FLOATING_WINDOW_HEIGHT + 100)  # 增加高度以容纳时间信息
        self.init_ui()
        
        # 设置定时器，每秒更新一次时间信息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_info)
        self.timer.start(1000)  # 1000毫秒 = 1秒
        
    def init_ui(self):
        """初始化悬浮窗口的用户界面。"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建时间信息区域
        time_info_widget = QWidget()
        time_info_widget.setStyleSheet("background-color: rgba(255, 255, 255, 220); border-radius: 8px; padding: 10px;")
        time_info_layout = QVBoxLayout(time_info_widget)
        
        # 当前时间显示 - 增大字体并增强对比度
        self.current_time_label = QLabel("加载中...")
        self.current_time_label.setFont(QFont("SimHei", 16, QFont.Bold))
        self.current_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_time_label.setStyleSheet("color: #000000;")
        time_info_layout.addWidget(self.current_time_label)
        
        # 倒计时信息显示 - 增大字体并增强对比度
        self.countdown_label = QLabel("加载中...")
        self.countdown_label.setFont(QFont("SimHei", 14, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("color: #000000;")
        time_info_layout.addWidget(self.countdown_label)
        
        # 下节课信息显示 - 增大字体并增强对比度
        self.next_course_label = QLabel("加载中...")
        self.next_course_label.setFont(QFont("SimHei", 12))
        self.next_course_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_course_label.setStyleSheet("color: #000000;")
        self.next_course_label.setWordWrap(True)  # 启用自动换行
        time_info_layout.addWidget(self.next_course_label)
        
        # 添加时间信息区域到主布局
        layout.addWidget(time_info_widget)
        
        # 获取今天是星期几
        today = datetime.now().weekday()  # 0=周一, 6=周日
        
        # 创建今天的课程标题 - 添加对周六和周日的处理
        if 0 <= today < len(self.day_names):
            today_label = QLabel(f"{self.day_names[today]}的课程")
        else:
            # 对于周六和周日，使用通用标题
            week_day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            today_label = QLabel(f"{week_day_names[today]}的课程")
            
        today_label.setFont(QFont("SimHei", 12, QFont.Bold))
        today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(today_label)
        
        # 创建课程列表
        course_layout = QVBoxLayout()
        course_layout.setSpacing(5)
        
        # 过滤今天的课程并按时间排序
        today_courses = [c for c in self.courses if c.day == today]
        today_courses.sort(key=lambda x: x.start_section)
        
        # 如果没有课程，显示提示信息
        if not today_courses:
            no_course_label = QLabel("今天没有课程")
            no_course_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_course_label.setStyleSheet("color: #666;")
            course_layout.addWidget(no_course_label)
        else:
            # 创建课程项
            for course in today_courses:
                course_item = QWidget()
                course_item.setStyleSheet(f"background-color: {course.color}80; border-radius: 5px; padding: 5px;")
                
                course_item_layout = QVBoxLayout(course_item)
                course_item_layout.setContentsMargins(5, 5, 5, 5)
                
                course_name = QLabel(f"{course.start_section}-{course.end_section}节: {course.name}")
                course_name.setFont(QFont("SimHei", 10, QFont.Bold))
                course_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
                course_info = QLabel(f"{course.teacher} | {course.classroom}")
                course_info.setFont(QFont("SimHei", 9))
                course_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
                course_item_layout.addWidget(course_name)
                course_item_layout.addWidget(course_info)
                course_layout.addWidget(course_item)
        
        layout.addLayout(course_layout)
        self.setLayout(layout)
        
        # 初始化时立即更新一次时间信息
        self.update_time_info()
        
    def mousePressEvent(self, event):
        # 记录鼠标按下的位置，用于窗口拖动
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        # 拖动窗口
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        # 双击关闭窗口
        if event.button() == Qt.MouseButton.LeftButton:
            self.close()
    
    def update_time_info(self):
        """更新时间信息，包括当前时间、倒计时和下节课信息。"""
        try:
            now = datetime.now()
            
            # 更新当前时间
            current_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
            self.current_time_label.setText(current_time_str)
            
            # 获取今天的课程
            today = now.weekday()
            today_courses = [c for c in self.courses if c.day == today]
            today_courses.sort(key=lambda x: x.start_section)
            
            countdown_text = ""
            next_course_text = ""
            
            # 计算当前是否有课程正在进行或即将开始
            has_current_course = False
            next_course = None
            
            # 确保配置项存在
            section_duration = getattr(config, 'SECTION_DURATION', 45)  # 默认45分钟一节课
            break_duration = getattr(config, 'BREAK_DURATION', 10)     # 默认10分钟课间
            
            for course in today_courses:
                # 计算课程开始和结束时间
                try:
                    start_time = datetime(now.year, now.month, now.day, 8, 0)
                    start_time += timedelta(minutes=(course.start_section - 1) * (section_duration + break_duration))
                    end_time = start_time + timedelta(minutes=section_duration)
                except Exception as e:
                    continue
                
                # 检查当前是否在上课中
                if start_time <= now < end_time:
                    has_current_course = True
                    # 计算离下课还有多长时间
                    remaining_minutes = int((end_time - now).total_seconds() / 60)
                    countdown_text = f"离下课还有: {remaining_minutes} 分钟"
                    break
                
                # 检查是否是即将开始的下一节课
                if not next_course and start_time > now:
                    next_course = course
                    # 计算离下节课还有多长时间
                    remaining_minutes = int((start_time - now).total_seconds() / 60)
                    countdown_text = f"离下节课还有: {remaining_minutes} 分钟"
                    next_course_text = f"下节课: {course.name} ({course.teacher})"
            
            # 如果没有当前课程也没有下节课
            if not has_current_course and not next_course:
                countdown_text = "今天没有课程了"
            
            self.countdown_label.setText(countdown_text)
            self.next_course_label.setText(next_course_text)
        except Exception as e:
            # 错误处理，确保界面不会空白
            self.countdown_label.setText("加载课程信息失败")
            self.next_course_label.setText("请检查课程数据")
        
    def closeEvent(self, event):
        """当悬浮窗口关闭时发送关闭信号。"""
        # 停止定时器
        self.timer.stop()
        # 发送关闭信号
        self.closed.emit()
        event.accept()

# 课程类
class Course:
    def __init__(self, name="", teacher="", classroom="", day=0, start_section=1, end_section=1, color="#4CAF50"):
        """初始化课程对象。"""
        self.name = name
        self.teacher = teacher
        self.classroom = classroom
        self.day = day  # 0-4 对应周一到周五
        self.start_section = start_section
        self.end_section = end_section
        self.color = color
        self.reminder = False  # 是否设置提醒
        self.reminder_minutes = config.DEFAULT_REMINDER_MINUTES  # 提前多少分钟提醒
        # 生成随机ID：8位字母数字组合
        self.id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 唯一标识符
        # 打印生成的随机ID
        print(f"创建新课程，生成的随机ID: {self.id}")

    def to_dict(self):
        """将课程对象转换为字典格式，用于保存到文件。"""
        return {
            'name': self.name,
            'teacher': self.teacher,
            'classroom': self.classroom,
            'day': self.day,
            'start_section': self.start_section,
            'end_section': self.end_section,
            'color': self.color,
            'reminder': self.reminder,
            'reminder_minutes': self.reminder_minutes,
            'id': self.id
        }

    @classmethod
    def from_dict(cls, data):
        """从字典数据创建课程对象，用于从文件加载。"""
        course = cls(
            data['name'],
            data['teacher'],
            data['classroom'],
            data['day'],
            data['start_section'],
            data['end_section'],
            data['color']
        )
        course.reminder = data.get('reminder', False)
        course.reminder_minutes = data.get('reminder_minutes', config.DEFAULT_REMINDER_MINUTES)
        # 如果提供了ID则使用，否则生成随机ID
        if 'id' in data:
            course.id = data['id']
            print(f"从字典加载课程，使用提供的ID: {course.id}")
        else:
            # 生成随机ID：8位字母数字组合
            course.id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            print(f"从字典加载课程，生成的随机ID: {course.id}")
        return course

# 添加/编辑课程对话框
class AddCourseDialog(QDialog):
    def __init__(self, parent=None, course=None, day_names=None):
        """初始化添加/编辑课程对话框。"""
        super().__init__(parent)
        self.setWindowTitle("添加课程" if course is None else "编辑课程")
        self.setGeometry(300, 300, 400, 350)
        self.course = course
        self.day_names = day_names or ["周一", "周二", "周三", "周四", "周五"]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 课程名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("课程名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 教师
        teacher_layout = QHBoxLayout()
        teacher_layout.addWidget(QLabel("教师姓名:"))
        self.teacher_edit = QLineEdit()
        teacher_layout.addWidget(self.teacher_edit)
        layout.addLayout(teacher_layout)

        # 教室
        classroom_layout = QHBoxLayout()
        classroom_layout.addWidget(QLabel("教室地点:"))
        self.classroom_edit = QLineEdit()
        classroom_layout.addWidget(self.classroom_edit)
        layout.addLayout(classroom_layout)

        # 星期几
        day_layout = QHBoxLayout()
        day_layout.addWidget(QLabel("星期几:"))
        self.day_combo = QComboBox()
        self.day_combo.addItems(self.day_names)
        day_layout.addWidget(self.day_combo)
        layout.addLayout(day_layout)

        # 开始节次
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("开始节次:"))
        self.start_spin = QSpinBox()
        self.start_spin.setRange(1, config.MAX_DAILY_SECTIONS)
        self.start_spin.setValue(1)
        start_layout.addWidget(self.start_spin)
        layout.addLayout(start_layout)

        # 结束节次
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("结束节次:"))
        self.end_spin = QSpinBox()
        self.end_spin.setRange(1, config.MAX_DAILY_SECTIONS)
        self.end_spin.setValue(1)
        end_layout.addWidget(self.end_spin)
        layout.addLayout(end_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("课程颜色:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.color_button.setStyleSheet("background-color: #4CAF50")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        layout.addLayout(color_layout)

        # 提醒设置
        reminder_layout = QHBoxLayout()
        self.reminder_check = QPushButton("设置提醒")
        self.reminder_check.setCheckable(True)
        self.reminder_minutes = QSpinBox()
        self.reminder_minutes.setRange(1, 60)
        self.reminder_minutes.setValue(config.DEFAULT_REMINDER_MINUTES)
        self.reminder_minutes.setEnabled(False)
        self.reminder_check.clicked.connect(self.toggle_reminder)
        reminder_layout.addWidget(self.reminder_check)
        reminder_layout.addWidget(QLabel("提前"))
        reminder_layout.addWidget(self.reminder_minutes)
        reminder_layout.addWidget(QLabel("分钟"))
        layout.addLayout(reminder_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 如果是编辑模式，填充现有数据
        if self.course:
            self.name_edit.setText(self.course.name)
            self.teacher_edit.setText(self.course.teacher)
            self.classroom_edit.setText(self.course.classroom)
            self.day_combo.setCurrentIndex(self.course.day)
            self.start_spin.setValue(self.course.start_section)
            self.end_spin.setValue(self.course.end_section)
            self.color_button.setStyleSheet(f"background-color: {self.course.color}")
            self.reminder_check.setChecked(self.course.reminder)
            self.reminder_minutes.setValue(self.course.reminder_minutes)
            self.reminder_minutes.setEnabled(self.course.reminder)

        # 确保结束节次不小于开始节次
        self.start_spin.valueChanged.connect(self.update_end_spin)

    def update_end_spin(self):
        """根据开始节次更新结束节次的可选范围。"""
        start = self.start_spin.value()
        if self.end_spin.value() < start:
            self.end_spin.setValue(start)
        self.end_spin.setMinimum(start)

    def choose_color(self):
        """打开颜色选择对话框，让用户选择课程颜色。"""
        # 创建颜色对话框实例
        color_dialog = QColorDialog(self)
        
        # 设置对话框标题为中文
        color_dialog.setWindowTitle("选择课程颜色")
        
        # 尝试设置中文显示选项
        color_dialog.setOptions(QColorDialog.ShowAlphaChannel | QColorDialog.DontUseNativeDialog)
        
        # 获取当前按钮的背景颜色作为初始颜色
        current_color = QColor()
        stylesheet = self.color_button.styleSheet()
        if stylesheet.startswith("background-color:"):
            color_name = stylesheet[len("background-color:"):].strip()
            current_color = QColor(color_name)
        
        # 如果当前颜色有效，则设置为初始颜色
        if current_color.isValid():
            color_dialog.setCurrentColor(current_color)
        
        # 显示对话框并获取用户选择的颜色
        if color_dialog.exec_() == QColorDialog.Accepted:
            color = color_dialog.selectedColor()
            if color.isValid():
                self.color_button.setStyleSheet(f"background-color: {color.name()}")

    def toggle_reminder(self):
        """切换课程提醒功能的开关状态。"""
        self.reminder_minutes.setEnabled(self.reminder_check.isChecked())

    def get_course_data(self):
        """获取用户在对话框中输入的课程数据，创建并返回课程对象。"""
        course = Course(
            self.name_edit.text(),
            self.teacher_edit.text(),
            self.classroom_edit.text(),
            self.day_combo.currentIndex(),
            self.start_spin.value(),
            self.end_spin.value(),
            self.color_button.styleSheet().split(':')[-1].strip()
        )
        course.reminder = self.reminder_check.isChecked()
        course.reminder_minutes = self.reminder_minutes.value()
        return course

# 课程表单元格组件
class ClassCell(QWidget):
    def __init__(self, course=None, parent=None):
        """初始化课程单元格组件。"""
        super().__init__(parent)
        self.course = course
        self.init_ui()

    def init_ui(self):
        self.setAutoFillBackground(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        if self.course:
            # 设置背景颜色
            palette = self.palette()
            palette.setColor(self.backgroundRole(), QColor(self.course.color))
            self.setPalette(palette)
            
            # 添加课程信息
            name_label = QLabel(self.course.name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            name_font = QFont()
            name_font.setBold(True)
            name_label.setFont(name_font)
            
            teacher_label = QLabel(f"{self.course.teacher}")
            teacher_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            teacher_label.setWordWrap(True)
            
            classroom_label = QLabel(f"{self.course.classroom}")
            classroom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            classroom_label.setWordWrap(True)
            
            layout.addWidget(name_label)
            layout.addWidget(teacher_label)
            layout.addWidget(classroom_label)
        
        self.setLayout(layout)

    def set_course(self, course):
        """设置课程单元格显示的课程信息。"""
        self.course = course
        self.init_ui()

# 课程表主窗口
class ClassTableApp(QMainWindow):
    def __init__(self):
        """初始化课程表应用程序的主窗口。"""
        super().__init__()
        self.courses = []
        self.day_names = ["周一", "周二", "周三", "周四", "周五"]
        self.week_names = [f"第{i+1}周" for i in range(config.TOTAL_WEEKS)]
        self.current_week = config.START_WEEK - 1
        self.schedule_file = config.SCHEDULE_FILE_PATH
        self.floating_window = None
        self.tray_icon = None
        self.init_ui()
        self.load_schedule()
        self.setup_reminders()
        self.init_system_tray()

    def init_ui(self):
        self.setWindowTitle(f"{config.APP_NAME} - 版本 {config.VERSION}")
        self.setGeometry(100, 100, config.MAIN_WINDOW_WIDTH, config.MAIN_WINDOW_HEIGHT)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("欢迎使用智能课程表")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 当前周显示和切换
        week_layout = QHBoxLayout()
        self.prev_week_btn = QPushButton("上一周")
        self.prev_week_btn.clicked.connect(self.prev_week)
        self.week_label = QLabel(f"当前周: {self.week_names[self.current_week]}")
        self.next_week_btn = QPushButton("下一周")
        self.next_week_btn.clicked.connect(self.next_week)
        
        week_layout.addWidget(self.prev_week_btn)
        week_layout.addWidget(self.week_label)
        week_layout.addWidget(self.next_week_btn)
        
        # 添加课程按钮
        self.add_course_btn = QPushButton("添加课程")
        self.add_course_btn.clicked.connect(self.add_course)
        
        # 日历组件
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumHeight(200)
        self.calendar.clicked[QDate].connect(self.on_date_selected)
        
        # 设置当前日期为选中状态
        self.calendar.setSelectedDate(QDate.currentDate())
        
        # 将组件添加到控制布局
        control_layout.addLayout(week_layout)
        control_layout.addWidget(self.add_course_btn)
        control_layout.addWidget(self.calendar)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 创建课程表视图
        self.schedule_widget = QWidget()
        self.schedule_layout = QGridLayout(self.schedule_widget)
        self.tab_widget.addTab(self.schedule_widget, "课程表视图")
        
        # 创建课程列表视图
        self.course_list_widget = QListWidget()
        self.tab_widget.addTab(self.course_list_widget, "课程列表")
        
        # 创建统计视图
        self.statistics_widget = QWidget()
        self.statistics_layout = QVBoxLayout(self.statistics_widget)
        self.tab_widget.addTab(self.statistics_widget, "课程统计")
        
        main_layout.addWidget(self.tab_widget)
        
        # 初始化课程表网格
        self.init_schedule_grid()
        
        # 连接选项卡切换信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def create_menu_bar(self):
        """创建应用程序的菜单栏。"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        save_action = QAction("保存课程表", self)
        save_action.triggered.connect(self.save_schedule)
        file_menu.addAction(save_action)
        
        load_action = QAction("加载课程表", self)
        load_action.triggered.connect(self.load_schedule)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("导入课程表", self)
        import_action.triggered.connect(self.import_schedule)
        file_menu.addAction(import_action)
        
        export_action = QAction("导出课程表", self)
        export_action.triggered.connect(self.export_schedule)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        load_example_action = QAction("加载示例课程表", self)
        load_example_action.triggered.connect(self.load_example_schedule)
        file_menu.addAction(load_example_action)
        
        file_menu.addSeparator()
        
        print_action = QAction("打印课程表", self)
        print_action.triggered.connect(self.print_schedule)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(lambda: self.close())
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        add_action = QAction("添加课程", self)
        add_action.triggered.connect(self.add_course)
        edit_menu.addAction(add_action)
        
        edit_action = QAction("编辑课程", self)
        edit_action.triggered.connect(self.edit_selected_course)
        edit_menu.addAction(edit_action)
        
        delete_action = QAction("删除课程", self)
        delete_action.triggered.connect(self.delete_selected_course)
        edit_menu.addAction(delete_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        for i, week_name in enumerate(self.week_names):
            week_action = QAction(week_name, self)
            week_action.setCheckable(True)
            if i == self.current_week:
                week_action.setChecked(True)
            week_action.triggered.connect(lambda checked, idx=i: self.set_week(idx))
            view_menu.addAction(week_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        update_log_action = QAction("更新日志", self)
        update_log_action.triggered.connect(self.show_update_log)
        help_menu.addAction(update_log_action)

    def create_tool_bar(self):
        """创建应用程序的工具栏。"""
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        add_action = QAction("添加课程", self)
        add_action.triggered.connect(self.add_course)
        toolbar.addAction(add_action)
        
        edit_action = QAction("编辑课程", self)
        edit_action.triggered.connect(self.edit_selected_course)
        toolbar.addAction(edit_action)
        
        delete_action = QAction("删除课程", self)
        delete_action.triggered.connect(self.delete_selected_course)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_schedule)
        toolbar.addAction(save_action)
        
        load_action = QAction("加载", self)
        load_action.triggered.connect(self.load_schedule)
        toolbar.addAction(load_action)
        
        toolbar.addSeparator()
        
        # 搜索框
        self.search_label = QLabel("搜索:")
        toolbar.addWidget(self.search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("按课程名、教师、教室搜索...")
        self.search_edit.textChanged.connect(self.search_courses)
        toolbar.addWidget(self.search_edit)
        
        # 默认隐藏搜索框
        self.search_label.hide()
        self.search_edit.hide()

    def init_schedule_grid(self):
        """初始化课程表网格布局。"""
        # 清空现有内容
        for i in reversed(range(self.schedule_layout.count())):
            widget = self.schedule_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)  # 传入None移除父对象
                widget.deleteLater()
        
        # 添加表头
        header_font = QFont()
        header_font.setBold(True)
        
        # 左上角空白
        empty_label = QLabel("")
        self.schedule_layout.addWidget(empty_label, 0, 0)
        
        # 星期表头
        for day_idx, day_name in enumerate(self.day_names[:config.WEEKLY_CLASS_DAYS]):
            day_label = QLabel(day_name)
            day_label.setFont(header_font)
            day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            self.schedule_layout.addWidget(day_label, 0, day_idx + 1)
        
        # 节次和课程单元格
        for section in range(1, config.MAX_DAILY_SECTIONS + 1):
            # 节次标签
            section_label = QLabel(f"第{section}节")
            section_label.setFont(header_font)
            section_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            section_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            self.schedule_layout.addWidget(section_label, section, 0)
            
            # 每天的课程单元格
            for day_idx in range(config.WEEKLY_CLASS_DAYS):
                # 查找是否有课程
                course = None
                for c in self.courses:
                    if c.day == day_idx and c.start_section <= section <= c.end_section:
                        # 只在开始节次创建课程单元格
                        if section == c.start_section:
                            course = c
                        break
                
                if course:
                    # 创建课程单元格并跨越多行
                    cell = ClassCell(course)
                    cell.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                    cell.customContextMenuRequested.connect(lambda pos, c=course: self.show_course_context_menu(pos, c))
                    # 为每个单元格创建独立的双击事件处理函数
                    """创建课程单元格的双击事件处理函数。"""
                    def create_double_click_handler(c):
                        def double_click_event(event):
                            self.edit_course(c)
                        return double_click_event
                    cell.mouseDoubleClickEvent = create_double_click_handler(course)
                    rowspan = course.end_section - course.start_section + 1
                    self.schedule_layout.addWidget(cell, section, day_idx + 1, rowspan, 1)

    def update_course_list(self):
        """更新课程列表视图。"""
        self.course_list_widget.clear()
        
        # 获取搜索文本
        search_text = self.search_edit.text().lower() if hasattr(self, 'search_edit') else ""
        
        for course in self.courses:
            # 搜索过滤
            if search_text and not (
                search_text in course.name.lower() or 
                search_text in course.teacher.lower() or 
                search_text in course.classroom.lower()
            ):
                continue
                
            item = QListWidgetItem(f"{self.day_names[course.day]} {course.start_section}-{course.end_section}节: {course.name} - {course.teacher} ({course.classroom})")
            item.setData(Qt.ItemDataRole.UserRole, course)
            # 设置背景颜色
            brush = QBrush(QColor(course.color))
            item.setBackground(brush)
            self.course_list_widget.addItem(item)
        
        # 连接双击事件
        self.course_list_widget.itemDoubleClicked.connect(lambda item: self.edit_course(item.data(Qt.ItemDataRole.UserRole)))
        # 设置右键菜单
        self.course_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.course_list_widget.customContextMenuRequested.connect(self.show_list_context_menu)

    def add_course(self):
        """添加新课程到课程表中。"""
        dialog = AddCourseDialog(self, day_names=self.day_names)
        if dialog.exec_():
            course = dialog.get_course_data()
            
            # 检查课程冲突
            if self.check_course_conflict(course):
                reply = QMessageBox.question(
                    self, "课程冲突", "该时间段已有课程安排，是否继续添加？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            self.courses.append(course)
            self.save_schedule()
            self.update_ui()
            self.statusBar().showMessage(f"已添加课程: {course.name}")

    def edit_course(self, course):
        """编辑选中的课程信息。"""
        dialog = AddCourseDialog(self, course, self.day_names)
        if dialog.exec_():
            new_course = dialog.get_course_data()
            
            # 检查课程冲突（排除当前正在编辑的课程）
            if self.check_course_conflict(new_course, exclude_id=course.id):
                reply = QMessageBox.question(
                    self, "课程冲突", "该时间段已有课程安排，是否继续修改？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 替换课程
            index = self.courses.index(course)
            self.courses[index] = new_course
            self.save_schedule()
            self.update_ui()
            self.statusBar().showMessage(f"已更新课程: {new_course.name}")

    def delete_course(self, course):
        """从课程表中删除选中的课程。"""
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除课程 '{course.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.courses.remove(course)
            self.save_schedule()
            self.update_ui()
            self.statusBar().showMessage(f"已删除课程: {course.name}")

    def check_course_conflict(self, new_course, exclude_id=None):
        """检查新课程是否与现有课程冲突。"""
        """参数:
            new_course: 要检查的新课程对象
            exclude_id: 要排除的课程ID（用于编辑课程时）"""
        for course in self.courses:
            # 排除当前正在编辑的课程
            if course.id == exclude_id:
                continue
            
            # 检查是否在同一天
            if course.day != new_course.day:
                continue
            
            # 检查时间冲突
            if not (new_course.end_section < course.start_section or new_course.start_section > course.end_section):
                return True
        return False

    def show_course_context_menu(self, position, course):
        """显示课程的右键菜单。"""
        menu = QMenu()
        edit_action = menu.addAction("编辑课程")
        delete_action = menu.addAction("删除课程")
        
        action = menu.exec_(self.sender().mapToGlobal(position))
        
        if action == edit_action:
            self.edit_course(course)
        elif action == delete_action:
            self.delete_course(course)

    def show_list_context_menu(self, position):
        """显示课程列表的右键菜单。"""
        item = self.course_list_widget.itemAt(position)
        if item:
            course = item.data(Qt.ItemDataRole.UserRole)
            menu = QMenu()
            edit_action = menu.addAction("编辑课程")
            delete_action = menu.addAction("删除课程")
            
            action = menu.exec_(self.course_list_widget.mapToGlobal(position))
            
            if action == edit_action:
                self.edit_course(course)
            elif action == delete_action:
                self.delete_course(course)

    def edit_selected_course(self):
        """编辑选中的课程。"""
        if self.tab_widget.currentIndex() == 0:  # 课程表视图
            # 在课程表视图中，需要获取选中的单元格
            # 这里简化处理，直接提示用户双击课程进行编辑
            QMessageBox.information(self, "提示", "请在课程表视图中双击要编辑的课程，或在课程列表中选择要编辑的课程。")
        else:  # 课程列表视图
            selected_items = self.course_list_widget.selectedItems()
            if selected_items:
                course = selected_items[0].data(Qt.ItemDataRole.UserRole)
                self.edit_course(course)
            else:
                QMessageBox.information(self, "提示", "请先选择要编辑的课程。")

    def delete_selected_course(self):
        """删除选中的课程。"""
        if self.tab_widget.currentIndex() == 0:  # 课程表视图
            QMessageBox.information(self, "提示", "请在课程表视图中右键点击要删除的课程，或在课程列表中选择要删除的课程。")
        else:  # 课程列表视图
            selected_items = self.course_list_widget.selectedItems()
            if selected_items:
                course = selected_items[0].data(Qt.ItemDataRole.UserRole)
                self.delete_course(course)
            else:
                QMessageBox.information(self, "提示", "请先选择要删除的课程。")

    def prev_week(self):
        """切换到上一周的课程表。"""
        if self.current_week > 0:
            self.current_week -= 1
            self.week_label.setText(f"当前周: {self.week_names[self.current_week]}")
            self.update_ui()

    def next_week(self):
        """切换到下一周的课程表。"""
        if self.current_week < len(self.week_names) - 1:
            self.current_week += 1
            self.week_label.setText(f"当前周: {self.week_names[self.current_week]}")
            self.update_ui()

    def set_week(self, week_idx):
        """设置当前显示的周数。"""
        if 0 <= week_idx < len(self.week_names):
            self.current_week = week_idx
            self.week_label.setText(f"当前周: {self.week_names[self.current_week]}")
            self.update_ui()

    def on_date_selected(self, date):
        """当用户在日历中选择日期时的处理函数。"""
        # 获取选中日期是星期几（周一=1，周二=2，...，周日=7）
        day_of_week = date.dayOfWeek() - 1  # 转换为0-6
        
        if 0 <= day_of_week < len(self.day_names):  # 只处理周一到周五
            # 这里可以添加跳转到对应日期的课程视图的功能
            self.statusBar().showMessage(f"已选择 {date.toString('yyyy年MM月dd日')} {self.day_names[day_of_week]}")

    def on_tab_changed(self, index):
        """当用户切换选项卡时的处理函数。"""
        if index == 1:  # 切换到课程列表视图
            self.update_course_list()
            # 显示搜索框
            self.search_label.show()
            self.search_edit.show()
        else:  # 切换到其他视图
            # 隐藏搜索框
            self.search_label.hide()
            self.search_edit.hide()
            
        if index == 2:  # 切换到统计视图
            self.update_statistics()
    
    def search_courses(self):
        """根据搜索文本过滤课程列表。"""
        self.update_course_list()
    
    def import_schedule(self):
        """导入课程表数据从JSON文件。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入课程表", ".", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 清除当前课程
                self.courses.clear()
                
                # 导入新课程
                for course_data in data.get('courses', []):
                    course = Course.from_dict(course_data)
                    self.courses.append(course)
                
                # 更新视图
                self.update_ui()
                self.update_course_list()
                
                self.statusBar().showMessage(f"成功从 {file_path} 导入课程表")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入课程表时发生错误: {str(e)}")
    
    def export_schedule(self):
        """导出课程表数据到JSON文件。"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出课程表", ".", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                data = {
                    'version': config.VERSION,
                    'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'courses': [course.to_dict() for course in self.courses]
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self.statusBar().showMessage(f"成功导出课程表到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出课程表时发生错误: {str(e)}")
    
    def update_statistics(self):
        """更新课程统计信息。"""
        # 清空统计视图
        for i in reversed(range(self.statistics_layout.count())):
            widget = self.statistics_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # 计算统计数据
        total_courses = len(self.courses)
        
        # 计算总学时（每节课按45分钟计算）
        total_class_hours = 0
        total_credits = 0
        unique_courses = set()
        
        for course in self.courses:
            # 计算课时
            hours = (course.end_section - course.start_section + 1) * 0.75  # 45分钟/节课
            total_class_hours += hours
            
            # 假设每门课有2学分
            # 注意：这里我们根据课程名称去重，因为同一个课程可能在不同时间重复出现
            course_key = f"{course.name}_{course.teacher}"
            if course_key not in unique_courses:
                unique_courses.add(course_key)
                total_credits += getattr(course, 'credits', 2)  # 如果没有学分属性，默认为2
        
        avg_credits = total_credits / len(unique_courses) if unique_courses else 0
        
        # 创建统计信息标签
        stats_group = QGroupBox("课程统计信息")
        stats_layout = QVBoxLayout()
        
        # 添加统计项
        stats_layout.addWidget(QLabel(f"总课程数: {total_courses}"))
        stats_layout.addWidget(QLabel(f"独立课程数: {len(unique_courses)}"))
        stats_layout.addWidget(QLabel(f"总学时: {total_class_hours:.1f} 小时"))
        stats_layout.addWidget(QLabel(f"总学分: {total_credits:.1f}"))
        stats_layout.addWidget(QLabel(f"平均学分: {avg_credits:.2f}"))
        
        # 添加更详细的统计
        stats_layout.addSpacing(10)
        stats_layout.addWidget(QLabel("课程分布:"))
        
        # 按星期统计课程数量
        day_counts = {day: 0 for day in self.day_names}
        for course in self.courses:
            if 0 <= course.day < len(self.day_names):
                day_name = self.day_names[course.day]
                day_counts[day_name] += 1
        
        for day, count in day_counts.items():
            stats_layout.addWidget(QLabel(f"{day}: {count} 门课程"))
        
        stats_group.setLayout(stats_layout)
        self.statistics_layout.addWidget(stats_group)
        
        # 添加导出统计按钮
        export_stats_btn = QPushButton("导出统计结果")
        export_stats_btn.clicked.connect(self.export_statistics)
        self.statistics_layout.addWidget(export_stats_btn)
        
        self.statistics_layout.addStretch()
    
    def export_statistics(self):
        """导出课程统计结果。"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出统计结果", ".", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 重新计算统计数据
                total_courses = len(self.courses)
                total_class_hours = 0
                total_credits = 0
                unique_courses = set()
                
                for course in self.courses:
                    # 计算课时
                    hours = (course.end_section - course.start_section + 1) * 0.75  # 45分钟/节课
                    total_class_hours += hours
                    
                    # 统计独立课程和学分
                    course_key = f"{course.name}_{course.teacher}"
                    if course_key not in unique_courses:
                        unique_courses.add(course_key)
                        total_credits += getattr(course, 'credits', 2)
                
                avg_credits = total_credits / len(unique_courses) if unique_courses else 0
                
                # 按星期统计
                day_counts = {day: 0 for day in self.day_names}
                for course in self.courses:
                    if 0 <= course.day < len(self.day_names):
                        day_name = self.day_names[course.day]
                        day_counts[day_name] += 1
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"课程表统计结果\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"软件版本: {config.VERSION}\n")
                    f.write("="*40 + "\n\n")
                    
                    f.write(f"总课程数: {total_courses}\n")
                    f.write(f"独立课程数: {len(unique_courses)}\n")
                    f.write(f"总学时: {total_class_hours:.1f} 小时\n")
                    f.write(f"总学分: {total_credits:.1f}\n")
                    f.write(f"平均学分: {avg_credits:.2f}\n\n")
                    
                    f.write("按星期分布:\n")
                    for day, count in day_counts.items():
                        f.write(f"{day}: {count} 门课程\n")
                
                self.statusBar().showMessage(f"成功导出统计结果到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出统计结果时发生错误: {str(e)}")

    def update_ui(self):
        """更新用户界面，刷新课程表显示和课程列表。"""
        self.init_schedule_grid()
        if self.tab_widget.currentIndex() == 1:
            self.update_course_list()

    def save_schedule(self):
        """保存当前课程表数据到文件中。"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump([course.to_dict() for course in self.courses], f, ensure_ascii=False, indent=2)
            self.statusBar().showMessage("课程表已保存")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法保存课程表: {str(e)}")

    def load_schedule(self):
        """从文件加载课程表数据。"""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    courses_data = json.load(f)
                    self.courses = [Course.from_dict(data) for data in courses_data]
                self.update_ui()
                self.statusBar().showMessage("课程表已加载")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载课程表: {str(e)}")

    def load_example_schedule(self):
        """加载示例课程表数据，将覆盖当前所有课程。"""
        reply = QMessageBox.question(
            self, "确认加载示例", 
            "加载示例课程表将覆盖当前的所有课程，确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(config.EXAMPLE_SCHEDULE_FILE_PATH):
                    with open(config.EXAMPLE_SCHEDULE_FILE_PATH, 'r', encoding='utf-8') as f:
                        courses_data = json.load(f)
                        self.courses = [Course.from_dict(data) for data in courses_data]
                    self.update_ui()
                    self.statusBar().showMessage("示例课程表已加载")
                else:
                    QMessageBox.warning(self, "文件不存在", f"示例课程表文件不存在: {config.EXAMPLE_SCHEDULE_FILE_PATH}")
            except Exception as e:
                QMessageBox.critical(self, "加载失败", f"无法加载示例课程表: {str(e)}")

    def print_schedule(self):
        """打印当前课程表。"""
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            # 创建打印预览对话框
            preview_dialog = QPrintPreviewDialog(printer, self)
            preview_dialog.paintRequested.connect(lambda p: self.print_document(p))
            preview_dialog.exec_()
            
    def print_document(self, printer):
        """绘制要打印的文档内容。"""
        painter = QPainter(printer)
        paper_rect = printer.pageRect()
        
        # 添加边距，确保内容不紧贴页面边缘
        margin = 20
        content_rect = QRectF(
            paper_rect.left() + margin,
            paper_rect.top() + margin,
            paper_rect.width() - 2 * margin,
            paper_rect.height() - 2 * margin
        )
        
        # 设置字体
        font = QFont(config.DEFAULT_FONT)
        font.setPointSize(12)
        painter.setFont(font)
        
        # 绘制标题
        title = f"{config.APP_NAME} - {self.week_names[self.current_week]}"
        title_rect = QRectF(content_rect)
        title_rect.setHeight(40)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title)
        
        # 绘制日期
        date_str = QDate.currentDate().toString("yyyy年MM月dd日")
        date_rect = QRectF(content_rect)
        date_rect.setTop(content_rect.top() + 40)
        date_rect.setHeight(20)
        painter.drawText(date_rect, Qt.AlignmentFlag.AlignCenter, date_str)
        
        # 创建课程表网格
        table_rect = QRectF(content_rect)
        table_rect.setTop(content_rect.top() + 70)
        table_rect.setBottom(content_rect.bottom() - 30)
        
        # 计算单元格大小
        cell_width = table_rect.width() / (config.WEEKLY_CLASS_DAYS + 1)
        cell_height = table_rect.height() / (config.MAX_DAILY_SECTIONS + 1)
        
        # 绘制表头和网格
        # 左上角空白
        header_font = QFont(config.DEFAULT_FONT)
        header_font.setBold(True)
        painter.setFont(header_font)
        
        # 星期表头
        for day_idx, day_name in enumerate(self.day_names[:config.WEEKLY_CLASS_DAYS]):
            rect = QRectF(table_rect.left() + cell_width * (day_idx + 1), table_rect.top(), cell_width, cell_height)
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, day_name)
        
        # 节次和课程单元格
        normal_font = QFont(config.DEFAULT_FONT)
        normal_font.setPointSize(50)  # 增大字体大小以提高可读性
        painter.setFont(normal_font)
        
        for section in range(1, config.MAX_DAILY_SECTIONS + 1):
            # 节次标签
            painter.setFont(header_font)
            rect = QRectF(table_rect.left(), table_rect.top() + cell_height * section, cell_width, cell_height)
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"第{section}节")
            painter.setFont(normal_font)
            
            # 每天的课程单元格
            for day_idx in range(config.WEEKLY_CLASS_DAYS):
                # 查找是否有课程
                course = None
                for c in self.courses:
                    if c.day == day_idx and c.start_section <= section <= c.end_section:
                        # 只在开始节次创建课程单元格
                        if section == c.start_section:
                            course = c
                        break
                
                rect = QRectF(table_rect.left() + cell_width * (day_idx + 1), table_rect.top() + cell_height * section, cell_width, cell_height)
                painter.drawRect(rect)
                
                if course:
                    # 计算课程单元格的实际大小
                    rowspan = course.end_section - course.start_section + 1
                    course_rect = QRectF(
                        table_rect.left() + cell_width * (day_idx + 1), 
                        table_rect.top() + cell_height * section, 
                        cell_width, 
                        cell_height * rowspan
                    )
                    
                    # 绘制课程背景
                    painter.save()
                    painter.setBrush(QBrush(QColor(course.color)))
                    painter.setOpacity(0.7)
                    painter.drawRect(course_rect)
                    painter.restore()
                    
                    # 绘制课程信息
                    text_rect = course_rect.adjusted(5, 5, -5, -5)
                    text_options = QTextOption()
                    text_options.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # 设置文本宽度
                    document = QTextDocument()
                    document.setPageSize(QSizeF(text_rect.width(), 0))
                    document.setDefaultFont(normal_font)
                    document.setHtml(f"<div style='text-align: center;'>{course.name}<br>{course.teacher}<br>{course.classroom}</div>")
                    
                    # 保存当前画家状态并移动到正确位置
                    painter.save()
                    painter.translate(text_rect.topLeft())
                    document.drawContents(painter)
                    painter.restore()
                    
                    # 绘制课程边框
                    painter.drawRect(course_rect)
        
        # 绘制页脚
        footer_font = QFont(config.DEFAULT_FONT)
        footer_font.setPointSize(8)
        painter.setFont(footer_font)
        footer_rect = QRectF(paper_rect)
        footer_rect.setTop(paper_rect.bottom() - 30)
        footer_rect.setHeight(20)
        painter.drawText(footer_rect, Qt.AlignmentFlag.AlignRight, f"{config.APP_NAME} 版本 {config.VERSION}")
        
        painter.end()
        
    def setup_reminders(self):
        """设置课程提醒定时器，每分钟检查一次是否有即将开始的课程。"""
        # 设置定时器，每分钟检查一次是否有即将开始的课程
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60000)  # 60000毫秒 = 1分钟

    def check_reminders(self):
        """检查是否有即将开始的课程，如果有则显示提醒。"""
        now = datetime.now()
        
        for course in self.courses:
            if course.reminder and config.ENABLE_POPUP_REMINDER:
                # 计算课程开始时间（假设课程从早上8点开始，每节课45分钟，课间休息10分钟）
                # 这里使用简化的时间计算，实际应用中可以根据学校的作息时间表进行调整
                try:
                    start_time = datetime(now.year, now.month, now.day, 8, 0)
                    start_time += timedelta(minutes=(course.start_section - 1) * 55)  # 45分钟课程 + 10分钟休息
                except Exception as e:
                    # 如果时间计算出错，跳过本次提醒
                    continue
                
                # 计算提前提醒的时间
                reminder_time = start_time - timedelta(minutes=course.reminder_minutes)
                
                # 检查是否需要提醒
                if now >= reminder_time and now < start_time:
                    # 计算剩余时间
                    remaining_minutes = int((start_time - now).total_seconds() / 60)
                    
                    # 显示提醒
                    QMessageBox.information(
                        self, "课程提醒",
                        f"{course.name} 将在 {remaining_minutes} 分钟后开始！\n"+
                        f"教师: {course.teacher}\n"+
                        f"教室: {course.classroom}\n"+
                        f"时间: {start_time.strftime('%H:%M')}"
                    )
                    
                    # 如果启用了声音提醒，可以在这里添加播放声音的代码
                    if config.ENABLE_SOUND_REMINDER:
                        pass  # 实际应用中可以添加播放提示音的代码

    def show_about(self):
        """显示关于对话框，包含软件版本、作者等信息。"""
        QMessageBox.about(
            self, "关于智能课程表",
            f"{config.APP_NAME} v{config.VERSION}\n\n"+
            "一个美观、功能多样的课程表管理软件\n\n"+
            "功能特点:\n"+
            "- 可视化课程表视图\n"+
            "- 课程列表管理\n"+
            "- 课程添加、编辑、删除\n"+
            "- 课程冲突检查\n"+
            "- 自定义课程颜色\n"+
            "- 课程提醒功能\n"+
            "- 多周课程表支持\n"+
            "- 课程表保存与加载\n"+
            "- 系统托盘支持\n"+
            "- 悬浮课程表功能\n"+
            "联系我们:qzrobotboar@gmail.com\n"+
            f"作者: {config.AUTHOR}\n"+
            f"版本: {config.VERSION}\n"+
            f"日期: {config.RELEASE_DATE}"
        )
    
    def show_update_log(self):
        """显示更新日志对话框。"""
        update_log_dialog = UpdateLogDialog(self)
        update_log_dialog.exec_()
        
    def init_system_tray(self):
        """初始化系统托盘图标和相关功能。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.information(self, "提示", "您的系统不支持系统托盘功能")
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建一个简单的图标（使用文字作为图标）
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(76, 175, 80))  # 使用绿色背景
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.setFont(QFont("SimHei", 12, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "课")
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        self.tray_icon.setToolTip("智能课程表")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示主窗口动作
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window)
        
        # 显示悬浮课程表动作
        float_action = tray_menu.addAction("显示悬浮课程表")
        float_action.triggered.connect(self.toggle_floating_window)
        
        # 退出动作
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        
    def on_tray_icon_activated(self, reason):
        """当系统托盘图标被点击时的处理函数。"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击
            self.toggle_floating_window()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:  # 双击
            self.show_main_window()
            
    def show_main_window(self):
        """显示主窗口。"""
        self.showNormal()
        self.activateWindow()
        
    def toggle_floating_window(self):
        """切换悬浮窗口的显示/隐藏状态。"""
        if self.floating_window is None:
            self.create_floating_window()
        else:
            self.close_floating_window()
            
    def create_floating_window(self):
        """创建悬浮窗口。"""
        if hasattr(self, 'courses'):
            self.floating_window = FloatingScheduleWindow(self.courses, self.day_names)
            self.floating_window.closed.connect(self.on_floating_window_closed)
            self.floating_window.show()
            self.statusBar().showMessage("已显示悬浮课程表")
            
    def close_floating_window(self):
        """关闭悬浮窗口。"""
        if self.floating_window:
            self.floating_window.close()
            self.floating_window = None
            self.statusBar().showMessage("已关闭悬浮课程表")
            
    def on_floating_window_closed(self):
        """当悬浮窗口关闭时的处理函数。"""
        self.floating_window = None
        
    def quit_application(self):
        """退出应用程序。"""
        if self.floating_window:
            self.floating_window.close()
        QApplication.quit()
        
    def closeEvent(self, event):
        """当主窗口关闭时的事件处理函数。"""
        if self.tray_icon and self.tray_icon.isVisible():
            # 询问用户是最小化到托盘还是退出
            reply = QMessageBox.question(
                self, "退出确认",
                "确定要退出智能课程表吗？\n选择'否'将最小化到系统托盘。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                self.hide()
                event.ignore()
                self.statusBar().showMessage("应用程序已最小化到系统托盘")
            else:
                if self.floating_window:
                    self.floating_window.close()
                event.accept()
        else:
            if self.floating_window:
                self.floating_window.close()
            event.accept()

# 启动画面类
class SplashScreen(QWidget):
    def __init__(self):
        """初始化启动画面。"""
        super().__init__()
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(config.SPLASH_SCREEN_WIDTH, config.SPLASH_SCREEN_HEIGHT)
        self.setStyleSheet(f"background-color: {config.PRIMARY_COLOR};")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 软件标题
        title_label = QLabel(config.APP_NAME)
        title_label.setFont(QFont(config.DEFAULT_FONT, config.TITLE_FONT_SIZE, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 版本号
        version_label = QLabel(f"版本: {config.VERSION}")
        version_label.setFont(QFont(config.DEFAULT_FONT, config.HEADER_FONT_SIZE))
        version_label.setStyleSheet("color: white;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 日期
        date_label = QLabel(f"日期: {config.RELEASE_DATE}")
        date_label.setFont(QFont(config.DEFAULT_FONT, config.FONT_SIZE))
        date_label.setStyleSheet("color: white;")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(date_label)
        
        self.setLayout(layout)
        # 居中显示
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())

# 更新日志对话框类
class UpdateLogDialog(QDialog):
    def __init__(self, parent=None):
        """初始化更新日志对话框。"""
        super().__init__(parent)
        self.setWindowTitle("更新日志")
        self.resize(600, 400)
        self.init_ui()
        
    def init_ui(self):
        """初始化更新日志对话框的用户界面。"""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QWidget()
        scroll_area.setStyleSheet(f"background-color: {config.BACKGROUND_COLOR};")
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = QLabel(f"{config.APP_NAME} 更新日志")
        title_label.setFont(QFont(config.DEFAULT_FONT, config.HEADER_FONT_SIZE, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {config.PRIMARY_COLOR};")
        scroll_layout.addWidget(title_label)
        
        scroll_layout.addSpacing(20)
        
        # 遍历更新日志，按版本号降序排列
        versions = sorted(config.UPDATE_LOGS.keys(), key=lambda x: [int(part) for part in x.split('.')], reverse=True)
        
        # 标记是否已经添加了当前版本
        current_version_added = False
        
        # 添加所有版本的更新日志
        for version in versions:
            log_info = config.UPDATE_LOGS[version]
            
            # 版本标签
            version_label = QLabel(f"版本 {version} ({log_info['date']})")
            
            if version == config.VERSION and not current_version_added:
                # 当前版本样式
                version_label.setFont(QFont(config.DEFAULT_FONT, config.FONT_SIZE + 2, QFont.Bold))
                version_label.setStyleSheet(f"color: {config.SECONDARY_COLOR};")
                
                # 添加历史版本标题（仅在第一次添加非当前版本时）
                current_version_added = True
                
                # 历史版本标题
                history_label_added = False
            else:
                # 历史版本样式
                version_label.setFont(QFont(config.DEFAULT_FONT, config.FONT_SIZE, QFont.Bold))
                
                # 第一次添加历史版本时，添加历史版本标题
                if not history_label_added:
                    scroll_layout.addSpacing(30)
                    history_version_label = QLabel("历史版本更新日志")
                    history_version_label.setFont(QFont(config.DEFAULT_FONT, config.FONT_SIZE + 2, QFont.Bold))
                    history_version_label.setStyleSheet(f"color: {config.SECONDARY_COLOR};")
                    scroll_layout.addWidget(history_version_label)
                    history_label_added = True
                
                # 添加版本间距
                scroll_layout.addSpacing(20)
            
            scroll_layout.addWidget(version_label)
            
            # 更新日志内容
            log_text = QLabel(log_info['content'].strip())
            log_text.setWordWrap(True)
            log_text.setStyleSheet(f"color: {config.TEXT_COLOR};")
            scroll_layout.addWidget(log_text)
        
        scroll_layout.addStretch()
        
        # 创建滚动区域并添加到主布局
        scroll_area_widget = QScrollArea()
        scroll_area_widget.setWidgetResizable(True)
        scroll_area_widget.setWidget(scroll_area)
        layout.addWidget(scroll_area_widget)
        
        # 添加关闭按钮
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

# 主函数
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，提供更现代的界面
    
    # 设置中文显示
    import locale
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    
    # 设置Qt应用程序的语言环境
    from PyQt5.QtCore import QLocale
    QLocale.setDefault(QLocale(QLocale.Chinese, QLocale.China))
    
    # 显示启动画面
    splash = SplashScreen()
    splash.show()
    
    # 等待1秒钟后隐藏启动画面
    app.processEvents()
    QTimer.singleShot(1000, splash.close)
    
    # 设置全局字体
    font = QFont(config.DEFAULT_FONT, config.FONT_SIZE)
    app.setFont(font)
    
    # 设置应用程序样式表，使界面更美观
    app.setStyleSheet(f"""QMainWindow {{background-color: {config.BACKGROUND_COLOR};}}
        QPushButton {{background-color: {config.PRIMARY_COLOR}; color: white; border-radius: 4px; padding: 6px;}}
        QPushButton:hover {{background-color: {config.SECONDARY_COLOR};}}
        QTabWidget::pane {{border: 1px solid #ccc; background-color: white;}}
        QTabBar::tab {{background-color: #f0f0f0; border: 1px solid #ccc; padding: 8px;}}
        QTabBar::tab:selected {{background-color: white; border-bottom-color: white;}}
        QCalendarWidget {{background-color: white;}}
        QStatusBar {{background-color: #f0f0f0;}}
        * {{color: {config.TEXT_COLOR};}}
    """)
    
    # 创建并显示主窗口
    window = ClassTableApp()
    QTimer.singleShot(1000, window.show)
    
    sys.exit(app.exec_())