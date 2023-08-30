<<<<<<< HEAD
<<<<<<< HEAD
# DP-GEN_fep-Tutorial
none
=======
# 使用说明

# DP-GEN fep使用说明

作者：梁晋山

日期：2023-8-9

## 一、环境与初始参数设置

环境配置：

1、Borhrium平台，选择配置容器节点 dpgen:0.11.0 ，任意配置机器启动即可(建议采用低配置）

2、主机或集群配置：尚未完善

初始参数设置：

工作路径目录如下：

![Untitled](%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%2009271a9011dc4e219cd1b09084f442aa/Untitled.png)

data：用于存放训练数据集和md初始结构

md:存放model_devi初始结构文件

neu:存放训练数据集(format = npy)

red:存放训练数据集(format = npy)

input_neu.inp:cp2k单点计算输入文件

input_red.inp：cp2k单点计算输入文件

machine.json：同DP_GENmachine.json

param.json:同DP_GENparam.json

## 二、param.json的修改

param.json有多处需要修改，第一部分配置训练网络请按自己需要进行修改，不修改可使用默认参数

"type_map”：根据计算系统修改

"mass_map”：type_map对应原子质量

"init_data_prefix”：初始数据集根路径

添加"init_neu_data_sys”键：neu相对路径

添加"init_red_data_sys”键：red相对路径

"sys_configs”:md初始结构路径

"temps”：当前测试用例温度设置为330

添加"neu_external_input_path”：cp2k输入文件路径

添加"red_external_input_path”：cp2k输入文件路径

## 三、machine.json的修改

machine.json没有什么需要特别修改的地方，使用默认参数即可，需要填写登录lbg的账号密码和项目id

"email”:bohrium账号

"password”：bohrium密码

"program_id”：项目id

使用vasp的单点计算功能暂未开放

## 四、Quick Start

```bash
cd workpath #根据你的项目路径修改

python run_fep_final.py param.json machine.json
```

# FEP_TI使用说明

FEP_TI是用于实现自由能计算最后一步的模块，使用训练好的势函数进行计算。

## 一、环境与初始参数设置

环境配置：

1、Borhrium平台，选择配置容器节点 dpgen:0.11.0 ，任意配置机器启动即可(建议采用低配置）

2、主机或集群配置：尚未完善

初始参数设置：

工作路径目录如下：

![Untitled](%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%2009271a9011dc4e219cd1b09084f442aa/Untitled%201.png)

## 二、Quick Start

修改fep_ti.py

```python
work_path = '/data/test/' #定义自由能计算工作路径  修改工作路径
machine = Machine.load_from_json(os.path.join(work_path,'machine.json'))
resources = Resources.load_from_json(os.path.join(work_path,'resource.json'))
all_models = glob.glob(os.path.join(work_path, "*.pb"))
threshold = 0.4 #自定义阈值
init_data = '1.data'#初始结构
```

bash:

```bash
cd workpath #根据你的项目路径修改
Python fep_ti.py
```
>>>>>>> 889a82d (readme update)
=======
# DP-GEN_fep-Tutorial
none
>>>>>>> 2829c0b6a2f3e3f9afb51f402399ac0dfa67f739
