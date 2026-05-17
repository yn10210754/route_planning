#!/bin/bash

# 地图路线规划器一键启动脚本
# 同时启动后端（FastAPI）和前端（Vue3）

echo "🚀 正在启动地图路线规划器..."
echo ""

# 停止可能残留的进程
echo "🛑 停止旧服务..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1

# 启动后端
echo "📡 启动后端（端口 8000）..."
cd /Users/yay_mac/Documents/code/route_planning/backend
source .venv/bin/activate
GAODE_KEY=50884c91861276ae0744cd025ce771b4 uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
sleep 2

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端启动成功: http://localhost:8000"
else
    echo "❌ 后端启动失败，查看日志: tail -f /tmp/uvicorn.log"
    exit 1
fi

echo ""

# 启动前端
echo "🎨 启动前端（端口 5173）..."
cd /Users/yay_mac/Documents/code/route_planning/frontend
npm run dev -- --host > /tmp/vite.log 2>&1 &
sleep 3

# 检查前端是否启动成功
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "✅ 前端启动成功: http://localhost:5173"
else
    echo "❌ 前端启动失败，查看日志: tail -f /tmp/vite.log"
    exit 1
fi

echo ""
echo "========================================"
echo "🎉 服务全部启动成功！"
echo ""
echo "📱 电脑访问: http://localhost:5173"
echo "📱 手机访问: http://192.168.1.2:5173"
echo ""
echo "🛑 停止服务: sh stop.sh"
echo "========================================"
