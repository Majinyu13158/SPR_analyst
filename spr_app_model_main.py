'''
这个文件是作为MVC架构的负责业务的model文件，主要负责各种数据类的定义与进行处理的函数的定义
本文件中的函数应当被GUI文件调用，但不应当调用GUI文件，防止循环引用
本文件应当调用controller文件，以使用controller文件中的函数
'''
import json_reader
import os
import sys
import spr_gui_main
from model_data_process.LocalBivariate import model_runner


#project思维是合理的吗？
#project思维的实现必须配合完善的数据结构的构思！
#啊，对了，我要导出一个自己的特有的文件后缀，这样读取的话就会保留各种特性




#定义project类，用于储存项目数据。project由用户自行关联组建，对应于prism的系列
#在project类中储存的有：
#1.所处理文件的信息，如文件名，文件路径，文件包含的数据，对应file_info_custom类
#2.拟合设置，如拟合的类型，拟合的参数，对应fitting_setting类
#3.结果，对应Result类
#

'''
{
    "CalculateDataSource": 1,
    "CalculateDataType": 1,
    "CalculateFormula": 102,
    "FittingOptions": {
      "KDBound": -15,
      "PunishUpper": 40,
      "PunishLower": -16,
      "PunishK": 2
    },
    "CalculateDataList": [
      {
        "ExperimentID": 1836307608651304960,
        "SampleID": 1836307608689053696,
        "Molecular": 150000.0,
        "SampleName": "多循环igg",
        "Concentration": 0.0,
        "ConcentrationUnit": "M",
        "HoleType": null,
        "BaseStartIndex": null,
        "CombineStartIndex": 0,
        "CombineEndIndex": 0,
        "DissociationEndIndex": null,
        "BaseData": [
          {
            "ID": 1836307608806494208,
            "Time": null,
            "XValue": 0.0,
            "YValue": 0.0,
            "YPrediction": 0.0
          },
          {
            "ID": 1836307608806494209,
            "Time": null,
            "XValue": 1.0,
            "YValue": -0.43000000000029104,
            "YPrediction": 0.0
          },

'''
class Project():
    def __init__(self):
        self.datas_dict = {}
        self.datas_count = 0
        self.imgs_dict = {}
        self.imgs_count = 0
        self.results_dict = {}
        self.results_count = 0
        self.project_details_dict = {}
        self.project_details_count = 0
    def set_connection(self,item,type_of_item):
        if type_of_item == 'data':
            self.datas_dict[self.datas_count] = item
            self.datas_count += 1
        elif type_of_item == 'img':
            self.imgs_dict[self.imgs_count] = item
            self.imgs_count += 1
        elif type_of_item == 'result':
            self.results_dict[self.results_count] = item
            self.results_count +=1
        elif type_of_item == 'project_details':
            self.project_details_dict[self.project_details_count] = item
            self.project_details_count +=1


'''
定义data类
在data类中储存的有：
未经历处理的原始数据，这种是直接读取json得来的，会把attributes里的各种数据都赋值
另一种是拟合得到的数据，这种的attributes都是空的，只有processed_data里面放数据
用户对原始数据编辑之后生成的所实际使用的数据
导入文件方式时对应的文件地址
'''
class Data():
    def __init__(self,item,itemtype):
        self.connectionid = None
        self.attributes = {
            'cauculatedatasource': None,
            'calculatedatatype': None,
            'fittingformula': None,
            'fittingoptions_kdbound': None,
            'fittingoptions_punishupper': None,
            'fittingoptions_punishlower': None,
            'fittingoptions_punishk': None,
            'calculatedatalist_experimentid': None,
            'calculatedatalist_sampleid': None,
            'calculatedatalist_molecular': None,
            'calculatedatalist_samplename': None,
            'calculatedatalist_concentration': None,
            'calculatedatalist_concentrationunit': None,
            'calculatedatalist_holetype': None,
            'basestaryindex': None,
            'calculatedatalist_combinestartindex': None,
            'calculatedatalist_combineendindex': None,
            'calculatedatalist_dissociationendindex': None,
            'ligandfixationdata': None,
            'ligandstabilitydata': None,
        }
        self.basedata={}
        self.processed_data = {}
        #诶，我应该这么写吗？还是放在一个字典里？
        if itemtype == 'file':
            self.data = item
            self.basedata = self.data['CalculateDataList'][0]['BaseData']
            self.attributes['cauculatedatasource'] = self.data['CalculateDataSource']
            self.attributes['calculatedatatype'] = self.data['CalculateDataType']
            self.attributes['fittingformula'] = self.data['CalculateFormula']
            self.attributes['fittingoptions_kdbound'] = self.data['FittingOptions_KDBound']
            self.attributes['fittingoptions_punishupper'] = self.data['FittingOptions_PunishUpper']
            self.attributes['fittingoptions_punishlower'] = self.data['FittingOptions_PunishLower']
            self.attributes['fittingoptions_punishk'] = self.data['FittingOptions_PunishK']
            self.attributes['calculatedatalist_experimentid'] = self.data['CalculateDataList'][0]['ExperimentID']
            self.attributes['calculatedatalist_sampleid'] = self.data['CalculateDataList'][0]['SampleID']
            self.attributes['calculatedatalist_molecular'] = self.data['CalculateDataList'][0]['Molecular']
            self.attributes['calculatedatalist_samplename'] = self.data['CalculateDataList'][0]['SampleName']
            self.attributes['calculatedatalist_concentration'] = self.data['CalculateDataList'][0]['Concentration']
            self.attributes['calculatedatalist_concentrationunit'] = self.data['CalculateDataList'][0]['ConcentrationUnit']
            self.attributes['calculatedatalist_holetype'] = self.data['CalculateDataList'][0]['HoleType']
            self.attributes['basestaryindex'] = self.data['CalculateDataList'][0]['BaseStartIndex']
            self.attributes['calculatedatalist_combinestartindex'] = self.data['CalculateDataList'][0]['CombineStartIndex']
            self.attributes['calculatedatalist_combineendindex'] = self.data['CalculateDataList'][0]['CombineEndIndex']
            self.attributes['calculatedatalist_dissociationendindex'] = self.data['CalculateDataList'][0]['DissociationEndIndex']
            self.attributes['ligandfixationdata'] = self.data['CalculateDataList'][-2]['LigandFixationData']
            self.attributes['ligandstabilitydata'] = self.data['CalculateDataList'][-1]['LigandStabilityData']

        elif itemtype == 'fitting':
            self.data = item
            self.processed_data = self.data
        else:
            self.data = None
            self.file_path = None
    def get_processed_data(self):
