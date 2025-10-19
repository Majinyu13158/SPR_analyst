import os
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from FunctionalBivariate2 import Bivariate2
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 定义米氏方程微分方程
# 设置NumPy的错误处理，使其在遇到溢出时抛出警告
@np.errstate(invalid="raise", over="raise")
def mf(
    R:float,
    radioligand:float,
    Rmax:float=100.0,
    kon:float=1e6,
    koff:float=1e-2):
    try:
        dRdt = kon * radioligand * (Rmax - R) - koff * R
    except FloatingPointError as e:
        dRdt = mf(Rmax,radioligand,Rmax,kon,koff)
    # logging.info(f"mf:kon:{kon:.4e},radoligand{np.max(radioligand):.4f},koff:{koff:.4e},R:{np.max(R):.4e},Rmax{np.max(Rmax):.4f}")
    return dRdt

# 这里开发向量化的多浓度计算模式
# 定义向量化运算浓度函数的方法 添加半步长的浓度计算
# 设置NumPy的错误处理，使其在遇到溢出时抛出警告
@np.errstate(invalid="raise", over="raise")
def diffused_concentration_array(time:np.ndarray,radioligands:np.ndarray,
                                 window_size:float,center_time:float,diffusion_cons:float=-0.2):
    # 如果时间长度过长会导致exp溢出 这里需要做放缩
    ranks_time = time / np.max(time)
    ranks_window_size = window_size / np.max(time)
    ranks_center_time = center_time / np.max(time)
    # 扩增ranks_time使得yy包含步长的精确浓度信息
    averages = (ranks_time[:-1] + ranks_time[1:]) / 2.0
    # 初始化oliveira数组，长度为2n-1
    enlarged_ranks_time = np.empty((2 * len(ranks_time) - 1,))
    # 将原始时间点和平均值交替填入oliveira数组
    enlarged_ranks_time[0::2] = ranks_time
    enlarged_ranks_time[1::2] = averages
    try:
        yy = 1/(1+np.exp(diffusion_cons*(enlarged_ranks_time+ranks_window_size-ranks_center_time))) + \
        1/(1+np.exp(-diffusion_cons*(enlarged_ranks_time-ranks_window_size-ranks_center_time))) - 1
    except FloatingPointError as e:
        # yy = diffused_concentration_array(time,radioligands,center_time,center_time,diffusion_cons/8)
        yy = np.ones_like(enlarged_ranks_time, dtype=float)
        yy[enlarged_ranks_time<=(center_time - window_size)] = 0.0
        yy[enlarged_ranks_time>=(center_time + window_size)] = 0.0
    yy = np.outer(yy, radioligands) # 秩不变 是对齐的
    return yy

# 定义Euler数值解法
# 向量化运算
def euler_numerical_mf_array(
    time:np.ndarray,
    radioligands:np.ndarray,
    window_size:float,
    center_time:float,
    diffusion_cons:float=-0.2,
    R0:float=0.0,
    Rmax:float=100.0,
    kon:float=1e6,
    koff:float=1e-2):
    # 扩增数据尺寸
    A_data = diffused_concentration_array(time,radioligands,window_size,center_time,diffusion_cons)
    T_data = np.tile(time, (radioligands.shape[1],1)).T
    # 如果检测到diffused_concentration_array溢出 说明参数不合适
    if not isinstance(A_data, np.ndarray):
        return -1.0
    
    if np.max(T_data.shape)*2-1 != np.max(A_data.shape):
        print(f"时间尺寸{T_data.shape}和浓度数据尺寸{A_data.shape}对不上")
        print(f"time_col shape:{time.shape},radioligands_row shape:{radioligands.shape}")
        return -1.0
    
    R_t = np.full(T_data.shape,R0) # 填充最终输出信号
    for index, tt in enumerate(time):
        if index == len(time) - 1:
            continue
        delta_t = T_data[index+1,:] - tt
        R_current = R_t[index,:]
        A_current = A_data[2*index,:]
        A_next = A_data[2*index+2,:]
        try:
            dR_one = delta_t * mf(R_current, A_current, Rmax, kon, koff) # tt处的导数
            dR_two = delta_t * mf(R_current + dR_one, A_next, Rmax, kon, koff)
            R_t[index+1,:] = R_t[index,:] + (dR_one + dR_two) / 2
        except FloatingPointError as e:
            print(
                f"euler_numerical_mf_array:{e}\nR:{np.max(R_current):4e},dR1:{np.max(dR_one):4e},dR2:{np.max(dR_two):4e}"
            )
            R_t[index+1,:] = R_t[index,:]
    return R_t

