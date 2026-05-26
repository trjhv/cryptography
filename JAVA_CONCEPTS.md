# Crypto App — Java & Javelit Implementation Explained

## Project Overview

This project implements **AES (Advanced Encryption Standard)** encryption and
decryption for both text and images, originally built in Java using the
**Javelit framework** (a Java equivalent of Python's Streamlit), and demonstrated
via a working Python+Streamlit implementation.

---

## 1. The Java AES Implementation

### Key Generation
```java
private static SecretKey makeKey(String raw, int keySizeBytes) {
    byte[] keyBytes = new byte[keySizeBytes]; // 16 bytes = AES-128, 32 = AES-256
    byte[] src = raw.getBytes(StandardCharsets.UTF_8);
    System.arraycopy(src, 0, keyBytes, 0, Math.min(src.length, keySizeBytes));
    return new SecretKeySpec(keyBytes, "AES");
}
```
- User's string key is converted to bytes and padded/trimmed to exactly 16 or 32 bytes
- `SecretKeySpec` wraps the raw bytes as an AES key object
- This mirrors Python's `(key.encode() + b'\x00' * size)[:size]`

### Encryption (AES-CBC with random IV)
```java
private static byte[] encrypt(byte[] data, SecretKey key) throws Exception {
    byte[] iv = new byte[16];
    new SecureRandom().nextBytes(iv);          // Random IV every time
    Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
    cipher.init(Cipher.ENCRYPT_MODE, key, new IvParameterSpec(iv));
    byte[] encrypted = cipher.doFinal(data);
    // Prepend IV to ciphertext: [16 bytes IV][ciphertext]
    byte[] result = new byte[16 + encrypted.length];
    System.arraycopy(iv, 0, result, 0, 16);
    System.arraycopy(encrypted, 0, result, 16, encrypted.length);
    return result;
}
```
**Why CBC mode?**
- CBC (Cipher Block Chaining) XORs each block with the previous ciphertext block
- Each block depends on all previous blocks — identical plaintexts produce different ciphertexts
- The IV (Initialization Vector) ensures even the same message+key produces different output each time

**Why prepend the IV?**
- The IV is not secret — it just needs to be the same for encrypt and decrypt
- Storing it with the ciphertext means you only need to share one piece of data

### Decryption
```java
private static byte[] decrypt(byte[] data, SecretKey key) throws Exception {
    byte[] iv = new byte[16];
    System.arraycopy(data, 0, iv, 0, 16);           // Extract first 16 bytes = IV
    byte[] cipherText = new byte[data.length - 16];
    System.arraycopy(data, 16, cipherText, 0, cipherText.length); // Rest = ciphertext
    Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
    cipher.init(Cipher.DECRYPT_MODE, key, new IvParameterSpec(iv));
    return cipher.doFinal(cipherText);
}
```

### Image Encryption
Images are just bytes — the same encrypt/decrypt functions work on any `byte[]`:
```java
byte[] imgBytes = imgFile.content();           // Read image as raw bytes
byte[] encrypted = encrypt(imgBytes, key);     // Encrypt the bytes
// Save as .enc file — when decrypted, bytes are a valid image again
byte[] decrypted = decrypt(encBytes, key);
Jt.image(decrypted).use(imgTab);              // Javelit renders the bytes as image
```

---

## 2. Javelit Framework Concepts

Javelit is a **Streamlit-for-Java** framework. It follows the same
reactive re-run model as Streamlit.

### How Javelit Works
```java
// Every interaction re-runs main() from top to bottom
public static void main(String[] args) {
    String input = Jt.textInput("Enter text").use();  // Widget rendered + value read
    if (Jt.button("Submit").use()) {                  // Button rendered + click detected
        Jt.success("You typed: " + input).use();      // Output rendered
    }
}
```

### Key Javelit Components Used
| Component | Java | Python Streamlit equiv |
|---|---|---|
| Text input | `Jt.textInput("label").use()` | `st.text_input("label")` |
| Text area | `Jt.textArea("label").use()` | `st.text_area("label")` |
| Radio | `Jt.radio("label", List.of(...)).use()` | `st.radio("label", [...])` |
| Button | `Jt.button("label").use()` | `st.button("label")` |
| File upload | `Jt.fileUploader("label").use()` | `st.file_uploader("label")` |
| Tabs | `Jt.tabs(List.of(...)).use()` | `st.tabs([...])` |
| Columns | `Jt.columns(2).use()` | `st.columns(2)` |
| Show image | `Jt.image(bytes).use()` | `st.image(bytes)` |
| HTML embed | `Jt.html("<div>...</div>").use()` | `st.html(...)` |

### The Widget Tree Rule (Critical Javelit Constraint)
```java
// ❌ WRONG — widget inside if/else causes DuplicateWidgetIDException
if (someCondition) {
    String input = Jt.textInput("Text").use(); // Different widget tree each run!
}

// ✅ CORRECT — widget always rendered, output gated
String input = Jt.textInput("Text").use();  // Always in tree
if (someCondition) {
    Jt.text("Result: " + input).use();       // Output only — safe in if/else
}
```

### Deployment with JBang
```java
///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS io.javelit:javelit:0.86.0
```
- The shebang line makes the `.java` file directly executable via JBang
- `//DEPS` declares Maven dependencies — JBang downloads them automatically
- No `pom.xml`, no build step, no JAR — just run `javelit run App.java`

---

## 3. Python ↔ Java — Concept Mapping

| Concept | Java (this project) | Python equivalent |
|---|---|---|
| AES key | `new SecretKeySpec(bytes, "AES")` | `key = raw_key[:16]` |
| CBC encrypt | `Cipher.getInstance("AES/CBC/PKCS5Padding")` | `modes.CBC(iv)` |
| Random IV | `new SecureRandom().nextBytes(iv)` | `os.urandom(16)` |
| PKCS5 padding | Built into `PKCS5Padding` | Manual pad or `cryptography` lib |
| Base64 encode | `Base64.getEncoder().encodeToString(bytes)` | `base64.b64encode(bytes).decode()` |
| Base64 decode | `Base64.getDecoder().decode(string)` | `base64.b64decode(string)` |
| Read file bytes | `imgFile.content()` (Javelit) | `uploaded_file.read()` (Streamlit) |
| Show image | `Jt.image(bytes).use()` | `st.image(bytes)` |
| Download file | `Jt.html(downloadLink(...)).use()` | `st.download_button(data=bytes)` |

---

## 4. Security Properties

| Property | Implementation |
|---|---|
| **Algorithm** | AES (Advanced Encryption Standard) — NIST standard, used worldwide |
| **Mode** | CBC (Cipher Block Chaining) — each block chained to previous |
| **Key sizes** | 128-bit (16 bytes) or 256-bit (32 bytes) |
| **IV** | 16 random bytes generated fresh per encryption (`SecureRandom`) |
| **Padding** | PKCS5/PKCS7 — pads plaintext to 16-byte block boundary |
| **IV storage** | Prepended to ciphertext (`[IV 16 bytes][ciphertext]`) |
| **Works on** | Any `byte[]` — text, images, any file type |

---

## 5. Deploy Instructions

### Python+Streamlit (Working Demo)
```bash
# Local
pip install streamlit cryptography
streamlit run app.py

# Deploy to Streamlit Cloud (free)
# 1. Push to GitHub
# 2. Go to share.streamlit.io
# 3. Connect repo → Deploy
```

### Java+Javelit (Original Implementation)
```bash
# Install JBang
curl -Ls https://sh.jbang.dev | bash -s - app setup

# Install Javelit CLI
jbang app install javelit@javelit

# Run locally
javelit run App.java

# Deploy to Railway
# 1. Push App.java to GitHub
# 2. railway.com/new/template/javelit-app → paste repo URL → Deploy
```

---

*AES-CBC implementation · Random IV per operation · PKCS5 padding · Java javax.crypto*
