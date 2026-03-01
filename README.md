# 隐私邮件搜索与解密系统

一个安全且隐私优先的邮件搜索系统，允许用户在**不向服务器泄露邮件内容或搜索关键词**的前提下，完成邮件的搜索与解密，基于 Flask、Jieba（中文 NLP）和现代 Web 加密技术构建。

## ✨ 核心功能

- 🔒 **端到端加密**：所有邮件使用 AES-256-GCM 算法加密存储
- 🔍 **隐私搜索**：基于加密索引的可搜索加密（SE）技术，服务器无法获知搜索词
- 🇨🇳 **中文 NLP 支持**：集成 Jieba 分词，专为中文邮件内容提取高质量关键词
- 💻 **客户端解密**：所有解密操作均在浏览器本地完成（基于 Web Crypto API），私钥不出域
- 🧩 **模块化设计**：清晰的后端（Flask）与前端（JS）分离架构，易于扩展

## 🛠️ 技术栈

| 组件 | 技术选型 |
|-----------|------------|
| **后端框架** | Python 3.8+, Flask |
| **加密库** | `cryptography` (RSA-OAEP, AES-GCM) |
| **前端 UI** | HTML5, Bootstrap 5, jQuery |
| **前端加密** | Forge.js (RSA), Web Crypto API (AES) |
| **中文处理** | Jieba (中文分词与关键词提取) |
| **数据存储** | 本地文件系统 (分块存储加密数据) |

## 📦 项目结构

```
privacy-email-search/
├── app.py                      # Flask 应用入口
├── client_se_index_builder.py  # 客户端工具：构建并上传加密索引
├── config.py                   # 系统配置
├── database.py                 # 加密数据库接口
├── key_management.py           # 密钥管理工具
├── routes.py                   # API 路由定义
├── services.py                 # 业务逻辑层
├── templates/
│   └── index.html              # 前端主界面（响应式设计）
├── data/
│   ├── blocks/                 # 加密后的邮件数据块
│   ├── ham/                    # 原始明文邮件目录（仅用于构建索引）
│   ├── manifest.json           # 文件元数据与分块结构
│   ├── private_key.pem         # 用户私钥（在客户端保留）
│   └── public_key.pem          # 服务器公钥
└── requirements.txt            # Python 依赖列表
```

## 🚀 快速开始

### 1. 环境准备
- Python 3.8 或更高版本

### 2. 安装依赖
```bash
git clone https://github.com/StuBoo3i/PrivateMailSearch-Decrypt.git
pip install -r requirements.txt
```

### 3. 数据准备与索引构建
1. 将原始邮件文本文件（`.txt`）放入 `data/ham/` 目录。
2. **关键步骤**：运行客户端工具构建加密索引。
   ```bash
   python client_se_index_builder.py
   ```
   > ⚠️ **注意**：此步骤会生成 `private_key.pem`并将加密后的索引上传至服务器，服务器只会存储哈希值。

### 4. 启动系统
1. 启动 Flask 服务器：
   ```bash
   python app.py
   ```
2. 在浏览器访问：`http://localhost:5000`

### 5. 使用流程
1. **加载私钥**：在网页顶部上传刚才生成的 `private_key.pem` 文件（私钥仅存于浏览器内存）。
2. **搜索邮件**：输入中文关键词（如“发票”、“合同”、“会议”）。
3. **解密查看**：点击搜索结果中的 "🔓 解密查看" 按钮。
4. **隐私验证**：观察控制台和网络请求，确认解密密钥和内容从未离开过您的浏览器。

## 🔐 安全模型

| 威胁场景 | 防护机制 |
|--------|----------------------|
| **服务器窃取邮件内容** | 邮件内容使用 AES-256-GCM 加密，服务器无私钥，仅存密文 |
| **搜索关键词泄露** | 使用可搜索加密（SE），服务器仅存储关键词的 SHA-256 哈希值 |
| **私钥泄露** | 私钥永远不传输、不存储于服务器，仅存在于用户浏览器内存中 |
| **中间人攻击** | 生产环境建议部署 HTTPS，防止传输过程被窃听 |
| **访问模式泄露** | 采用分块（Block）架构，结合 PIR 思想模糊具体文件访问请求 |
---
