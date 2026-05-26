import streamlit as st
import streamlit.components.v1 as components
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os, base64

st.set_page_config(page_title="🔐 Crypto App", page_icon="🔐", layout="wide")

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #0f1117; }
    .block-container { padding-top: 2rem; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; }
    .result-box {
        background: #1e1e2e; color: #cdd6f4;
        padding: 14px; border-radius: 8px;
        font-size: 12px; word-break: break-all;
        white-space: pre-wrap; max-height: 200px;
        overflow-y: auto; font-family: monospace;
        margin-top: 8px;
    }
    .info-box {
        background: #1a1a2e; border-left: 4px solid #1565c0;
        padding: 12px 16px; border-radius: 4px; margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── AES helpers ───────────────────────────────────────────────────────────────
def make_key(raw: str, size: int) -> bytes:
    k = raw.encode("utf-8")
    return (k + b'\x00' * size)[:size]

def aes_encrypt(data: bytes, key: bytes) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    # PKCS7 padding
    pad = 16 - len(data) % 16
    data += bytes([pad] * pad)
    return iv + enc.update(data) + enc.finalize()

def aes_decrypt(data: bytes, key: bytes) -> bytes:
    iv, ct = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    dec = cipher.decryptor()
    padded = dec.update(ct) + dec.finalize()
    pad = padded[-1]
    return padded[:-pad]

def human_size(b: int) -> str:
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    return f"{b/1048576:.2f} MB"

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔐 Crypto App")
st.markdown("**AES-128 / AES-256** encryption & decryption for text and images.")
st.divider()

# ── Key config ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    aes_mode = st.radio("AES Strength", ["AES-128 (16-char key)", "AES-256 (32-char key)"])
    key_size = 32 if "256" in aes_mode else 16

with col2:
    secret_key = st.text_input("🔑 Secret Key",
        placeholder="mysecretkey12345" if key_size == 16 else "mysecretkey1234567890123456789012",
        type="password")

key_ok = bool(secret_key and secret_key.strip())

if not key_ok:
    st.warning("Enter a secret key to begin.")
else:
    n = len(secret_key)
    if n == key_size:
        st.success(f"✅ Key is exactly {key_size} chars — perfect.")
    elif n < key_size:
        st.info(f"ℹ️ Key is {n} chars — will be zero-padded to {key_size}.")
    else:
        st.info(f"ℹ️ Key is {n} chars — will be trimmed to {key_size}.")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_text, tab_image, tab_js = st.tabs(["📝 Text", "🖼️ Image", "⚡ Live JS Demo"])

# ══════════════════════════════════════════════════════════════════════════════
# TEXT TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_text:
    mode = st.radio("Mode", ["🔒 Encrypt", "🔓 Decrypt"], horizontal=True)

    if mode == "🔒 Encrypt":
        plain = st.text_area("Plain text to encrypt", placeholder="Type your secret message here…", height=120)
        if st.button("🔒 Encrypt Text", type="primary"):
            if not key_ok:
                st.error("Enter a secret key first.")
            elif not plain.strip():
                st.warning("Enter some text to encrypt.")
            else:
                try:
                    key = make_key(secret_key, key_size)
                    enc = aes_encrypt(plain.encode("utf-8"), key)
                    b64 = base64.b64encode(enc).decode()
                    st.success(f"✅ Encrypted!  {human_size(len(plain))} → {human_size(len(b64))}")
                    st.markdown("**Encrypted output (Base64) — copy and paste into Decrypt:**")
                    st.markdown(f'<div class="result-box">{b64}</div>', unsafe_allow_html=True)
                    st.code(b64, language=None)   # also shows a native copy button
                except Exception as e:
                    st.error(f"Encryption error: {e}")
    else:
        cipher_b64 = st.text_area("Paste encrypted Base64 here", placeholder="Paste the Base64 cipher text…", height=120)
        if st.button("🔓 Decrypt Text", type="primary"):
            if not key_ok:
                st.error("Enter a secret key first.")
            elif not cipher_b64.strip():
                st.warning("Paste the Base64 encrypted text above.")
            else:
                try:
                    key = make_key(secret_key, key_size)
                    raw = base64.b64decode(cipher_b64.strip())
                    plain = aes_decrypt(raw, key).decode("utf-8")
                    st.success("✅ Decrypted successfully!")
                    st.markdown("**Decrypted message:**")
                    st.text_area("Result", plain, height=120)
                except Exception as e:
                    st.error(f"Decryption failed — wrong key or corrupted data? ({type(e).__name__})")

# ══════════════════════════════════════════════════════════════════════════════
# IMAGE TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_image:
    img_mode = st.radio("Mode", ["🔒 Encrypt Image", "🔓 Decrypt Image"], horizontal=True)

    if img_mode == "🔒 Encrypt Image":
        st.info("Upload a PNG, JPG, or BMP → encrypt → download the `.enc` file.")
        uploaded = st.file_uploader("Upload image to encrypt", type=["png", "jpg", "jpeg", "bmp"])
        if uploaded:
            img_bytes = uploaded.read()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Original image:**")
                st.image(img_bytes, use_container_width=True)
                st.caption(f"{uploaded.name}  ·  {human_size(len(img_bytes))}")
            if st.button("🔒 Encrypt Image", type="primary"):
                if not key_ok:
                    st.error("Enter a secret key first.")
                else:
                    try:
                        key = make_key(secret_key, key_size)
                        enc = aes_encrypt(img_bytes, key)
                        base = uploaded.name.rsplit(".", 1)[0]
                        with c2:
                            st.markdown("**Encrypted file:**")
                            st.markdown(f"`{base}.enc`  ·  {human_size(len(enc))}")
                            st.markdown("Binary data — not displayable as image.")
                        st.success(f"✅ Image encrypted!  {human_size(len(img_bytes))} → {human_size(len(enc))}")
                        st.download_button(
                            label=f"⬇️ Download {base}.enc",
                            data=enc,
                            file_name=f"{base}.enc",
                            mime="application/octet-stream",
                            type="primary"
                        )
                        st.info(f"Upload `{base}.enc` in Decrypt mode with the same key to restore.")
                    except Exception as e:
                        st.error(f"Encryption error: {e}")
    else:
        st.info("Upload the `.enc` file → use the same key → get your image back.")
        enc_file = st.file_uploader("Upload .enc file to decrypt", type=["enc"])
        if enc_file:
            st.markdown(f"Selected: `{enc_file.name}`  ·  {human_size(enc_file.size)}")
            if st.button("🔓 Decrypt Image", type="primary"):
                if not key_ok:
                    st.error("Enter a secret key first.")
                else:
                    try:
                        key = make_key(secret_key, key_size)
                        enc_bytes = enc_file.read()
                        dec = aes_decrypt(enc_bytes, key)
                        base = enc_file.name.replace(".enc", "")
                        if not any(base.endswith(x) for x in [".png",".jpg",".jpeg",".bmp",".gif",".webp"]):
                            base += ".png"
                        st.success(f"✅ Image decrypted!  ({human_size(len(dec))})")
                        st.markdown("**Restored image:**")
                        st.image(dec, use_container_width=True)
                        st.download_button(
                            label=f"⬇️ Download {base}",
                            data=dec,
                            file_name=base,
                            mime="image/png",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Decryption failed — wrong key or AES mode? ({type(e).__name__})")

# ══════════════════════════════════════════════════════════════════════════════
# JS DEMO TAB — AES via Web Crypto API embedded in Streamlit
# ══════════════════════════════════════════════════════════════════════════════
with tab_js:
    st.markdown("### ⚡ Live JavaScript AES Demo")
    st.markdown("""
This tab runs **AES-GCM encryption entirely in your browser** using the
[Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto) —
the same AES algorithm as the Java/Javelit implementation, running as JavaScript.
This proves the concept works end-to-end in any language.
    """)
    components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: sans-serif; background: #0f1117; color: #cdd6f4; padding: 16px; margin: 0; }
  input, textarea { width: 100%; padding: 8px; margin: 6px 0 12px;
    background: #1e1e2e; color: #cdd6f4; border: 1px solid #444;
    border-radius: 6px; font-size: 13px; box-sizing: border-box; }
  textarea { height: 80px; resize: vertical; font-family: monospace; word-break: break-all; }
  button { padding: 9px 20px; border: none; border-radius: 6px;
    font-size: 14px; font-weight: 600; cursor: pointer; margin: 4px 4px 4px 0; }
  .btn-enc { background: #1565c0; color: #fff; }
  .btn-dec { background: #2e7d32; color: #fff; }
  .btn-copy { background: #37474f; color: #fff; font-size: 12px; padding: 6px 12px; }
  .out { background: #1e1e2e; border: 1px solid #333; border-radius: 6px;
    padding: 12px; font-size: 11px; font-family: monospace;
    word-break: break-all; white-space: pre-wrap; min-height: 40px; }
  .ok  { color: #a6e3a1; } .err { color: #f38ba8; }
  label { font-size: 13px; font-weight: 600; color: #89b4fa; }
  .row { display: flex; gap: 8px; align-items: flex-end; }
  .note { font-size: 11px; color: #888; margin-top: 4px; }
  h4 { color: #89b4fa; margin: 0 0 12px; }
</style>
</head>
<body>
<h4>🔑 AES-GCM — Web Crypto API</h4>

<label>Secret Key (any length)</label>
<input id="key" type="password" placeholder="mysecretkey12345" value="mysecretkey12345">

<label>Plain text to encrypt</label>
<textarea id="plain">Hello, this is a secret message!</textarea>

<div>
  <button class="btn-enc" onclick="doEncrypt()">🔒 Encrypt</button>
  <button class="btn-dec" onclick="doDecrypt()">🔓 Decrypt</button>
  <button class="btn-copy" onclick="copyOut()">📋 Copy output</button>
</div>

<label style="margin-top:12px;display:block">Output</label>
<div class="out" id="out">Click Encrypt or Decrypt above.</div>
<p class="note" id="note"></p>

<script>
// Convert any string key to 256-bit AES key via SHA-256
async function deriveKey(raw) {
  const enc = new TextEncoder().encode(raw);
  const hash = await crypto.subtle.digest("SHA-256", enc);
  return crypto.subtle.importKey("raw", hash, { name: "AES-GCM" }, false, ["encrypt","decrypt"]);
}

async function doEncrypt() {
  const out = document.getElementById("out");
  const note = document.getElementById("note");
  try {
    const key = await deriveKey(document.getElementById("key").value);
    const iv  = crypto.getRandomValues(new Uint8Array(12));
    const data = new TextEncoder().encode(document.getElementById("plain").value);
    const enc = await crypto.subtle.encrypt({ name:"AES-GCM", iv }, key, data);
    // Pack: iv (12 bytes) + ciphertext, encode as base64
    const combined = new Uint8Array(12 + enc.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(enc), 12);
    const b64 = btoa(String.fromCharCode(...combined));
    out.className = "out ok";
    out.textContent = b64;
    note.textContent = "✅ Encrypted with AES-256-GCM. Copy output → paste into decrypt.";
  } catch(e) { out.className="out err"; out.textContent="Error: "+e.message; }
}

async function doDecrypt() {
  const out = document.getElementById("out");
  const note = document.getElementById("note");
  try {
    const b64 = document.getElementById("plain").value.trim();
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const iv  = bytes.slice(0, 12);
    const ct  = bytes.slice(12);
    const key = await deriveKey(document.getElementById("key").value);
    const dec = await crypto.subtle.decrypt({ name:"AES-GCM", iv }, key, ct);
    out.className = "out ok";
    out.textContent = new TextDecoder().decode(dec);
    note.textContent = "✅ Decrypted successfully.";
  } catch(e) { out.className="out err"; out.textContent="Decryption failed — wrong key or not encrypted text? ("+e.message+")"; }
}

function copyOut() {
  const text = document.getElementById("out").textContent;
  navigator.clipboard.writeText(text).then(() => {
    const b = event.target;
    b.textContent = "✅ Copied!";
    setTimeout(() => b.textContent = "📋 Copy output", 1500);
  });
}
</script>
</body>
</html>
""", height=420)
