# MID 阅读器

一个使用 PyQt 和 PyQt-Fluent-Widgets 构建的现代 UI Python MIDI 文件阅读器应用。

## 功能

- MIDI 可视化,仿Synthesizer V Studio piano视图
- 针对不同轨道歌词内容的修改导出
- 响应式侧边栏界面，可根据窗口大小自动调整  
- 设置中可调整 UI 缩放倍率，适配不同的 DPI  
- 使用 PyQt-Fluent-Widgets 实现现代 Fluent 风格

## 安装

1. 克隆本仓库  
2. 安装依赖：
```
pip install -r requirements.txt
```
3. 运行应用：
```
python main.py
```

## 依赖

- Python 3.6+
- PyQt5
- PyQt-Fluent-Widgets
- mido（用于 MIDI 文件处理）

## 项目结构

- `main.py`: 应用入口  
- `app/`: 主应用包  
  - `view/`: 界面组件  
  - `core/`: MIDI 处理核心功能
  - `resources/`: 应用资源与本地化
- `demo_mid/`: 存放用于演示的mid文件
- `config/`: 存放软件设置
- `output/`: 存放输出的mid文件

## 编译

运行compile.bat
```