import json
from datetime import datetime

REQUIRED_KEYS = ["CalculateDataSource", "CalculateDataType", "CalculateFormula", "FittingOptions", "CalculateDataList"]
FITTING_OPTIONS_KEYS = ["KDBound", "PunishUpper", "PunishLower", "PunishK"]
REQUIRED_ITEM_KEYS = ["ExperimentID", "SampleID", "Molecular", "SampleName", "Concentration", "ConcentrationUnit", "HoleType", "BaseData", "CombineData", "DissociationData"]
HOLE_TYPE = [0,1,2,3]
DATA_KEYS = ["BaseData", "CombineData", "DissociationData"]
DATA_DOT_KEYS = ["ID", "Time", "XValue", "YValue"]

def check_unpredicted_json_format(json_path):
    try:
        # 读取 JSON 文件
        with open(json_path, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
        
        # 检查顶层结构
        required_keys = REQUIRED_KEYS
        if not all(key in data for key in required_keys):
            print("缺乏顶层键之一")
            return False
        
        # 检查 FittingOptions
        fitting_options_keys = FITTING_OPTIONS_KEYS
        if not all(key in data["FittingOptions"] for key in fitting_options_keys):
            print("FittingOptions内缺少一个键")
            return False
        
        # 检查 CalculateDataList
        for item in data["CalculateDataList"]:
            # 检查必要字段
            required_item_keys = REQUIRED_ITEM_KEYS
            if not all(key in item for key in required_item_keys):
                print("CalculateData内缺少一个键")
                return False
            
            # 检查 HoleType
            if item["HoleType"] is not None and item["HoleType"] not in HOLE_TYPE:
                print("HoleType不对")
                return False
            
            # 检查数据列表
            for data_list in DATA_KEYS:
                if not isinstance(item[data_list], list):
                    print("数据点list不对")
                    return False
                for data_point in item[data_list]:
                    if not all(key in data_point for key in DATA_DOT_KEYS):
                        print("数据点内容不对")
                        return False
                    # 检查 Time 格式
                    if data_point["Time"] is not None:
                        try:
                            datetime.fromisoformat(data_point["Time"])
                        except ValueError:
                            print("时间不对")
                            return False
        
        return True
    
    except json.JSONDecodeError:
        return False
    except IOError:
        print("IO错误")
        return False