#这个地方得是gui那边写一个读取table用的函数，然后这里调用
        pass



#定义result类，对应于一个拟合
#在result类中储存的有：
#1. 处理得到的拟合过程的数据，对应process_data类
#2. 动力学拟合数据如kakd，对应fitting_result类
class Result():
    def __init__(self, name,fitsetings,data):
        #self.toolbar = NavigationToolbar(self.MplCanvas, parent)
        self.name = name
        self.fitting_setting = Fitting_setting(fitsetings)
        self.kinetic_result,self.processed_data = model_runner(self.fitting_setting,data)
#要把model_runner重写为一个适配于这里的函数
'''
看来要写出model_runner返回两个值，一个是拟合结果，一个是处理后的数据，分别生成两个类
'''


#定义fitting_setting类，用于储存拟合设置
#在fitting_setting类中储存的有：
#1.拟合方法
#2.拟合参数
class Fitting_setting():
    def __init__(self, fitting_type, fitting_parameter):
        self.fitting_type = fitting_type
        self.fitting_parameter = fitting_parameter

'''
定义Figure类，用于对应图片
在Figure类中储存的有：
1.图片的png？或者别的格式
2.绘图的设置
'''
class Figure():
    def __init__(self, figure,name,figure_settings):
        #self.toolbar = NavigationToolbar(self.MplCanvas, parent)
        self.name = name

    def tab_change(self):
#这个函数是用来调用gui里的tab在调整了setting之后进行更新绘图
        pass

'''
定义figure_settings类，用于储存绘图设置
在figure_settings类中储存的有：
1.
2.
'''
class Figure_settings():
    def __init__(self, parent, name):
        self.name = name
        self.settings = {}


'''
定义一个project_details类，用于储存项目的详细信息
在project_details类中储存的有：
1.项目的名字
2.项目的创建时间
3，项目的内容
4.项目的创建者
5.项目的标签
6.项目的描述
'''
class Project_details():
    def __init__(self, item):
        self.details = item

class Model():
    def __init__(self):

        self.datas = {}
        self.figures = {}
        self.results = {}
        self.project_details = {}
        self.projects = {}

        self.datas_counter = 0
        self.figures_counter = 0
        self.results_counter = 0
        self.project_details_counter = 0
        self.projects_counter = 0

        self.connection = {}
        '''
        我准备用字典与connection_id两个方法来实现，我还没有想好？
        connection_id可以横跨三个文件，但是字典只能在一个文件中
        '''

    def add_new_data(self, data, itemtype):
        self.thedata = Data(data, itemtype)
        self.datas[self.datas_counter] = self.thedata
        self.datas_counter += 1
        print(self.thedata.attributes['cauculatedatasource'])

    def add_new_figure(self, data, itemtype, figure_settings):
        self.thefigure = Figure(data, itemtype, figure_settings)
        self.figures[self.figures_counter] = self.thefigure
        self.figures_counter += 1

    def add_new_project_details(self, data, itemtype):
        self.theproject_details = Project_details(data)
        self.project_details[self.project_details_counter] = self.theproject_details
        self.project_details_counter += 1

    def add_new_result(self, data, itemtype):
        self.theresult = Result(data, itemtype)
        self.results[self.results_counter] = self.theresult
        self.results_counter += 1

    def set_connection(self, item1, item2):
        pass
#体现交互逻辑可以做到吗？我点击修改拟合设置，然后发送信号给controller，controller调用model中的函数，修改拟合设置，重新拟合，然后返回新的结果，在之后调用gui上的函数重新绘图
