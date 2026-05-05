FROM node:22-alpine AS uibuild
WORKDIR /build
COPY frontend/package.json ./frontend/
WORKDIR /build/frontend
RUN npm install
COPY frontend/ ./
ENV NODE_ENV=production
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY mcp_server ./mcp_server
COPY knowledge ./knowledge
COPY scripts ./scripts
COPY --from=uibuild /build/app/static_ui ./app/static_ui

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
