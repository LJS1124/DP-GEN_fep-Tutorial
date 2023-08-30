
import pandas as pd
import glob
import os
import numpy as np
import fc
import shutil
from dpdispatcher import Machine, Resources, Task, Submission

#初始化
work_path = '/data/test/' #定义自由能计算工作路径
machine = Machine.load_from_json(os.path.join(work_path,'machine.json'))
resources = Resources.load_from_json(os.path.join(work_path,'resource.json'))
all_models = glob.glob(os.path.join(work_path, "*.pb"))
threshold = 0.4
init_data = '1.data'

if not os.path.exists(work_path):
    try:
        os.makedirs(work_path)
        print(f"文件夹 '{work_path}' 创建成功！")
    except OSError as e:
        print(f"创建文件夹 '{work_path}' 失败：{e}")
else:
    pass
#DP-GEN运行预留空位


#插点
folder = np.linspace(0, 1, 5)
current_path = os.getcwd()
print(current_path)

for num in folder:
    folder_name = str(num)
    folder_name = os.path.join(work_path, folder_name)
    os.makedirs(folder_name, exist_ok=True) #创建文件夹
    # 创建文件
    if num == 0:
        fstate=0.0001
    elif num == 1:
        fstate=0.9999
    else:
        fstate=num
    
    file_in = fc.make_in_fep(
    nsteps=2000,
    dt=0.0005,
    trj_freq=100,
    mass1=1,
    mass2=16,
    temp=330,
    fstate=fstate,
    tau_t=0.05,
    pres=1.0000,
)
    with open(os.path.join(folder_name,"in.fep_red"), "w") as fp:
        fp.write(file_in)

    #复制文件
    shutil.copy(os.path.join(work_path,init_data), folder_name)


#文件创建完毕进行第一次提交
#数值列表转换为字符串列表
folder_list = [str(item) for item in folder]
tasks = [Task(command='lmp -i in.fep_red',
              task_work_path=f'./{work_path_value}',
              forward_files=['1.data', 'in.fep_red'],
              backward_files=['fep_mix.test', 'out.lmp'],
              outlog='log.lammps') for work_path_value in folder_list]
print(tasks)
#将模型取出放列表传入
model_names = [os.path.basename(ii) for ii in all_models]
submission = Submission(work_base=work_path,
    machine=machine,
    resources=resources,
    task_list=tasks,
    forward_common_files=model_names,
    backward_common_files=[]
)
print(submission)
#运行完成前进程会进行阻塞
submission.run_submission()


#判断采样是否足够不足则继续插点计算
while True:
    #fc.get_outgap可以提取含lammps计算结果的文件进行分析，返回垂直平均能差
    mean_data = fc.get_outgap(work_path)
    print(mean_data)

    mean_data['Mean_Diff'] = mean_data['Mean'].diff().abs()
    mean_data['Mean_Diff_Greater_threshold'] = mean_data['Mean_Diff'] > threshold #阈值可自行设置
    mask = mean_data['Mean_Diff'] > threshold
    mean_data['Next_Column'] = mean_data['Column'].shift(1)
    mean_data['Column'] = mean_data['Column'].astype(float)
    mean_data['Next_Column'] = mean_data['Next_Column'].astype(float)
    mean_data['Column_Average'] = (mean_data['Column'] + mean_data['Next_Column']) / 2
    mean_data.drop(columns=['Next_Column'], inplace=True)
    result_list = []
    result_list = mean_data[mask]['Column_Average'].tolist()
    print(result_list)
    #提交任务
    str_list = [str(item) for item in result_list]
    if not result_list:
        print('well done')
        break
    else:
        #创建缺省文件
        for num in result_list:
            folder_name = str(num)
            folder_name = os.path.join(work_path, folder_name)
            os.makedirs(folder_name, exist_ok=True) #创建文件夹
            if num == 0:
                fstate=0.0001
            elif num == 1:
                fstate=0.9999
            else:
                fstate=num
            
            file_in = fc.make_in_fep(
            nsteps=2000,
            dt=0.0005,
            trj_freq=100,
            mass1=1,
            mass2=16,
            temp=330,
            fstate=fstate,
            tau_t=0.05,
            pres=1.0000,
        )
            with open(os.path.join(folder_name,"in.fep_red"), "w") as fp:
                fp.write(file_in)
            #复制文件
            shutil.copy(os.path.join(work_path,init_data), folder_name)

        print("准备计算" + str(result_list)) 
        retasks = [Task(command='lmp -i in.fep_red',
              task_work_path=f'./{work_path_value}',
              forward_files=['1.data', 'in.fep_red'],
              backward_files=['fep_mix.test', 'out.lmp'],
              outlog='log.lammps') for work_path_value in str_list]
        print(retasks)

        resubmission = Submission(work_base=work_path,
        machine=machine,
        resources=resources,
        task_list=retasks,
        forward_common_files=model_names,
        backward_common_files=[]
    )
        resubmission.run_submission()