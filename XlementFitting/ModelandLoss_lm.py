import numpy as np
from XlementFitting import FittingOptions

# 专门为了Levenberg–Marquardt法实现的算法后台

# 处理无穷情况的值取float64最大值的近似值
INF_value = 1.797e+308 # 1.7976931348623157e+308

# 定义我们的模型
@np.errstate(invalid="raise", over="raise")
def model_all_in_one(
    radioligands: np.ndarray,
    T_array: np.ndarray,
    Bmax_value: float,
    kon_log: float,
    koff_log: float, 
    Time0: float,
    BackGround: float = 0.0):
    
    Y_pred = np.zeros(T_array.shape) # 生成Y_pred
    R = Bmax_value
    KD_log = koff_log - kon_log
    
    if KD_log < -25.0:
        return np.ones_like(T_array) * INF_value
    
    try:
        
        # 对数转化为本来的值
        kon = np.power(10,kon_log)
        koff = np.power(10,koff_log)
        
        # 正式的模型计算
        # print(f"浓度类型:{radioligands},kon类型:{kon}")
        Kob=np.longdouble(radioligands*kon+koff)
        # Kd=np.power(10,KD_log)
        # Eq=np.longdouble(Bmax_value*radioligands/(radioligands + Kd))
        # YatTime0 = np.longdouble(Eq*(1-np.exp(-1*Kob*Time0)))
        YatTime0 = (radioligands*R*kon + 
                  np.exp(-Kob*Time0)*(BackGround*koff+radioligands*(-R+BackGround)*kon))/Kob
        
        # 判断时间段
        T_flag_diss = np.float32(T_array>Time0) # 解离
        T_flag_ass = np.float32(T_array<=Time0) # 结合
        
        # # 最终大模型
        # Y_pred = YatTime0 * np.exp(-1 * koff * (T_array - Time0)) * T_flag_diss + Eq * (1-np.exp(-1*Kob*T_array)) * T_flag_ass
        
        Y_pred = (radioligands*R*kon + np.exp(-Kob*T_array) *  
                  (BackGround*koff+radioligands*(-R+BackGround)*kon))/Kob * T_flag_ass + \
                  YatTime0 * np.exp(-1 * koff * (T_array - Time0)) * T_flag_diss
    except FloatingPointError as e:  # 如果有警告发生
        
        Y_pred = np.ones_like(T_array) * INF_value  # 如果有溢出，可以将Y设置为INF_value
        
    return Y_pred # 不含时间

# 损失函数
# A_data是浓度数据, 应该是一个向量而不是单个值
# T_data是时间数据
# Y_data是信号数据
# T_break是结合解离的分割时间
@np.errstate(invalid="raise", over="raise")
def loss_all_in_one_lm(
    params,
    # 以下三个Data应该保持相同大小
    A_data: np.ndarray,
    T_data: np.ndarray,
    Y_data: np.ndarray,
    T_break: float,
    bg: float = 0.0,
    split_flag: bool = False): # 是否按行输出损失
    
    R_max_array = params[:-2]
    ka = params[-2]
    kd = params[-1]
    Y_predictions = model_all_in_one(A_data,T_data,R_max_array,ka,kd,T_break,BackGround=bg)
    residuals = Y_predictions - Y_data
    
    # 将Y_data中的nan值对应的残差设置为零
    residuals[np.isnan(Y_data)] = 0.0
    
    INF_root = np.power(10,np.log10(INF_value) / 3.0)
    residuals_limited = residuals.copy()
    residuals_limited[residuals_limited>INF_root] = INF_root
    
    # 如果按照列求损失
    if split_flag:
        Loss = np.sum(np.square(residuals_limited), axis=0)
        return Loss
    
    # 把不同浓度
    # residuals = np.square(residuals_limited)
    return residuals

# 构造惩罚函数
def punish_function(p, lower_bound = -10.0, upper_bound = 0.0, k = 10):
    if np.abs(p) > 20:
        return 1.0
    return 2.0 - 1 / (1 + np.exp(-k * (p - lower_bound))) - 1 / (1 + np.exp(-k * (-p + upper_bound)))

# 构造带惩罚和正则化的损失函数
def loss_punished_lm(
    params,
    A_data: np.ndarray,
    T_data: np.ndarray,
    Y_data: np.ndarray,
    T_break: float,
    options: FittingOptions=FittingOptions({'eps': 1e-3, 'init_params': [1.5,4,-4]}),
    bg: float = 0.0,):
    
    # 校验异常值
    ka_log = params[-2]
    kd_log = params[-1]
    kD_log = kd_log - ka_log
    
    # 真实的损失
    real_loss = loss_all_in_one_lm(params, A_data, T_data, Y_data, T_break, bg=bg)
    # print(f"ka:{np.power(10, ka_log)}, koff:{np.power(10, kd_log)}")
    
    # 构造惩罚项
    punishment = punish_function(kD_log,
        lower_bound=options.get_punish_lower(),
        upper_bound=options.get_punish_upper(),
        k=options.get_punish_k()) * Y_data.size * options.get_punish_lam() # 这里的浮点数是一个系数
    real_loss = real_loss.flatten()
    # print(f"损失尺寸{real_loss.shape}")
    return real_loss + punishment