import os
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from pathlib import Path
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# 建议使用Bivariate2接口
# 172行和244行根据OS不同做的区分没有经过验证!!!
'''
这段代码是Bivariate2的函数式写法  
陈铭潜 2024年1月11日开始书写

主要计算接口:
Bivariate2_init(Data, time0, init_params, options)输入四个参数
1. Data是一个numpy的ndarray, 第一列是时间列, 第一列第一行空置
Data自第二列开始就是数据, 每一列的第一行是用浮点数表示的单位M
的浓度数据
2. time0表示结合的最后一点也是结合解离的分界点
3. init_params是一个数组包括Rmax猜测的初始系数, kon和koff的初始值
4. options是传给minimize的option是用来设置学习率, 一般是1e-3
返回值则是Rmax kon koff Loss四个值

辅助接口:
Get_data_from_path(file_path)负责从一个file_path解析出我们需要的
Data的数据格式, 返回Data

split_data(Dataframe)负责把数据分割成浓度 时间 值等项
不一一列举

调用接口:
GlobalBivariate2(file_path, time0, options)内部含两个Bivariate2_init
分别从不同的拟合起点开始运算, 返回Loss较小的那个的Rmax kon koff Loss四个值
write_file=True时
写入Excel FittedCurve的具体数据excel文件在'../Results/'路径下G开头
返回值的第二个是Excel的路径
write_file=True时
返回值的第二个就是具体的FittedCurve值
file_path用来传入需要的文件路径

LocalBivariate2(file_path, time0, options, write_file=True)内部含2*n个Bivariate2_init
每个浓度梯度执行一次GlobalBivariate2
返回Rmax的算术平均值 kon koff各自的几何平均值 Loss的和四个值
write_file=True时
写入Excel FittedCurve的具体数据excel文件在'../Results/'路径下L开头
返回值的第二个是Excel的路径
write_file=True时
返回值的第二个就是具体的FittedCurve值
file_path用来传入需要的文件路径

Bivariate2(file_path, time0, options, run_local=Flase)
前面3个参数和其他一致 是一个集成前两个接口的接口
如果run_local=True那么就会按照全部参数Local的模式拟合
默认情况下run_local=False会按照全部参数Global的模式拟合

2024年1月12日主体完成

Bivariate2-1添加了保存图片的功能
会保存在代码路径的'./Output/'路径下, 文件名和excel文件相同
Bivariate2接口的参数`save_png`bool参数控制是否输出图片
图片格式做了变换

2024年4月18日添加R2 Chi2计算
'''

# 处理无穷情况的值取float64最大值的近似值
INF_value = 1.797e+308 # 1.7976931348623157e+308

# 定义我们的模型
@np.errstate(invalid="raise", over="raise")
def model_all_in_one(
    radioligands: np.ndarray, T_array: np.ndarray, Bmax_value: float, kon_log: float, koff_log: float, Time0: float):
    
    Y_pred = np.zeros(T_array.shape) # 生成Y_pred
    
    try:
        
        # 对数转化为本来的值
        kon = np.power(10,kon_log)
        koff = np.power(10,koff_log)
        
        # 正式的模型计算
        Kob=np.longdouble(radioligands*kon+koff)
        Kd=np.longdouble(koff/kon)
        Eq=np.longdouble(Bmax_value*radioligands/(radioligands + Kd))
        YatTime0 =np.longdouble(Eq*(1-np.exp(-1*Kob*Time0)))
        
        # 判断时间段
        T_flag_diss = np.float32(T_array>Time0) # 解离
        T_flag_ass = np.float32(T_array<=Time0) # 结合
        
        # 最终大模型
        Y_pred = YatTime0 * np.exp(-1 * koff * (T_array - Time0)) * T_flag_diss + Eq * (1-np.exp(-1*Kob*T_array)) * T_flag_ass
        
    except FloatingPointError as e:  # 如果有警告发生
        
        Y_pred = np.ones_like(T_array) * INF_value  # 如果有溢出，可以将Y设置为INF_value
        
    return Y_pred # 不含时间

# 损失函数
# A_data是浓度数据, 应该是一个向量而不是单个值
# T_data是时间数据
# Y_data是信号数据
# T_break是结合解离的分割时间
@np.errstate(invalid="raise", over="raise")
def loss_all_in_one(
    params, A_data: np.ndarray, T_data: np.ndarray, Y_data: np.ndarray, T_break: float):
    
    R_max, ka, kd = params
    Y_predictions = model_all_in_one(A_data,T_data,R_max,ka,kd,T_break)
    residuals = Y_predictions - Y_data
    
    # 计算总残差平方和
    try:
        Loss = np.sum(np.square(residuals))
        
    except FloatingPointError as e:  # 如果有警告发生
        
        Loss = INF_value  # 如果有溢出，可以将Y设置为无穷大或合适的值
            
    return Loss

# 从file_path转换为Data数组
def Get_Data_from_path(file_path):
    dataframe = pd.read_excel(file_path)
    # data_array = dataframe.to_numpy()
    return dataframe

