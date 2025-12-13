# L4D2 VPK Manager - Flet MVVM 架构设计文档

## 架构概述

本项目采用 **分层 MVVM (Model-View-ViewModel)** 架构模式，根据功能的复杂度灵活选择架构层级：

- **简单功能**：仅需 Screen + ViewModel（如 VPK Manager）
- **复杂功能**：需要完整的 Screen + ViewModel + Service + Model 分层

### 核心架构目标

1. **灵活分层** - 根据功能复杂度选择合适的架构
2. **职责分离** - 清晰的代码职责划分
3. **可维护性** - 易于扩展和修改
4. **可测试性** - 各层之间低耦合

## 项目结构

```
src/
├── app.py                          # 应用入口和主UI
├── __init__.py                     # 包初始化
├── core/                           # 核心层
│   ├── services/                   # 共享服务接口和实现
│   │   ├── __init__.py
│   │   ├── i_*.py                  # 服务接口 (I前缀)
│   │   └── *.py                    # 服务实现
│   ├── viewmodels/                 # 基础和共享ViewModel
│   │   ├── __init__.py
│   │   ├── base_viewmodel.py       # ViewModel基类
│   │   └── app_viewmodel.py        # 应用全局ViewModel
│   ├── widgets/                    # 可复用UI组件
│   │   ├── __init__.py
│   │   └── *.py                    # 通用Widget
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py               # 日志工具
│   │   └── *.py                    # 其他工具
│   ├── di.py                       # 依赖注入容器
│   ├── routes.py                   # 路由配置（如需要）
│   └── theme.py                    # 主题配置
│
└── features/                       # 功能模块
    └── vpk_manager/               # VPK管理模块（简单功能示例）
        ├── screens/
        │   ├── __init__.py
        │   └── vpk_manager_screen.py    # UI屏幕
        └── viewmodels/
            ├── __init__.py
            └── vpk_manager_viewmodel.py # ViewModel（含数据模型和业务逻辑）
```

## 架构模式说明

### 模式 1：简单功能 - Screen + ViewModel

**适用场景**：功能简单，业务逻辑不复杂，无需多个服务

**结构**：
```
feature/
├── screens/
│   └── my_screen.py           # UI 层
└── viewmodels/
    └── my_viewmodel.py        # 状态管理 + 业务逻辑 + 数据模型
```

**示例 - VPK Manager**：

```python
# viewmodels/vpk_manager_viewmodel.py
from dataclasses import dataclass
from src.core.viewmodels.base_viewmodel import BaseViewModel

@dataclass
class VpkFile:
    """数据模型 - 定义在 ViewModel 中"""
    name: str
    path: str
    size: int
    modified_time: str
    is_valid: bool = True

class VpkManagerViewModel(BaseViewModel):
    """ViewModel - 包含状态、业务逻辑和数据访问"""
    
    def __init__(self):
        super().__init__()
        self._vpk_files: List[VpkFile] = []
        self._is_loading = False
        self._error_message: str = ''
    
    async def load_vpk_files(self, directory: str):
        """业务逻辑方法"""
        self._set_loading(True)
        try:
            self._vpk_files = self._get_vpk_files(directory)
        except Exception as e:
            self._error_message = str(e)
        finally:
            self._set_loading(False)
    
    def _get_vpk_files(self, directory: str) -> List[VpkFile]:
        """数据访问方法"""
        vpk_files = []
        path = Path(directory)
        
        for file_path in path.glob('*.vpk'):
            stat = file_path.stat()
            vpk_file = VpkFile(
                name=file_path.name,
                path=str(file_path),
                size=stat.st_size,
                modified_time=str(stat.st_mtime),
            )
            vpk_files.append(vpk_file)
        
        return vpk_files
```

**优点**：
- 代码少，结构清晰
- 快速开发和迭代
- 容易理解和维护

### 模式 2：复杂功能 - Screen + ViewModel + Service + Model（仅在需要时）

**适用场景**：功能复杂，需要多个服务、复杂的业务逻辑、需要高度可测试性

**结构**：
```
feature/
├── di/
│   └── feature_module.py      # DI 配置
├── models/
│   └── data_model.py          # 数据模型
├── screens/
│   └── feature_screen.py      # UI 层
├── services/
│   ├── i_service.py           # 服务接口
│   └── service_impl.py        # 服务实现
└── viewmodels/
    └── feature_viewmodel.py   # ViewModel
```

**职责划分**：
- **Screen**：仅负责 UI 渲染和用户交互
- **ViewModel**：状态管理，协调 Screen 和 Service
- **Service**：实现业务逻辑，数据访问，与外部系统交互
- **Model**：纯数据结构定义

## 迁移指南

### 从复杂到简单的重构步骤

