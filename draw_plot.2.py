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
import plotly.graph_objects as go

def draw_plot(dataframe, save_dir):
    # 画图
    for index, row in dataframe.iterrows():
        feature_id = row['feature_id']
        rts = row['rts']
        intensity = row['intensity']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rts, y=intensity, mode='lines', name=feature_id))
        fig.update_layout(title=feature_id, xaxis_title='Retention Time (min)', yaxis_title='Intensity')
        
        save_path = os.path.join(save_dir, f'{feature_id}.png')
        fig.write_image(save_path)

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
