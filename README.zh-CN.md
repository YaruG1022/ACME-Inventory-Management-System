# ACME 食品银行库存管理系统

[English](README.md) | **简体中文**

基于 Flask 的库存管理应用，用于记录捐赠的食品和卫生用品、接收方订单及库存报表。
项目最初为华盛顿州立大学（WSU）2021 年夏季 CPTS 322 课程作业。

## 系统概览

从[系统概览](docs/system-overview.zh-CN.md)开始，了解应用的用途、业务术语、主要流程、
系统结构和当前限制。概览为操作人员、项目相关方、测试、开发及维护人员提供专题文档入口。
图示采用 Mermaid，直接维护在 Markdown 文档中。

## 安装与启动

需要 Python 3.10 或更新版本。在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m flask --app acme_inventory init-db
python -m flask --app acme_inventory run
```

在 macOS/Linux 上，使用 `source .venv/bin/activate` 激活虚拟环境，使用
`cp .env.example .env` 复制配置。打开 http://127.0.0.1:5000 并注册本地账户。
程序不会自动创建默认账户或密码。

导入应用模块不会创建数据库表。`init-db` 用于初始化新数据库并执行版本化的结构升级。
已有安装应先停止服务器，再运行 `flask --app acme_inventory upgrade-db`。
SQLite 升级会在修改前，在数据库所在目录创建带时间戳的备份。
本地数据、密钥和上传文件存放在 Flask 的实例目录中，与应用包分离。
如需指定目录，可在 `.env` 中设置绝对路径形式的 `ACME_INSTANCE_PATH`。

## 功能

- 注册、登录、退出、个人资料与密码修改，以及基于身份验证器的双因素认证（2FA）。
- 商品唯一 SKU、别名、固定基础单位和最低库存阈值。
- 独立入库批次，记录来源、有效期、实物数量和预留数量。
- 订单可用库存预览、先到期先出（FEFO）分配、预留、取消和发放。
- 带操作记录的实盘调整、报损、隔离与解除隔离，以及库存流水查询。
- 低库存与有效期筛选，以及库存、订单、批次和流水的 CSV/XLSX 导出。

所有数量均为商品基础单位下的整数，系统不进行单位换算。
当前不包含库位管理、采购、需求预测或基于角色的权限控制。
所有注册用户拥有相同的业务操作权限，尚未实现 Agent 或模型训练。
开放注册用于课程及演示场景，公开部署前应重新审视这一访问方式。

## 导入旧版数据

先停止旧版应用并备份数据。导入前**不要**运行 `init-db`。
指定一个全新的实例目录，然后执行：

```powershell
python -m flask --app acme_inventory import-legacy --database src/data/inventory.db --images src/static/img
```

从其他工作副本导入时，请使用源文件的绝对路径。命令会复制数据库和可选的图片，
仅在副本中改写图片 URL，源文件保持不变；如果目标数据库已存在，导入会被拒绝。

用户、密码哈希和 2FA 密钥会保留。现有库存余额转换为期初批次；历史订单保留为只读的
`Legacy recorded` 记录，同时保存原状态，不会再次扣减历史库存。
用户需要重新登录。详情参见[开发与迁移说明（英文）](docs/development.md)。

## 项目结构

```text
src/acme_inventory/
  __init__.py       应用工厂
  config.py        运行配置
  extensions.py    共享 Flask 扩展
  cli.py           初始化、升级和旧版数据导入
  migrations.py    版本化 SQLite 结构与数据迁移
  models/          数据库模型映射
  routes/          HTTP 入口和访问检查
  services/        业务操作与集成
  templates/       按功能组织的页面和共享组件
  static/          共享 CSS、页面 JS 模块、内置图片
tests/             使用隔离数据的回归测试
docs/              系统概览、架构、数据模型、业务流程和开发说明
```

## 验证与部署

```powershell
python -m pytest
python -m ruff check src/acme_inventory tests
python -m build
```

开发时可通过 `flask run --debug` 显式启用调试模式。
旧的 `src/app.py`、`server.ini`、TLS 启动器及原型路由已停用。

部署时应使用生产级 WSGI 服务器加载 `acme_inventory:create_app()`，
由反向代理处理 HTTPS，配置稳定的 `ACME_SECRET_KEY`，并备份实例数据。
不要通过关闭防火墙来开放应用访问。

## 文档

目前提供本 README 和系统概览的简体中文版；其余专题文档仍为英文。
中英文版本通过页面顶部的链接切换。

- [系统概览与文档导航](docs/system-overview.zh-CN.md)
- [架构与命名（英文）](docs/architecture.md)
- [数据模型与兼容性（英文）](docs/data-model.md)
- [业务流程（英文）](docs/workflows.md)
- [开发与 API 变更（英文）](docs/development.md)

项目使用 [MIT 许可证](LICENSE.txt)。
