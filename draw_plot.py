"""
dataframe 包含 3 列：'feature_id', 'rts', 'intensity'
feature_id: 特征的 id,str
rts: retention time, array
intensity: intensity, array
批量画图
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MaxNLocator

# 使用 agg 后端加速绘图
matplotlib.use('agg')

# 设置字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (8, 6)

def draw_plot(dataframe, save_dir):
    # 画图
    for index, row in dataframe.iterrows():
        feature_id = row['feature_id']
        rts = row['rts']
        intensity = row['intensity']
        
        fig, ax = plt.subplots()
        ax.plot(rts, intensity, label=feature_id)
        ax.set_xlabel('Retention Time (min)')
        ax.set_ylabel('Intensity')
        ax.legend()
        
        save_path = os.path.join(save_dir, f'{feature_id}.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    # 读取数据
    dataframe = pd.read_csv('data.csv')
    
    # 处理数据
    dataframe['rts'] = dataframe['rts'].apply(lambda x: np.fromstring(x, sep=','))
    dataframe['intensity'] = dataframe['intensity'].apply(lambda x: np.fromstring(x, sep=','))
    
    save_dir = 'plots'
    os.makedirs(save_dir, exist_ok=True)
    
    draw_plot(dataframe, save_dir)

if __name__ == '__main__':
    main()