1. **评估功能复杂度**
   - 仅 1-2 个相关的数据模型 → 可以简化
   - 业务逻辑简单（几个方法） → 可以简化
   - 无需复用的 Service → 可以简化

2. **合并 Model 和 Service 到 ViewModel**
   - 将数据模型 dataclass 复制到 ViewModel
   - 将 Service 的业务逻辑方法复制为 ViewModel 的私有方法
   - 移除依赖注入

3. **简化导入**
   - 移除 DI 配置文件
   - ViewModel 直接在 Screen 中初始化
   - 去掉复杂的导入链

4. **清理不再需要的文件**
   - 删除 `services/` 文件夹
   - 删除 `models/` 文件夹
   - 删除 `di/` 文件夹

## 代码示例对比

### 之前（复杂）

```python
# VpkManagerScreen 初始化
viewmodel = VpkManagerViewModel(
    vpk_service=VpkService()  # 依赖注入
)
screen = VpkManagerScreen(viewmodel)

# 文件结构
features/vpk_manager/
├── di/vpk_manager_module.py
├── models/vpk_file.py
├── services/
│   ├── i_vpk_service.py
│   └── vpk_service.py
├── screens/vpk_manager_screen.py
└── viewmodels/vpk_manager_viewmodel.py
```

### 之后（简化）

```python
# VpkManagerScreen 初始化
viewmodel = VpkManagerViewModel()  # 直接创建
screen = VpkManagerScreen(viewmodel)

# 文件结构
features/vpk_manager/
├── screens/vpk_manager_screen.py
└── viewmodels/vpk_manager_viewmodel.py
```

## 何时选择各种模式

| 因素 | 简单模式 | 复杂模式 |
|-----|---------|---------|
| 数据模型数量 | 1-2 个 | 3 个以上 |
| Service 数量 | 0-1 个 | 2 个以上 |
| 业务逻辑复杂度 | 低 | 高 |
| 代码行数 | 200-500 | 500+ |
| 可测试性要求 | 中等 | 高 |
| 代码复用需求 | 低 | 高 |
| 团队规模 | 小 | 大 |

## 最佳实践

1. **从简开始** - 先用简单模式，复杂时再重构
2. **明确职责** - 每一层只做一件事
3. **接口优先** - 复杂模式中一定要用接口（I 前缀）
4. **异步处理** - 耗时操作使用 async/await
5. **错误处理** - 始终有错误捕获和消息提示
6. **状态通知** - ViewModel 修改状态后调用 `notify_listeners()`

### 3. ViewModel 层（状态管理）

**职责**：管理UI状态、协调Model和Service、处理用户交互

```python
# src/core/viewmodels/base_viewmodel.py
class BaseViewModel:
    """ViewModel基类"""
    
    def __init__(self):
        self._listeners = set()
    
    def add_listener(self, callback):
        """添加监听者"""
        self._listeners.add(callback)
    
    def remove_listener(self, callback):
        """移除监听者"""
        self._listeners.discard(callback)
    
    def notify_listeners(self):
        """通知所有监听者"""
        for callback in self._listeners:
            callback()
    
    def dispose(self):
        """清理资源"""
        self._listeners.clear()


# features/vpk_manager/viewmodels/vpk_manager_viewmodel.py
import asyncio
from typing import List
from ..models.vpk_file import VpkFile
from ..services.i_vpk_service import IVpkService
from .....core.viewmodels.base_viewmodel import BaseViewModel
from .....core.utils.logger import TaggedLogger

class VpkManagerViewModel(BaseViewModel):
    """VPK管理器ViewModel"""
    
    def __init__(self, vpk_service: IVpkService):
        super().__init__()
        self._vpk_service = vpk_service
        self._logger = TaggedLogger('VpkManagerViewModel')
        
        # 状态管理
        self._vpk_files: List[VpkFile] = []
        self._is_loading = False
        self._error_message: str = ''
        self._selected_file: VpkFile = None
    
    # Getter 方法
    @property
    def vpk_files(self) -> List[VpkFile]:
        return self._vpk_files
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
    
    @property
    def has_error(self) -> bool:
        return len(self._error_message) > 0
    
    @property
    def error_message(self) -> str:
        return self._error_message
    
    @property
    def selected_file(self) -> VpkFile:
        return self._selected_file
    
    # 业务逻辑方法
    async def load_vpk_files(self, directory: str):
        """加载VPK文件列表"""
        self._set_loading(True)
        try:
            self._vpk_files = await self._vpk_service.get_vpk_files(directory)
            self._error_message = ''
            self._logger.debug(f'Loaded {len(self._vpk_files)} VPK files')
        except Exception as e:
            self._error_message = str(e)
            self._logger.error(f'Failed to load VPK files: {e}')
        finally:
            self._set_loading(False)
    
    async def select_file(self, file: VpkFile):
        """选择VPK文件"""
        self._selected_file = file
        self._logger.debug(f'Selected file: {file.name}')
        self.notify_listeners()
    
    async def extract_selected_file(self, output_dir: str) -> bool:
        """提取选中的VPK文件"""
        if not self._selected_file:
            self._error_message = 'No file selected'
            return False
        
        self._set_loading(True)
        try:
            success = await self._vpk_service.extract_vpk(
                self._selected_file.path, 
                output_dir
            )
            if success:
                self._error_message = ''
            else:
                self._error_message = 'Failed to extract VPK file'
            return success
        except Exception as e:
            self._error_message = str(e)
            self._logger.error(f'Error extracting VPK: {e}')
            return False
        finally:
            self._set_loading(False)
    
    def _set_loading(self, loading: bool):
        """设置加载状态"""
        self._is_loading = loading
        self.notify_listeners()
    
    def dispose(self):
        """清理资源"""
        super().dispose()
        self._vpk_files.clear()
        self._selected_file = None
```