# 定义四阶R-K数值解法
# 向量化运算
# def RK_numerical_mf_array(time:np.ndarray,radioligands:np.ndarray,window_size:float,
#                         center_time:float,diffusion_cons:float=-0.2,R0:float=0.0,
#                         Rmax:float=100.0,kon:float=1e6,koff:float=1e-2):
#     # 扩增数据尺寸
#     A_data = diffused_concentration_array(time,radioligands,window_size,center_time,diffusion_cons)
#     T_data = np.tile(time, (radioligands.shape[1],1)).T
    
#     # 如果检测到diffused_concentration_array溢出 说明参数不合适
#     if not isinstance(A_data, np.ndarray):
#         return -1.0
    
#     if np.max(T_data.shape)*2-1 != np.max(A_data.shape):
#         print(f"时间尺寸{T_data.shape}和浓度数据尺寸{A_data.shape}对不上")
#         print(f"time_col shape:{time.shape},radioligands_row shape:{radioligands.shape}")
#         return -1.0
    
#     R_t = np.full(T_data.shape,R0) # 填充最终输出信号
#     for index, tt in enumerate(time):
#         if index == len(time) - 1: # 控制循环结束
#             continue
#         delta_t = T_data[index+1,:] - tt
#         R_current = R_t[index,:]
#         A_current = A_data[2*index,:]
#         A_half_plus = A_data[2*index+1,:]
#         A_next = A_data[2*index+2,:]
#         try:
#             k1 = delta_t * mf(R_current, A_current, Rmax, kon, koff) # tt处的导数
#             k2 = delta_t * mf(R_current + k1/2, A_half_plus, Rmax, kon, koff)
#             k3 = delta_t * mf(R_current + k2/2, A_half_plus, Rmax, kon, koff)
#             k4 = delta_t * mf(R_current + k3, A_next, Rmax, kon, koff)
#             R_t[index+1,:] = R_t[index,:] + (k1 + 2*k2 + 2*k3 + k4) / 6
#         except FloatingPointError as e:
#             print(
#                 f"RK_numerical_mf_array:{e}\nk1:{np.max(k1):4e},k2:{np.max(k2):4e},k3:{np.max(k3):4e},k4:{np.max(k4):4e}"
#             )
#             R_t[index+1,:] = R_t[index,:]
#     return R_t

# 定义模型
def model_numerical_mf(
    T_data_col:np.ndarray,
    A_data_row:np.ndarray,
    window_size:float,
    center_time:float,
    diffusion_cons:float=-0.2,
    Rmax:float=100.0,
    kon:float=1e6,
    koff:float=1e-2,
    R0:float=0.0):

    Y_predictions = euler_numerical_mf_array(
    time=T_data_col,
    radioligands=A_data_row,
    window_size=window_size,
    center_time=center_time,
    diffusion_cons=diffusion_cons,
    Rmax=Rmax,kon=kon,koff=koff,R0=R0)
    
    return Y_predictions

# 定义损失函数
# 定义把时间项作为待拟合参数的损失函数
def loss_numerical_mf_time_fitted(
    params,
    T_data_col:np.ndarray,
    A_data_row:np.ndarray,
    Y_real:np.ndarray,
    R0:float=0.0,
    numerical_method="R-K",
    bind_end_time:float=1.0):
    # 待拟合参数包括: 结合半窗长 结合中心时间 扩散常数 Rmax kon koff
    Rmax_array = params[:-5]
    window_size,center_time,diffusion_cons_sqrt,kon_log,koff_log = params[-5:]
    if np.max(np.abs([kon_log, koff_log])) > 50.0: # 运算出错 直接返回一个超大的损失
        return 1.7e+300
    # 结合半窗长 结合中心时间 Rmax kon koff 必须大于0
    kon, koff = np.power(10,(kon_log, koff_log))
    window_size,center_time = np.square((window_size, center_time))
    # 扩散常数必须小于0 变化区间比较小使用2的对数和指数变化
    diffusion_cons = - np.square(diffusion_cons_sqrt)
    # 计算预测值
    Y_predicted = model_numerical_mf(
        T_data_col,
        A_data_row,
        window_size,
        center_time,
        diffusion_cons,
        Rmax_array,
        kon,
        koff,
        R0)
    if not isinstance(Y_predicted, np.ndarray): # 运算出错 直接返回一个超大的损失
        return 1.7e+300
    # 计算损失 限制损失过大
    residuals = Y_real - Y_predicted
    residuals[residuals>4e100] = 4e100
    try:
        squared_residuals = np.square(residuals)
        Loss = np.sum(squared_residuals)
        # 以下惩罚的目的在于约束拟合的结合时间保持在实验真实的结合时间以内
        # 如果结合中心时间<结合半窗长 施加惩罚
        Loss = Loss + np.exp(window_size-center_time)
        # 如果(结合中心时间+结合半窗长)<结合终止时间 施加惩罚
        Loss = Loss + np.exp(bind_end_time - (window_size + center_time))
    except FloatingPointError as e:
        print(f"loss_numerical_mf_time_fitted:{e}\nMax Residual:{np.max(residuals):4e}")
        Loss = 1.7e+300
    return Loss

