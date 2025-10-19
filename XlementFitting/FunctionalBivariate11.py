import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from XlementFitting import FittingOptions
from XlementFitting.ModelandLoss import model_all_in_one, loss_all_in_one, loss_punished, INF_value
from XlementFitting.FileProcess.Json2Data import transform_dataframe
from XlementFitting.FileProcess.ExcelandImage import excel_output, save_output_img
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
# 建议使用Bivariate11接口

'''
基于Biavriate2算法改进
改变method并添加约束和罚函数项
'''

__all__ = ["LocalBivariate", "GlobalBivariate"]

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
    Data: np.ndarray,
    time0: float = -1,
    init_params: list = [1.5,4,-4],
    options: FittingOptions=FittingOptions({'eps': 1e-3, 'init_params': [1.5,4,-4]})):
    
    # 数据整理
    Y_data, A_data, T_data, R_guess = Data
    initial_guess = [init_params[0], init_params[1], init_params[2]]
    
    # 构造constrains
    KD_bound = options.get_KD_bound()
    cons = ({'type': 'ineq', 'fun': lambda p: p[2] - p[1] - KD_bound})
    
    eps = options.get_eps()
    result = minimize(loss_punished,
                      initial_guess,
                      args=(A_data,
                            T_data,
                            Y_data/R_guess,
                            time0,
                            options), 
                      method='SLSQP',
                      constraints=cons, 
                      options={'eps': eps}) # Y_data归一化
    
    R_opt, ka_opt_log, kd_opt_log = result.x
    result.x[0]*=R_guess # 反归一化
    ka_opt, kd_opt = np.power(10,(ka_opt_log, kd_opt_log))
    Loss = loss_all_in_one(
        result.x,
        A_data,
        T_data,
        Y_data,
        time0,
        split_flag=True)
    
    Results = {"Rmax":R_opt*R_guess,
               "kon":ka_opt,
               "koff":kd_opt,
               "KD":kd_opt/ka_opt,
               "Loss":Loss}
    return Results

# 全局拟合最终接口
def GlobalBivariate(
    data_frame: pd.DataFrame, 
    time0: float = -1, 
    options: FittingOptions=FittingOptions(), 
    write_file: bool=True, 
    save_png: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    Y_data, A_data, T_data = transform_dataframe(data_frame)
    R_guess = np.max(Y_data)
    Data = [Y_data, A_data, T_data, R_guess]
    init_params_list = options.get_init_params_list()
    
    # 找出总损失最小的结果
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
    y_predictions = model_all_in_one(
        A_data,
        T_data,
        Result_Rmax_array,
        np.log10(Results["kon"]),
        np.log10(Results["koff"]),
        time0)
    
    # 计算R2
    TSS_array = np.sum((Y_data - np.mean(Y_data,axis=0))**2.0,axis=1)
    R2 = 1.0 - np.sum(Results['Loss'][0])/np.sum((Y_data - np.mean(Y_data))**2.0)
    R2_array = 1.0 - Results['Loss'][0]/TSS_array
    Results["R2"] = R2_array.tolist()
    Results["Chi2"] = [Results['Loss'][0]/(Y_data.size - 3)]
    Results["Chi2"] = Results["Chi2"][0].tolist()
    # 计算Chi2并且梳理输出
    # 确保输出等长且为一个python的list
    Results["Global R2"] = [R2]
    Results["Global Chi2"] = [np.sum(Results['Loss'][0])/(Y_data.size - 2 - Conc_num)]
    Results["Rmax"] = Results["Rmax"]
    # Results["Rmax"] = Results["Rmax"]
    Results["Conc"] = Results["Conc"][0]
    Results["Loss"] = Results["Loss"][0].tolist()
    print(f"Global:{Results["Chi2"]}")
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
            global_flag='G')
        
    if save_png: # 如果需要画图
        i_path = save_output_img(file_path,
                                 T_data=T_data,
                                 Y_data=Y_data,
                                 Y_pred=y_predictions,
                                 Concs=A_data,
                                 res=Results,
                                 target_dir=png_path,
                                 global_flag='G')
    else:
        i_path = ''
    
    return Results, r_path, i_path # 如果不写入路径那么在Results之后返回Y的预测值


