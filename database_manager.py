import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
import streamlit as st

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path="text_analysis.db"):
        """初期化"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 分析結果テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                text_content TEXT,
                text_length INTEGER,
                analysis_type TEXT,
                basic_stats TEXT,
                language_detection TEXT,
                sentiment_analysis TEXT,
                readability_score TEXT,
                word_frequency TEXT,
                sentence_analysis TEXT,
                character_analysis TEXT,
                file_name TEXT,
                file_size INTEGER
            )
        ''')
        
        # 統計情報テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_analyses INTEGER,
                avg_text_length REAL,
                most_common_language TEXT,
                avg_sentiment_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_analysis_result(self, text_content, results, file_name=None, file_size=None):
        """分析結果をデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_length = len(text_content)
        
        cursor.execute('''
            INSERT INTO analysis_results (
                timestamp, text_content, text_length, analysis_type,
                basic_stats, language_detection, sentiment_analysis,
                readability_score, word_frequency, sentence_analysis,
                character_analysis, file_name, file_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, text_content, text_length, "comprehensive",
            json.dumps(results['basic_stats']),
            json.dumps(results['language_detection']),
            json.dumps(results['sentiment_analysis']),
            json.dumps(results['readability_score']),
            json.dumps(results['word_frequency']),
            json.dumps(results['sentence_analysis']),
            json.dumps(results['character_analysis']),
            file_name, file_size
        ))
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid
    
    def get_all_analyses(self):
        """すべての分析結果を取得"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT id, timestamp, text_content, text_length, file_name,
                   basic_stats, language_detection, sentiment_analysis,
                   readability_score, word_frequency, sentence_analysis,
                   character_analysis
            FROM analysis_results
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # JSON文字列を辞書に変換
        for col in ['basic_stats', 'language_detection', 'sentiment_analysis',
                   'readability_score', 'word_frequency', 'sentence_analysis',
                   'character_analysis']:
            df[col] = df[col].apply(lambda x: json.loads(x) if pd.notna(x) else {})
        
        return df
    
    def get_analysis_by_id(self, analysis_id):
        """特定の分析結果を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analysis_results WHERE id = ?
        ''', (analysis_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # 結果を辞書形式に変換
            columns = [description[0] for description in cursor.description]
            analysis_dict = dict(zip(columns, result))
            
            # JSON文字列を辞書に変換
            for col in ['basic_stats', 'language_detection', 'sentiment_analysis',
                       'readability_score', 'word_frequency', 'sentence_analysis',
                       'character_analysis']:
                if analysis_dict[col]:
                    analysis_dict[col] = json.loads(analysis_dict[col])
            
            return analysis_dict
        
        return None
    
    def delete_analysis(self, analysis_id):
        """分析結果を削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analysis_results WHERE id = ?', (analysis_id,))
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def export_to_csv(self, analysis_ids=None):
        """分析結果をCSVファイルにエクスポート"""
        if analysis_ids:
            # 特定の分析結果のみエクスポート
            conn = sqlite3.connect(self.db_path)
            placeholders = ','.join(['?' for _ in analysis_ids])
            query = f'''
                SELECT id, timestamp, text_content, text_length, file_name,
                       basic_stats, language_detection, sentiment_analysis,
                       readability_score, word_frequency, sentence_analysis,
                       character_analysis
                FROM analysis_results
                WHERE id IN ({placeholders})
                ORDER BY timestamp DESC
            '''
            df = pd.read_sql_query(query, conn, params=analysis_ids)
            conn.close()
        else:
            # すべての分析結果をエクスポート
            df = self.get_all_analyses()
        
        # 分析結果をフラット化
        export_data = []
        for _, row in df.iterrows():
            basic_stats = row['basic_stats']
            sentiment = row['sentiment_analysis']
            language = row['language_detection']
            
            export_row = {
                'ID': row['id'],
                'タイムスタンプ': row['timestamp'],
                'ファイル名': row['file_name'] or 'テキスト入力',
                '文字数': row['text_length'],
                '言語': language.get('language_name', ''),
                '感情': sentiment.get('sentiment', ''),
                'ポジティブ度': sentiment.get('polarity_percentage', 0),
                '主観性': sentiment.get('subjectivity', 0),
                '単語数': basic_stats.get('word_count', 0),
                '文の数': basic_stats.get('sentence_count', 0),
                '段落数': basic_stats.get('paragraph_count', 0),
                '平均単語数/文': basic_stats.get('average_words_per_sentence', 0),
                '平均文字数/単語': basic_stats.get('average_characters_per_word', 0)
            }
            export_data.append(export_row)
        
        return pd.DataFrame(export_data)
    
    def export_to_txt(self, analysis_ids=None):
        """分析結果をTXTファイルにエクスポート"""
        if analysis_ids:
            analyses = [self.get_analysis_by_id(id) for id in analysis_ids]
        else:
            df = self.get_all_analyses()
            analyses = []
            for _, row in df.iterrows():
                analysis = {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'text_content': row['text_content'],
                    'file_name': row['file_name'],
                    'basic_stats': row['basic_stats'],
                    'language_detection': row['language_detection'],
                    'sentiment_analysis': row['sentiment_analysis'],
                    'readability_score': row['readability_score'],
                    'word_frequency': row['word_frequency'],
                    'sentence_analysis': row['sentence_analysis'],
                    'character_analysis': row['character_analysis']
                }
                analyses.append(analysis)
        
        txt_content = "=== テキスト分析結果 ===\n\n"
        
        for analysis in analyses:
            txt_content += f"分析ID: {analysis['id']}\n"
            txt_content += f"タイムスタンプ: {analysis['timestamp']}\n"
            txt_content += f"ファイル名: {analysis['file_name'] or 'テキスト入力'}\n"
            txt_content += f"テキスト長: {len(analysis['text_content'])} 文字\n\n"
            
            # 基本統計
            basic_stats = analysis['basic_stats']
            txt_content += "【基本統計】\n"
            txt_content += f"文字数: {basic_stats.get('character_count', 0)}\n"
            txt_content += f"単語数: {basic_stats.get('word_count', 0)}\n"
            txt_content += f"文の数: {basic_stats.get('sentence_count', 0)}\n"
            txt_content += f"段落数: {basic_stats.get('paragraph_count', 0)}\n"
            txt_content += f"平均単語数/文: {basic_stats.get('average_words_per_sentence', 0):.1f}\n"
            txt_content += f"平均文字数/単語: {basic_stats.get('average_characters_per_word', 0):.1f}\n\n"
            
            # 言語検出
            language = analysis['language_detection']
            txt_content += "【言語検出】\n"
            txt_content += f"言語: {language.get('language_name', '')} ({language.get('language_code', '')})\n\n"
            
            # 感情分析
            sentiment = analysis['sentiment_analysis']
            txt_content += "【感情分析】\n"
            txt_content += f"感情: {sentiment.get('sentiment', '')}\n"
            txt_content += f"ポジティブ度: {sentiment.get('polarity_percentage', 0)}%\n"
            txt_content += f"主観性: {sentiment.get('subjectivity', 0):.3f}\n\n"
            
            # 可読性分析
            readability = analysis['readability_score']
            txt_content += "【可読性分析】\n"
            txt_content += f"Flesch可読性スコア: {readability.get('flesch_score', 0):.1f}\n"
            txt_content += f"可読性レベル: {readability.get('readability_level', '')}\n"
            txt_content += f"音節数: {readability.get('syllable_count', 0)}\n\n"
            
            # 単語頻度
            word_freq = analysis['word_frequency']
            txt_content += "【単語頻度分析】\n"
            txt_content += f"ユニーク単語数: {word_freq.get('unique_words', 0)}\n"
            txt_content += f"分析対象単語数: {word_freq.get('total_words_analyzed', 0)}\n"
            
            if word_freq.get('most_common_words'):
                txt_content += "最も頻繁に使用される単語:\n"
                for word, count in word_freq['most_common_words'][:10]:
                    txt_content += f"  {word}: {count}回\n"
            txt_content += "\n"
            
            # 文の分析
            sentence = analysis['sentence_analysis']
            txt_content += "【文の分析】\n"
            txt_content += f"平均文の長さ: {sentence.get('average_sentence_length', 0):.1f} 単語\n"
            txt_content += f"最短文: {sentence.get('shortest_sentence', 0)} 単語\n"
            txt_content += f"最長文: {sentence.get('longest_sentence', 0)} 単語\n\n"
            
            # 文字分析
            char = analysis['character_analysis']
            txt_content += "【文字分析】\n"
            txt_content += f"総文字数: {char.get('total_letters', 0)}\n"
            txt_content += f"ユニーク文字数: {char.get('unique_letters', 0)}\n"
            
            if char.get('most_common_letters'):
                txt_content += "最も頻繁に使用される文字:\n"
                for letter, count in char['most_common_letters'][:10]:
                    txt_content += f"  {letter}: {count}回\n"
            txt_content += "\n"
            
            txt_content += "=" * 50 + "\n\n"
        
        return txt_content
    
    def get_statistics(self):
        """統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 総分析数
        cursor.execute('SELECT COUNT(*) FROM analysis_results')
        total_analyses = cursor.fetchone()[0]
        
        # 平均テキスト長
        cursor.execute('SELECT AVG(text_length) FROM analysis_results')
        avg_text_length = cursor.fetchone()[0] or 0
        
        # 最も一般的な言語
        cursor.execute('''
            SELECT language_detection, COUNT(*) as count
            FROM analysis_results
            GROUP BY language_detection
            ORDER BY count DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        most_common_language = "不明"
        if result and result[0]:
            try:
                lang_data = json.loads(result[0])
                most_common_language = lang_data.get('language_name', '不明')
            except:
                pass
        
        # 平均感情スコア
        cursor.execute('''
            SELECT AVG(CAST(
                json_extract(sentiment_analysis, '$.polarity_percentage') AS REAL
            )) FROM analysis_results
        ''')
        avg_sentiment_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_analyses': total_analyses,
            'avg_text_length': round(avg_text_length, 1),
            'most_common_language': most_common_language,
            'avg_sentiment_score': round(avg_sentiment_score, 1)
        }
