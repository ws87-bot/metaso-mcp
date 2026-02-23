# 秘塔AI搜索 MCP Server

将秘塔AI搜索接入Claude，提供高质量中文信息检索能力。

## 功能

| 工具 | 说明 | 适用场景 |
|------|------|---------|
| `metaso_search` | 通用中文搜索（简洁/深入/研究三种模式） | 行业趋势、政策法规、新闻动态 |
| `metaso_person_intel` | 人物情报搜索（自动优化查询） | 会议前调研对方背景 |
| `metaso_company_intel` | 企业情报搜索（多维度覆盖） | 商务合作前的企业尽调 |

## 部署方式

### 方式一：Render 一键部署（推荐）

1. Fork 或上传本项目到 GitHub
2. 登录 [render.com](https://render.com)
3. New → Web Service → 连接 GitHub 仓库
4. 配置：
   - **Runtime**: Docker
   - **Environment Variables**: 
     - `METASO_API_KEY` = 你的秘塔API Key
   - **Instance Type**: Free 或 Starter
5. Deploy → 获得公网 URL（如 `https://metaso-mcp-xxxx.onrender.com`）

### 方式二：Railway 部署

```bash
railway login
railway init
railway add --docker
railway variables set METASO_API_KEY=你的密钥
railway up
```

### 方式三：本地运行

```bash
pip install -r requirements.txt
export METASO_API_KEY=你的密钥
python server.py --http
# 服务启动在 http://localhost:8000
```

## 接入 Claude.ai

部署完成后：

1. 打开 Claude.ai → Settings → Connectors (or MCP Servers)
2. 添加新的 MCP Server
3. 输入你的服务 URL：`https://你的域名/mcp`
4. 保存

之后在对话中，Claude 就可以自动调用秘塔搜索来获取中文信息了。

## 配合 VVIP Meeting Prep Skill 使用

在 VVIP Meeting Prep skill 的 Step 2（情报搜集）中：
- 搜索中国人物 → 自动调用 `metaso_person_intel`
- 搜索中国企业 → 自动调用 `metaso_company_intel`
- 搜索行业趋势 → 调用 `metaso_search` + research 模式

## 费用

秘塔API定价：**¥0.03/次查询**，非常便宜。
每次会议准备大约 3-5 次查询 = ¥0.09-0.15。
