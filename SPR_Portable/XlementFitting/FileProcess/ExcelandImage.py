import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from openpyxl import load_workbook
import openpyxl.utils.exceptions

# 判断str文件路径是否有效果
def is_valid_xlsx(file_path: str) -> bool:
    if not isinstance(file_path, Path): path = Path(file_path)
    else: path = file_path

    # 检查路径是否存在且是一个文件
    if not path.is_file():
        print(f"{file_path}不是正确xlsx文件路径")
        return False

    # 尝试用 openpyxl 打开文件
    try:
        load_workbook(file_path)
        return True
    except (openpyxl.utils.exceptions.InvalidFileException, IOError):
        print(f"{file_path}不是正确xlsx文件路径")
        return False

# 从file_path转换为Data数组
def Get_Data_from_path(file_path):
    if not is_valid_xlsx(file_path):
        return None
    dataframe = pd.read_excel(file_path)
    # data_array = dataframe.to_numpy()
    return dataframe

# 把Data分割成不同的部分
def split_data(Dataframe: pd.DataFrame):
    Data = Dataframe.to_numpy()
    # print(Dataframe)
    # 用最大信号值作为R_max的估计
    Y_data = Data[:,1:]
    Y_data = Y_data.astype(np.longdouble)
    R_guess = np.max(Y_data)
    # 获取浓度数据
    A_data = np.array(Dataframe.columns)
    A_data_row = A_data[1:]
    A_data = A_data_row.astype(np.longdouble)
    A_data = np.tile(A_data, (Y_data.shape[0], 1))# 用M做单位

    # 获取时间数据
    T_data_col = Data[:,0]
    T_data = np.tile(T_data_col,(Y_data.shape[1],1))
    T_data = T_data.transpose()
    T_data = T_data.astype(np.longdouble)
    return Y_data, A_data, T_data, R_guess

# 把浓度数据转换为图中输出的文字信息
def convert_from_concs_2name(A_data):
    first_row = A_data[0]
    conc_names = []
    for num in first_row:
        if num < 1e-9:
            num *= 1e12
            conc_names.append(r'$'+f'{num:.1f}'+r'$pM')
        elif num < 1e-6:
            num *= 1e9
            conc_names.append(r'$'+f'{num:.1f}'+r'$nM')
        elif num < 1e-3:
            num *= 1e6
            conc_names.append(r'$'+f'{num:.1f}'+r'\mu'+'$M')
        elif num < 1:
            num *= 1e3
            conc_names.append(r'$'+f'{num:.1f}'+r'$mM')
        else:
            conc_names.append(r'$'+f'{num:.1f}'+r'$M')
    return conc_names

