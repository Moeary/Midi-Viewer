@echo off

echo ===== MID Reader Compiler =====
echo 开始编译流程...

REM 启动 Conda base 环境
echo 正在激活 Conda base 环境...
CALL conda activate base
if %ERRORLEVEL% neq 0 (
    echo 错误：无法激活 Conda base 环境！
    echo 请确保已正确安装并初始化 Conda。
    pause
    exit /b 1
)

REM 检查 Python 是否可用
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：在激活的环境下未找到 Python！
    pause
    exit /b 1
)

REM 检查是否安装了 Nuitka
python -c "import nuitka" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 警告：未检测到 Nuitka。将尝试安装...
    conda install -c conda-forge nuitka -y
    if %ERRORLEVEL% neq 0 (
        echo 通过 Conda 安装 Nuitka 失败，尝试使用 pip...
        pip install nuitka
        if %ERRORLEVEL% neq 0 (
            echo 无法安装 Nuitka，编译过程中止。
            pause
            exit /b 1
        )
    )
)

REM 安装缺失的依赖项
echo 正在安装缺失的依赖项 backports.tarfile...
pip install backports.tarfile
if %ERRORLEVEL% neq 0 (
    echo 错误：无法安装 backports.tarfile！
    pause
    exit /b 1
)

echo 正在使用 Nuitka 编译应用...
echo 这可能需要数分钟时间，请耐心等待...

REM 创建日志目录
if not exist logs mkdir logs

REM 主编译命令 - 增强版本
python -m nuitka --onefile ^
    --enable-plugin=pyqt5 ^
    --include-package=mido ^
    --include-package=rtmidi ^
    --include-package=qfluentwidgets ^
    --include-package=PyQt5 ^
    --include-package=backports ^
    --include-package=backports.tarfile ^
    --include-package=datetime ^
    --include-package=ordered_set ^
    --include-data-dir=app/resource=app/resource ^
    --output-dir=build ^
    --windows-disable-console ^
    --python-flag=no_site ^
    --follow-imports ^
    --report=logs\compilation_report.xml ^
    --show-modules ^
    --include-module=backports.tarfile ^
    --disable-console ^
    --standalone ^
    --windows-icon-from-ico=icon.ico ^
    --lto=yes ^
    --windows-company-name="MIDI Reader" ^
    --windows-product-name="MIDI Reader" ^
    --windows-file-version="1.0.0.0" ^
    --windows-product-version="1.0.0" ^
    --nofollow-import-to=setuptools ^
    --nofollow-import-to=setuptools._vendor ^
    --nofollow-import-to=importlib_metadata ^
    --prefer-source-code ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo 编译过程中出现错误，错误码 %ERRORLEVEL%。
    echo 详细日志请查看 logs 目录。
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo 编译已成功完成！
echo 可执行文件位于 build 目录下。
echo.

pause