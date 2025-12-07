# Yield Curve Mobile App (React Native)

Native iOS/Android app for the UST Yield Curve Dashboard.

## Setup

### Prerequisites

- Node.js (v16 or later)
- npm or yarn
- Expo CLI: `npm install -g expo-cli`
- For iOS: Xcode (Mac only)
- For Android: Android Studio

### Installation

```bash
cd mobile_app
npm install
```

### Running the App

#### Development Mode

```bash
# Start Expo development server
npm start

# Or use Expo CLI
expo start
```

Then:
- Press `i` to open iOS simulator
- Press `a` to open Android emulator
- Scan QR code with Expo Go app on your phone

#### For Physical Device Testing

1. Make sure your phone and computer are on the same WiFi network
2. Update `API_BASE` in `App.js` to your computer's local IP address:
   ```javascript
   const API_BASE = 'http://192.168.1.XXX:8888'; // Your computer's IP
   ```
3. Start the Flask dashboard server:
   ```bash
   cd web_dashboard
   python app.py
   ```
4. Start Expo:
   ```bash
   npm start
   ```
5. Scan QR code with Expo Go app

### Building for Production

#### iOS

```bash
# Build for App Store
expo build:ios

# Or create local build
eas build --platform ios
```

#### Android

```bash
# Build for Play Store
expo build:android

# Or create local build
eas build --platform android
```

## Features

- ✅ Real-time yield curve visualization
- ✅ Today vs yesterday comparison
- ✅ Day-over-day changes
- ✅ Top news articles
- ✅ Pull-to-refresh
- ✅ Push notifications for daily updates
- ✅ Native iOS/Android experience

## Configuration

### API Endpoint

Update the `API_BASE` constant in `App.js`:

```javascript
const API_BASE = 'http://your-server-ip:8888';
```

For local development on physical device:
- Find your computer's IP: `ifconfig` (Mac/Linux) or `ipconfig` (Windows)
- Use that IP instead of `localhost`

### Notifications

The app requests notification permissions on first launch and schedules daily updates at 5 PM.

## Troubleshooting

### Can't Connect to Server

1. Make sure Flask dashboard is running
2. Check firewall settings
3. Verify IP address is correct
4. Ensure phone and computer are on same network

### Build Errors

- Clear cache: `expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check Expo SDK version compatibility

## Development

### Project Structure

```
mobile_app/
├── App.js           # Main app component
├── app.json         # Expo configuration
├── package.json     # Dependencies
└── assets/          # Icons, images (create these)
```

### Adding Features

1. Install new packages: `npm install package-name`
2. Import in `App.js`
3. Add UI components and logic
4. Test on device/simulator

## Publishing

### App Store (iOS)

1. Create Apple Developer account
2. Configure `app.json` with your bundle ID
3. Run `expo build:ios`
4. Submit to App Store Connect

### Play Store (Android)

1. Create Google Play Developer account
2. Configure `app.json`
3. Run `expo build:android`
4. Upload APK to Play Console

