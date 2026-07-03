# Inscura 的 Plex 元数据插件

语言： [English](../README.md) | **简体中文** | [日本語](README-ja.md) | [한국어](README-ko.md)

Inscura 是一个本地媒体库应用，可以整理影片信息、演员、分类、合集、封面和背景图等资料。Plex 负责播放和管理媒体库，但它自身并不知道 Inscura 已经整理好的这些数据。

这个插件用于把 Inscura 的本地接口服务接入 Plex。Plex 扫描影片时，插件会把标题、简介、发布日期、评分、类型、标签、合集、演员、导演、编剧、制片人、封面和背景图写入 Plex 元数据。

插件只读取 Inscura 的媒体库数据和库内生成的图片资源，不会下载、移动、重命名、删除或修改原始媒体文件。

## 当前能力

- 按 Plex 传入的真实文件路径和文件名优先匹配，减少因 Plex 标题被手动修改导致的误匹配。
- 找不到路径匹配时，会继续尝试编号、文件名中的识别码和 Plex 标题。
- 使用 Plex 传入的时长辅助评分，提高同名或相近文件的匹配准确性。
- 支持写入 Plex 可接收的电影元数据字段，包括标题、原始标题、排序标题、简介、标语、发布日期、年份、评分、内容分级、制作方、类型、国家、标签、合集、演员、导演、编剧、制片人、海报和背景图。
- Plex 元数据代理不能从元数据响应里创建预告片或花絮视频条目，所以 Inscura 中的预告片资源不会写入 Plex 的不支持字段。

## 开启 Inscura 本地接口服务

1. 打开 Inscura，并打开要同步到 Plex 的媒体库。
2. 进入设置中的API 接口服务设置，开启本地接口服务。
3. 鉴权方式建议保持令牌模式，并保存设置页显示的接口令牌。
4. 在 Plex 服务器所在设备上访问健康检查地址，确认服务可达。

示例：

```bash
curl "http://[ip]:28687/api/v1/health"
```

如果 Plex 和 Inscura 不在同一台机器上，插件里的服务地址不能填写 `127.0.0.1`，要填写运行 Inscura 的那台电脑在局域网中的地址，例如：

```text
http://[ip]:28687
```

本地接口服务会跟随当前媒体库生命周期运行：媒体库打开且服务已启用时监听端口，**媒体库锁定、关闭或应用退出时停止服务。**

## 插件文件

