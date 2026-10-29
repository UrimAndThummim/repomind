FROM python:3.12-slim

WORKDIR /app

# 先复制依赖描述，利用 Docker 层缓存
COPY pyproject.toml README.md ./
COPY repomind ./repomind

RUN pip install --no-cache-dir .

EXPOSE 8501

CMD ["streamlit", "run", "repomind/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