# 这个是用来给LocalBivariate调用的代码 把GlobalBivariate11的第一个输入从file_path变成了np_ndarray
def Bivariate11_for_local(
    Data: np.ndarray,
    time0: float,
    options: FittingOptions):
    
    Y_data, A_data, T_data= transform_dataframe(Data)
    R_guess  = np.max(Y_data)
    init_params_list = options.get_init_params_list()
    Data = [Y_data, A_data, T_data, R_guess]
    Results = Bivariate_init(
        Data,
        time0,
        [1.0,4,0],
        options)
    last_min_loss = np.sum(Results["Loss"])
    for init_params in init_params_list:
        current_result =  Bivariate_init(Data, time0, init_params, options)
        if last_min_loss > np.sum(current_result["Loss"]):
            Results = current_result
            last_min_loss = np.sum(current_result["Loss"])
    
    Y_pred = model_all_in_one(A_data, T_data, Results["Rmax"],
                              np.log10(Results["kon"]), np.log10(Results["koff"]), 
                              time0)
    
    # 计算R2
    # print(Results)
    Results['Loss'] = Results['Loss'][0]
    TSS_array = np.sum((Y_data - np.mean(Y_data))**2.0,axis=0)
    R2 = 1.0 - np.sum(Results['Loss'])/np.sum(TSS_array)
    Results["R2"] = R2
    Results["Chi2"] = Results['Loss']/(Y_data.size - 3)

    return Results, Y_pred # 如果不写入路径那么在Results之后返回Y的预测值

# 定义一个生成器函数，它会遍历每一列（除了第一列）
# 生成一个list 里面的每个元素是一个单独的浓度数据+时间
def local_data_generator(dataframe: pd.DataFrame):
    # 获取第一列
    first_column = dataframe.iloc[:, 0]
    for i in range(1, dataframe.shape[1]):
        dataframe_iter = pd.DataFrame({
            dataframe.columns[0]: first_column,
            dataframe.columns[i]: dataframe.iloc[:, i]
        })
        yield dataframe_iter
        
# 对Results中相同的键的值求几何均值
def get_geometric_mean(r_list: list, key):
    # 对数求法
    sum = 0.0
    for r in r_list:
        sum += np.log10(r[key])
    mean = sum/len(r_list)
    mean = np.power(10,mean)
    return mean