**特点**：
- 继承基础ViewModel类
- 管理所有UI相关状态
- 通过Service处理业务逻辑
- 提供Getter方法供View查询状态
- 提供业务方法供View调用
- 通知观察者状态变更

### 4. View 层（用户界面）

**职责**：UI界面定义、事件处理、状态绑定

```python
# features/vpk_manager/screens/vpk_manager_screen.py
import flet as ft
from ..viewmodels.vpk_manager_viewmodel import VpkManagerViewModel
from ..widgets.vpk_list_widget import VpkListWidget
from .....core.utils.logger import TaggedLogger

class VpkManagerScreen:
    """VPK管理器屏幕"""
    
    def __init__(self, viewmodel: VpkManagerViewModel):
        self._viewmodel = viewmodel
        self._logger = TaggedLogger('VpkManagerScreen')
        self._viewmodel.add_listener(self._on_state_changed)
    
    def build(self) -> ft.Column:
        """构建UI"""
        return ft.Column([
            self._build_header(),
            self._build_content(),
            self._build_footer(),
        ])
    
    def _build_header(self) -> ft.Row:
        """构建头部"""
        return ft.Row([
            ft.Text('VPK Manager', size=24, weight='bold'),
        ])
    
    def _build_content(self) -> ft.Container:
        """构建内容区域"""
        if self._viewmodel.is_loading:
            return ft.Container(
                content=ft.ProgressRing(),
                alignment=ft.alignment.center,
            )
        
        if self._viewmodel.has_error:
            return ft.Container(
                content=ft.Text(
                    f'Error: {self._viewmodel.error_message}',
                    color='red'
                ),
                alignment=ft.alignment.center,
            )
        
        return VpkListWidget(
            vpk_files=self._viewmodel.vpk_files,
            on_select=self._on_file_select,
        ).build()
    
    def _build_footer(self) -> ft.Row:
        """构建底部"""
        return ft.Row([
            ft.ElevatedButton(
                'Extract',
                on_click=self._on_extract_click,
                disabled=self._viewmodel.selected_file is None,
            ),
        ])
    
    def _on_file_select(self, file):
        """处理文件选择"""
        import asyncio
        asyncio.run(self._viewmodel.select_file(file))
    
    def _on_extract_click(self, e):
        """处理提取按钮点击"""
        import asyncio
        asyncio.run(self._viewmodel.extract_selected_file('./output'))
    
    def _on_state_changed(self):
        """状态变更回调"""
        self._logger.debug('ViewModel state changed')
        # 在此处触发UI更新
    
    def dispose(self):
        """清理资源"""
        self._viewmodel.dispose()
```

**特点**：
- 仅包含UI定义和事件处理
- 通过ViewModel获取状态
- 通过ViewModel的方法处理用户交互
- 监听ViewModel状态变更并更新UI
- 不包含业务逻辑

### 5. Module 层（依赖注入）

**职责**：组织特性模块、初始化依赖、提供UI入口

```python
# features/vpk_manager/di/vpk_manager_module.py
from ..services.vpk_service import VpkService
from ..services.i_vpk_service import IVpkService
from ..viewmodels.vpk_manager_viewmodel import VpkManagerViewModel
from ..screens.vpk_manager_screen import VpkManagerScreen
from .....core.utils.logger import TaggedLogger

class VpkManagerModule:
    """VPK管理模块"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._logger = TaggedLogger('VpkManagerModule')
        
        # 初始化依赖
        self._vpk_service: IVpkService = VpkService()
        self._viewmodel = VpkManagerViewModel(self._vpk_service)
        
        self._initialized = True
        self._logger.debug('VpkManagerModule initialized')
    
    def provide_screen(self) -> VpkManagerScreen:
        """提供屏幕实例"""
        return VpkManagerScreen(self._viewmodel)
    
    def get_viewmodel(self) -> VpkManagerViewModel:
        """获取ViewModel"""
        return self._viewmodel
    
    def dispose(self):
        """清理资源"""
        self._viewmodel.dispose()
```

