# 🔥 资讯热榜

聚合微博、知乎、百度、抖音、B站、IT之家等平台热点资讯。

## 访问地址
- GitHub Pages: https://jinzc.github.io/news-hot-topics/
- Gitee Pages: https://jinzc.gitee.io/news-hot-topics/

## 更新频率
- **7:00-23:00**：每小时整点更新
- **23:00-次日6:00**：合并至次日6:00统一更新

## 技术栈
- 前端：纯 HTML/CSS/JS（无需构建）
- 后端：Python3 爬虫（标准库，无额外依赖）
- 部署：GitHub Actions 自动更新 + Gitee Pages 国内访问

## 部署步骤

### 1. GitHub 仓库设置
- 创建仓库 `news-hot-topics`
- 上传所有代码（保持文件夹结构）
- 开启 GitHub Actions（自动开启）

### 2. Gitee 镜像设置
- 在 Gitee 创建同名仓库
- 设置镜像：GitHub → Gitee（拉取）
- 开启自动同步

### 3. Gitee Pages
- 仓库 → 服务 → Gitee Pages
- 选择分支 `main`，目录 `/`
- 点击启动

## 文件结构
```
news-hot-topics/
├── .github/workflows/
│   └── update.yml          # GitHub Actions 配置
├── data/
│   └── hot_topics.json     # 热榜数据
├── scripts/
│   └── fetch_hot_topics.py # 爬虫脚本
├── index.html              # 前端页面
├── .gitignore
└── README.md
```

## 免责声明
本项目仅供学习交流使用，所有数据来源于各平台公开接口，版权归原平台所有。
