# Troubleshooting Guide

## "Too Many Open Files" Error

If you see `EMFILE: too many open files`, try these solutions:

### Solution 1: Increase File Limit (Quick Fix)

```bash
# Increase limit for current session
ulimit -n 4096

# Then start Expo
npm start
```

### Solution 2: Install Watchman (Recommended)

Watchman is Facebook's file watching service, recommended for React Native:

```bash
# Install via Homebrew
brew install watchman

# Then restart Expo
npm start
```

### Solution 3: Permanent Fix (macOS)

Add to your `~/.zshrc` or `~/.bash_profile`:

```bash
# Increase file descriptor limit
ulimit -n 4096
```

Then restart your terminal.

### Solution 4: Use the Fix Script

```bash
./fix-file-limit.sh
```

## Fix Dependency Version Issues

If you see version mismatch warnings:

```bash
npm run fix-deps
# or
npx expo install --fix
```

## Clear Cache

If you're having issues, try clearing the cache:

```bash
# Clear Expo cache
expo start -c

# Or clear Metro bundler cache
rm -rf node_modules/.cache
npm start -- --reset-cache
```

## Network Issues

If you can't connect from your phone:

1. Make sure your phone and computer are on the same WiFi
2. Find your computer's IP: `ifconfig | grep "inet "`
3. Update `API_BASE` in `App.js` to use your IP instead of `localhost`
4. Make sure Flask dashboard is running on port 8888

## Port Already in Use

If port 8081 is busy:

```bash
# Kill process on port 8081
lsof -ti:8081 | xargs kill -9

# Or use a different port
expo start --port 8082
```

