import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from text_analyzer import TextAnalyzer
import os

# ページ設定
st.set_page_config(
    page_title="テキスト分析アプリ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        color: white;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #5a6fd8, #6a4190);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# アプリケーションの初期化
@st.cache_resource
def init_analyzer():
    return TextAnalyzer()

analyzer = init_analyzer()

# メインアプリケーション
def main():
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>📊 テキスト分析アプリ</h1>
        <p>テキストを入力またはファイルをアップロードして、詳細な分析結果を取得しましょう</p>
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバー
    st.sidebar.title("📝 入力方法")
    input_method = st.sidebar.radio(
        "入力方法を選択してください",
        ["テキスト入力", "ファイルアップロード"]
    )
    
    # テキスト入力
    if input_method == "テキスト入力":
        text_input = st.text_area(
            "分析したいテキストを入力してください",
            height=200,
            placeholder="ここにテキストを入力してください..."
        )
        
        if st.button("🔍 分析開始", type="primary"):
            if text_input.strip():
                with st.spinner("テキストを分析中..."):
                    results = analyzer.analyze_text(text_input)
                display_results(results)
            else:
                st.error("テキストを入力してください")
    
    # ファイルアップロード
    else:
        uploaded_file = st.file_uploader(
            "テキストファイルをアップロード",
            type=['txt'],
            help="テキストファイル（.txt）のみ対応しています"
        )
        
        if uploaded_file is not None:
            if st.button("📁 ファイル分析", type="primary"):
                with st.spinner("ファイルを分析中..."):
                    text_content = uploaded_file.read().decode('utf-8')
                    if text_content.strip():
                        results = analyzer.analyze_text(text_content)
                        display_results(results)
                    else:
                        st.error("ファイルが空です")

def display_results(results):
    st.success("✅ 分析完了！")
    
    # タブで結果を表示
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 基本統計", "🌍 言語検出", "💝 感情分析", 
        "📖 可読性", "📈 単語頻度", "📝 文の分析", "🔤 文字分析"
    ])
    
    # 基本統計
    with tab1:
        basic_stats = results['basic_stats']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("文字数", f"{basic_stats['character_count']:,}")
            st.metric("単語数", f"{basic_stats['word_count']:,}")
        
        with col2:
            st.metric("文の数", f"{basic_stats['sentence_count']:,}")
            st.metric("段落数", f"{basic_stats['paragraph_count']:,}")
        
        with col3:
            st.metric("平均単語数/文", f"{basic_stats['average_words_per_sentence']:.1f}")
            st.metric("平均文字数/単語", f"{basic_stats['average_characters_per_word']:.1f}")
    
    # 言語検出
    with tab2:
        lang = results['language_detection']
        st.info(f"🌍 検出された言語: **{lang['language_name']}** ({lang['language_code']})")
    
    # 感情分析
    with tab3:
        sentiment = results['sentiment_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            sentiment_color = "green" if sentiment['sentiment'] == 'ポジティブ' else "red" if sentiment['sentiment'] == 'ネガティブ' else "orange"
            st.metric("感情", sentiment['sentiment'], delta=f"{sentiment['polarity_percentage']}%")
            
            # 感情スコアのプログレスバー
            st.progress(sentiment['polarity_percentage'] / 100)
            st.caption(f"ポジティブ度: {sentiment['polarity_percentage']}%")
        
        with col2:
            st.metric("主観性", f"{(sentiment['subjectivity'] * 100):.1f}%")
            
            # 感情の円グラフ
            fig = go.Figure(data=[go.Pie(
                labels=['ポジティブ', 'ネガティブ', '中性'],
                values=[sentiment['polarity_percentage'], 100-sentiment['polarity_percentage'], 0],
                hole=0.3
            )])
            fig.update_layout(title="感情分布")
            st.plotly_chart(fig, use_container_width=True)
    
    # 可読性分析
    with tab4:
        readability = results['readability_score']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Flesch可読性スコア", f"{readability['flesch_score']:.1f}")
            st.metric("音節数", f"{readability['syllable_count']:,}")
        
        with col2:
            st.info(f"📖 可読性レベル: **{readability['readability_level']}**")
            
            # 可読性スコアのゲージ
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = readability['flesch_score'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "可読性スコア"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgray"},
                        {'range': [30, 70], 'color': "gray"},
                        {'range': [70, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
    
    # 単語頻度
    with tab5:
        word_freq = results['word_frequency']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("ユニーク単語数", f"{word_freq['unique_words']:,}")
            st.metric("分析対象単語数", f"{word_freq['total_words_analyzed']:,}")
        
        with col2:
            if word_freq['most_common_words']:
                # 上位10単語の棒グラフ
                top_words = word_freq['most_common_words'][:10]
                words, counts = zip(*top_words)
                
                fig = px.bar(
                    x=words, 
                    y=counts,
                    title="最も頻繁に使用される単語（上位10）",
                    labels={'x': '単語', 'y': '出現回数'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    # 文の分析
    with tab6:
        sentence_analysis = results['sentence_analysis']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("平均文の長さ", f"{sentence_analysis['average_sentence_length']:.1f} 単語")
        
        with col2:
            st.metric("最短文", f"{sentence_analysis['shortest_sentence']} 単語")
        
        with col3:
            st.metric("最長文", f"{sentence_analysis['longest_sentence']} 単語")
        
        # 文の長さ分布のヒストグラム
        if 'sentence_lengths' in sentence_analysis:
            fig = px.histogram(
                x=sentence_analysis['sentence_lengths'],
                title="文の長さ分布",
                labels={'x': '文の長さ（単語数）', 'y': '頻度'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 文字分析
    with tab7:
        char_analysis = results['character_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("総文字数", f"{char_analysis['total_letters']:,}")
            st.metric("ユニーク文字数", f"{char_analysis['unique_letters']:,}")
        
        with col2:
            if char_analysis['most_common_letters']:
                # 上位10文字の棒グラフ
                top_letters = char_analysis['most_common_letters'][:10]
                letters, counts = zip(*top_letters)
                
                fig = px.bar(
                    x=letters, 
                    y=counts,
                    title="最も頻繁に使用される文字（上位10）",
                    labels={'x': '文字', 'y': '出現回数'}
                )
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
