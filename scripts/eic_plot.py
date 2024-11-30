import pandas as pd
import numpy as np
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tqdm

def safe_string_to_array(x):
    try:
        return np.fromstring(x, sep=',')
    except Exception as e:
        print(f"Error converting {x}: {e}")
        return np.array([])

def main(feature_matrix_file):
    # 读取数据
    feature_matrix = pd.read_csv(feature_matrix_file, float_precision='high')
    for col in ["EIC_RT", "EIC_intensity"]:
        feature_matrix[col] = feature_matrix[col].apply(safe_string_to_array)

    # 创建输出目录
    os.makedirs('eic_plot', exist_ok=True)  

    # 创建图形和轴对象
    fig, ax = plt.subplots()  # 初始化图形对象
    
    # 通过遍历逐行处理数据
    for _, row in tqdm.tqdm(feature_matrix.iterrows(), total=len(feature_matrix)):
        feature_id = row["feature_id"]
        ax.plot(row["EIC_RT"], row["EIC_intensity"])  # 绘制图像
        
        # 保存图像并清除图形数据
        fig.savefig(f"eic_plot/{feature_id}.jpg")  
        ax.clear()  # 清除当前图形，准备下一个图形

if __name__ == '__main__':
    feature_matrix_file = sys.argv[1]
    main(feature_matrix_file)
