"""
MCE 化合物信息爬取脚本
用于爬取 MedChemExpress 网站的内源性代谢物化合物信息

使用说明：
1. 遵守 robots.txt 规则
2. 合理控制请求频率，避免对服务器造成过大压力
3. 仅用于学习和研究目的
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
from typing import List, Dict
import re
import random
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MCECompoundScraper:
    def __init__(self, delay_range=(3, 6), max_retries=3):
        """
        初始化爬虫
        
        Args:
            delay_range: 请求间隔时间范围（秒），tuple (最小值, 最大值)
            max_retries: 请求失败时的最大重试次数
        """
        self.base_url = "https://www.medchemexpress.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.medchemexpress.cn/',
        }
        self.session = requests.Session()
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.request_count = 0
        self.start_time = datetime.now()
        
        # 用户代理池（可选，增加多样性）
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
    def _random_delay(self):
        """随机延迟，模拟人类行为"""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        logging.info(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def _rotate_user_agent(self):
        """随机更换 User-Agent"""
        self.headers['User-Agent'] = random.choice(self.user_agents)
    
    def _check_rate_limit(self):
        """检查请求频率，防止过快"""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        if elapsed_time > 0:
            rate = self.request_count / elapsed_time
            if rate > 0.5:  # 每秒不超过0.5个请求（即2秒一个）
                logging.warning(f"请求频率过快 ({rate:.2f} req/s)，增加延迟...")
                time.sleep(2)
        
    def fetch_page(self, url: str) -> str:
        """
        获取网页内容（带重试机制）
        
        Args:
            url: 目标URL
            
        Returns:
            网页HTML内容，失败返回None
        """
        for attempt in range(self.max_retries):
            try:
                # 检查请求频率
                self._check_rate_limit()
                
                # 随机更换 User-Agent
                self._rotate_user_agent()
                
                logging.info(f"正在请求: {url} (尝试 {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(url, headers=self.headers, timeout=30)
                self.request_count += 1
                
                # 检查响应状态
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    logging.info(f"请求成功: {url}")
                    return response.text
                    
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = 60 * (attempt + 1)
                    logging.warning(f"请求过于频繁 (429)，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    
                elif response.status_code == 403:  # Forbidden
                    logging.error(f"访问被拒绝 (403)，可能被封禁")
                    return None
                    
                else:
                    logging.warning(f"响应状态码: {response.status_code}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logging.warning(f"请求超时，重试 {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    
            except requests.exceptions.ConnectionError as e:
                logging.error(f"连接错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(10 * (attempt + 1))
                    
            except requests.RequestException as e:
                logging.error(f"请求失败: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(5 * (attempt + 1))
        
        logging.error(f"多次尝试后仍然失败: {url}")
        return None
    
    def parse_compounds(self, html: str) -> List[Dict]:
        """解析化合物信息"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        compounds = []
        
        # 查找化合物列表容器
        compound_list = soup.find('ul', class_='sub_ctg_list_con')
        if not compound_list:
            print("未找到化合物列表容器")
            return []
        
        # 查找所有化合物项
        product_items = compound_list.find_all('li', recursive=False)
        print(f"找到 {len(product_items)} 个化合物")
        
        for item in product_items:
            compound_data = {}
            
            # 提取产品编号 (Cat. No.)
            cat_no_tag = item.find('dt', class_='dnr_pro_list_cat')
            if cat_no_tag:
                cat_link = cat_no_tag.find('a')
                if cat_link:
                    compound_data['catalog_no'] = cat_link.get_text(strip=True)
                    # 提取产品链接
                    href = cat_link.get('href', '')
                    if href.startswith('/'):
                        compound_data['url'] = self.base_url + href
            
            # 提取产品名称
            name_tag = item.find('th', class_='dnr_pro_list_name')
            if name_tag:
                strong_tag = name_tag.find('strong')
                if strong_tag:
                    compound_data['name_en'] = strong_tag.get_text(strip=True)
                
                # 提取中文名称
                cn_name_tag = name_tag.find('p', id='list-name-cn')
                if cn_name_tag:
                    cn_link = cn_name_tag.find('a')
                    if cn_link:
                        compound_data['name_cn'] = cn_link.get_text(strip=True)
            
            # 提取 CAS 号
            cas_tag = item.find('th', class_='dnr_pro_list_cas')
            if cas_tag:
                cas_text = cas_tag.get_text(strip=True)
                if cas_text:
                    compound_data['cas_no'] = cas_text
            
            # 提取纯度
            purity_tag = item.find('th', class_='dnr_pro_list_purity')
            if purity_tag:
                purity_text = purity_tag.get_text(strip=True)
                if purity_text:
                    compound_data['purity'] = purity_text
            
            # 提取简介
            brief_tag = item.find('td', class_='dnr_pro_list_brief')
            if brief_tag:
                # 移除HTML标签，获取纯文本
                brief_text = brief_tag.get_text(strip=True)
                if brief_text:
                    compound_data['description'] = brief_text
            
            # 提取结构图链接
            structure_tag = item.find('dt', class_='dnr_pro_list_structure')
            if structure_tag:
                img_tag = structure_tag.find('img')
                if img_tag:
                    img_src = img_tag.get('src', '')
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    compound_data['structure_image'] = img_src
            
            # 只添加包含有效信息的化合物
            if len(compound_data) > 2:
                compounds.append(compound_data)
        
        return compounds
    
    def scrape_page(self, page_num: int = 4) -> List[Dict]:
        """
        爬取指定页面
        
        Args:
            page_num: 页码
            
        Returns:
            化合物信息列表
        """
        url = f"{self.base_url}/NaturalProducts/endogenous-metabolites.html?page={page_num}"
        logging.info(f"开始爬取第 {page_num} 页")
        
        html = self.fetch_page(url)
        if not html:
            logging.error("获取页面内容失败")
            return []
        
        # 保存原始HTML用于调试
        filename = f'page_{page_num}_raw.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        logging.info(f"原始HTML已保存到 {filename}")
        
        compounds = self.parse_compounds(html)
        logging.info(f"从第 {page_num} 页提取到 {len(compounds)} 个化合物")
        
        return compounds
    
    def scrape_multiple_pages(self, start_page: int = 1, end_page: int = 4) -> List[Dict]:
        """
        爬取多个页面
        
        Args:
            start_page: 起始页码
            end_page: 结束页码
            
        Returns:
            所有化合物信息列表
        """
        all_compounds = []
        
        logging.info(f"开始批量爬取: 第 {start_page} 页到第 {end_page} 页")
        
        for page_num in range(start_page, end_page + 1):
            try:
                compounds = self.scrape_page(page_num)
                all_compounds.extend(compounds)
                
                # 每爬取一页后随机延迟
                if page_num < end_page:
                    self._random_delay()
                    
            except KeyboardInterrupt:
                logging.warning("用户中断爬取")
                break
                
            except Exception as e:
                logging.error(f"爬取第 {page_num} 页时出错: {e}")
                continue
        
        logging.info(f"批量爬取完成，共获取 {len(all_compounds)} 个化合物")
        return all_compounds
    
    def save_to_json(self, compounds: List[Dict], filename: str = 'compounds.json'):
        """保存为JSON格式"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(compounds, f, ensure_ascii=False, indent=2)
            logging.info(f"已保存到 {filename}")
        except Exception as e:
            logging.error(f"保存JSON失败: {e}")
    
    def save_to_csv(self, compounds: List[Dict], filename: str = 'compounds.csv'):
        """保存为CSV格式"""
        if not compounds:
            logging.warning("没有数据可保存")
            return
        
        try:
            df = pd.DataFrame(compounds)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logging.info(f"已保存到 {filename}")
        except Exception as e:
            logging.error(f"保存CSV失败: {e}")
    
    def save_to_excel(self, compounds: List[Dict], filename: str = 'compounds.xlsx'):
        """保存为Excel格式"""
        if not compounds:
            logging.warning("没有数据可保存")
            return
        
        try:
            df = pd.DataFrame(compounds)
            df.to_excel(filename, index=False, engine='openpyxl')
            logging.info(f"已保存到 {filename}")
        except Exception as e:
            logging.error(f"保存Excel失败: {e}")
    
    def get_statistics(self) -> Dict:
        """获取爬取统计信息"""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        return {
            'total_requests': self.request_count,
            'elapsed_time': f"{elapsed_time:.2f}秒",
            'average_rate': f"{self.request_count / elapsed_time:.2f}次/秒" if elapsed_time > 0 else "N/A"
        }


def check_robots_txt(base_url: str):
    """
    检查 robots.txt 文件
    
    Args:
        base_url: 网站基础URL
    """
    robots_url = f"{base_url}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            logging.info("=" * 60)
            logging.info("robots.txt 内容:")
            logging.info("=" * 60)
            print(response.text[:500])  # 显示前500字符
            logging.info("=" * 60)
        else:
            logging.warning(f"无法获取 robots.txt (状态码: {response.status_code})")
    except Exception as e:
        logging.error(f"检查 robots.txt 失败: {e}")


def main():
    """主函数"""
    logging.info("=" * 80)
    logging.info("MCE 化合物信息爬取工具")
    logging.info("=" * 80)
    
    # 1. 检查 robots.txt（可选，但建议）
    check_robots_txt("https://www.medchemexpress.cn")
    
    # 2. 初始化爬虫
    # delay_range: 请求间隔时间范围（秒）
    # max_retries: 失败重试次数
    scraper = MCECompoundScraper(
        delay_range=(30, 60),  # 每次请求间隔30-60秒
        max_retries=3         # 失败后最多重试3次
    )
    
    # 3. 选择爬取方式
    
    # 方式1: 爬取单个页面（推荐用于测试）
    logging.info("\n开始爬取第1页数据...")
    compounds = scraper.scrape_page(page_num=1)
    
    # 方式2: 爬取多个页面（谨慎使用）
    # logging.info("\n开始爬取多页数据...")
    # compounds = scraper.scrape_multiple_pages(start_page=1, end_page=2)
    
    # 4. 显示结果
    if compounds:
        logging.info(f"\n{'=' * 80}")
        logging.info(f"成功提取 {len(compounds)} 个化合物信息")
        logging.info(f"{'=' * 80}")
        
        logging.info("\n前3个化合物示例:")
        for i, compound in enumerate(compounds[:3], 1):
            logging.info(f"\n化合物 {i}:")
            for key, value in compound.items():
                # 描述字段太长，只显示前100个字符
                if key == 'description' and len(str(value)) > 100:
                    logging.info(f"  {key}: {value[:100]}...")
                else:
                    logging.info(f"  {key}: {value}")
        
        # 5. 保存数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scraper.save_to_json(compounds, f'mce_compounds_{timestamp}.json')
        scraper.save_to_csv(compounds, f'mce_compounds_{timestamp}.csv')
        
        # 如果安装了 openpyxl，也可以保存为 Excel
        try:
            scraper.save_to_excel(compounds, f'mce_compounds_{timestamp}.xlsx')
        except ImportError:
            logging.warning("提示: 安装 openpyxl 可以导出 Excel 格式 (pip install openpyxl)")
        
        # 6. 显示统计信息
        stats = scraper.get_statistics()
        logging.info(f"\n{'=' * 80}")
        logging.info("爬取统计信息:")
        logging.info(f"  总请求次数: {stats['total_requests']}")
        logging.info(f"  总耗时: {stats['elapsed_time']}")
        logging.info(f"  平均速度: {stats['average_rate']}")
        logging.info(f"{'=' * 80}")
        
    else:
        logging.error("\n未能提取到化合物信息")
        logging.info("\n可能的原因:")
        logging.info("1. 网络连接问题")
        logging.info("2. 网页结构发生变化")
        logging.info("3. 访问被限制（IP被封禁）")
        logging.info("4. 请求频率过快")
        logging.info("\n建议:")
        logging.info("1. 检查网络连接")
        logging.info("2. 查看保存的 HTML 文件分析网页结构")
        logging.info("3. 增加请求间隔时间")
        logging.info("4. 等待一段时间后重试")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("\n用户中断程序")
    except Exception as e:
        logging.error(f"\n程序异常: {e}", exc_info=True)
