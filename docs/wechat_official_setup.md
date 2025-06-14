# 微信公众号接入本地Dify详细指南

## 🎯 目标
将本地Dify AI助手接入微信公众号，实现智能对话功能。

## 📋 前置条件
- ✅ 已注册微信公众号（订阅号或服务号）
- ✅ 本地Dify服务正常运行
- ✅ Dify2WeChat服务已启动（http://localhost:8000）

## 🔧 配置步骤

### 1️⃣ 获取微信公众号信息

登录 [微信公众平台](https://mp.weixin.qq.com/)：

1. **获取AppID和AppSecret**：
   - 进入「开发」→「基本配置」
   - 复制「开发者ID(AppID)」
   - 点击「生成」获取「开发者密码(AppSecret)」

2. **设置服务器配置**：
   - 在「基本配置」页面找到「服务器配置」
   - 点击「修改配置」

### 2️⃣ 配置服务器信息

在微信公众平台的服务器配置中填入：

```
服务器地址(URL): http://你的域名:8000/wechat/official
令牌(Token): wechat_dify_token_2024
消息加解密密钥: （可选，留空使用明文模式）
消息加解密方式: 明文模式（推荐）或兼容模式
```

⚠️ **重要提醒**：
- 如果你在本地开发，需要使用内网穿透工具（如ngrok、frp等）
- 微信服务器需要能够访问你的服务器地址

### 3️⃣ 更新配置文件

编辑项目根目录的 `config.yaml` 文件：

```yaml
# 微信公众号配置
wechat_official:
  enabled: true
  app_id: "你的AppID"                    # 🔑 替换为实际AppID
  app_secret: "你的AppSecret"            # 🔑 替换为实际AppSecret  
  token: "wechat_dify_token_2024"       # 🔑 与微信后台设置的Token一致
  encoding_aeskey: ""                   # 可选，如使用加密模式则填入
```

### 4️⃣ 内网穿透配置（本地开发必需）

如果你在本地开发，需要使用内网穿透：

#### 方案1：使用ngrok
```bash
# 安装ngrok
brew install ngrok

# 启动内网穿透
ngrok http 8000
```

#### 方案2：使用frp
```bash
# 下载frp客户端
# 配置frp连接到你的服务器
```

获得公网地址后，将微信后台的服务器地址设置为：
```
http://你的公网域名/wechat/official
```

### 5️⃣ 验证配置

1. **保存微信后台配置**：
   - 在微信公众平台点击「提交」
   - 系统会向你的服务器发送验证请求

2. **检查服务日志**：
   ```bash
   tail -f server.log
   ```

3. **测试对话**：
   - 关注你的微信公众号
   - 发送消息测试AI回复

## 🔍 故障排除

### 常见问题

1. **Token验证失败**
   - 检查config.yaml中的token是否与微信后台一致
   - 确认服务器地址可以被微信服务器访问

2. **服务器无响应**
   - 检查防火墙设置
   - 确认端口8000已开放
   - 验证内网穿透是否正常

3. **消息无回复**
   - 检查Dify连接是否正常
   - 查看服务日志排查错误

### 调试命令

```bash
# 查看服务状态
curl http://localhost:8000/health

# 查看实时日志
tail -f server.log

# 重启服务
pkill -f "python main.py"
source venv/bin/activate && nohup python main.py > server.log 2>&1 &
```

## 🎉 完成

配置完成后，用户向你的微信公众号发送消息，就会收到Dify AI助手的智能回复！

## 📞 技术支持

如遇问题，请检查：
1. 服务日志：`server.log`
2. Dify连接：运行 `python test_local_dify.py`
3. 配置文件：确认所有参数正确填写

## 1. 准备工作

### 1.1 确认本地Dify运行状态

```bash
# 检查Dify是否正常运行
curl http://localhost:3001/health

# 检查API是否可访问
curl -H "Authorization: Bearer app-your-api-key" \
     -H "Content-Type: application/json" \
     http://localhost:3001/v1/parameters
```

### 1.2 获取Dify API密钥

1. 访问本地Dify控制台：`http://localhost:3000`（或你的Dify前端地址）
2. 进入你的应用 → 设置 → API访问
3. 复制API密钥，格式类似：`app-xxxxxxxxxxxxxx`

## 2. 微信公众号配置

### 2.1 注册微信公众号

1. 访问 [微信公众平台](https://mp.weixin.qq.com/)
2. 注册订阅号（个人可申请）或服务号（企业申请，功能更丰富）
3. 完成基本信息填写

### 2.2 开发者配置

1. 登录微信公众平台
2. 左侧菜单：**开发** → **基本配置**
3. 点击**修改配置**，获取以下信息：

#### AppID 和 AppSecret
- **AppID**：在基本配置页面直接显示
- **AppSecret**：点击"重置"按钮，用管理员微信扫码获取

#### 自定义Token
- 建议使用随机字符串，例如：`wechat_dify_token_2024`
- 长度3-32位，只能包含字母和数字

## 3. 服务器配置

### 3.1 内网穿透（开发环境）

由于微信需要访问公网地址，本地开发需要内网穿透：

#### 方案一：使用ngrok
```bash
# 安装ngrok
# macOS
brew install ngrok

# 启动内网穿透
ngrok http 8000
```

#### 方案二：使用frp
```bash
# 需要有公网服务器支持
# 配置frp客户端
./frpc -c frpc.ini
```

#### 方案三：使用花生壳等工具
- 申请花生壳账号
- 下载客户端配置内网穿透

### 3.2 获取公网地址

内网穿透成功后，会得到类似地址：
- ngrok: `https://abc123.ngrok.io`
- frp: `https://yourdomain.com:port`

## 4. 微信服务器配置

### 4.1 设置服务器地址

在微信公众平台 → 开发 → 基本配置：

1. **服务器地址(URL)**：`https://你的公网地址/wechat/official`
2. **令牌(Token)**：填入你在配置文件中设置的token
3. **消息加解密密钥(EncodingAESKey)**：可选，点击随机生成

### 4.2 验证服务器

配置完成后点击**提交**按钮，微信会向你的服务器发送验证请求。

## 5. 本地配置文件

### 5.1 复制配置模板

```bash
cp config.local-dify.yaml config.yaml
```

### 5.2 编辑配置文件

```yaml
# Dify配置（本地部署）
dify:
  api_base: "http://localhost:3001/v1"  # 确认你的本地Dify API地址
  api_key: "app-your-actual-api-key"    # 替换为实际的API密钥

# 微信公众号配置
wechat_official:
  enabled: true
  app_id: "wx1234567890abcdef"          # 替换为你的AppID
  app_secret: "your-actual-app-secret"  # 替换为你的AppSecret
  token: "your_custom_token_here"       # 替换为你的自定义Token
```

## 6. 启动服务

### 6.1 安装依赖

```bash
pip install -r requirements.txt
```

### 6.2 启动服务

```