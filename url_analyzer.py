import requests
from bs4 import BeautifulSoup
import re
import streamlit as st
from urllib.parse import urlparse
import time

class URLAnalyzer:
    """URLからテキストを取得・分析するクラス"""
    
    def __init__(self):
        """初期化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def validate_url(self, url):
        """URLの妥当性をチェック"""
        try:
            # URLスキームがない場合はhttp://を追加
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # URLの形式をチェック
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "無効なURL形式です"
            
            return True, url
        except Exception as e:
            return False, f"URLの検証中にエラーが発生しました: {str(e)}"
    
    def extract_text_from_url(self, url):
        """URLからテキストを抽出"""
        try:
            # URLの妥当性をチェック
            is_valid, result = self.validate_url(url)
            if not is_valid:
                return False, result
            
            url = result
            
            # ページを取得
            with st.spinner("URLからテキストを取得中..."):
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
            
            # HTMLを解析
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 不要な要素を削除
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # メインコンテンツを抽出
            main_content = ""
            
            # メインタグを探す
            main_tag = soup.find('main')
            if main_tag:
                main_content = main_tag.get_text(separator=' ', strip=True)
            else:
                # メインタグがない場合はarticleタグを探す
                article_tags = soup.find_all('article')
                if article_tags:
                    for article in article_tags:
                        main_content += article.get_text(separator=' ', strip=True) + " "
                else:
                    # それもない場合はbody全体から抽出
                    body = soup.find('body')
                    if body:
                        main_content = body.get_text(separator=' ', strip=True)
                    else:
                        main_content = soup.get_text(separator=' ', strip=True)
            
            # テキストのクリーニング
            cleaned_text = self.clean_text(main_content)
            
            if not cleaned_text.strip():
                return False, "ページからテキストを抽出できませんでした"
            
            return True, cleaned_text
            
        except requests.exceptions.RequestException as e:
            return False, f"URLへのアクセスに失敗しました: {str(e)}"
        except Exception as e:
            return False, f"テキスト抽出中にエラーが発生しました: {str(e)}"
    
    def clean_text(self, text):
        """テキストをクリーニング"""
        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text)
        
        # 改行を適切に処理
        text = re.sub(r'\n+', '\n', text)
        
        # 特殊文字を削除
        text = re.sub(r'[^\w\s\.,!?;:()\[\]{}"\'-]', '', text)
        
        # 先頭と末尾の空白を削除
        text = text.strip()
        
        return text
    
    def get_page_info(self, url):
        """ページの基本情報を取得"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # タイトルを取得
            title = soup.find('title')
            title_text = title.get_text() if title else "タイトルなし"
            
            # メタディスクリプションを取得
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content') if meta_desc else ""
            
            # 文字数を取得
            text = soup.get_text(separator=' ', strip=True)
            char_count = len(text)
            
            return {
                'title': title_text,
                'description': description,
                'char_count': char_count,
                'url': url
            }
            
        except Exception as e:
            return {
                'title': "情報取得エラー",
                'description': f"エラー: {str(e)}",
                'char_count': 0,
                'url': url
            }
