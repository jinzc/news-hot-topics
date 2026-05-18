# 🔥 资讯热榜

聚合微博、知乎、百度、抖音、B站、IT之家等平台热点资讯。

## 访问地址
https://你的用户名.gitee.io/news-hot-topics/

## 更新频率
- **7:00-23:00**：每小时整点更新
- **23:00-次日6:00**：合并至次日6:00统一更新

## 技术栈
- 前端：纯 HTML/CSS/JS（无需构建）
- 后端：Python3 爬虫（标准库，无额外依赖）
- 部署：Gitee Pages + Gitee Actions

## 部署步骤

### 1. 创建 Gitee 仓库
- 仓库名：`news-hot-topics`
- 设置为**公开**（Gitee Pages 需要）

### 2. 上传代码
将所有文件上传到仓库根目录，确保结构如下：
```
news-hot-topics/
├── .gitee/workflows/
│   └── update.yml      # 自动更新配置
├── data/
│   └── hot_topics.json  # 初始数据文件
├── scripts/
│   └── fetch_hot_topics.py  # 爬虫脚本
├── index.html           # 前端页面
├── .gitignore
└── README.md
```

### 3. 开启 Gitee Pages
- 仓库 → 服务 → Gitee Pages
- 选择分支 `master` 或 `main`，目录 `/`
- 点击启动，等待生成访问链接

### 4. 配置自动更新
- 确保 Gitee Actions 已启用（仓库设置 → 功能管理）
- 进入 Actions 页面，手动运行一次测试
- 检查 `data/hot_topics.json` 是否被更新

### 5. 刷新 Pages
- Gitee Pages 有缓存，数据更新后可能需要手动刷新
- 在 Gitee Pages 设置页点击"更新"按钮

## 常见问题

### Q: 页面显示"数据加载失败"
A: 检查 `data/hot_topics.json` 是否存在。首次部署时需要手动上传初始数据文件，然后运行一次 Actions。

### Q: Actions 运行失败
A: 查看 Actions 日志，常见原因：
- 平台反爬：多试几次，或更换 User-Agent
- 网络超时：Gitee 服务器访问某些平台可能受限
- 权限问题：确保 Actions 有写入仓库的权限

### Q: 数据更新了但页面没变化
A: Gitee Pages 有缓存机制，需要：
1. 在 Gitee Pages 设置页点击"更新"按钮
2. 或等待 5-10 分钟自动刷新
3. 浏览器强制刷新（Ctrl+F5 或 Cmd+Shift+R）

## 免责声明
本项目仅供学习交流使用，所有数据来源于各平台公开接口，版权归原平台所有。如有侵权或违规，请联系删除。