从 [GitHub](https://github.com/InscuraApp/inscura-plex-plugin/archive/refs/heads/main.zip) 或 [Releases](https://github.com/InscuraApp/inscura-plex-plugin/releases) 下载最新的插件 zip 文件

本仓库包含两个需要安装到 Plex 的文件：


| 文件                   | 放置位置                                                       | 用途                    |
| -------------------- | ---------------------------------------------------------- | --------------------- |
| `Inscura.bundle`     | /PlexMediaServer/AppData/Plex Media Server/Plug-ins        | 元数据代理，负责搜索、匹配和写入元数据   |
| `Inscura Scanner.py` | /PlexMediaServer/AppData/Plex Media Server/Scanners/Movies | 扫描影片文件，并把真实文件路径传给匹配流程 |


安装后，Plex 中应该能看到：

- 扫描器：`Inscura Scanner`
- 代理：`Inscura`



## Plex 数据目录

Plex 的实际目录会受套件来源、系统版本、卷名、容器映射和安装方式影响。下面列出的是常见位置；如果你的设备不一致，以 Plex 套件页面、容器映射或系统中的实际数据目录为准。

[如何找到 Plex 插件目录?](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/)

找到 Plex 数据目录后，本插件要放到：

```text
Plex 数据目录/Plug-ins/Inscura.bundle
Plex 数据目录/Scanners/Movies/Inscura Scanner.py
```



## 在 Plex 中启用插件

1. 进入 Plex 的资料库管理。
2. 编辑已有电影资料库。
3. 在高级设置中把扫描器改为 `Inscura Scanner`。
4. 把代理改为 `Inscura`。
5. 填写 Inscura 服务地址和接口令牌。
6. 保存设置。
7. 对资料库执行重新扫描。
8. 对已有影片执行重新匹配或刷新元数据，让 Plex 写入 Inscura 的匹配标识和元数据。



## 插件设置说明


| 设置            | 说明                                                                  |
| ------------- | ------------------------------------------------------------------- |
| Inscura 服务地址  | Inscura 本地接口服务地址。Plex 和 Inscura 不在同一台机器时必须填写局域网地址                   |
| Inscura 接口令牌  | 本地接口服务使用令牌鉴权时填写；如果 Inscura 设置为无鉴权，可以留空                              |
| 搜索结果数量        | 每次匹配时从 Inscura 请求的候选数量                                              |
| 自动匹配最低分       | 候选分数低于该值时，插件不会自动采用该候选                                               |
| 导入 Inscura 合集 | 关闭后，插件完全不改动 Plex 中已有的合集                                             |
| 替换 Plex 合集    | 仅在导入合集开启时生效。开启后清空 Plex 现有合集并写入 Inscura 的合集和系列；关闭后只追加 Inscura 的合集和系列 |


合集设置的组合规则：


| 导入 Inscura 合集 | 替换 Plex 合集 | 结果                          |
| ------------- | ---------- | --------------------------- |
| 关闭            | 关闭或开启      | 不写入合集，保留 Plex 现有合集          |
| 开启            | 关闭         | 追加 Inscura 合集和系列            |
| 开启            | 开启         | 用 Inscura 合集和系列替换 Plex 现有合集 |




## 使用建议

- 首次使用时，建议先选择少量影片重新匹配，确认标题、演员、封面和合集符合预期后，再批量刷新资料库。
- 如果 Plex 中影片标题曾被手动改过，插件仍会优先使用真实文件路径和文件名匹配，不依赖标题作为唯一依据。
- 如果 Inscura 服务地址或令牌修改过，需要在 Plex 插件设置中同步更新，然后刷新元数据。
- 如果 Inscura 媒体库被锁定或关闭，Plex 将无法读取元数据。



## 排查问题



### Plex 看不到 Inscura 代理或扫描器

1. 确认 `Inscura.bundle` 位于 `Plex 数据目录/Plug-ins/Inscura.bundle`。
2. 确认 `Inscura.bundle/Contents` 存在。
3. 确认 `Inscura Scanner.py` 位于 `Plex 数据目录/Scanners/Movies/Inscura Scanner.py`。
4. 确认 Plex 进程有读取这些文件的权限。
5. 重启 Plex 媒体服务器。
6. 重新打开 Plex 网页端，进入资料库高级设置检查。



### Plex 能看到插件，但没有元数据

1. 在 Plex 服务器所在设备上访问 Inscura 健康检查地址。
2. 确认 Inscura 媒体库已经打开，且本地接口服务处于开启状态。
3. 确认 Plex 插件里的服务地址不是错误的 `127.0.0.1`。
4. 如果接口使用令牌鉴权，确认 Plex 插件里填写了正确令牌。
5. 对影片执行重新匹配或刷新元数据。



### 封面或演员头像不显示

1. 确认 Plex 服务器能访问 Inscura 服务地址。
2. 如果接口使用令牌鉴权，确认插件令牌正确。
3. 确认 Inscura 中对应媒体或演员确实有可用图片资源。
4. 刷新该影片元数据。



## 升级插件

1. 停止或准备重启 Plex 媒体服务器。
2. 删除旧的 `Plex 数据目录/Plug-ins/Inscura.bundle`。
3. 复制新的 `Inscura.bundle` 到插件目录。
4. 覆盖 `Plex 数据目录/Scanners/Movies/Inscura Scanner.py`。
5. 修正权限。
6. 重启 Plex 媒体服务器。

升级后如果 Plex 网页端仍显示旧设置，先强制刷新浏览器页面，再重新打开资料库编辑窗口。
