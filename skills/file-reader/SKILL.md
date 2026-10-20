---
name: file-reader
description: 从微信 iLink 机器人收到的文件消息中下载、解密并解析文本（PDF/Word/txt），附带追问存档。适用于任何需要"让机器人读懂用户发来的文件"的场景。
---

# File Reader Skill

让微信机器人（iLink 协议）能读取用户发来的文件。

## 协议要点

- 入站消息 `item_list[]` 的 `type`：1 文本 / 2 图片 / 3 语音 / **4 文件** / 5 视频
- 文件消息结构：`item.file_item.media` 含 `aes_key`（base64，两种编码：16 字节原文或 32 字符 hex）与 `full_url`（CDN 下载地址）；`item.file_item.file_name` / `len`
- CDN 文件用 **AES-128-ECB** 加密，PKCS7 填充

## 用法

```python
from file_reader import download_media_item, extract_file_text

# item 是入站消息 item_list 中的文件 item（type == 4）
raw_bytes = download_media_item(item)          # 下载并解密 -> 原始字节
text, pages = extract_file_text(raw_bytes, "讲义.pdf")  # 解析纯文本
```

## 支持的格式

| 格式 | 解析方式 |
|------|----------|
| PDF | pypdf，按页提取 |
| docx | python-docx，按段落提取 |
| txt / md / csv / json / log | UTF-8 解码 |

图片（type 2）暂不支持，语音（type 3）暂不支持。

## 依赖

```
cryptography   # AES 解密
pypdf          # PDF 解析
python-docx    # Word 解析
requests       # CDN 下载
```
