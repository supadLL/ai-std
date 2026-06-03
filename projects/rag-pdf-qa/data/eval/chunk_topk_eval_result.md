# chunk / top_k 参数评估结果

- 数据集：guiagent_pdf_rag_eval 0.1.0
- 来源文件：D:\ll-work\ai-play\dive-into-llms\documents\chapter9\GUIagent.pdf
- embedding：BAAI/bge-small-zh-v1.5
- 低分噪声阈值：score < 0.45
- 推荐参数：chunk_size=800，overlap=100，top_k=5

| chunk_size | overlap | top_k | chunk_count | hit_rate | page_hit_rate | keyword_hit_rate | low_score_count | 稳定性 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 500 | 80 | 3 | 43 | 1.0000 | 0.7143 | 1.0000 | 0 | 检索依据稳定，适合作为 RAG 回答输入。 |
| 500 | 80 | 5 | 43 | 1.0000 | 0.8571 | 1.0000 | 0 | 检索依据稳定，适合作为 RAG 回答输入。 |
| 800 | 100 | 3 | 43 | 1.0000 | 0.7143 | 1.0000 | 0 | 检索依据稳定，适合作为 RAG 回答输入。 |
| 800 | 100 | 5 | 43 | 1.0000 | 0.8571 | 1.0000 | 0 | 检索依据稳定，适合作为 RAG 回答输入。 |
| 1000 | 150 | 3 | 43 | 1.0000 | 0.7143 | 1.0000 | 0 | 检索依据稳定，适合作为 RAG 回答输入。 |
| 1000 | 150 | 5 | 43 | 1.0000 | 0.8571 | 1.0000 | 0 | 检索依据稳定，适合作为 RAG 回答输入。 |

## 说明

本评估只调用本地 embedding 和本地 Qdrant，不调用 DeepSeek。
回答稳定性是基于检索命中稳定性推断的前置指标。
