# L4D2 VPK Manager - 国际化 (i18n) 系统

## 概述

本项目采用 **ARB (Application Resource Bundle)** 文件格式进行国际化管理，参考 Flutter 的 i18n 实现方式。ARB 是 Google 开发的用于应用本地化的 JSON 扩展格式。

## 文件结构

```
assets/
└── i18n/
    ├── en.arb          # 英文翻译
    └── zh.arb          # 中文翻译

src/core/localization/
├── __init__.py         # 模块初始化
└── localizations.py    # 本地化管理器（Singleton）
```

## ARB 文件格式

ARB 文件是 JSON 格式，包含以下特点：

### 元数据（以 @@ 开头）
```json
{
  "@@locale": "en",              // 指定语言代码
  "@@author": "Team Name",       // 作者信息
  "@@version": "1.0.0"           // 版本号
}
```

### 翻译键值对
```json
{
  "appTitle": "L4D2 VPK Manager",
  "directoryPathLabel": "L4D2 directory path",
  "localVpkFiles": "Local VPK Files"
}
```

### 带参数的翻译
```json
{
  "error": "Error: {error}",
  "@error": {
    "placeholders": {
      "error": {
        "type": "String"
      }
    }
  },
  "fileSize": "{size} MB",
  "@fileSize": {
    "placeholders": {
      "size": {
        "type": "String"
      }
    }
  }
}
```

## 使用方法

### 1. 基本翻译

```python
from src.core.localization import localization

# 设置语言
localization.set_locale('zh')  # 切换到中文
localization.set_locale('en')  # 切换到英文

# 获取翻译
text = localization.t('appTitle')  # 返回对应语言的文本
```

### 2. 带参数的翻译

```python
# 在ARB文件中定义参数化翻译
# "error": "Error: {error}"

# 在代码中使用
error_text = localization.t('error', error='File not found')
# 返回: "Error: File not found"
```

### 3. 获取可用的语言列表

```python
locales = localization.get_available_locales()
# 返回: ['en', 'zh']
```

### 4. 在 Flet UI 中使用

```python
import flet as ft
from src.core.localization import localization

# 在 UI 组件中使用翻译
ft.TextField(label=localization.t('directoryPathLabel'))
ft.Text(localization.t('appTitle'))
ft.IconButton(tooltip=localization.t('browseFolder'))
```

## Localizations 类 API

### 方法列表

| 方法 | 说明 | 参数 | 返回值 |
|-----|-----|------|--------|
| `set_locale(locale)` | 设置当前语言 | locale: str | None |
| `get_locale()` | 获取当前语言 | - | str |
| `get_available_locales()` | 获取可用语言列表 | - | list |
| `translate(key, params)` | 翻译指定键 | key: str, params: Dict | str |
| `t(key, **kwargs)` | 翻译的简写形式 | key: str, **kwargs | str |
| `get_translation_dict(locale)` | 获取特定语言的所有翻译 | locale: str (可选) | Dict |
| `reload_translations()` | 重新加载翻译文件 | - | None |

## 添加新语言

### 步骤

1. 在 `assets/i18n/` 目录创建新的 ARB 文件（如 `es.arb` 用于西班牙语）
2. 复制其他 ARB 文件的键值对结构
3. 填入目标语言的翻译
4. 确保所有键都被翻译（为了一致性）
5. 重新启动应用或调用 `localization.reload_translations()`

### 示例

```json
// assets/i18n/es.arb
{
  "@@locale": "es",
  "@@author": "L4D2 VPK Manager Team",
  "appTitle": "Administrador de VPK de L4D2",
  "directoryPathLabel": "Ruta de directorio de L4D2",
  "browseFolder": "Examinar carpeta"
}
```

## 最佳实践

1. **保持一致性** - 确保所有 ARB 文件包含相同的键
2. **使用描述性的键** - 使用清晰的英文键名，便于理解
3. **参数化字符串** - 对于需要动态值的文本，使用 `{placeholder}` 格式
4. **注释和文档** - 在 ARB 文件中添加必要的注释说明
5. **版本控制** - 更新翻译时更新版本号

## 多语言应用切换

在 `src/app.py` 中初始化时设置默认语言：

```python
# 在 main() 函数中
localization.set_locale('zh')  # 默认中文
# 或根据系统语言自动设置
import locale as sys_locale
system_locale = sys_locale.getdefaultlocale()[0]
if system_locale.startswith('zh'):
    localization.set_locale('zh')
else:
    localization.set_locale('en')
```

## 参考

- [ARB 规范](https://github.com/google/app-resource-bundle/wiki)
- [Flutter i18n 最佳实践](https://flutter.dev/docs/development/accessibility-and-localization/internationalization)
