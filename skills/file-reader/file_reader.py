"""file-reader: 从微信 iLink 文件消息下载、解密、解析纯文本。

由 Sunny 为微信 ClawBot 开发，可独立复用。
协议：item.type == 4 为文件；media.aes_key 为 base64（16 字节原文或 32 字符 hex）；
media.full_url 为 CDN 地址；内容为 AES-128-ECB(PKCS7) 加密。
"""
import base64
import io

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def parse_aes_key(aes_key_base64: str) -> bytes:
    raw = base64.b64decode(aes_key_base64)
    if len(raw) == 16:
        return raw
    if len(raw) == 32:
        return bytes.fromhex(raw.decode("ascii"))
    raise ValueError(f"aes_key 长度异常：{len(raw)}")


def decrypt_aes_ecb(ciphertext: bytes, key: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    dec = cipher.decryptor()
    pt = dec.update(ciphertext) + dec.finalize()
    pad = pt[-1]
    if 1 <= pad <= 16 and pt.endswith(bytes([pad]) * pad):
        pt = pt[:-pad]
    return pt


def download_media_item(item: dict, timeout: int = 180) -> bytes:
    """从入站消息 item（image/voice/file/video）下载并解密，返回原始字节。"""
    t = item.get("type")
    sub = (item.get({2: "image_item", 3: "voice_item", 4: "file_item",
                     5: "video_item"}.get(t, "")) or {})
    media = sub.get("media") or {}
    aes_b64 = media.get("aes_key")
    if not aes_b64:
        aes_hex = sub.get("aeskey")  # 图片有时直接给 hex
        if aes_hex:
            aes_b64 = base64.b64encode(bytes.fromhex(aes_hex)).decode("ascii")
    if not aes_b64:
        raise ValueError("aes_key 缺失，无法下载")
    url = media.get("full_url")
    if not url:
        raise ValueError("CDN 下载地址缺失")
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return decrypt_aes_ecb(r.content, parse_aes_key(aes_b64))


def extract_file_text(data: bytes, filename: str):
    """从文件字节提取纯文本。返回 (text, pages)；不支持返回 (None, 0)。"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        return text.strip() or None, len(reader.pages)
    if ext == "docx":
        from docx import Document
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text.strip() or None, 0
    if ext in ("txt", "md", "csv", "json", "log"):
        return data.decode("utf-8", errors="ignore").strip() or None, 0
    return None, 0
