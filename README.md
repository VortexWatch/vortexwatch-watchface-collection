# 💎 VortexWatch Studio: Timepiece Collection & Python DevKit

Welcome to the official repository of **VortexWatch Studio**. This project bridges premium luxury watch face design curation with open-source local developer automation scripts. 

Here we host our curated catalog of minimal, premium timepiece designs engineered natively for the **240x284 display architecture (IDW13, IDW19, IDW25, IDW26, IDW29)**, alongside a suite of local Python utility scripts to automate asset parsing, schema validation, and staging pipeline deployment.

---

## 📲 Premium Timepiece Collection

### Featured Asset: Roman Numeral Minimal (Gold Edition)
<img width="174" height="196" alt="preview" src="https://github.com/user-attachments/assets/e81aef1b-63d4-4e13-9d29-d05bfebf701d" />

---

## 🚀 Desktop Bluetooth Sideloading Blueprint (Recommended)

To bypass the official smartphone application cache completely, you can flash our pre-compiled custom `.iwf` binaries directly over Bluetooth Low Energy (BLE) using the community's open-source cross-platform desktop sideloader.

### 💻 Direct Bluetooth Deployment (Windows / macOS / Linux)

1. **Download the Target Assets:** Download our pre-compiled `Roman_Gold.iwf` binary from our [Releases](https://github.com) tab.
2. **Launch the Sideloader Environment:** Clone and initialize the community's official **VeryLoad** desktop utility:
   ```bash
   git clone https://github.com/coolsteel712/VeryLoad
   cd VeryLoad
   pip install -r requirements.txt
   python main.py
   ```
3. **Scan and Connect:** Click **Scan Devices** inside VeryLoad, select your target smartwatch from the list, and establish a live GATT communication channel.
4. **Flash the Face:** Click **Browse...**, select our downloaded `Roman_Gold.iwf` package file, and hit **Upload**. Keep the watch near your computer adapter until the log displays `Upload complete`. The screen will instantly clear and render our custom gold layout!

### Proof of success
<img width="3000" height="4000" alt="20260801_184342" src="https://github.com/user-attachments/assets/95eda7a9-c713-476c-8bb0-ffdde356464b" />


---
*Disclaimer: VortexWatch Studio operates as an independent design and automation collective. All layout configurations and parsing scripts are developed under clean-room specifications and are distributed strictly for educational and evaluation purposes. We are not affiliated with Shenzhen DO Intelligent Technology Co., Ltd or individual repository developers.*
