import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# 你之前提供的处理函数，需要放在这段代码中
from XlementFitting.FileProcess.JsonFormat import check_unpredicted_json_format
from XlementFitting.FileProcess.Json2Data import read_and_process_json, get_fitting_options
from XlementFitting.FileProcess.Data2Json import process_and_save_json
from XlementFitting import PartialBivariate, GlobalBivariate, LocalBivariate


# xlement_fitting_json_input 函数
def xlement_fitting_json_input(path):
    # 将字符串路径转换为 Path 对象
    path = Path(path)

    # 获取文件名（不包含后缀）和后缀
    stem = path.stem
    suffix_original = path.suffix

    # 创建新的文件名
    new_filename = f"{stem}{'-fit'}{suffix_original}"
    new_path = path.with_name(new_filename)

    # 检查json格式
    if not check_unpredicted_json_format(path):
        print(f"{path}格式有问题")
        return None

    fitting_options, df, time0, f = read_and_process_json(path)
    origin_df = df.copy()
    if f == 103:
        r, p, i = PartialBivariate(
            data_frame=df,
            time0=time0,
            options=get_fitting_options(fitting_options),
            write_file=False,
            excel_path='FittingResultFile'
        )
    elif f == 101:
        r, p, i = LocalBivariate(
            data_frame=df,
            time0=time0,
            options=get_fitting_options(fitting_options),
            write_file=False,
            excel_path='FittingResultFile'
        )
    elif f == 102:
        r, p, i = GlobalBivariate(
            data_frame=df,
            time0=time0,
            options=get_fitting_options(fitting_options),
            write_file=False,
            excel_path='FittingResultFile'
        )

    # 返回处理结果的 DataFrame 进行绘图
    return origin_df, p


# GUI 类
class DragDropButton(QPushButton):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        # 如果拖拽的是文件，可以接受拖拽
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        # 当文件被放下时，处理文件路径
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.handle_file(file_path)

    def handle_file(self, file_path):
        # 调用处理函数并绘图
        print(f"File dropped: {file_path}")
        df, processed_data = xlement_fitting_json_input(file_path)
        if df is not None and processed_data is not None:
            self.plot_data(df, processed_data)

    def plot_data(self, df, processed_data):
        # 绘图：第一列作为X轴
        x = df.iloc[:, 0]  # 第一列作为X轴

        # 检查 x 和 y 的维度是否一致
        for col in range(processed_data.shape[1]):
            y = processed_data[:, col]  # 使用 numpy 数组索引

            # 确保 x 和 y 的长度一致
            if len(x) != len(y):
                min_length = min(len(x), len(y))
                x = x[:min_length]
                y = y[:min_length]

            # 绘制每一列的 y 值
            plt.plot(x, y, label=f"Processed Column {col + 1}")

        plt.xlabel(df.columns[0])
        plt.ylabel("Values")
        plt.title("Plot from processed JSON data")
        plt.legend()
        plt.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口标题
        self.setWindowTitle("File Drag-and-Drop for JSON Processing")

        # 创建主布局
        layout = QVBoxLayout()

        # 创建按钮
        self.button = DragDropButton("Drag JSON file here", self)
        layout.addWidget(self.button)

        # 设置主窗口的中心部件
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


# 主程序入口

app = QApplication(sys.argv)

# 创建主窗口
window = MainWindow()
window.resize(300, 200)
window.show()

app.exec()

















import json
import pandas as pd

# Correct the file path using raw string
file_path = r"C:\Users\86155\Documents\WeChat Files\wxid_2c9vxqufytta22\FileStorage\File\2024-09\One&100多循环v4.json"

# Open JSON file and read data using utf-8-sig encoding to handle BOM
with open(file_path, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)  # Parse JSON data into a Python dictionary

# Pretty-print JSON data
formatted_data = json.dumps(data, indent=4, ensure_ascii=False)
print(formatted_data)

# Check if the data is a dictionary and convert it to a list of dictionaries
if isinstance(data, dict):
    data = [data]

# Convert JSON data to a DataFrame
df = pd.DataFrame(data)

# Save DataFrame to an Excel file
output_path = r"C:\Users\86155\Desktop\qweqwe.xlsx"
df.to_excel(output_path, index=False)

print(f"Data has been written to {output_path}")