# 图片输出接口
def save_output_img(file_path,
                    T_data:np.ndarray,
                    Y_data: np.ndarray,
                    Y_pred: np.ndarray,
                    Concs: np.ndarray,
                    res: dict,
                    target_dir: str,
                    global_flag: str = 'G',
                    time_start: float = 0.0):
    # 检查数据格式大小
    if not (T_data.shape == Y_data.shape):
        print(f"save_output_img: Tshape:{T_data.shape} Yshape:{Y_data.shape}")
        return
    if T_data.size > Y_pred.size:
        # 计算需要填充的零行数
        rows_to_fill = Y_data.shape[0] - Y_pred.shape[0]

        # 创建一个全零的矩阵，其行数等于 rows_to_fill，列数与 Y_pred 相同
        zero_rows = np.zeros((rows_to_fill, Y_pred.shape[1]))

        # 将全零矩阵和 Y_pred 垂直堆叠起来
        Y_pred = np.vstack((zero_rows, Y_pred))

    # 确保输出目录存在
    output_dir = Path(target_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取文件路径（假设file_path是一个字符串）
    file_path = Path(file_path)

    # 获取文件名并生成输出路径
    batch_name = file_path.stem  # 获取文件名（不包括扩展名）

    # 转换Cons为字符串
    if global_flag != 'B': Concs_name = convert_from_concs_2name(np.flipud(Concs.T).T)

    # 根据Y_pred创建DataFrame
    if global_flag == 'S': # 单循环就展平数据
        Y_pred = Y_pred.transpose().flatten()
        Y_pred = Y_pred[~np.isnan(Y_pred)]
        Y_data = Y_data.transpose().flatten()
        Y_data = Y_data[~np.isnan(Y_data)]
        Y_data = Y_data[::-1]
        T_data = T_data.transpose() + time_start.reshape(-1, 1)
        T_data = T_data.flatten()
        T_data = T_data[~np.isnan(T_data)]
        Concs_name = ['Data','Fit']

    if global_flag == 'B': # 如果是Balance循环
        plt.figure(dpi=300)
        plt.scatter(Concs, Y_data, label='Data', linewidth=2)
        plt.plot(np.linspace(np.min(Concs), np.max(Concs), 100), Y_pred, color='k', label='Fit', linewidth=1.5)
        plt.legend()
        # 添加文字
        plt.figtext(0.1,0.01,
                f"$R_{{max}}$:{res['Rmax']:.4f}, "
                f"$k_D$:{res['KD']:.4e}, "
                f"$R^2$:{res['R2']:.4f}",
                fontsize=10,
                color='gray')
    else:
        # 做图
        plt.figure(dpi=300)
        plt.plot(T_data, np.flipud(Y_data.T).T, label='Data', linewidth=2)
        plt.plot(T_data, Y_pred, color='k', label='Fit', linewidth=1.5)
        # 添加图例
        plt.legend(Concs_name)
        # 添加文字
        plt.figtext(0.1,0.01,
                f"$k_a$:{res['kon'][-1]:.4e}, $k_d$:{res['koff'][-1]:.4e}, "
                f"$k_D$:{res['KD'][-1]:.4e}, "
                f"$R^2$:{res['Global R2'][0]:.4f}, ${{\\chi}}^2$:{res['Global Chi2'][0]:.4f}",
                fontsize=10,
                color='gray')
    # 确定类型
    if global_flag == 'G':
        plt.title(batch_name+"(GlobalBiv)",fontsize=14)
    elif global_flag == 'L':
        plt.title(batch_name+"(LocalBiv)",fontsize=14)
    elif global_flag == 'P':
        plt.title(batch_name+"(PartialBiv)",fontsize=14)
    elif global_flag == 'S':
        plt.title(batch_name+"(SingleCycle)",fontsize=14)
    elif global_flag == 'B':
        plt.title(batch_name+"(BalanceFitting)",fontsize=14)
    output_path = output_dir / f'{global_flag}Biv-{batch_name}.png'
    plt.savefig(output_path)
    plt.close()
    return output_path

# 填充Results dict
def fill_results_for_excel(results:dict):
    # print(results)
    max_length = max(len(v) for v in results.values())
    # print([v for v in results.values()])
    # 创建一个新的字典，其中每个键对应一个填充后的列表
    filled_results = {}
    for key, value in results.items():
        # 对于长度较短的值, 使用第一个值填充较短的列表
        if len(value) < max_length:
            value.extend([value[0]] * (max_length - len(value)))
        filled_results[key] = value
    return filled_results

# 全局拟合文件输出接口
def excel_output(
    file_path,
    Data,
    time0: float, # 遗留的接口 已经被改造用来传递单循环的起点时间
    results:dict,
    Y_pred: np.ndarray,
    target_dir: str = 'Result',
    global_flag: str = 'G'):

    Y_data, A_data, T_data, R_guess = Data
    results = fill_results_for_excel(results)

    # 创建Opt_df
    Opt_df = pd.DataFrame(results)
    Opt_df = pd.concat([Opt_df["Conc"], Opt_df.drop(columns="Conc")],axis=1)

    # 根据Y_pred创建DataFrame
    if global_flag == 'S': # 单循环就展平数据
        Y_pred = Y_pred.transpose().flatten()
        Y_pred = Y_pred[~np.isnan(Y_pred)]
        T_data = T_data.transpose() + time0.reshape(-1, 1)
        T_data = T_data.flatten()
        T_data = T_data[~np.isnan(T_data)]
        Y_pred_df = pd.DataFrame(Y_pred)
        Y_pred_df.insert(0, 'Time', T_data)
        Y_pred_df.columns = ['Time','Cycle']
    else:
        Y_pred_df = pd.DataFrame(Y_pred)
        # 获取A_data的列名，并插入'Time'作为第一列
        Y_pred_df.insert(0, 'Time', T_data[:,0])
        Y_pred_df.columns = ['Time'] + A_data[0,:].tolist()

    col_name_list = list(Opt_df.columns)
    col_name_df = pd.DataFrame(col_name_list).T
    col_name_df.columns = col_name_list
    Opt_df.columns = col_name_list

    # 确保输出目录存在
    output_dir = Path(target_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取文件路径（假设file_path是一个字符串）
    file_path = Path(file_path)

    # 获取文件名并生成输出路径
    batch_name = file_path.stem  # 获取文件名（不包括扩展名）
    result_path = output_dir / f'{global_flag}Biv-{batch_name}.xlsx'

    with pd.ExcelWriter(result_path) as writer:
        Opt_df.to_excel(writer, sheet_name='拟合结果', index=False)
        Y_pred_df.to_excel(writer, sheet_name='拟合曲线', index=False)

    return result_path