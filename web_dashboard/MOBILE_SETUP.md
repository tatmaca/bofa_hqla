# Mobile App Setup Guide

## Option 1: Progressive Web App (PWA) - Easiest

The web dashboard is already configured as a PWA and can be installed on iPhone!

### Install on iPhone:

1. **Open Safari** (Chrome won't work for PWA installation on iOS)
2. Navigate to your dashboard: `http://your-server-ip:8888`
3. Tap the **Share button** (square with arrow)
4. Scroll down and tap **"Add to Home Screen"**
5. Customize the name if desired
6. Tap **"Add"**

The app will now appear on your home screen and launch in fullscreen mode!

### Features:
- ✅ Works offline (cached resources)
- ✅ Fullscreen experience
- ✅ No App Store needed
- ✅ Automatic updates when you refresh

## Option 2: React Native App - Native Experience

For a more native iOS/Android app, use the React Native app in `../mobile_app/`

### Quick Start:

```bash
cd mobile_app
npm install
npm start
```

Then scan QR code with Expo Go app on your iPhone.

### For Physical Device:

1. Update `API_BASE` in `mobile_app/App.js` to your computer's IP
2. Make sure Flask dashboard is running on port 8888
3. Start Expo: `npm start`
4. Scan QR code with Expo Go app

## Comparison

| Feature | PWA | React Native |
|---------|-----|--------------|
| Installation | Safari → Add to Home Screen | Expo Go or App Store |
| Offline Support | ✅ (Service Worker) | ✅ (Expo) |
| Native Feel | Good | Excellent |
| Push Notifications | Limited | Full Support |
| App Store | No | Yes |
| Development Time | ✅ Ready Now | Requires Setup |

## Recommendation

**Start with PWA** - It's ready to use right now! Just add to home screen from Safari.

If you want a more native experience or need App Store distribution, use the React Native app.