# 把Data分割成不同的部分
def split_data(Dataframe: pd.DataFrame):
    Data = Dataframe.to_numpy()
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
    Data: np.ndarray, time0: float = -1, init_params: list = [1.5,4,-4], options: dict={'eps': 1e-3}):
    
    Y_data, A_data, T_data, R_guess = split_data(Data)
    initial_guess = [R_guess*init_params[0], init_params[1], init_params[2]]
    result = minimize(loss_all_in_one, initial_guess, args=(A_data, T_data, Y_data, time0), 
                  method='BFGS',options=options)
    
    R_opt, ka_opt_log, kd_opt_log = result.x
    ka_opt, kd_opt = np.power(10,(ka_opt_log, kd_opt_log))
    Loss = loss_all_in_one(result.x,A_data,T_data,Y_data,time0)
    
    Results = {"Rmax":R_opt,
               "kon":ka_opt,
               "koff":kd_opt,
               "KD":kd_opt/ka_opt,
               "Loss":Loss,
               "InitRmax":initial_guess[0],
               "Initkon":initial_guess[1],
               "Initkoff":initial_guess[2]}
    return Results

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
                    target_dir: str):
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
    
    # 确保输出目录存在
    output_dir = Path(target_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取文件路径（假设file_path是一个字符串）
    file_path = Path(file_path)

    # 获取文件名并生成输出路径
    batch_name = file_path.stem  # 获取文件名（不包括扩展名）
    
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
             f"$k_a$:{res['kon'][0]:.4e}, $k_d$:{res['koff'][0]:.4e}, "
             f"$k_D$:{res['KD'][0]:.4e}, $R_{{max}}$:{res['Rmax'][0]:.2f}, "
             f"$R^2$:{res['R2'][0]:.4f}",
             fontsize=10,
             color='gray')
    # 确定Global还是local
    if res['Conc'] == ['Local']:
        plt.title(batch_name+"(LBiv11)",fontsize=14)
        output_path = output_dir / f'LBiv11-{batch_name}.png'
    else:
        plt.title(batch_name+"(GBiv11)",fontsize=14)
        output_path = output_dir / f'GBiv11-{batch_name}.png'
    plt.savefig(output_path)
    
    return output_path

# 全局拟合文件输出接口
def excel_output_global(file_path,
                        time0: float,
                        results:dict,
                        Y_pred: np.ndarray,
                        target_dir: str):
    
    Y_data, A_data, T_data, R_guess = split_data(Get_Data_from_path(file_path))
    
    # 创建Opt_df
    Opt_df = pd.DataFrame(results)
    Opt_df = pd.concat([Opt_df["Conc"], Opt_df.drop(columns="Conc")],axis=1)
    
    # 根据Y_pred创建DataFrame
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
    result_path = output_dir / f'Biv2-{batch_name}.xlsx'
    with pd.ExcelWriter(result_path) as writer:
        Opt_df.to_excel(writer, sheet_name='拟合结果', index=False)
        Y_pred_df.to_excel(writer, sheet_name='拟合曲线', index=False)
    
    return result_path

