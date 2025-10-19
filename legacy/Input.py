from XlementFitting.FileProcess.JsonFormat import check_unpredicted_json_format
from XlementFitting.FileProcess.Json2Data import read_and_process_json, get_fitting_options
from XlementFitting.FileProcess.Data2Json import process_and_save_json
from XlementFitting import PartialBivariate, GlobalBivariate, LocalBivariate
from pathlib import Path
import argparse
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
        return

    fitting_options, df, time0, f = read_and_process_json(path)
    # print(f"df:{df}")
    origin_df = df.copy()
    if f == 103:
        r,p,i = PartialBivariate(
            data_frame=df,
            time0=time0,
            options=get_fitting_options(fitting_options),
            write_file=False,
            excel_path='FittingResultFile'
        )
        f_type = 'Partial'
    elif f == 101:
        r,p,i = LocalBivariate(
            data_frame=df,
            time0=time0,
            options=get_fitting_options(fitting_options),
            write_file=False,
            excel_path='FittingResultFile'
        )
        f_type = 'Local'
    elif f == 102:
        r,p,i = GlobalBivariate(
            data_frame=df,
            time0=time0,
            options=get_fitting_options(fitting_options),
            write_file=False,
            excel_path='FittingResultFile'
        )
        f_type = 'Global'

    # 获取 DataFrame 的行数和列数
    rows, cols = origin_df.shape

    # 获取要插入的数据的行数和列数
    new_rows, new_cols = p.shape
    # 确保新数据不会超出 DataFrame 的边界
    if new_rows > rows - 1 or new_cols > cols - 1:
        raise ValueError("新数据的大小超出了 DataFrame 的可用空间")

    # 将新数据插入到 DataFrame 中，从第二列第二行开始
    origin_df.iloc[1:1+new_rows, 1:1+new_cols] = p

    process_and_save_json(
        json_file_path=path,
        df=origin_df,
        output_json_path=new_path,
        fitting_result = r
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a file with a given path.")
    parser.add_argument("file_path", help="Path to the file to be processed")
    
    args = parser.parse_args()
    
    xlement_fitting_json_input(args.file_path)