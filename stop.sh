#!/bin/bash

echo "🛑 正在停止服务..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
echo "✅ 服务已停止"
