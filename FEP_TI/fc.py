# 导入模块
import pandas as pd
import glob
import os
import numpy as np
import shutil

#文件名提取函数

# 指定目录的路径
work_path = '/data/AI4EC/01.fep_ti_inp/'
def get_outgap(directory_path):
    #传入搜索的工作路径，返回标签和平均gap
# 使用glob.glob()函数查找包含'fep_mix.test'文件的多个文件夹路径
    file_paths = glob.glob(directory_path + '/**/fep_mix.test', recursive=True)
    #file_paths = glob.glob('**/fep_mix.test', recursive=True)
    #print(folder_paths)
    folder_names = []
    for file_path in file_paths:
        folder_path = os.path.dirname(file_path)
        print(folder_path)
        folder_name = os.path.basename(folder_path)
        folder_names.append(folder_name)
    #print(folder_names)
    # 创建一个dataframe
    gap_data = pd.DataFrame()
    #同步读取文件名与路径信息
    for file_path, folder_name in zip(file_paths, folder_names):
        data = pd.read_csv(file_path, sep='\s+')
        GAP = data.loc[:,'GAP']
        gap_data = gap_data.assign(**{folder_name: GAP})
        #通过**操作符，将字典对象解包为关键字参数
        #print(folder_name)
        # 计算每列的平均值
    mean_values = gap_data.mean()

    # 创建新的 DataFrame 保存平均值
    mean_data = pd.DataFrame({'Column': mean_values.index, 'Mean': mean_values.values})
    return mean_data

def get_outgap1():
    file_paths = glob.glob('**/fep_mix.test', recursive=True)

    # 获取文件所在的文件夹名称并保存
    folder_names = []
    for file_path in file_paths:
        folder_path = os.path.dirname(file_path)
        folder_name = os.path.basename(folder_path)
        folder_names.append(folder_name)
    #file_paths相对文件路径列表  folder_names文件名列表

    # 创建一个dataframe
    gap_data = pd.DataFrame()
    #同步读取文件名与路径信息
    for file_path, folder_name in zip(file_paths, folder_names):
        data = pd.read_csv(file_path, sep='\s+')
        GAP = data.loc[:,'GAP']
        gap_data = gap_data.assign(**{folder_name: GAP})
        #通过**操作符，将字典对象解包为关键字参数
        #print(folder_name)

    # 计算每列的平均值
    mean_values = gap_data.mean()

    # 创建新的 DataFrame 保存平均值
    mean_data = pd.DataFrame({'Column': mean_values.index, 'Mean': mean_values.values})
    return mean_data


    #输入文件写入
def make_in_fep(
    nsteps,
    dt,
    trj_freq,
    mass1,
    mass2,
    temp,
    fstate,
    tau_t=0.05,
    pres=1.0000,
):

    fep  = "# --------------------- VARIABLES------------------------- \n"
    fep += "variable        NSTEPS          equal %d\n" % nsteps
    fep += "variable        THERMO_FREQ     equal %d\n" % trj_freq #100
    fep += "variable        DUMP_FREQ       equal %d\n" % trj_freq
    fep += "variable        TEMP            equal %d\n" % temp #330
    fep += "variable        PRES            equal %f\n" % pres
    fep += "variable        TAU_T           equal %f\n" % tau_t
    fep += "variable        plus            equal %d\n" % 1
    fep += "variable        minus           equal %d\n" % -1
    fep += "variable        LAMBDA_f        equal %f\n" % fstate
    fep += "variable        LAMBDA_i        equal 1-v_LAMBDA_f \n"

    fep += "# --------------------- INITIALIZAITION------------------------- \n"
    fep += "units           metal\n"
    fep += "boundary        p p p\n"
    fep += "atom_style      atomic\n"
    fep += "atom_modify map yes\n"
    fep += "# --------------------- ATOM DEFINITION ------------------\n"
    fep += "read_data   1.data\n"
    fep += "mass		1 15.999\n"  #mass1
    fep += "mass 		2 1.00800\n" #mass2 #考虑提取jdata数据
    fep += "# --------------------- FORCE FIELDS ---------------------\n"
    fep += "pair_style hybrid/overlay &\n \t\t\tdeepmd ../neu.pb  &\n \t\t\tdeepmd ../red.pb \n"
    fep += "\n"
    fep += "pair_coeff    *  * deepmd 1 *\n"
    fep += "pair_coeff    *  * deepmd 2 *\n"
    fep += "\n"
    fep += "fix     sampling_PES all adapt 0 &\n \t\tpair deepmd:1 scale * * v_LAMBDA_i &\n \t\tpair deepmd:2 scale * * v_LAMBDA_f &\n \t\tscale yes\n"
    fep += "\n"
    fep += "compute ini all pair deepmd 1\n"
    fep += "compute fin all pair deepmd 2\n"
    fep += "compute PE all pe\n"
    fep += "compute KE all ke\n"
    fep += "# --------------------- PRINT SECTION ----------------------\n"
    fep += "variable PE  equal c_PE\n"
    fep += "variable KE  equal c_KE\n"
    fep += "variable ini equal c_ini/v_LAMBDA_i\n"
    fep += "variable fin equal c_fin/v_LAMBDA_f\n"
    fep += "variable GAP equal v_ini-v_fin\n"
    fep += "variable time equal step*dt\n"
    fep += "variable temp equal temp\n"
    fep += "\n"
    fep += "variable float1 format time %10.4f\n"
    fep += "variable float2 format temp %14.7f\n"
    fep += "variable float3 format PE   %14.7f\n"
    fep += "variable float4 format KE   %14.7f\n"
    fep += "variable float5 format ini  %14.7f\n"
    fep += "variable float6 format fin  %14.7f\n"
    fep += "variable float7 format GAP  %14.7f\n"
    fep += "\n"
    fep += 'fix 3 all print ${DUMP_FREQ} "${float1}  ${float2}  ${float3}  ${float4}  ${float5}  ${float6}  ${float7}" file fep_mix.test screen "no" title "#time T PE KE ini fin GAP"'
    fep += "\n"
    fep += "\n"
    fep += "# --------------------- MD SETTINGS ----------------------\n"
    fep += "velocity        all create ${TEMP} 206210\n"
    fep += "neighbor        2.0 bin\n"
    fep += "neigh_modify    every 1\n"
    fep += "timestep        %f\n" % dt
    fep += "fix             1 all nvt temp ${TEMP} ${TEMP} ${TAU_T}\n"
    fep += "thermo          ${THERMO_FREQ}\n"
    fep += "thermo_style    custom step temp pe ke etotal c_ini c_fin\n"
    fep += "thermo_modify   format float %15.7f\n"
    fep += "dump        TRAJ all xyz ${DUMP_FREQ} oh.xyz\n"
    fep += 'dump_modify TRAJ element O H  format line " %2s    %12.6f    %12.6f   %12.6f"\n'
    fep += "\n"
    fep += "# --------------------- RUN ------------------------------\n"
    fep += "run             ${NSTEPS}\n"
    fep += "write_data      out.lmp\n"
    fep += "\n"
    return fep