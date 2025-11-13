```markdown
# 按摩店线上结账与日报管理系统

这是一个为按摩店 / 足疗店设计的线上结账与日报管理 Web 应用（中文界面），主要特点：

- 支持在手机、平板、电脑浏览器中访问（响应式 UI，适配触控操作）
- 支持记录每笔服务：项目、时长、技师、刷卡、现金、客人数、备注
- 技师管理与业绩统计（按时间范围）
- 统计图表（Chart.js）
- 导出 CSV（可按筛选范围导出）
- 可选：自动备份到 Google Sheets
- 用户登录（Owner / Staff），默认会在首次运行创建 admin 账号

技术栈（推荐部署配置）：
- Python 3.10+
- Flask + SQLAlchemy + Flask-Login
- PostgreSQL（线上推荐）或 SQLite（本地/小规模使用）
- Chart.js 前端图表
- 可部署平台推荐：Render / Railway / Fly.io。本文以 Render（快速、支持 Postgres）为主要部署示例。

目录结构（重要文件）
- app.py - 应用入口
- models.py - SQLAlchemy 模型（users / therapists / records）
- auth.py - 登录登出路由
- views.py - 业务相关路由（记录、历史、统计、导出、技师管理、图表）
- sheets.py - 可选 Google Sheets 备份（可关闭）
- utils.py - 工具（创建默认 admin 等）
- templates/ - Jinja2 模板（中文界面）
- static/ - 静态文件（CSS）
- requirements.txt - 依赖
- Procfile - 用于 Gunicorn（部署）

快速开始（本地开发）
1. 克隆代码并进入目录
2. 创建并激活虚拟环境（可选）
   python -m venv venv
   source venv/bin/activate   # macOS / Linux
   venv\Scripts\activate      # Windows
3. 安装依赖
   pip install -r requirements.txt
4. 复制 .env.example 为 .env，并根据需要修改（至少修改 SECRET_KEY、DEFAULT_ADMIN_PASSWORD）
5. 启动（开发模式）
   export FLASK_ENV=development
   python app.py
   然后访问 http://localhost:5000
   默认会在第一次启动时创建一个管理员账户（来自 .env 中的 DEFAULT_ADMIN_USERNAME/DEFAULT_ADMIN_PASSWORD）

生产部署（推荐：Render + PostgreSQL）
下面以 Render 为例说明如何部署并获得固定 URL：

1) 在 Render 上注册并登录（https://render.com）

2) 创建 PostgreSQL 数据库（在 Render Dashboard -> New -> Database -> PostgreSQL）
   - 记下 DATABASE_URL（类似 postgresql://user:pass@host:port/dbname）

3) 新建 Web 服务（服务类型：Web Service）
   - 连接到你的 GitHub 仓库（将本项目推到 GitHub）
   - 在 Render 的服务设置里：
     - Build Command: pip install -r requirements.txt
     - Start Command: gunicorn app:app --workers 2 --threads 4
   - 添加环境变量（Environment -> Environment Variables）：
     - DATABASE_URL = (上一步的 PostgreSQL URL)
     - SECRET_KEY = (设置一个随机字符串)
     - DEFAULT_ADMIN_USERNAME = admin
     - DEFAULT_ADMIN_PASSWORD = (设置安全密码)
     - SHEETS_ENABLED = false  (如果不使用 Google Sheets)
   - 部署 -> Render 会构建并生成一个固定的 URL（例如 https://your-app.onrender.com）

注意：若使用 SQLite（data.db），请确保在 Render 上使用持久化存储或改为 PostgreSQL。

启用 Google Sheets 自动备份（可选）
1. 在 Google Cloud Console 创建一个 Service Account，并为其开启 Google Sheets API。
2. 创建服务账户密钥（JSON），下载并保存为 credentials.json。
3. 在目标 Google Sheet 中，点击「共享」，将服务账户的 client_email（在 JSON 中）添加为编辑者。
4. 将密钥上传到部署平台：
   - Render: 在 Environment -> Files（或将 JSON 内容作为环境变量）
   - 可将 JSON 内容放到环境变量 GOOGLE_SERVICE_ACCOUNT_INFO（请将 JSON 字符串放入该变量）
   - 或上传文件并设置 GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json（并将文件包含在部署）
5. 设置环境变量：
   - SHEETS_ENABLED=true
   - SHEET_ID=（你的 Google Sheet ID，见 URL 的 /d/ID/ 部分）
   - SHEET_NAME=Sheet1

安全与账户
- 默认管理员用户名和密码来自 .env（DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD）。
- 强烈建议部署后立即修改管理员密码或在环境变量中设置新的密码。
- 密码使用 bcrypt 加密存储。

数据库迁移与结构（已实现）
Models:
- users
  - id, username, password_hash, role, created_at
- therapists
  - id, name, status, commission_rate, created_at, updated_at
- records
  - id, date, datetime_created, card_amount, cash_amount, total_amount, customer_count, note, service_type, duration, therapist_id, created_at, updated_at

初始化：
- app.py 在首次运行时会调用 db.create_all() 并创建默认管理员（适合小型项目）。如果需要在更大项目上使用，请改用 Flask-Migrate/ Alembic 并在部署时执行迁移。

主要功能说明（使用说明）
1. 登录后可看到「当天记录」页面（首页），输入服务项目、时长、技师、刷卡、现金、客人数、备注并保存。
2. 历史记录页面支持按日期范围、项目、技师筛选、分页并导出 CSV。
3. 统计页面可选择区间（本周/本月/自定义），展示总刷卡、总现金、总营业额、总客数、平均每日收入与客数，并显示图表：
   - 收入折线图（每日）
   - 服务项目收入柱状图
   - 技师营业额柱状图
4. 技师管理：新增/编辑技师及其状态、提成比例（示例）。
5. 导出 CSV 支持导出当前筛选区间（包含服务、时长、技师、金额等字段）。
6. 可选 Google Sheets 自动备份：每新增一条记录，会把此条记录追加到指定的 Google Sheet（需在环境变量配置凭据与 SHEET_ID）。

如何修改默认管理员密码
- 修改 .env 中 DEFAULT_ADMIN_PASSWORD，然后重启应用。首次运行应用会创建默认管理员，若你已经创建过管理员，需手动在数据库中修改或添加新用户（可通过 SQL 或临时扩展管理界面）。

后续扩展建议
- 添加用户管理界面（新增、修改员工登录）
- 添加按技师导出、按日期打印友好页面（用于打印日报）
- 添加每笔订单的消费明细（若店内需要分拆多项收费）
- 使用 Flask-Migrate 进行版本化迁移（更适合生产）

---

如果你希望我：
- 把这个完整项目打包成一个可直接推到 GitHub 的仓库（我会生成所有文件内容）；
- 或者我可以把部署到 Render 的具体步骤写成逐步截图 / 自动化 Render 的 render.yaml；
告诉我你的偏好，我会继续把剩余文件（如果你还需要 Dockerfile、render.yaml 或 CI）补全并引导你完成上线。
```
