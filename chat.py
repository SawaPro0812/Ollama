from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # ダミー値でOK
)

response = client.chat.completions.create(
    model="hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M",
    messages=[
        {"role": "system", "content": "あなたは日本語の分析アシスタントです。"},
        {"role": "user", "content": "次のテキストを要約してキーワードを抽出してください: 人工知能は近年急速に発展しており、医療、教育、製造業など様々な分野で活用されています。"}
    ]
)
print(response.choices[0].message.content)
