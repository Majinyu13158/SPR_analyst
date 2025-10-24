import numpy as np
import pandas as pd
from scipy.optimize import minimize, least_squares
from pathlib import Path
import matplotlib.pyplot as plt
from XlementFitting import FittingOptions
from XlementFitting.ModelandLoss import balance_loss, balance_model, INF_value
from XlementFitting.ModelandLoss_lm import loss_all_in_one_lm, loss_punished_lm
from FileProcess.ExcelandImage import excel_output, save_output_img
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']

__all__ = ["BalanceFitting"]

# 从file_path转换为Data数组
def Get_Data_from_path(file_path):
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

def get_data4balance_fitting(
    file_path,
    balance_time_start,
    balance_time_end
):
    Y_data, A_data, T_data, R_guess = split_data(Get_Data_from_path(file_path=file_path))
    balance_singal_array = Y_data[balance_time_start:balance_time_end]
    return balance_singal_array, A_data[0,:], R_guess

def balance_fitting_init(
    balance_signal_array, # 这里传进来的应该是归一化的信号
    concentrations,
    options:FittingOptions=FittingOptions()
):
    L1_flag = True # 此处为True则把亲和力纳入正则化考虑
    params = options.get_init_params_list()
    init_params = list(map(lambda x: [x[0], x[2] - x[1]], params))
    Result = minimize(
        balance_loss,
        init_params[0],
        args=(
            balance_signal_array,
            concentrations,
            L1_flag
        )
    )
    for init_param in init_params:
        Result0 = minimize(
            balance_loss,
            init_param,
            args=(
                balance_signal_array,
                concentrations,
                L1_flag
            ),
            method='SLSQP'
        )
        if Result.fun > Result0.fun:
            Result = Result0

    Rmax_predicted, affinity_predicted_log = Result.x
    loss = balance_loss(
        params=[Rmax_predicted, affinity_predicted_log],
        y_real=balance_signal_array,
        concentrations=concentrations,
        L1_regularized=False
    )
    Results = {
        "Loss":loss,
        "Rmax":Rmax_predicted,
        "KD":affinity_predicted_log
    }
    return Results
        
def BalanceFitting(
    file_path,
    custom_options:FittingOptions = FittingOptions(),
    balance_time_start:int = -1.0,
    balance_time_end:int = -1.0,
    write_file:bool = False,
    save_png:bool = False,
    excel_path:Path = Path('.'),
    png_path:Path = Path('.')
):
    if balance_time_start == -1.0 or balance_time_end == -1.0:
        raise ValueError("Set start and end time for balance fitting!")
    if balance_time_end <= balance_time_start:
        raise ValueError(f"Balance end time {balance_time_end} is earlier than start time {balance_time_start}")
    if not isinstance(balance_time_start, int) or not isinstance(balance_time_end, int):
        raise TypeError("The balance end time and start time should be integral!")
    
    Balance_signal_array, Concs, Signal_max = get_data4balance_fitting(
        file_path=file_path,
        balance_time_start=balance_time_start,
        balance_time_end=balance_time_end
    )

    Balance_signal_array_norm = Balance_signal_array / Signal_max # 归一化
    
    Results = balance_fitting_init(
        balance_signal_array=Balance_signal_array_norm,
        concentrations=Concs,
        options=custom_options
    )
    
    TSS = np.sum((Balance_signal_array - np.mean(Balance_signal_array))**2.0)
    Results["Loss"] = Results["Loss"]*(Signal_max**2)
    Results["Rmax"] = Results["Rmax"]*Signal_max
    Results["R2"] = 1.0 - Results["Loss"]/TSS
    
    if not isinstance(excel_path, Path):
        excel_path = Path(excel_path)
    if not isinstance(png_path, Path):
        png_path = Path(png_path)
        
    Concs_curve = np.linspace(np.min(Concs), np.max(Concs), 100)
    predictions = balance_model(
        concentrations=Concs_curve,
        Rmax=Results["Rmax"],
        Affinity=np.power(10,Results["KD"])
    )
    r_path = predictions
    if write_file: # 如果写入文件那么返回的是文件路径
        pass
        
    if save_png: # 如果需要画图
        Results["KD"] = np.power(10,Results["KD"])
        i_path = save_output_img(
            file_path,
            T_data=np.mean(Balance_signal_array, axis=0),
            Y_data=np.mean(Balance_signal_array, axis=0),
            Y_pred=predictions,
            Concs=Concs,
            res=Results,
            target_dir=png_path,
            global_flag='B')
        # print(f"写入excel:{i_path}")
        
    else:
        i_path = ''
    
    return Results, r_path, i_path # 如果不写入路径那么在Results之后返回Y的预测值