# 全体local计算
def LocalBivariate(
    data_frame: pd.DataFrame,
    time0: float = -1,
    options: FittingOptions=FittingOptions(), 
    write_file: bool=True,
    save_png: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    # 提取 'XValue' 列，跳过第一行（假设第一行是浓度）
    x_values = data_frame['XValue'].iloc[1:].to_numpy()

    # 计算最小值
    min_x = np.min(x_values)

    # 对 'XValue' 列进行归零操作，保持第一行不变
    data_frame.loc[1:, 'XValue'] = data_frame.loc[1:, 'XValue'] - min_x
    
    Data = data_frame
    
    # 拆分为不同的浓度组
    local_datas = local_data_generator(Data)
    
    current_results_list = []
    y_predictions_list = []
    
    # 遍历每一个单独的浓度组
    num_params = 0
    for local_data in local_datas:
        # print(f"LocalBivariate:local_data: {local_data}")
        num_params += 3.0
        current_results, y_prediction = Bivariate11_for_local(local_data,time0,options)
        current_results["Conc"] = local_data.iat[0,1]
        y_predictions_list.append(np.squeeze(y_prediction))
        if np.array(local_data.columns)[1] != 0.0: # 0浓度参与拟合不参与最终ka和kd的计算
            current_results_list.append(current_results)
        
    # 把所有的预测值变成一个大表
    y_predictions = np.column_stack(y_predictions_list)
    r_path = y_predictions # 如果不写入文件那么计算结果就会作为第二个返回值
        
    # 求Rmax算数平均值
    results_global_from_local_Rmax = sum(d['Rmax'] for d in current_results_list)/len(current_results_list)
    
    # 求Loss的和
    results_global_from_local_Loss = sum(d['Loss'] for d in current_results_list)
    
    # 求kon和koff几何平均值
    results_global_from_local_kon = get_geometric_mean(current_results_list,'kon')
    results_global_from_local_koff = get_geometric_mean(current_results_list,'koff')
    
    # 计算R2
    Y_data, A_data, T_data, R_guess = split_data(Data)
    Conc_num = A_data.shape[1]
    TSS = np.sum((Y_data - np.mean(Y_data))**2.0)
    R2 = 1 - results_global_from_local_Loss/TSS
    
    # 计算Chi2
    Chi2 = results_global_from_local_Loss/(Y_data.size - num_params)
    
    # 获得最后的总输出
    total_results = {"Rmax":results_global_from_local_Rmax,
                     "kon":results_global_from_local_kon,
                     "koff":results_global_from_local_koff,
                     "KD":results_global_from_local_koff/results_global_from_local_kon,
                     "R2":R2,
                     "Chi2":Chi2,
                     "Loss":results_global_from_local_Loss,
                     "Conc":'Total'} # 确保格式一致
    
    # 合并输出Results
    # current_results_list.append(total_results)
    
    # 合并字典为Results，每个键对应一个向量
    Results = {key: [d[key] for d in current_results_list] for key in current_results_list[0]}
    # print(f"LocalResult输出:{Results}")
    # 计算Chi2并且梳理输出
    # 确保输出等长且为一个python的list
    Results["Global R2"] = [R2]
    Results["Global Chi2"] = [np.sum(Results['Loss'][0])/(Y_data.size - 2 - Conc_num)]
    Results["Rmax"] = Results["Rmax"]
    # Results["Rmax"] = Results["Rmax"][0:Conc_num]
    Results["Conc"] = Results["Conc"]
    Results["Loss"] = Results["Loss"]

    Data = [Y_data, A_data, T_data, R_guess]
    if write_file: # 如果写入文件那么返回的是文件路径
        r_path = excel_output(
            file_path,
            Data,
            time0=time0,
            results=Results,
            Y_pred=y_predictions,
            target_dir=excel_path,
            global_flag='L')
        
    if save_png:
        # total_results = {key: [total_results[key]] for key in total_results}
        i_path = save_output_img(
            file_path,
            T_data=T_data,
            Y_data=Y_data,
            Y_pred=y_predictions,
            Concs=A_data,
            res=Results,
            target_dir=png_path,
            global_flag='L')
    else:
        i_path = ''
    
    return Results , r_path , i_path # 如果不写入路径那么在Results之后返回Y的预测值

# 汇总接口Bivariate11
def Bivariate11(
    file_path,
    time0: float=-1,
    options: FittingOptions = FittingOptions(), 
    write_file: bool=True,
    run_local: bool= False,
    save_png: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    if isinstance(options, dict):
        options = FittingOptions(options)
        
    if not isinstance(options, FittingOptions):
        return [None, None, None]
    
    if run_local: # 如果选择以local的形式拟合
        return LocalBivariate(file_path,
                               time0,
                               options,
                               write_file,
                               save_png,
                               excel_path,
                               png_path)
    else: # 否则就按照全局的形式拟合
        return GlobalBivariate(file_path,
                               time0,
                               options,
                               write_file,
                               save_png,
                               excel_path,
                               png_path)

if __name__ == "__main__":
    file_path = "../../SourceData/黄某辉虚拟数据集/12号样本100st0.xlsx" # 输入文件路径
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
    r,p,i = Bivariate11(file_path,
                        time0=100.0,
                        options=custom_options,
                        write_file=False,
                        save_png=False) # 全局拟合
    print(r)