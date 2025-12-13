# GitHub Copilot 指南 - L4D2 VPK 管理器

## 项目概述
L4D2 VPK 管理器是一个基于 Flet 的 Python 应用程序，用于管理求生之路 2 (Left 4 Dead 2) 的 VPK（游戏包）文件。该项目采用简化的 MVVM 架构，并内置了使用 ARB 文件的国际化支持。

## 架构规则

### 文件结构
```
src/
  core/
    localization/         # 本地化系统（单例模式）
    widgets/             # 共享UI组件
    viewmodels/          # 基础 ViewModel 类
  features/
    vpk_manager/
      screens/           # UI 屏幕（仅用于简单功能）
      viewmodels/        # 状态管理和业务逻辑
      models/            # 数据模型（数据类）
  app.py                # 应用入口点
assets/
  i18n/                 # 国际化文件（ARB 格式）
    en.arb
    zh.arb
```

### 简单功能的 MVVM 模式
对于像 VPK 管理器这样的简单功能，仅使用两层：
- **Screen**（`screens/vpk_manager_screen.py`）：UI 层 - 渲染组件，处理用户交互
- **ViewModel**（`viewmodels/vpk_manager_viewmodel.py`）：状态和逻辑层 - 管理状态，加载数据，通知监听器

不要为简单功能创建单独的 Service 或 Model 文件夹。直接在 ViewModel 中使用数据类或内联方式处理数据模型。

### 复杂功能的 MVVM 模式
复杂功能应包括：
- **Screen**：UI 渲染和用户交互
- **ViewModel**：状态管理和功能编排
- **Service**：业务逻辑和外部集成
- **Model**：数据结构（数据类）

## 代码风格规则

### 导入语句
- 始终使用来自工作空间根目录的绝对导入
- 对于本地化：`from core.localization import localization`
- 不要使用相对导入，如 `from ..` 或 `from src.`
- 导入顺序：标准库 → 第三方 → 本地（使用 Pylint 顺序）

### 类和函数命名
- 类：PascalCase（例如 `VpkManagerScreen`、`VpkManagerViewModel`）
- 函数和方法：snake_case（例如 `build()`、`_on_folder_selected()`）
- 私有方法：前缀为 `_`（例如 `_on_state_changed()`）
- 私有属性：前缀为 `_`（例如 `self._page`、`self._viewmodel`）

### UI 组件创建
- 在 `build()` 方法中创建 UI 组件以支持动态本地化
- 对于需要更新的交互组件：将引用存储为实例变量（例如 `self._directory_input`）
- 对于应该直接编辑的输入字段使用 `read_only=True`
- 除非需要指定特定宽度/高度，否则始终为布局组件设置 `expand=True`

### 状态管理
- ViewModel 扩展 `BaseViewModel` 使用监听器模式
- 使用 `add_listener()` 和 `notify_listeners()` 进行响应式更新
- 将 UI 状态（如展开/折叠）存储在 Screen 中，而不是 ViewModel 中
- 将业务状态（数据、选择）存储在 ViewModel 中

## 国际化规则

### ARB 文件（`assets/i18n/`）
- 使用英文文件名：`en.arb`、`zh.arb`
- 结构：包含元数据（`@@locale`、`@@author`、`@@version`）和翻译键的 JSON
- 键：camelCase（例如 `directoryPathLabel`、`browseFolder`）
- 参数：使用花括号进行插值（例如 `"error": "Error: {message}"`）

### 翻译使用
- 始终使用 `localization.t('key')` 获取用户面向的字符串
- 传递参数：`localization.t('fileSize', size='100MB')`
- 在 `app.py` 中设置默认区域：`localization.set_locale('zh')`
- 本地化必须在构建 UI 组件之前初始化

### 支持的语言区域
- `en`：英文
- `zh`：简体中文（中文）

## 文件选择器和系统集成

### 文件选择器使用
- 使用 Flet 的 `ft.FilePicker` 来选择文件/文件夹
- 文件选择器回调同步运行
- 不要在文件选择器回调中使用 `asyncio.create_task()`
- 存储回调结果并同步更新状态

### 目录输入显示
- 当需要更新时，始终将 TextField 引用存储为实例变量
- 直接更新 TextField 值：`self._text_field.value = new_value`
- 在更改组件属性后调用 `self._page.update()`
- 永远不要依赖再次调用 `build()` 方法来更新现有组件

## Flet 特定规则

### Flutter 中常见的 API 差异
- TextField 参数：`read_only`（不是 `readonly`）
- Column 参数：使用 `Container` 包装器进行填充（不是直接填充）
- 无 `ExpansionTile`：为折叠部分使用 `Card` + 切换逻辑
- ScrollView：使用 `scroll=ft.ScrollMode.AUTO` 进行自动滚动
- 文件选择器：通过回调返回路径，而不是对话框

