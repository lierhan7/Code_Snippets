import os
import argparse
from bs4 import BeautifulSoup
import pandas as pd
import json

def parse_html_tables(html_file_path):
    """
    解析HTML文件中的表格数据
    
    Args:
        html_file_path: HTML文件的路径
    
    Returns:
        包含所有表格数据的列表
    """
    # 检查文件是否存在
    if not os.path.exists(html_file_path):
        print(f"错误：文件 {html_file_path} 不存在")
        return None
    
    # 读取HTML文件
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找所有表格
    tables = soup.find_all('table')
    
    if not tables:
        print("未在HTML中找到表格")
        # 尝试查找其他可能包含数据的元素
        return extract_data_from_divs(soup)
    
    all_tables_data = []
    
    for idx, table in enumerate(tables):
        print(f"\n正在处理第 {idx + 1} 个表格...")
        
        # 提取表格数据
        table_data = []
        headers = []
        
        # 提取表头
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        else:
            # 如果没有thead，尝试从第一行获取表头
            first_row = table.find('tr')
            if first_row:
                headers = [cell.get_text(strip=True) for cell in first_row.find_all(['th'])]
                if not headers:
                    headers = [cell.get_text(strip=True) for cell in first_row.find_all(['td'])]
        
        # 提取表格内容
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for row in rows:
            # 跳过表头行
            if row.find('th') and not tbody:
                continue
                
            row_data = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
            if row_data:
                table_data.append(row_data)
        
        # 创建DataFrame
        if table_data:
            if headers and len(headers) == len(table_data[0]):
                df = pd.DataFrame(table_data, columns=headers)
            else:
                df = pd.DataFrame(table_data)
            
            all_tables_data.append({
                'table_index': idx + 1,
                'dataframe': df,
                'raw_data': table_data
            })
            
            print(f"表格 {idx + 1} 包含 {len(df)} 行数据")
            print(df.head())
    
    return all_tables_data

def extract_data_from_divs(soup):
    """
    如果没有找到表格，尝试从div元素中提取结构化数据
    
    Args:
        soup: BeautifulSoup对象
    
    Returns:
        提取的数据
    """
    data_containers = []
    
    # 查找可能包含数据的div元素
    # 常见的类名模式
    possible_classes = ['data-table', 'table', 'grid', 'list', 'results', 'data-container']
    
    for class_name in possible_classes:
        divs = soup.find_all('div', class_=lambda x: x and class_name in x.lower() if x else False)
        for div in divs:
            text_content = div.get_text(strip=True)
            if text_content:
                data_containers.append({
                    'type': 'div',
                    'class': div.get('class'),
                    'content': text_content[:500]  # 只显示前500个字符
                })
    
    # 查找所有包含数据属性的元素
    elements_with_data = soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()))
    
    for elem in elements_with_data[:10]:  # 限制显示前10个元素
        data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
        if data_attrs:
            data_containers.append({
                'type': elem.name,
                'data_attributes': data_attrs,
                'text': elem.get_text(strip=True)[:200]
            })
    
    return data_containers

def save_to_excel(tables_data, output_file):
    """
    将表格数据保存到Excel文件
    
    Args:
        tables_data: 表格数据列表
        output_file: 输出文件路径
    """
    if not tables_data:
        print("没有数据可保存")
        return
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for table_info in tables_data:
            if 'dataframe' in table_info:
                sheet_name = f"Table_{table_info['table_index']}"
                table_info['dataframe'].to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"已保存表格 {table_info['table_index']} 到工作表 {sheet_name}")

def save_to_json(data, output_file):
    """
    将数据保存到JSON文件
    
    Args:
        data: 要保存的数据
        output_file: 输出文件路径
    """
    # 处理DataFrame对象
    json_data = []
    for item in data:
        if isinstance(item, dict):
            if 'dataframe' in item:
                item_copy = item.copy()
                item_copy['dataframe'] = item['dataframe'].to_dict('records')
                json_data.append(item_copy)
            else:
                json_data.append(item)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {output_file}")

def args_parser():
    parser = argparse.ArgumentParser(description="从HTML文件中提取表格数据并保存为Excel和JSON格式")
    parser.add_argument('--html_file', type=str, help="HTML文件的路径")
    parser.add_argument('--output_dir', type=str, default='.', help="输出目录")
    return parser.parse_args()

def main():
    args = args_parser()
    html_file = args.html_file
    output_dir = args.output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # HTML文件路径
    #html_file = r"c:\Users\lierhan\Desktop\mzcloud\mzCloud - Advanced Mass Spectral Database.html"
    
    # 解析HTML并提取表格
    print(f"正在解析文件: {html_file}")
    tables_data = parse_html_tables(html_file)
    
    if tables_data:
        # 检查是否包含DataFrame
        has_dataframes = any('dataframe' in item for item in tables_data if isinstance(item, dict))
        
        if has_dataframes:
            # 保存到Excel
            excel_output = os.path.join(output_dir, "extracted_tables.xlsx")
            save_to_excel(tables_data, excel_output)
            print(f"\n表格数据已保存到: {excel_output}")
        
        # 保存到JSON
        json_output = os.path.join(output_dir, "extracted_data.json")
        save_to_json(tables_data, json_output)
    else:
        print("\n未能提取到有效数据")

if __name__ == "__main__":
    main()