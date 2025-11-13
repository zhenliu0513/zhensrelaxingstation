# 按摩店结账和日报系统

一个简单的 Web 应用，用于按摩店记录每日收款、客人数并导出 CSV。界面为中文，使用 Python + Flask + SQLite。

主要功能
- 当天记录页面（可选日期）: 保存刷卡金额、现金金额、客人数、备注
- 历史记录: 按日期查看、排序、按时间区间筛选
- 统计汇总: 在指定区间显示总刷卡、现金、总额、总客人数、平均每日收入与客人数
- 导出: 导出所有记录为 CSV（Excel 可打开）
- 首次运行自动建表（使用 data.db）

安装与运行（在支持 Python 的环境）
1. 克隆或把本项目文件复制到一个目录
2. 创建虚拟环境（可选）
   python -m venv venv
   source venv/bin/activate  # macOS / Linux
   venv\Scripts\activate     # Windows
3. 安装依赖
   pip install -r requirements.txt
4. 启动应用
   python app.py
5. 在浏览器中打开
   http://localhost:5000

文件说明
- app.py: Flask 应用入口，包含路由和视图逻辑
- db.py: SQLite 数据库操作（自动初始化表）
- templates/: HTML 模板（Jinja2，中文界面）
- static/style.css: 简单样式
- data.db: SQLite 数据库文件（首次运行自动创建）

注意
- 当前项目使用 Flask 内置开发服务器，仅用于开发或店铺内部小规模使用。如果需要公开访问，请部署到生产 WSGI（例如 gunicorn / uWSGI）并保护好 secret_key。
- 若需导入/备份数据，直接保存 data.db 或使用导出 CSV 功能。

欢迎根据你的店铺需要进一步定制（例如添加用户登录、每笔项目明细、按技师统计等）。