import os
import re
import numpy as np
import pandas as pd
import zipfile
import warnings
import json
from ..FittingOptions import FittingOptions

__all__ = ['XlementDataFrame']

class XlementDataFrame:
    def __init__(self, init_options: dict):
        # init_options是options.json的第一个节点, 应该另外传入
        self._validate_init_options(init_options)

        self._device = init_options['device']
        self._dtype = init_options['dtype']
        self._unit = init_options['unit']
        self._molecular_mass = init_options['molecular_mass']
        self._hole_info = init_options['hole_info'] if self._device == '100' or self._device == '100-capture' else None


        file_path = init_options['file_path']
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        data = self._format_data(file_path)
        
        self._hole_names = data['hole_names'] if self._device == '100' or self._device == '100-capture' else None
        self._concentrations = data['concentrations']
        self._concentrations_M = self._convert_concentration_to_Mole(self._concentrations, self._unit, self._molecular_mass)
        self._raw_baseline_signals = data['baseline_signals']
        self._raw_association_signals = data['association_signals']
        self._raw_dissociation_signals = data['dissociation_signals']

        self._dissociation_time_start = None # 获得解离开始时间


    def _format_data(self, file_path):

        data = None

        if self._device == 'one' and self._dtype == 'excel':
            data = self._format_one_excel(file_path)
        elif self._device == 'one' and self._dtype == 'zip':
            data = self._format_one_zipped(file_path)
        elif self._device == '100' or self._device == '100-capture':
            data = self._format_100(file_path)
        elif self._dtype == 'json':
            data = self._format_json(file_path)
        else:
            raise ValueError(f"Unsupported device and data type combination: {self._device}, {self._dtype}")
        
        return data
    
    def _format_json(self, file_path)->dict:
        with open(file_path, 'r', encoding='utf-8-sig') as json_file:
            json_data = json_file.read()
        original_data = json.loads(json_data)
        
        # 创建 FittingOptions 实例
        fitting_options = FittingOptions()
        
        # 从 JSON 中提取 FittingOptions 相关数据并设置
        if 'FittingOptions' in original_data:
            fo = original_data['FittingOptions']
            if 'KDBound' in fo:
                fitting_options.set_KD_bound(fo['KDBound'])
            if 'PunishUpper' in fo:
                fitting_options.set_punish_upper(fo['PunishUpper'])
            if 'PunishLower' in fo:
                fitting_options.set_punish_lower(fo['PunishLower'])
            if 'PunishK' in fo:
                fitting_options.set_punish_k(fo['PunishK'])
        
        # 处理 CalculateDataList
        calculate_data_list = original_data.get('CalculateDataList', [])
        
        # 创建一个字典来存储每个样品的数据
        sample_data = {}
        signals = []
        concentration_molar = []
        time_split = []
        
        for sample in calculate_data_list:
            sample_id = sample['SampleID']
            original_data = sample['OriginalDataList']
            
            # 排序 OriginalDataList 按 ID
            sorted_data = sorted(original_data, key=lambda x: x['ID'])
            
            # 提取 Value 并存储
            sample_data[sample_id] = [item['Value'] for item in sorted_data]
            signals.append(sample_data[sample_id])
            
            # 计算 ConcentrationMolar（这里需要您提供具体的计算方法）
            concentration_molar.append(['Concentration'] * 0.001 / sample['Molecular'])  # 这里需要根据实际情况进行转换
            
            # 记录时间分割点, 把每个基线开始时间, 结合开始时间, 结合结束时间以及解离开始时间记录下来
            # 最后一个覆盖之前的, 考虑新json这些都对齐了
            time_split = [
                sample['BaseStartIndex'],
                sample['CombineStartIndex'],
                sample['CombineEndIndex'],
                sample['DissociationEndIndex']
                ]
        #split signals
        baseline_start, association_start, association_finish, dissociation_finish = time_split

        baseline_signals = signals[baseline_start:association_start, :]
        association_signals = signals[association_start:association_finish, :]
        dissociation_signals = signals[association_finish:dissociation_finish, :]
        
        result = {

            'concentrations': concentration_molar,

            'time_split': time_split,
            'baseline_start': baseline_start,
            'association_start': association_start,
            'association_finish': association_finish,
            'dissociation_finish': dissociation_finish,

            'baseline_signals': baseline_signals,
            'association_signals': association_signals,
            'dissociation_signals': dissociation_signals
        }

        return result


    def _format_one_excel(self, file_path)->dict:

        original_data = pd.read_excel(file_path)

        conc_df = original_data[original_data.iloc[:, 0] == 'Sample concentration(M)']
        conc_df = conc_df.dropna(axis=1, inplace=False)
        conc_list = conc_df.iloc[0, :].tolist()

        # unit = conc_list[1].split(' ')[-1]
        concentrations = []

        for conc in conc_list:
            if conc is None or conc == 'Sample concentration(M)': continue
            concentrations.append(conc)
        
        time_split = []
        HEADERAS = ['Base line(s)', 'Association start(s)', 'Association finish(s)', 'Dissociation finish(s)']

        for header in HEADERAS:
            _ = original_data[original_data.iloc[:, 0] == header].index[0]
            time_split.append(original_data.iloc[_, 1])
        
        signal_index = original_data[original_data.iloc[:, 0] == 'Time'].index[0]
        signal_df = original_data.iloc[signal_index:, :]

        signals = np.array([])
        for i in range(len(concentrations)):
            assert signal_df.iloc[0, 3*i + 1] == 'Test'
            assert signal_df.iloc[0, 3*i + 2] == 'Refe'

            signal_refe = signal_df.iloc[1:, 3*i + 1].to_numpy().astype(np.float64)
            signal_test = signal_df.iloc[1:, 3*i + 2].to_numpy().astype(np.float64)
            signal = signal_refe - signal_test
            signal = signal.reshape(-1, 1)

            # signals = np.concatenate([signals, signal], axis=1) if signals.size else signal
            signals = np.hstack([signals, signal]) if signals.size else signal
        
        #split signals
        baseline_start, association_start, association_finish, dissociation_finish = time_split

        baseline_signals = signals[baseline_start:association_start, :]
        association_signals = signals[association_start:association_finish, :]
        dissociation_signals = signals[association_finish:dissociation_finish, :]

        result = {

            'concentrations': concentrations,

            'time_split': time_split,
            'baseline_start': baseline_start,
            'association_start': association_start,
            'association_finish': association_finish,
            'dissociation_finish': dissociation_finish,

            'baseline_signals': baseline_signals,
            'association_signals': association_signals,
            'dissociation_signals': dissociation_signals
        }

        return result


    def _format_one_zipped(self, file_path)->dict:

        time_split = []
        signals = np.array([])
        concentrations = []

        with zipfile.ZipFile(file_path, 'r') as zip_dir:
            for zip_file_name in zip_dir.namelist():

                concentrations.append(zip_file_name.split(' ')[1].split('_')[0])
                with zip_dir.open(zip_file_name) as f:
                    signal_df = pd.read_csv(f, delimiter='\t', encoding='utf-8')
                    signal = signal_df['差值'].to_numpy().reshape(-1, 1)
                    signal = signal.astype(np.float64)
                    signals = np.hstack([signals, signal]) if signals.size else signal
                    
                    time_split = signal_df.columns[5:9].tolist() 
        
        time_split = [int(i) for i in time_split]
        association_start, association_finish, dissociation_finish, baseline_start = time_split

        baseline_signals = signals[baseline_start:association_start, :]
        association_signals = signals[association_start:association_finish, :]
        dissociation_signals = signals[association_finish:dissociation_finish, :]

        result = {

        'concentrations': concentrations,

        'time_split': time_split,
        'baseline_start': baseline_start,
        'association_start': association_start,
        'association_finish': association_finish,
        'dissociation_finish': dissociation_finish,

        'baseline_signals': baseline_signals,
        'association_signals': association_signals,
        'dissociation_signals': dissociation_signals
        }

        return result
    

    def _format_100(self, file_path)->dict:

        original_data_dflist = []

        sheet_names = ['基线', '结合', '解离']
        if self._device == '100-capture':
            sheet_names = ['配体稳定', '结合', '解离']

        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            original_data_dflist.append(df)
        
        baseline_df, association_df, dissociation_df = original_data_dflist

        # TODO: filter invalid concentrations and hole name, for example, -1
        # more info needed

        hole_names = []
        hole_concentrations = []

        hole_info = self._hole_info.replace(' ', '').replace('，', ',')
        for _ in hole_info.split(','):
            hole_name, conc = _.split(':')
            if conc.startswith('-'): continue

            hole_names.append(hole_name)
            hole_concentrations.append(conc + self._unit)

        baseline_time, baseline_signals = self._extract_time_and_signals(baseline_df, hole_names)
        association_time, association_signals = self._extract_time_and_signals(association_df, hole_names)
        dissociation_time, dissociation_signals = self._extract_time_and_signals(dissociation_df, hole_names)
        
        result = {

            'hole_names': hole_names,
            'concentrations': hole_concentrations,

            'baseline_time': baseline_time,
            'association_time': association_time,
            'dissociation_time': dissociation_time,

            'baseline_signals': baseline_signals,
            'association_signals': association_signals,
            'dissociation_signals': dissociation_signals
            }

        return result
    
    
    def _process_data_pipeline(self, pipeline: dict):

        concentration_M = self._concentrations_M
        baseline_signals = self._raw_baseline_signals
        association_signals = self._raw_association_signals
        dissociation_signals = self._raw_dissociation_signals

        ASSOCIATION_TRUNCATE = 15

        if self._device == 'one':
            try:
                association_signals = association_signals[ASSOCIATION_TRUNCATE:, :]
            except IndexError:
                warnings.warn(f"Association signals are too short, no truncation applied.\n"
                            f"Expected length: {ASSOCIATION_TRUNCATE}, actual length: {association_signals.shape[0]}")
            
            association_length = association_signals.shape[0]
            dissociation_length = dissociation_signals.shape[0]
            if dissociation_length > 2 * association_length:
                dissociation_signals = dissociation_signals[:2 * association_length, :]

        zero_indice_list = [i for i, c in enumerate(concentration_M) if c == 0]
        zero_index = -1

        if len(zero_indice_list) == 0:
            warnings.warn("No zero concentration found in the data.")
        elif len(zero_indice_list) > 1:
            raise ValueError("More than one zero concentration found in the data.")
        else:
            zero_index = zero_indice_list[0]


        if pipeline['clear_zero_concentration'] and zero_index != -1:
            baseline_signals[:, zero_index] = 0
            association_signals[:, zero_index] = 0
            dissociation_signals[:, zero_index] = 0

        if pipeline['delete_zero_concentration'] and zero_index != -1:
            concentration_M.pop(zero_index)
            baseline_signals = np.delete(baseline_signals, zero_index, axis=1)
            association_signals = np.delete(association_signals, zero_index, axis=1)
            dissociation_signals = np.delete(dissociation_signals, zero_index, axis=1)
        
        alpha = pipeline['signal_expansion_coefficient']
        if alpha != 1:
            baseline_signals = baseline_signals * alpha
            association_signals = association_signals * alpha
            dissociation_signals = dissociation_signals * alpha

        if pipeline['100_truncate'] and self._device == '100':
            baseline_start = pipeline['100_truncate_params']['baseline_start']
            baseline_end = pipeline['100_truncate_params']['baseline_end']
            association_start = pipeline['100_truncate_params']['association_start']
            association_end = pipeline['100_truncate_params']['association_end']
            dissociation_start = pipeline['100_truncate_params']['dissociation_start']
            dissociation_end = pipeline['100_truncate_params']['dissociation_end']

            if baseline_start != -1 and baseline_end != -1:
                baseline_signals = baseline_signals[baseline_start:baseline_end, :]
            if association_start != -1 and association_end != -1:
                association_signals = association_signals[association_start:association_end, :]
            if dissociation_start != -1 and dissociation_end != -1:
                dissociation_signals = dissociation_signals[dissociation_start:dissociation_end, :]
        
        mode = pipeline['zeroing_logic_mode']
        _ = self._align_signals(baseline_signals, association_signals, dissociation_signals, mode)

        return _


    def process(self, pipeline: dict)->pd.DataFrame:
        
        time_interval = pipeline['time_interval']
        if self._device == 'one'and time_interval != 1:
            time_interval = 1
            warnings.warn("device 'one' only supports time_interval=1, setting it to 1 automatically.")

        baseline_signals, association_signals, dissociation_signals = self._process_data_pipeline(pipeline)

        processed_signals = np.vstack(
            [baseline_signals, association_signals, dissociation_signals] 
            if pipeline['baseline_included'] 
            else [association_signals, dissociation_signals]
        )

        self._dissociation_time_start = (baseline_signals.shape[0] * pipeline['baseline_included'] + association_signals.shape[0]) * time_interval
        self._dissociation_time_start = round(self._dissociation_time_start)

        time_array = np.array([i * time_interval for i in range(processed_signals.shape[0])])
        concentrations_M = self._concentrations_M

        result_df = pd.DataFrame(processed_signals)
        result_df.insert(0, 'Time(s)', time_array)
        concentrations_M.insert(0, '')
        result_df.loc[-1] = concentrations_M
        result_df.index = result_df.index + 1
        result_df.sort_index(inplace=True)

        sorted_columns = result_df.columns[1:][result_df.iloc[0, 1:].argsort()]
        result_df = result_df[['Time(s)'] + sorted_columns.tolist()]

        return result_df


    @staticmethod
    def _extract_time_and_signals(df: pd.DataFrame,
                                 hole_names: list
                                 )->tuple:
        # works both for 100 and 100-capture 
        time_df = df[df.iloc[:, 0] == 'Time [s]']
        time_df = time_df.iloc[0].dropna(inplace=False)
        time_data = time_df.iloc[1:].to_list()
        time_data = [round(_) for _ in time_data]

        time_data = np.array(time_data)

        signals = np.array([])
        for hole_name in hole_names:
            
            signal = df[df.iloc[:, 0] == hole_name]
            signal = signal.dropna(axis=1, inplace=False)

            if signal.empty:
                raise ValueError(f"Signal is empty for hole name '{hole_name}'! Check if it is valid.")

            signal_575 = signal.iloc[0, 1:].to_numpy().astype(np.float64)
            signal_595 = signal.iloc[1, 1:].to_numpy().astype(np.float64)
            signal = signal_595 - signal_575
            signal = signal.reshape(-1, 1)

            signals = np.hstack([signals, signal]) if signals.size else signal
        
        return time_data, signals

    @staticmethod
    def _align_signals(baseline_signals: np.ndarray,
                      association_signals: np.ndarray,
                      dissociation_signals: np.ndarray,
                      mode='slow')->tuple:
        
        VAILD_MODE = ['slow', 'fast']
        
        # zeroing signals and concating

        baseline_signals = baseline_signals - baseline_signals[0, :]
        association_tradeoff = association_signals[0, :] - baseline_signals[-1, :]
        association_signals = association_signals - association_tradeoff

        if mode == 'fast':
            dissociation_signals = dissociation_signals - association_tradeoff
        elif mode == 'slow':
            dissociation_tradeoff = dissociation_signals[0, :] - association_signals[-1, :]
            dissociation_signals = dissociation_signals - dissociation_tradeoff
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {VAILD_MODE}")
        
        return baseline_signals, association_signals, dissociation_signals


    @staticmethod
    def _validate_init_options(init_options: dict):

        VALID_DEVICE = ['one', '100', '100-capture']
        VALID_DTYPE = ['excel', 'zip', 'json']
        VALID_UNIT = ["M", "mg/ml", "ng/ml", "pg/ml", "μg/ml", "ug/ml", "nM", "µM", "uM", "mM", "particles/ml", "vp/ml"]

        if init_options['device'] not in VALID_DEVICE:
            raise ValueError(f"Invalid device: {init_options['device']}. Must be one of {VALID_DEVICE}")
        if init_options['dtype'] not in VALID_DTYPE:
            raise ValueError(f"Invalid data type: {init_options['data type']}. Must be one of {VALID_DTYPE}")
        if init_options['unit'] not in VALID_UNIT:
            raise ValueError(f"Invalid unit: {init_options['unit']}. Must be one of {VALID_UNIT}")


    @staticmethod
    def _convert_concentration_to_Mole(concentrations : list,
                                      unit : str,
                                      mole : float = 50000,
                                    ) -> list:
        """
        Parameters:
        ------------
        concentrate: list of concentrations, e.g. ['0.1ug/ml', '0.2ug/ml', '0.3ug/ml']. 
        unit: unit of the concentration, multiple units supported. e.g. 'ug/ml', 'nM'.
        mole: molecular mass, by default 50000.
        ------------
        Return:
        a list of converted concentrations in Mole.
        ------------
        """
        
        if mole == 0:
            warnings.warn("Mole is 0, setting it to 1.0 automatically.")
            mole = 1.0
    
        pattern = re.compile(r'(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?')
        concentrations_ = [float(pattern.match(c).group(0)) for c in concentrations if pattern.match(c)]
        
        if len(concentrations_) != len(concentrations):
            warnings.warn(
                "Some concentration values could not be parsed. "
                "The unit data in the original file may be missing, corrupted, or incorrectly formatted."
            )

        concentrations_array = np.array(concentrations_, dtype=np.float64)

        if unit == "M":
            pass
        elif unit == "mg/ml":
            concentrations_array = concentrations_array / mole
        elif unit == "μg/ml" or unit == "ug/ml":
            concentrations_array = concentrations_array / 1e3 / mole
        elif unit == "ng/ml":
            concentrations_array = concentrations_array / 1e6 / mole
        elif unit == "pg/ml":
            concentrations_array = concentrations_array / 1e9 / mole
        elif unit == "mM":
            concentrations_array = concentrations_array / 1e3
        elif unit == "µM" or unit == "uM":
            concentrations_array = concentrations_array / 1e6
        elif unit == 'nM':
            concentrations_array = concentrations_array / 1e9
        elif unit == "particles/ml" or unit == "vp/ml":
            concentrations_array = concentrations_array / 6.02E+20
        else:
            raise ValueError(f"Unit '{unit}' is not supported for conversion.")
        
        return concentrations_array.tolist()
    
    @property
    def device(self):
        return self._device
    
    @device.setter
    def device(self, value):
        raise AttributeError("Cannot change device value after initialization.")
    
    @property
    def dtype(self):
        return self._dtype
    
    @dtype.setter
    def dtype(self, value):
        raise AttributeError("Cannot change dtype value after initialization.")
    
    @property
    def unit(self):
        return self._unit
    
    @unit.setter
    def unit(self, value):
        raise AttributeError("Cannot change unit value after initialization.")

    @property
    def molecular_mass(self):
        return self._molecular_mass
    
    @molecular_mass.setter
    def molecular_mass(self, value):
        raise AttributeError("Cannot change molecular_mass value after initialization.")
    
    @property
    def hole_info(self):
        return self._hole_info
    
    @hole_info.setter
    def hole_info(self, value):
        raise AttributeError("Cannot change hole_info value after initialization.")
    
    @property
    def hole_names(self):
        return self._hole_names
    
    @hole_names.setter
    def hole_names(self, value):
        raise AttributeError("Cannot change hole_names value after initialization.")
    
    @property
    def concentrations(self):
        return self._concentrations
    
    @concentrations.setter
    def concentrations(self, value):
        raise AttributeError("Cannot change concentrations value after initialization.")
    
    @property
    def concentrations_M(self):
        return self._concentrations_M
    
    @concentrations_M.setter
    def concentrations_M(self, value):
        raise AttributeError("Cannot change concentrations_M value after initialization.")
    
    @property
    def raw_baseline_signals(self):
        return self._raw_baseline_signals
    
    @raw_baseline_signals.setter
    def raw_baseline_signals(self, value):
        raise AttributeError("Cannot change raw_baseline_signals value after initialization.")
    
    @property
    def raw_association_signals(self):
        return self._raw_association_signals
    
    @raw_association_signals.setter
    def raw_association_signals(self, value):
        raise AttributeError("Cannot change raw_association_signals value after initialization.")
    
    @property
    def raw_dissociation_signals(self):
        return self._raw_dissociation_signals
    
    @raw_dissociation_signals.setter
    def raw_dissociation_signals(self, value):
        raise AttributeError("Cannot change raw_dissociation_signals value after initialization.")
    
    @property
    def dissociation_time_start(self):
        return self._dissociation_time_start
    
    @dissociation_time_start.setter
    def dissociation_time_start(self, value):
        raise AttributeError("Cannot change dissociation_time_start value after processing.")

