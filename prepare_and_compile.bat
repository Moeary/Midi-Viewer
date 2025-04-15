@echo off

echo ===== MIDI Reader Build Preparation =====
echo 准备编译环境...

REM 启动 Conda base 环境
echo 正在激活 Conda base 环境...
CALL conda activate base

REM 安装必要的依赖
echo 正在安装必要的依赖...
pip install backports.tarfile
pip install ordered-set

REM 更新关键包
echo 更新关键包...
pip install --upgrade setuptools wheel pip

REM 运行编译脚本
echo 运行主编译脚本...
call compile.bat

echo 构建过程完成。
pause
