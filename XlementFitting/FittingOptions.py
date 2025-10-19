import numpy as np
import pandas as pd
from pathlib import Path
import warnings
'''
用来给Bivariate系列函数提供设置的类
'''
__all__ = ['FittingOptions']

# 自定义警告类
class FittingOptionsWarning(UserWarning):
    pass

class FittingOptions:
    def __init__(self,
        dict_options: dict = {'init_params':[1.5,3,-1],
                              'eps': 1e-6}):
        # 设置拟合起始点
        init_params = dict_options.pop('init_params', None)
        if init_params is not None and self.is_valid_init_params_list(init_params): 
            self.init_params_list = self._convert2_valid_init_params_list(init_params)
        else:
            self.init_params_list = [
                [1.5,6,-2],
                [1.5,4,-4],
                [150,4,-2],
                [1500,4,0]
            ]
            
        # 设置学习率
        eps = dict_options.pop('eps', None)
        if eps is not float:
            self.eps = 1e-6
        elif eps > 0.1:
            self.eps = 1e-6
            warnings.warn(f"eps不能设置过大,请通过set_eps接口设置,已经设置为{self.eps:.4e}",FittingOptionsWarning)
        else:
            self.eps = eps
            
        # 最小KD边界
        self.KD_bound = -12
        
        # 设置惩罚上界
        self.punish_upper = 40
        
        # 设置惩罚下届
        self.punish_lower = -20
        
        # 设置惩罚强度
        self.punish_k = 1.0
        
        # 设置惩罚率
        self.punish_lam = 1.0
        
        # 设置单循环找点的高度限制
        self.peak_height = 0.02
        pass
    
    def is_valid_init_params_list(self,lst):
        # 判断是否不是长度为3的list
        if not isinstance(lst, list):
            return False
        
        if len(lst) != 3:
            # 判断每个元素是否也是长度为3的list
            for elem in lst:
                if not isinstance(elem, list) or len(elem) != 3:
                    return False   
        
        return True
    
    # 把一个单元list包起来
    def _convert2_valid_init_params_list(self,lst):
        # 判断是否是长度为3的list
        if len(lst) != 3: # 如果长度不为3那必然不需要转换
            return lst
        
        for elem in lst:
            if not isinstance(elem, float) and not isinstance(elem, int): # 存在一个非float|int类型元素
                return lst # 不需要转换
            
        return [lst]
    
    # Check Punish的上下界是否保证顺序
    def _is_punish_upper_bigger_lower(self, exchange: bool = False):
        if self.punish_lower >= self.punish_upper:
            warnings.warn(f"惩罚项下界应当小于上界",FittingOptionsWarning)
            if exchange:
                term = self.punish_upper
                self.punish_upper = self.punish_lower
                self.punish_lower = term
            return False
        
        if self.punish_lower > -12:
            warnings.warn(f"惩罚项下界{self.punish_lower:.4e}可能太大",FittingOptionsWarning)
            
        if self.punish_upper < 0:
            warnings.warn(f"惩罚项上界{self.punish_lower:.4e}可能太小",FittingOptionsWarning)
            
        return True
    
    # 覆盖原有的所有拟合起始点
    def set_init_params(self,init_params: list = None):
        if not isinstance(init_params,list) or not self.is_valid_init_params_list(init_params): # 如果输入不合法就还原为基本设置
            self.init_params_list = [
                [1.5,4,-4],
                [1.5,6,-2],
                [1.5,4,0]
            ]
            print("已经重置拟合起始点")

        if self.is_valid_init_params_list(init_params): # 如果输入了一个合法的拟合起始点
            self.init_params_list = self._convert2_valid_init_params_list(init_params)
            
    
    # 添加一个拟合起始点
    def add_init_params(self,new_init_params):
        if self.is_valid_init_params_list(new_init_params):
            self.init_params_list += self._convert2_valid_init_params_list(new_init_params)
    
    # 设置新的学习率
    def set_eps(self,new_eps: float = None):
        if not isinstance(new_eps, float):
            self.eps = 1e-6
        else:
            self.eps = new_eps
        
        if new_eps > 0.1:
            warnings.warn(f"eps设置成功,但是{new_eps:.4e}太大了",FittingOptionsWarning)
    
    # 设置最小KD边界
    def set_KD_bound(self,new_KD_bound: float = None):
        if not isinstance(new_KD_bound,float) and not isinstance(new_KD_bound,int):
            self.KD_bound = -12.0
        else:
            self.KD_bound = float(new_KD_bound)
        
        if new_KD_bound > -10.0:
            warnings.warn(f"新的亲和力下限{new_KD_bound:.2f}可能太大")
            
    
    # 设置惩罚上界
    def set_punish_upper(self,new_punish_upper: float = None):
        if not isinstance(new_punish_upper,float) and not isinstance(new_punish_upper,int):
            self.punish_upper = 40
        else:
            self.punish_upper = float(new_punish_upper)
        return self._is_punish_upper_bigger_lower(exchange=True)
    
    # 设置惩罚下届
    def set_punish_lower(self,new_punish_lower: float = None):
        if not isinstance(new_punish_lower,float) and not isinstance(new_punish_lower,int):
            self.punish_lower = -20
        else:
            self.punish_lower = float(new_punish_lower)
        return self._is_punish_upper_bigger_lower(exchange=True)
    
    # 设置惩罚强度
    def set_punish_k(self,new_punish_k: float = None):
        if not isinstance(new_punish_k, float):
            self.punish_k = 1.0
        elif new_punish_k < 0.0:
            self.punish_k = new_punish_k
            warnings.warn(f"惩罚强度{new_punish_k:.2f}小于0, 这是不合适的")
        else:
            self.punish_k = new_punish_k
    
    # 设置惩罚率
    def set_punish_lam(self,new_punish_lam: float = None):
        if not isinstance(new_punish_lam, float):
            self.punish_lam = 1.0
        elif new_punish_lam < 0.0:
            self.punish_lam = new_punish_lam
            warnings.warn(f"惩罚率{new_punish_lam:.2f}小于0, 这是不合适的")
        else:
            self.punish_lam = new_punish_lam
            
    # 设置高度
    def set_peak_height(self, new_peak_height: float = None):
        if not isinstance(new_peak_height, float) and not isinstance(new_peak_height, int):
            self.peak_height = 0.02 # 重置
        
        if new_peak_height > 0.1 or new_peak_height< 0.0:
            self.peak_height = float(new_peak_height)
            warnings.warn(f"高度阈值{new_peak_height:.2f}不合适的")
        self.peak_height = float(new_peak_height)
            
    # 获取init_params
    def get_init_params_list(self):
        return self.init_params_list
    
    def get_eps(self):
        return self.eps
    
    def get_punish_lower(self):
        return self.punish_lower
    
    def get_punish_upper(self):
        return self.punish_upper
    
    def get_punish_k(self):
        return self.punish_k
    
    def get_KD_bound(self):
        return int(self.KD_bound)
    
    def get_punish_lam(self):
        return self.punish_lam
    
    def get_peak_height(self):
        return self.peak_height
            
    # 设置Print函数
    def __str__(self):
        return (f"起始点:{self.init_params_list}\n精确度:{self.eps:.4e}\n惩罚区:[{self.punish_lower},{self.punish_upper}]\n"
               f"惩罚强度:{self.punish_k}\nKD限:{self.KD_bound}\n惩罚率:{self.punish_lam}")
        
if __name__ == "__main__":
    test_fo = FittingOptions()
    print(test_fo.is_valid_init_params_list([
        [1.5,6,-2],
        [15,4,-4],
        [150,3,-2],
        [1500,4,0]
    ]))
    test_fo.set_init_params([
        [1.5,6,-2],
        [15,4,-4],
        [150,3,-2],
        [1500,4,0]
    ])
    test_fo.set_punish_lower(-11.0)
    test_fo.set_punish_upper(-14)
    print(test_fo)