# 定义把时间项作为输入参数的损失函数
# def loss_numerical_mf_time_input(params,T_data_col:np.ndarray,A_data_row:np.ndarray,Y_real:np.ndarray,
#                                  R0:float=0.0,numerical_method="R-K",window_size:float=20,center_time:float=25):
#     # 待拟合参数包括: 结合半窗长 结合中心时间 扩散常数 Rmax kon koff
#     diffusion_cons_sqrt,Rmax,kon_log,koff_log = params
#     if np.max(np.abs([kon_log, koff_log])) > 50: # 运算出错 直接返回一个超大的损失
#         return 1.7e+300
#     # 结合半窗长 结合中心时间 Rmax kon koff 必须大于0
#     kon, koff = np.power(10,(kon_log, koff_log))
#     # 扩散常数必须小于0 变化区间比较小使用2的对数和指数变化
#     diffusion_cons = - np.square(diffusion_cons_sqrt)
#     # 计算预测值
#     Y_predicted = model_numerical_mf(
#         T_data_col,
#         A_data_row,
#         window_size,
#         center_time,
#         diffusion_cons,
#         Rmax,
#         kon,
#         koff,
#         R0,
#         numerical_method)
#     if not isinstance(Y_predicted, np.ndarray): # 运算出错 直接返回一个超大的损失
#         return 1.7e+300
#     # 计算损失 限制损失过大
#     residuals = Y_real - Y_predicted
#     residuals[residuals>4e100] = 4e100
#     try:
#         squared_residuals = np.square(residuals)
#         Loss = np.sum(squared_residuals)
#     except FloatingPointError as e:
#         print(f"loss_numerical_mf_time_input:{e}\nMax Residual:{np.max(residuals):4e}")
#         Loss = 1.7e+300
#     return Loss

# 定义训练函数
def curve_fit_numerical_mf(
    time_data_col:np.ndarray,
    Conc_data_row:np.ndarray,
    Y_real_data:np.ndarray,
    bind_start_time:float,
    bind_end_time:float,
    diffusion_cons_sqrt:float=-2.3,
    Rmax_init:float=100.0,
    kon_log:float=6,
    koff_log:float=-2,
    R0:float=0.0,
    custom_method:dict={"numerical":"R-K","time type":"fitted","optimize":'TNC',"eps":1e-3}):
    custom_numerical_method = custom_method["numerical"] # 解包数值计算方式
    # 初始化拟合时间项
    window_size_init = np.sqrt((bind_end_time - bind_start_time) / 2.0)
    center_time_init = np.sqrt((bind_end_time + bind_start_time) / 2.0)
    if custom_method["time type"] == "fitted": # 如果时间项是待拟合的
        initial_params = Rmax_init + [window_size_init, center_time_init, diffusion_cons_sqrt,
                          kon_log, koff_log]
        result = minimize(
            loss_numerical_mf_time_fitted,
            initial_params, 
            args=(
                time_data_col,
                Conc_data_row,
                Y_real_data,
                R0,
                custom_numerical_method,
                bind_end_time),
            method=custom_method["optimize"],
            options={'eps': custom_method["eps"]})
    # elif custom_method["time type"] == "input":
    #     initial_params = [diffusion_cons_sqrt, Rmax_init, kon_log, koff_log]
    #     result = minimize(loss_numerical_mf_time_input, initial_params, 
    #                       args=(time_data_col,Conc_data_row,Y_real_data,R0,custom_numerical_method,
    #                             window_size_init,center_time_init),
    #                             method=custom_method["optimize"],options={'eps': custom_method["eps"]})
    return result

