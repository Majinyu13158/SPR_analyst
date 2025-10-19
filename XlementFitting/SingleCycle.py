import numpy as np
import pandas as pd
from pathlib import Path
import scipy
import matplotlib.pyplot as plt
import scipy.optimize
from XlementFitting import FittingOptions
from XlementFitting.ModelandLoss import model_all_in_one, loss_all_in_one, loss_punished, INF_value
from XlementFitting.FileProcess.ExcelandImage import excel_output, save_output_img, Get_Data_from_path, is_valid_xlsx
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']

NORM_RANK = 5 # 这个数表示用每个浓度的前几个来归0


__all__ = ["SingelCycleFitting"]

# 分割信号为不同的段
def segment_data(
    data,
    peaks_pos: list):
    # 获取第一个显著变化点后所有的数据段
    # peaks_pos表示增长率急剧变高的点
    # 这种点一般表示结合起点
    segments = []
    start_index = peaks_pos[0] + 1  # 跳过第一个显著变化点前的数据

    for i in range(len(peaks_pos) - 1):
        end_index = peaks_pos[i + 1] + 1
        # print(f"当前起点:{start_index}, 当前终点:{end_index}")
        segments.append(data[start_index:end_index])
        start_index = end_index

    # 添加最后一个段
    segments.append(data[start_index:])

    # 找到最长段的长度
    max_length = max(len(segment) for segment in segments)

    # 用NaN填充较短的段，并转换为ndarray
    segments_array = np.full((max_length, len(segments)), np.nan)
    for i, segment in enumerate(segments):
        segments_array[:len(segment), i] = segment
    
    return segments_array

# 把分割点转换成对应的秩
def convert_peaks_to_index_ofdata(
    peaks,
    data):
    # 创建一个空数组来存储结果
    peaks_index = np.empty_like(peaks)

    # 对于每个peak，找到data中小于它的最大值的索引
    for i, peak in enumerate(peaks):
    # 找到小于peak的所有元素的索引
        valid_indices = np.where(data == peak)[0]
        if valid_indices.size > 0:
        # 找到这些元素中最大值的索引
            max_index = valid_indices[-1]
            peaks_index[i] = max_index
        else:
        # 如果没有小于peak的元素，设定为-1（或其他适当的值）
            peaks_index[i] = -1
            
    return peaks_index.astype(int)

def find_longest_time(
    peaks_pos_index,
    data_np,
    Y_shape):
    # 计算所有区间的起始和结束索引
    start_indices = peaks_pos_index
    end_indices = np.append(peaks_pos_index[1:], data_np.shape[0]-1)
    # 计算每个区间的长度
    lengths = end_indices - start_indices
    # 找到最长区间的索引
    max_index = np.argmax(lengths)
    # 提取最长区间的数据
    T_data = data_np[start_indices[max_index]:end_indices[max_index], 0] - data_np[start_indices[max_index], 0]
    # print(f"find_longest_time,起始index:{start_indices[max_index]},结束index:{end_indices[max_index]}")
    T_data = np.tile(T_data, (Y_shape[1], 1))
    T_data = T_data.transpose()
    return T_data

def convert_data_single_cycle(
    file_path: str,
    options: FittingOptions):
    
    if not is_valid_xlsx(file_path):
        return [None, None, None, None, None, None]
    if not isinstance(file_path, Path): file_path = Path(file_path)
    try:
        sheet_data = pd.read_excel(file_path,sheet_name="信号").dropna()
        sheet_info = pd.read_excel(file_path,sheet_name="测试信息")
        data_np = sheet_data.to_numpy()
        concs_np = sheet_info["浓度"].to_numpy()
    except:
        print(f"{file_path}格式不对")
        return [None, None, None, None, None, None]
    
    # 找到对应截取点 
    peaks_pos = sheet_info["结合起点"].to_numpy()
    peaks_neg = sheet_info["解离起点"].to_numpy(),
    peaks_pos_index = convert_peaks_to_index_ofdata(sheet_info["结合起点"].to_numpy(),data_np[:,0])
    peaks_neg_index = convert_peaks_to_index_ofdata(sheet_info["解离起点"].to_numpy(),data_np[:,0])
    data = data_np[:,1]
    
    # 分割信号并重组
    Y_data = segment_data(data, peaks_pos_index)
        
    # 重组不同的时间 浓度 信号
    A_data = np.tile(concs_np, (Y_data.shape[0], 1))
    # T_data = data_np[peaks_pos_index[-1]+1:,0] - data_np[peaks_pos_index[-1]+1,0]
    # T_data = np.tile(T_data, (Y_data.shape[1], 1))
    # T_data = T_data.transpose()
    T_data = find_longest_time(
        peaks_pos_index=peaks_pos_index,
        data_np=data_np,
        Y_shape=Y_data.shape
    )
    # print(f"数据尺寸{Y_data.shape},第一{Y_data[0,:]}")
    initial_signal = np.mean(Y_data[0:NORM_RANK,:],axis=0) # 使用前NORM_RANK个点均值归0
    Y_data = Y_data - initial_signal
    R_guess = np.max(data)
    Time0 = peaks_neg - peaks_pos
    return Y_data, A_data, T_data, R_guess, Time0, peaks_pos, initial_signal