## 核心模式说明

### 观察者模式（Observer Pattern）

ViewModel 通过观察者模式通知 View 更新：

```python
# ViewModel中
def notify_listeners(self):
    for callback in self._listeners:
        callback()

# View中
viewmodel.add_listener(lambda: update_ui())
```

### 依赖注入（Dependency Injection）

通过构造函数注入依赖，便于测试和解耦：

```python
class VpkManagerViewModel(BaseViewModel):
    def __init__(self, vpk_service: IVpkService):  # 注入依赖
        self._vpk_service = vpk_service
```

### 单例模式（Singleton Pattern）

模块使用单例模式确保全应用唯一实例：

```python
class VpkManagerModule:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## 数据流向

```
User Interaction (点击、输入)
        ↓
    View (屏幕)
        ↓
ViewModel (处理交互)
        ↓
Service (业务逻辑)
        ↓
Model (数据处理)
        ↓
    (数据库/文件系统)
        ↓
    Model (返回数据)
        ↓
Service (处理结果)
        ↓
ViewModel (更新状态)
        ↓
notify_listeners()
        ↓
View (刷新UI)
        ↓
User (看到结果)
```

## 编码规范

### 命名约定

- **模块/功能**: `snake_case` (例: `vpk_manager`)
- **类名**: `PascalCase` (例: `VpkManagerViewModel`)
- **方法/函数**: `snake_case` (例: `load_vpk_files`)
- **常量**: `SCREAMING_SNAKE_CASE` (例: `DEFAULT_TIMEOUT`)
- **私有成员**: `_leading_underscore` (例: `_vpk_service`)
- **接口**: `IPascalCase` (例: `IVpkService`)

### 导入组织

```python
# 标准库
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

# 第三方库
import flet as ft

# 本地导入（相对路径）
from ..models.vpk_file import VpkFile
from .....core.utils.logger import TaggedLogger
```

### 类型注解

```python
# 使用类型注解提高代码可读性
def load_vpk_files(self, directory: str) -> List[VpkFile]:
    """加载VPK文件列表"""
    pass
```

## 扩展指南

### 添加新功能模块

1. 在 `features/` 下创建新目录 (例: `search`)
2. 创建模块结构:
   - `models/` - 数据模型
   - `services/` - 业务逻辑服务
   - `viewmodels/` - 状态管理
   - `screens/` - UI界面
   - `di/` - 模块DI配置

3. 在模块的 `di/module.py` 中实现Module类
4. 在主应用中注册模块

### 添加共享服务

1. 在 `core/services/` 中创建接口和实现
2. 在 `core/di.py` 中注册服务
3. 在需要的地方注入使用

### 添加UI组件

1. 在 `core/widgets/` 中创建可复用组件
2. 使用 Flet 的控制对象
3. 接受回调函数处理交互

## 测试策略

### 单元测试

```python
# tests/features/vpk_manager/test_vpk_service.py
import pytest
from src.features.vpk_manager.services.vpk_service import VpkService

@pytest.mark.asyncio
async def test_get_vpk_files():
    service = VpkService()
    files = await service.get_vpk_files('./test_data')
    assert len(files) > 0
```

### Mock和模拟

```python
from unittest.mock import Mock, AsyncMock

# Mock服务进行ViewModel测试
mock_service = Mock(spec=IVpkService)
mock_service.get_vpk_files = AsyncMock(return_value=[])

viewmodel = VpkManagerViewModel(mock_service)
```

## 最佳实践

1. **分离关注点** - 每个层只做自己的事情
2. **依赖倒置** - 依赖抽象而不是具体实现
3. **异步处理** - 耗时操作使用 async/await
4. **错误处理** - 完整的异常捕获和日志记录
5. **资源清理** - 及时调用 dispose 方法释放资源
6. **日志记录** - 使用 TaggedLogger 记录关键操作
7. **代码复用** - 提取共同逻辑到 core 层

## 相关文件

- [Logger 工具](./../../core/utils/logger.md) - 日志系统说明
- [DI 容器](./../../core/di.md) - 依赖注入说明
- [主题系统](./../../core/theme.md) - 主题配置说明

## 参考资源

本架构参考自 AllTheTools Flutter 应用的 MVVM 架构设计，并根据 Flet 框架的特性进行了适配。

---

**版本**: 1.0  
**最后更新**: 2025年12月13日