# 定义数据处理函数
def get_data_from_path(file_path):
    data_frame = pd.read_excel(file_path)
    data_array = data_frame.to_numpy()
    # 获取浓度行
    A_data = np.array(data_frame.columns)
    Conc_row =  A_data[1:].reshape((1,len(A_data)-1))
    
    # 获取时间列
    time_col = data_array[:,0]
    
    # 获取信号
    signal_data = data_array[:,1:]
    # signal_data = np.flip(signal_data, axis=1)
    
    # 估算最大值
    Y_max = np.max(signal_data)
    
    return time_col, Conc_row, signal_data, Y_max

# 使用Biv2算法预拟合亲和力相关参数
def curve_fit_numerical_mf_biv2(file_path,bind_start_time:float,bind_end_time:float,diffusion_cons_sqrt:float=-2.3,
                        R0:float=0.0,customized_methods:dict={"numerical":"R-K","time type":"fitted","optimize":'TNC',"eps":1e-3}):
    r,p,_ = Bivariate2(file_path,time0=bind_end_time,write_file=False,run_local=True) # Biv2全局预拟合
    R_max_biv2 = r["Rmax"][:-1]
    # print(f"Rmax是:{R_max_biv2}")
    kon_log10_biv2 = np.log10(r["kon"][0])
    koff_log10_biv2 = np.log10(r["koff"][0])
    time_col, conc_row, signal_real, Ymax = get_data_from_path(file_path)
    # print(f"浓度是:{conc_row}")
    ND_result = curve_fit_numerical_mf(
        time_data_col=time_col,
        Conc_data_row=conc_row,
        Y_real_data=signal_real,
        bind_start_time=bind_start_time,
        bind_end_time=bind_end_time,
        Rmax_init=R_max_biv2,
        kon_log=kon_log10_biv2,
        koff_log=koff_log10_biv2,
        diffusion_cons_sqrt=diffusion_cons_sqrt,
        custom_method=customized_methods)
    return ND_result

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
def save_output_img(file_path, T_data:np.ndarray, Y_data: np.ndarray,
                    Y_pred: np.ndarray, Concs: np.ndarray, res: dict):
   # 检查数据格式大小
    if not (T_data.shape == Y_data.shape):
        return
    if T_data.size > Y_pred.size:
        # 计算需要填充的零行数
        rows_to_fill = Y_data.shape[0] - Y_pred.shape[0]

        # 创建一个全零的矩阵，其行数等于 rows_to_fill，列数与 Y_pred 相同
        zero_rows = np.zeros((rows_to_fill, Y_pred.shape[1]))

        # 将全零矩阵和 Y_pred 垂直堆叠起来
        Y_pred = np.vstack((zero_rows, Y_pred))
    
    # 确定图片保存路径
    if not os.path.exists('./Output/'): os.makedirs('./Output/')
    batchName = file_path.split('/')
    if batchName[-1]:
        pass
    else:
        batchName = file_path.split('\\')
    output_path = './Output/ND4-' + batchName[-1][:-4] + 'png'
    
    # 转换Cons为字符串
    Concs_name = convert_from_concs_2name(np.flipud(Concs.T).T)
    
    # 做图
    plt.figure(dpi=300)
    plt.plot(T_data, np.flipud(Y_data.T).T, label='Data', linewidth=2)
    plt.plot(T_data, Y_pred, color='k', label='Fit', linewidth=1.5)
    # 添加图例
    plt.legend(Concs_name)
    # 添加文字
    plt.figtext(0.1,0.01,
             f"$k_a$:{res['kon'][0]:.4e}, $k_d$:{res['koff'][0]:.4e}, $k_D$:{res['KD'][0]:.4e}, $R_{{max}}$:{res['Rmax'][0]:.2f}, 扩散参数:{res['量准扩散系数'][0]:.2f}",
             fontsize=10,
             color='gray')
    
    plt.title(batchName[-1][:-5]+"(ND4)",fontsize=14)
    plt.savefig(output_path)
    
    return output_path

