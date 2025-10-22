import numpy as np
import pandas as pd
import logging
import warnings
from datetime import datetime
from scipy.optimize import minimize
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
import ctypes
import sys
import os

import os



matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['font.family'] = 'sans-serif'



# 日志配置

#logging_save_path = r"C:\Users\86155\Desktop\try_for_admin_1"
#logging.basicConfig(filename=logging_save_path, level=logging.INFO, filemode='a')

#filename = r"C:\Users\86155\Desktop\try_for_admin_1\log.log"
# 日志打印 记录错误
# 创建一个用于记录警告的函数

def model_runner(filename):
    filename= filename
    def log_warning(message, category, filename, lineno, file=None, line=None):
        now = datetime.now()
        time_tickle = now.strftime("%Y-%m-%d-%H:%M:%S")
        log_msg = f"{time_tickle}: \n {category.__name__}: {message} at line {lineno} in {filename}"
        logging.warning(log_msg)

    # 将警告转化为异常
    warnings.simplefilter('error', RuntimeWarning)

    # 处理无穷情况的值取float64最大值的近似值
    INF_value = 1.797e+308 # 1.7976931348623157e+308

    # 定义一个阵列计算而不是遍历的算法
    def model_local_in_one(radioligands: np.ndarray, T_array: np.ndarray, Bmax_value: float, kon: float, koff: float, Time0: float):
        Y = np.zeros(T_array.shape) # 生成Y
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            kon = np.power(10,kon)
            koff = np.power(10,koff)
            Kob=np.longdouble(radioligands*kon+koff)
            Kd=np.longdouble(koff/kon)
            Eq=np.longdouble(Bmax_value*radioligands/(radioligands + Kd))
            YatTime0 =np.longdouble(Eq*(1-np.exp(-1*Kob*Time0)))
            # 判断时间段
            T_flag_diss = np.float32(T_array>Time0) #解离
            T_flag_ass = np.float32(T_array<=Time0) #结合

            Y = YatTime0 * np.exp(-1 * koff * (T_array - Time0)) * T_flag_diss + Eq * (1-np.exp(-1*Kob*T_array)) * T_flag_ass
            if len(w) > 0:  # 如果有警告发生
                for warning in w:
                    # 使用自定义的日志记录函数记录警告信息
                    log_warning(warning.message, warning.category, warning.filename, warning.lineno)
                    # logging.info("时间:{}, koff:{}, exp内:{}, YatTime0:{}, -kob*Time0:{}, kon:{}, kob:{}".format(
                        # T, koff, -1 * koff * (T - Time0), YatTime0, -Kob*Time0, kon, Kob))
                Y = INF_value  # 如果有溢出，可以将Y设置为无穷大或合适的值
        return Y

    # 目标函数
    # A_data是浓度数据, 应该是一个向量而不是单个值
    # T_data是时间数据
    # Y_data是信号数据
    # T_break是结合解离的分割时间

    def Loss_local_in_one(params, A_data: np.ndarray, T_data: np.ndarray, Y_data: np.ndarray, T_break: float):
        R, ka, kd = params
        Y_predictions = model_local_in_one(A_data,T_data,R,ka,kd,T_break)
        residuals = Y_predictions - Y_data
        # 计算总残差平方和
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            R2 = np.sum(np.square(residuals))
            if len(w) > 0:  # 如果有警告发生
                for warning in w:
                    # 使用自定义的日志记录函数记录警告信息
                    log_warning(warning.message, warning.category, warning.filename, warning.lineno)
                    logging.info("koff{}, kon内{}".format(kd, ka))
                R2 = INF_value  # 如果有溢出，可以将Y设置为无穷大或合适的值
        return R2



    # 读取数据
    dataframe = pd.read_excel(
        filename)
    data_array = dataframe.to_numpy()
    # 用最大信号值作为R_max的估计
    Y_data = data_array[:,1:]
    Y_data = Y_data.astype(np.longdouble)
    R_guess = np.max(Y_data)
    # 获取浓度数据
    A_data = np.array(dataframe.columns)
    A_data = A_data[1:]
    A_data = A_data.astype(np.longdouble)
    A_data = np.tile(A_data, (Y_data.shape[0], 1))# 用M做单位

    # 获取时间数据
    T_data = data_array[:,0]
    T_data = np.tile(T_data,(Y_data.shape[1],1))
    T_data = T_data.transpose()
    T_data = T_data.astype(np.longdouble)

    # 分段时间（自动估计：找到Y值最大值的位置）
    try:
        Y_max_idx = np.unravel_index(np.argmax(Y_data), Y_data.shape)[0]
        time_break = float(T_data[Y_max_idx, 0])
        # 确保time_break在合理范围内
        if time_break < 1 or time_break >= T_data.shape[0]:
            time_break = T_data.shape[0] // 2
        print(f"[AutoEstimate] time_break: {time_break} (Y_max at row {Y_max_idx})")
    except Exception as e:
        # 回退：使用数据范围的一半
        time_break = T_data.shape[0] // 2
        print(f"[Warning] time_break estimation failed, using default: {time_break}, error: {e}")
    
    R_guess

    # 初始参数猜测
    initial_guess = [R_guess*1.5, 6, -2]
    # 记录参数的变化情况
    R2_values = []
    ka_values = []
    kd_values = []

    #链家 执行优化
    # 设置范围 R, ka, kd = params
    bnds = ((0,np.inf),(0,np.inf),(-np.inf,np.inf))
    result = minimize(Loss_local_in_one, initial_guess, args=(A_data, T_data, Y_data, time_break),
                      method='BFGS',options={'eps': 1e-3})

    # 最优参数
    R_opt, ka_opt, kd_opt = result.x
    ka_opt_p, kd_opt_p = np.power(10,(ka_opt, kd_opt))
    # 看看结果
    print("Rmax: {:.4f}\nkon: {:.4e}\nkoff: {:.4e}\nKD: {:.4e}".format(R_opt, ka_opt_p, kd_opt_p, kd_opt_p/ka_opt_p))

    # 计算Predictions
    Y_pred = model_local_in_one(A_data, T_data, R_opt, ka_opt, kd_opt, time_break)
    print(Y_pred.shape)

    # 做图看看效果
    # ⭐ 返回数据和参数（用于新项目）
    return {
        'T_data': T_data,
        'Y_data': Y_data,
        'Y_pred': Y_pred,
        'parameters': {
            'Rmax': R_opt,
            'kon': ka_opt_p,
            'koff': kd_opt_p,
            'KD': kd_opt_p / ka_opt_p
        }
    }
    # 创建一个figure和一个axes
    '''plt.figure(dpi=300)
    fig, ax = plt.subplots()

    # 绘制原始数据点
    ax.scatter(T_data, Y_data, color='blue', label='Data')
    ax.plot(T_data, Y_pred, color='red', label='Fit')

    # 添加图例
    ax.legend(['Data', 'Fit'])

    # 显示图形
    plt.show()'''