# 全局拟合最终接口
def GlobalBivariate2(
    file_path, 
    time0: float = -1, 
    options: dict={'eps': 1e-3}, 
    write_file: bool=True, 
    save_img: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    Data = Get_Data_from_path(file_path)
    results1 = Bivariate_init(Data, time0, [1.5,4,-4], options)
    results2 = Bivariate_init(Data, time0, [1.5,6,-2], options)
    
    if results1["Loss"] > results2["Loss"]: #取最小的那个拟合
        Results = results2
    else:
        Results = results1
    
    # 填充浓度项
    Results["Conc"] = 'Global'
    
    # 转换值为list以保证输出一致
    Results = {key: [value] for key, value in Results.items()}
    
    Y_data, A_data, T_data, R_guess = split_data(Get_Data_from_path(file_path))
    y_predictions = model_all_in_one(A_data, T_data, Results["Rmax"],
                              np.log10(Results["kon"]), np.log10(Results["koff"]), 
                              time0)
    
    # 计算R2
    TSS = np.sum((Y_data - np.mean(Y_data))**2.0)
    R2 = 1.0 - Results['Loss'][0]/TSS
    Results["R2"] = [R2]
    
    # 计算Chi2
    Results["Chi2"] = [Results['Loss'][0]/(Y_data.size - 3)]
    
    r_path = y_predictions
    if write_file: # 如果写入文件那么返回的是文件路径
        r_path = excel_output_global(file_path, 
                                     time0=time0,
                                     results=Results, 
                                     Y_pred=y_predictions,
                                     target_dir=excel_path)
        
    if save_img: # 如果需要画图
        i_path = save_output_img(file_path,
                                 T_data=T_data,
                                 Y_data=Y_data,
                                 Y_pred=y_predictions,
                                 Concs=A_data,
                                 res=Results,
                                 target_dir=png_path)
    else:
        i_path = ''
    
    return Results, r_path, i_path # 如果不写入路径那么在Results之后返回Y的预测值

# Local拟合文件输出接口
def excel_output_local(file_path, time0: float, results:dict, Y_pred: np.ndarray, target_dir: str):
    
    Y_data, A_data, T_data, R_guess = split_data(Get_Data_from_path(file_path))
    
    # 创建Opt_df
    Opt_df = pd.DataFrame(results)
    Opt_df = pd.concat([Opt_df["Conc"], Opt_df.drop(columns="Conc")],axis=1)
    
    # 根据Y_pred创建DataFrame
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
    result_path = output_dir / f'Biv2-{batch_name}.xlsx'
    with pd.ExcelWriter(result_path) as writer:
        Opt_df.to_excel(writer, sheet_name='拟合结果', index=False)
        Y_pred_df.to_excel(writer, sheet_name='拟合曲线', index=False)
    
    return result_path

# 这个是用来给LocalBivariate调用的代码 把GlobalBivariate2的第一个输入从file_path变成了np_ndarray
def bivariate2_for_local(
    Data: np.ndarray, time0: float = -1, options: dict={'eps': 1e-3}):
    results1 = Bivariate_init(pd.DataFrame(Data), time0, [1.5,4,-4], options)
    results2 = Bivariate_init(pd.DataFrame(Data), time0, [1.5,6,-2], options)
    
    if results1["Loss"] > results2["Loss"]: #取最小的那个拟合
        Results = results2
    else:
        Results = results1
    
    Y_data, A_data, T_data, R_guess = split_data(Data)
    Y_pred = model_all_in_one(A_data, T_data, Results["Rmax"],
                              np.log10(Results["kon"]), np.log10(Results["koff"]), 
                              time0)
    
    # 计算R2
    TSS = np.sum((Y_data - np.mean(Y_data))**2.0)
    R2 = 1 - Results["Loss"]/TSS
    Results["R2"] = R2
    
    # 计算Chi2
    Results["Chi2"] = Results["Loss"]/(Y_data.size - 3)

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
def LocalBivariate2(
    file_path,
    time0: float = -1,
    options: dict={'eps': 1e-3}, 
    write_file: bool=True,
    save_img: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    Data = Get_Data_from_path(file_path)
    
    # 拆分为不同的浓度组
    local_datas = local_data_generator(Data)
    
    current_results_list = []
    y_predictions_list = []
    
    # 遍历每一个单独的浓度组
    num_params = 0
    for local_data in local_datas:
        num_params += 3.0
        current_results, y_prediction = bivariate2_for_local(local_data,time0,options)
        current_results["Conc"] = np.array(local_data.columns)[1]
        current_results_list.append(current_results)
        y_predictions_list.append(np.squeeze(y_prediction))
        
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
    Y_data, _A_data, _T_data, _R_guess = split_data(Data)
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
                     "Conc":'Local',
                     "InitRmax":'',
                     "Initkon":'',
                     "Initkoff":''} # 确保格式一致
    
    # 合并输出Results
    current_results_list.append(total_results)
    
    # 合并字典为Results，每个键对应一个向量
    Results = {key: [d[key] for d in current_results_list] for key in current_results_list[0]}
    
    if write_file: # 如果写入文件那么返回的是文件路径
        r_path = excel_output_local(file_path,
                                    time0=time0, 
                                    results=Results,
                                    Y_pred=y_predictions,
                                    target_dir=excel_path)
        
    if save_img:
        Y_data, A_data, T_data, R_guess = split_data(Get_Data_from_path(file_path))
        total_results = {key: [total_results[key]] for key in total_results}
        i_path = save_output_img(file_path, T_data=T_data, Y_data=Y_data,
                                 Y_pred=y_predictions,Concs=A_data,res=total_results,target_dir=png_path)
    else:
        i_path = ''
    
    return Results , r_path , i_path # 如果不写入路径那么在Results之后返回Y的预测值

# 汇总接口Bivariate2
def Bivariate2(
    file_path,
    time0: float=-1,
    options: dict={'eps': 1e-3}, 
    write_file: bool=True,
    run_local: bool= False,
    save_png: bool=False,
    excel_path: str='Result',
    png_path: str='Output'):
    
    if run_local: # 如果选择以local的形式拟合
        return LocalBivariate2(file_path,
                               time0,
                               options,
                               write_file,
                               save_png,
                               excel_path,
                               png_path)
    else: # 否则就按照全局的形式拟合
        return GlobalBivariate2(file_path,
                                time0,
                                options,
                                write_file,
                                save_png,
                                excel_path,
                                png_path)

print("成功调入")
if __name__ == "__main__":
    file_path = "SourceData/240523-黄某辉2号蛋白-112st0.xlsx" # 输入文件路径
    r,p,i = Bivariate2(file_path,time0=113.0,write_file=False,run_local=False,save_png=True) # 全局拟合
    print(r)