# 全局拟合文件输出接口
def excel_output_global(file_path, results:dict, Y_pred: np.ndarray):
    
    T_data, A_data, Y_data, R_guess = get_data_from_path(file_path)
    
    # 创建Opt_df
    Opt_df = pd.DataFrame(results)
    Opt_df = pd.concat([Opt_df["Conc"], Opt_df.drop(columns="Conc")],axis=1)
    
    # 根据Y_pred创建DataFrame
    Y_pred_df = pd.DataFrame(Y_pred)
       
    # 获取A_data的列名，并插入'Time'作为第一列
    Y_pred_df.insert(0, 'Time', T_data[:])
    Y_pred_df.columns = ['Time'] + A_data[0,:].tolist()
    
    col_name_list = list(Opt_df.columns)
    col_name_df = pd.DataFrame(col_name_list).T
    col_name_df.columns = col_name_list
    Opt_df.columns = col_name_list
    
    # 合并两个DataFrame，这里假设我们是在纵向合并（增加行数）
    Output_df = pd.concat([Y_pred_df,Opt_df],axis=1,join='outer',ignore_index=False)

    # 获取时间戳
    now = datetime.now()
    time_tickle = now.strftime("%s")[-5:]

    # 获取文件名
    if not os.path.exists('./Result/'): os.makedirs('./Result/')
    
    # 根据OS修改不同的文件名创建方式
    batchName = file_path.split('/')
    if batchName[-1]:
        pass
    else:
        batchName = file_path.split('\\')
    result_path = './Result/' + \
        'GND4-' + time_tickle + '-' + batchName[-1]
    Output_df.to_excel(result_path, index=False)
    
    return result_path

# 定义最终的调用接口
def NumericalDiffusion4(file_path,bind_start_time:float,bind_end_time:float,diffusion_cons_sqrt:float=-2.3,
                        R0:float=0.0,customized_methods:dict={"numerical":"R-K","time type":"fitted","optimize":'TNC',"eps":1e-3},
                        write_file:bool=False,output_img:bool=False):
    ND_result = curve_fit_numerical_mf_biv2(file_path=file_path,bind_start_time=bind_start_time,
                                            bind_end_time=bind_end_time,diffusion_cons_sqrt=diffusion_cons_sqrt,
                                            R0=R0,customized_methods=customized_methods)
    time_col, conc_row, signal_real, Ymax = get_data_from_path(file_path)

    Rmax_opt_array = ND_result.x[:-5]
    Rmax_opt = np.mean(ND_result.x[:-5])
    wsize_opt_sqrt,ctime_opt_sqrt,dc_opt_sqrt,kon_opt_log,koff_opt_log = ND_result.x[-5:]
    print(f"kon_opt_log:{kon_opt_log}")
    wsize_opt,ctime_opt = np.square((wsize_opt_sqrt,ctime_opt_sqrt))
    kon_opt, koff_opt = np.power(10,(kon_opt_log, koff_opt_log))
    dc_opt = - np.square(dc_opt_sqrt)
    
    # 整理结果
    Results = {
        'Conc':['Partial'],
        'Rmax':[Rmax_opt],
        'kon':[kon_opt],
        'koff':[koff_opt],
        'KD':[koff_opt/kon_opt],
        '量准扩散系数':[dc_opt],
        'wsize':[wsize_opt],
        'ctime':[ctime_opt]
    }
    y_predictions = model_numerical_mf(T_data_col=time_col, A_data_row=conc_row, window_size=wsize_opt,
                                 center_time=ctime_opt, diffusion_cons=dc_opt, Rmax=Rmax_opt_array,
                                 kon=kon_opt, koff=koff_opt)
    
    if write_file:
        f_path = excel_output_global(file_path,results=Results,Y_pred=y_predictions)
    else:
        f_path = y_predictions
        
    if output_img:
        T_data = np.tile(time_col, (signal_real.shape[1],1)).T
        i_path = save_output_img(file_path,T_data,signal_real,y_predictions,conc_row,res=Results)
    else:
        i_path=''
    
    return Results, f_path, i_path

if __name__ == "__main__":
    file_path = "SourceData/240806_黄博士数据G1_109st0.xlsx" # 输入文件路径
    this_methods={
        "numerical":"Euler",
        "time type":"fitted",
        "optimize":'TNC',
        "eps":1e-3
        }
    r,p,i = NumericalDiffusion4(file_path,
                                bind_start_time=0.0,
                                bind_end_time=109.0,
                                diffusion_cons_sqrt=10.0,
                                customized_methods=this_methods,
                                write_file=False,output_img=True) # 全局拟合
    print(r)