def single_cycle_init(
    Data,
    time0,
    init_params,
    options: FittingOptions
):

    Y_data, A_data, T_data, R_guess = Data
    Conc_num = A_data.shape[1]
    initial_guess = [init_params[0]]*Conc_num + [init_params[1], init_params[2]]
    
    # 构造constrains
    KD_bound = options.get_KD_bound()
    cons = ({'type': 'ineq', 'fun': lambda p: p[2] - p[1] - KD_bound})
    
    eps = options.get_eps()
    result = scipy.optimize.minimize(
        loss_punished,
        initial_guess,
        args=(
            A_data,
            T_data,
            Y_data/R_guess, # 归一化
            time0,
            options,
            Y_data[0,:]/R_guess), # 归一化
        method='SLSQP',
        constraints=cons, 
        options={'eps': eps}
        ) # Y_data归一化
    
    R_opt_array = result.x[:-2]
    ka_opt_log = result.x[-2]
    kd_opt_log = result.x[-1]
    R_opt_array = np.array(R_opt_array) # 反归一化
    ka_opt, kd_opt = np.power(10,(ka_opt_log, kd_opt_log))
    Loss_array = loss_all_in_one(result.x,
                                 A_data,
                                 T_data,
                                 Y_data/R_guess,
                                 time0,
                                 split_flag=True)
    
    Results = {"Rmax":R_opt_array*R_guess,
               "kon":ka_opt,
               "koff":kd_opt,
               "KD":kd_opt/ka_opt,
               "Loss":Loss_array*(R_guess**2)}
    return Results

def SingleCycleFitting(
    file_path,
    options: FittingOptions = FittingOptions(), 
    write_file: bool=True,
    save_png: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    # 这里返回的Y_data已经归0了, signal_start是归0值, 之后要加回来
    Y_data, A_data, T_data, R_guess, time0, peaks_pos, signal_start = convert_data_single_cycle(file_path,options)
    Data = [Y_data, A_data, T_data, R_guess]
    
    init_params_list = options.get_init_params_list()
        
    Results = single_cycle_init(Data, time0, [1.0,4,0], options)
    last_min_loss = np.sum(Results["Loss"])
    for init_params in init_params_list:
        current_result =  single_cycle_init(Data, time0, init_params, options)
        if last_min_loss > np.sum(current_result["Loss"]):
            Results = current_result
            last_min_loss = np.sum(current_result["Loss"])
    
    # 填充浓度项
    Results["Conc"] = A_data[0].tolist()
    
    # 转换值为list以保证输出一致
    Results = {key: [value] for key, value in Results.items()}
    
    # Conc_num = A_data.shape[1]
    # Result_Rmax_array = Results["Rmax"][0].tolist()
    y_predictions = model_all_in_one(
        A_data,
        T_data,
        Results["Rmax"][0],
        np.log10(Results["kon"]),
        np.log10(Results["koff"]), 
        time0,
        BackGround=Y_data[0,:])
    
    # 计算R2
    Y_value = Y_data.copy() + signal_start
    Y_value[np.isnan(Y_value)] = 0.0
    TSS_array = np.sum((Y_value - np.mean(Y_value,axis=0))**2.0,axis=0)
    R2 = 1.0 - np.sum(Results['Loss'][0])/np.sum(TSS_array)
    R2_array = 1.0 - Results['Loss'][0]/TSS_array
    Results["R2"] = R2_array
    Results["Chi2"] = [Results['Loss'][0]/(Y_value.size - 3)]
    
    # 计算Chi2并且梳理输出
    # 确保输出等长且为一个python的list
    Results["Global R2"] = [R2]
    Results["Global Chi2"] = [np.sum(Results['Loss'][0])/(Y_value.size - 3)]
    Results["Rmax"] = Results["Rmax"]
    Results["Conc"] = Results["Conc"][0]
    Results["Loss"] = Results["Loss"]
    
    r_path = y_predictions
    T_data[np.isnan(Y_data)] = np.nan
    y_predictions[np.isnan(Y_data)] = np.nan
    Data = [Y_data+signal_start, A_data, T_data, R_guess]
    if write_file: # 如果写入文件那么返回的是文件路径
        r_path = excel_output(
            file_path,
            Data,
            time0=peaks_pos,
            results=Results,
            Y_pred=y_predictions+signal_start,
            target_dir=excel_path,
            global_flag='S')
        # print(f"写入excel:{r_path}")
        
    if save_png: # 如果需要画图
        i_path = save_output_img(
            file_path,
            T_data=T_data,
            Y_data=Y_data+signal_start,
            Y_pred=y_predictions+signal_start,
            Concs=A_data,
            res=Results,
            target_dir=png_path,
            global_flag='S',
            time_start=peaks_pos)
        # print(f"写入excel:{i_path}")
        
    else:
        i_path = ''
    
    return Results, r_path, i_path # 如果不写入路径那么在Results之后返回Y的预测值
    
