# add_data() 关键字参数支持修复

## 问题
用户报错：`DataManager.add_data() got an unexpected keyword argument 'name'`

## 原因
`add_data()` 方法签名使用的是位置参数 `name_or_item`，但代码中有地方使用关键字参数 `name=` 调用。

## 修复

### 修改前
```python
def add_data(self, name_or_item, dataframe_or_type=None) -> int:
    # 只支持位置参数
    if isinstance(name_or_item, str):
        ...
```

### 修改后
```python
def add_data(self, name_or_item=None, dataframe_or_type=None, **kwargs) -> int:
    # 支持位置参数和关键字参数
    if 'name' in kwargs or 'dataframe' in kwargs:
        # 关键字参数方式
        name = kwargs.get('name', name_or_item)
        dataframe = kwargs.get('dataframe', dataframe_or_type)
        ...
    elif isinstance(name_or_item, str):
        # 位置参数方式
        ...
```

## 现在支持的所有调用方式

### 1. DataFrame - 位置参数
```python
data_id = dm.add_data("样本A", df)
```

### 2. DataFrame - 关键字参数 ✅ 新增
```python
data_id = dm.add_data(name="样本A", dataframe=df)
```

### 3. JSON - 位置参数
```python
data_id = dm.add_data(json_dict, 'file')
```

### 4. JSON - 关键字参数
```python
data_id = dm.add_data(item=json_dict, itemtype='file')
```

## 测试验证

运行 `tests/test_add_data_kwargs.py`，所有测试通过 ✅

## 修改的文件

- ✅ `src/models/data_model.py` - DataManager.add_data() 方法
- ✅ 修复了 `get_xy_data()` 方法的缩进错误（同时修复）

## 影响

- ✅ 向后兼容：所有现有调用方式保持不变
- ✅ 新增支持：现在可以使用关键字参数
- ✅ 无破坏性变更