### 布局和样式
- 使用 `ft.Row` 和 `ft.Column` 进行布局
- 用 `ft.Container` 包装以进行填充和调整大小
- 使用 `expand=True` 填充可用空间
- 使用 `spacing=10` 保持项目间的一致间距
- 使用 `vertical_alignment=ft.CrossAxisAlignment.CENTER` 进行垂直居中

### 事件处理程序
- 将处理程序函数前缀为 `on_`（例如 `on_click`、`on_result`）
- 在方法中使用嵌套函数作为事件处理程序以访问 `self`
- 始终检查回调中的有效结果（例如 `if e.path:`）

## 调试和日志记录

### 控制台输出
- 使用 `print()` 进行调试日志记录
- 在日志消息中包含上下文：`print(f"method_name: action - result")`
- 示例：`print(f"_on_folder_selected: selected path={e.path}")`

### 启动配置
- VS Code 调试控制台：`launch.json` 中的 `internalConsole` 设置
- 从启动的应用程序输出的控制台输出进入 VS Code 调试控制台
- 使用 print 语句跟踪执行流程

### 应用启动规则
- 禁止在 agent 模式下运行应用
- **必须使用 launch.json 中配置的调试配置启动应用**
- 禁止使用终端命令直接启动应用（如 `python main.py` 或 `conda run -n flet-env python main.py`）
- 通过 VS Code 的"运行和调试"面板启动应用，或使用快捷键 `F5`
- 这确保了调试器正确附加，控制台输出正确定向到 VS Code 调试控制台

### Hot Reload 开发模式
- **推荐用于开发**：使用 `Flet Hot Reload Dev` 启动配置
- Hot reload 会监视当前目录及所有子目录中的文件变化（使用 `-d -r` 标志）
- 文件保存后应用会自动重新加载，无需手动重启
- 使用 `flet run -d -r main.py` 命令（通过启动配置或任务）
- 详见 [Flet 官方文档](https://flet.dev/docs/getting-started/running-app/#hot-reload)

## 依赖管理

### 必需的依赖项
- `flet==0.x.x`：GUI 框架
- `pydantic`：（可选）用于数据验证
- `python-dotenv`：（可选）用于环境配置

### 安装
- 使用 `conda` 进行环境管理
- 环境文件：`environment.yml`
- Python 包：`requirements.txt`
- 安装：在 conda 环境中运行 `pip install -r requirements.txt`

## 测试和验证

### 代码质量
- 使用 `pylint` 进行代码检查：`pylint main.py`
- 遵循 PEP 8 风格指南
- 为类和公共方法添加三引号文档字符串

### 手动测试清单
- [ ] 应用程序启动无错误
- [ ] 所有 UI 文本以正确的语言显示
- [ ] 文件选择器回调正常工作并更新 UI
- [ ] 可折叠部分正确切换
- [ ] 选择目录时 VPK 文件加载
- [ ] 无控制台错误或异常

## 版本控制

### Git 约定
- 分支命名：`feature/feature-name` 或 `fix/issue-name`
- 提交消息：现在时态，描述性强（例如 "Add i18n support for Chinese"）
- 避免提交：`__pycache__/`、`.venv/`、特定于环境的文件

## 常见问题和解决方案

### 本地化不工作
- **问题**：中文文本显示为乱码（乱码）
- **解决方案**：确保 ARB 文件采用 UTF-8 编码，并在 UI 创建前初始化本地化

### TextField 值不更新
- **问题**：用户选择文件夹，但路径未显示在输入中
- **解决方案**：将 TextField 引用存储在实例变量中并直接更新：`self._directory_input.value = path`

### 文件选择器回调未触发
- **问题**：文件夹选择对话框不触发回调
- **解决方案**：确保 FilePicker 已添加到页面覆盖层：`self._page.overlay.append(self._folder_picker)`

### 导入路径问题
- **问题**：重复的单例实例或导入错误
- **解决方案**：使用一致的绝对导入（没有 `from src.` 路径）

## 快速参考命令

```bash
# 激活 conda 环境
conda activate flet-env

# 运行应用程序
python main.py

# 或使用 conda
conda run -n flet-env python main.py

# 使用 Flet CLI 运行
flet run main.py -v

# 安装依赖
pip install -r requirements.txt

# 代码检查
pylint main.py
```

## 何时寻求人工帮助
- 重大架构变更
- 添加新功能层（Service/Model）
- 主要依赖更新
- 复杂的异步/等待模式
- 性能优化需求
