import numpy as np
import pandas as pd
from scipy.optimize import minimize, least_squares
import matplotlib.pyplot as plt
from XlementFitting import FittingOptions
from XlementFitting.ModelandLoss import model_all_in_one, loss_all_in_one, loss_punished, INF_value
from XlementFitting.FileProcess.Json2Data import transform_dataframe
from FileProcess.ExcelandImage import excel_output, save_output_img
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
# 建议使用Bivariate12接口

'''
基于Biavriate2算法改进
改变method并添加约束和罚函数项
实现可变数量Bmax参数拟合
'''

__all__ = ["PartialBivariate"]

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

# 主要接口 计算都在这里
def Bivariate_init(
    Data: list,
    time0: float = -1,
    init_params: list = [1.5,4,-4],
    options: FittingOptions=FittingOptions({'eps': 1e-3, 'init_params': [1.5,4,-4]})):
    
    # 数据整理
    Y_data, A_data, T_data, R_guess = Data
    Conc_num = A_data.shape[0]
    initial_guess = [init_params[0]]*Conc_num + [init_params[1], init_params[2]]
    
    # 构造constrains
    KD_bound = options.get_KD_bound()
    cons = ({'type': 'ineq', 'fun': lambda p: p[2] - p[1] - KD_bound})
    
    # 开始运算
    eps = options.get_eps()
    # print("least_square")
    result = minimize(loss_punished,
                      initial_guess,
                      args=(A_data,
                            T_data,
                            Y_data/R_guess,
                            time0,
                            options), 
                      method='SLSQP',
                      constraints=cons, 
                      options={'eps': eps}
                      ) 
    
    R_opt_array = result.x[-Conc_num-2:-2]
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



# 全局拟合最终接口
def PartialBivariate12(
    data_frame: pd.DataFrame,
    time0: float = -1,
    options: FittingOptions=FittingOptions(), 
    write_file: bool=True,
    save_img: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    Y_data, A_data, T_data = transform_dataframe(data_frame)
    R_guess = np.max(Y_data)
    Data = [Y_data, A_data, T_data, R_guess]
    init_params_list = options.get_init_params_list()
        
    Results = Bivariate_init(Data, time0, [1.0,4,0], options)
    last_min_loss = np.sum(Results["Loss"])
    for init_params in init_params_list:
        current_result =  Bivariate_init(Data, time0, init_params, options)
        if last_min_loss > np.sum(current_result["Loss"]):
            Results = current_result
            last_min_loss = np.sum(current_result["Loss"])
    
    # 填充浓度项
    Results["Conc"] = A_data[:,0].tolist()
    
    # 转换值为list以保证输出一致
    Results = {key: [value] for key, value in Results.items()}
    
    Conc_num = A_data.shape[1]
    Result_Rmax_array = Results["Rmax"][0].tolist()
    y_predictions = model_all_in_one(A_data, T_data, Results["Rmax"][0],
                              np.log10(Results["kon"]), np.log10(Results["koff"]), 
                              time0)
    
    # 计算R2
    TSS_array = np.sum((Y_data - np.mean(Y_data,axis=0))**2.0,axis=1)
    R2 = 1.0 - np.sum(Results['Loss'][0])/np.sum((Y_data - np.mean(Y_data))**2.0)
    R2_array = 1.0 - Results['Loss'][0]/TSS_array
    Results["R2"] = R2_array.tolist()
    Results["Chi2"] = Results['Loss'][0]/(Y_data.size - 3)
    Results["Chi2"] = Results["Chi2"].tolist()
    
    # 计算Chi2并且梳理输出
    # 确保输出等长且为一个python的list
    Results["Global R2"] = [R2]
    Results["Global Chi2"] = [np.sum(Results['Loss'][0])/(Y_data.size - 2 - Conc_num)]
    Results["Rmax"] = Results["Rmax"][0].tolist()
    Results["Rmax"] = Results["Rmax"][0:Conc_num]
    Results["Conc"] = Results["Conc"][0]
    Results["Loss"] = Results["Loss"][0].tolist()
    
    r_path = y_predictions.T
    Data = [Y_data, A_data, T_data, R_guess]
    if write_file: # 如果写入文件那么返回的是文件路径
        r_path = excel_output(
            file_path,
            Data,
            time0=time0,
            results=Results,
            Y_pred=y_predictions,
            target_dir=excel_path,
            global_flag='P')
        # print(f"写入excel:{r_path}")
        
    if save_img: # 如果需要画图
        i_path = save_output_img(file_path,
                                 T_data=T_data,
                                 Y_data=Y_data,
                                 Y_pred=y_predictions,
                                 Concs=A_data,
                                 res=Results,
                                 target_dir=png_path,
                                 global_flag='P')
        # print(f"写入excel:{i_path}")
        
    else:
        i_path = ''
    
    return Results, r_path, i_path # 如果不写入路径那么在Results之后返回Y的预测值

        
# 对Results中相同的键的值求几何均值
def get_geometric_mean(r_list: list, key):
    # 对数求法
    sum = 0.0
    for r in r_list:
        sum += np.log10(r[key])
    mean = sum/len(r_list)
    mean = np.power(10,mean)
    return mean

# 汇总接口Bivariate12
def PartialBivariate(
    data_frame,
    time0: float=-1,
    options: FittingOptions = FittingOptions(), 
    write_file: bool=True,
    save_png: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):

    # print(type(options))
    # 检查拟合输入
    if isinstance(options, dict):
        options = FittingOptions(options)
        return PartialBivariate12(data_frame,
                             time0,
                             options,
                             write_file,
                             save_png,
                             excel_path,
                             png_path)
    if isinstance(options, FittingOptions):
        return PartialBivariate12(data_frame,
                             time0,
                             options,
                             write_file,
                             save_png,
                             excel_path,
                             png_path)

    print("拟合选项输入错误")
    return [None, None, None]
    
    
if __name__ == "__main__":
    file_path = "SourceData/24080901-李嘉聪-300st0.xlsx" # 输入文件路径
    custom_options = FittingOptions()
    # custom_options.set_init_params([
    #     [1.5,6,-2],
    #     [15,4,-4],
    #     [1500,4,0],
    # ])
    custom_options.set_init_params([
        [1.5,6,-2],
        [1.5,4,-4],
        [150,4,-2],
        [1500,4,0]
    ])
    custom_options.set_punish_k(5.0)
    custom_options.set_KD_bound(-15)
    r,p,i = PartialBivariate(file_path,
                        time0=300.0,
                        options=custom_options,
                        write_file=False,
                        save_png=False) # 全局拟合
    print(r)