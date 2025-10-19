from FileProcess.JsonFormat import check_unpredicted_json_format
from FileProcess.Json2Data import read_and_process_json, get_fitting_options

path = "/Users/chenmingqian/Code/KineticsFitting/SourceData/One&100多循环v4.json"
print(check_unpredicted_json_format(path))
fitting_options, df, time0 = read_and_process_json(path)

print("FittingOptions:")
print(get_fitting_options(fitting_options))
print("\nDataFrame:")
print(df)
print("\nCombineEndTime:")
print(time0)