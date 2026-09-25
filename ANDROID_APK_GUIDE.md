# Android APK Build Guide — OmniGrab

The Android project has been generated using **Capacitor** and is located at:
`d:\Project\old\mediaproject\frontend\android`

---

## 🛠 Step 1: Install Required Tools

To compile the Android project into an `.apk` file:
1. **Download & Install Android Studio**:
   - Download free from: [https://developer.android.com/studio](https://developer.android.com/studio)
   - During installation, leave the default options checked (Android SDK, Android SDK Platform, Android Virtual Device).
   *(Android Studio includes JDK 17/21 bundled inside).*

---

## 🚀 Step 2: Open and Generate the APK

### Option A: Using the Helper Script
Simply double-click:
```bat
build_android.bat
```
This builds the latest Angular frontend, copies all files to the native Android directory, and launches Android Studio.

### Option B: Open Manually in Android Studio
1. Open **Android Studio**.
2. Click **Open** and select the folder:
   ```
   D:\Project\old\mediaproject\frontend\android
   ```
3. Allow Android Studio to finish indexing and Gradle sync (first time takes 1–2 minutes).
4. In the top menu bar, click:
   **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**
5. When the build finishes, a notification bubble will appear in the bottom right:
   Click **"locate"** to open the folder containing your APK:
   ```
   frontend\android\app\build\outputs\apk\debug\app-debug.apk
   ```

---

## 📱 Step 3: Connecting the APK to Your Backend

When the APK runs on your physical Android phone, `localhost` refers to the phone itself. To connect to your backend:

1. **Option 1: Using your PC's Wi-Fi IP (For Local Testing)**
   - Connect your phone and PC to the same Wi-Fi network.
   - Find your PC's IP address (Run `ipconfig` in PowerShell, e.g. `192.168.1.50`).
   - Run backend on `0.0.0.0`:
     ```powershell
     cd backend
     .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
     ```
   - In the app, requests will route to `http://192.168.1.50:8000/api`.

2. **Option 2: Cloud Deployed Backend (Recommended for Daily Use)**
   - Deploy backend using Render (via included `render.yaml`) or Railway.
   - Set the cloud URL (e.g., `https://your-service.onrender.com/api`).

---

## 📲 Step 4: Installing on Your Phone
1. Transfer `app-debug.apk` to your phone via USB cable, Google Drive, WhatsApp, or Telegram.
2. Tap the file on your phone and tap **Install** (allow "Install unknown apps" if prompted).
