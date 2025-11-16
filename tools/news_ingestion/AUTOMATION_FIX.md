# Automation Fix Summary

## Issue Identified

The launchd automation service is failing due to macOS security restrictions on the Downloads folder. When the laptop is locked or sleeping, macOS restricts access to files in the Downloads folder, causing the error:

```
Operation not permitted
can't open file '/Users/josh_li/Downloads/bofa_hqla/tools/news_ingestion/run_daily.sh'
```

## Fixes Applied

1. **Updated Python Path**: Changed from pyenv shim to actual Python binary
   - Old: `/Users/josh_li/.pyenv/shims/python3`
   - New: `/Users/josh_li/.pyenv/versions/3.12.11/bin/python3`

2. **Added Environment Variables**: Added PATH and PYENV_ROOT to plist for proper environment setup

3. **Verified Plist**: Confirmed plist syntax is valid and service is loaded

## Remaining Issue: macOS Downloads Folder Security

The Downloads folder has special security restrictions in macOS. When the laptop is locked or sleeping, launchd cannot access files in Downloads.

## Solutions (Choose One)

### Option 1: Grant Full Disk Access (Quick Fix)

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Privacy & Security** → **Full Disk Access**
3. Click the **+** button
4. Navigate to and add:
   - `/Users/josh_li/.pyenv/versions/3.12.11/bin/python3`
   - Or add Terminal/iTerm if you use it to run scripts
5. Restart your Mac or reload the service:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.news.ingestion.plist
   launchctl load ~/Library/LaunchAgents/com.news.ingestion.plist
   ```

### Option 2: Move Project Out of Downloads (Recommended)

Move the project to a location that doesn't have these restrictions:

```bash
# Create a projects directory
mkdir -p ~/Projects

# Move the project
mv ~/Downloads/bofa_hqla ~/Projects/

# Update the plist paths
# Edit ~/Library/LaunchAgents/com.news.ingestion.plist
# Change all occurrences of:
#   /Users/josh_li/Downloads/bofa_hqla
# To:
#   /Users/josh_li/Projects/bofa_hqla

# Reload the service
launchctl unload ~/Library/LaunchAgents/com.news.ingestion.plist
launchctl load ~/Library/LaunchAgents/com.news.ingestion.plist
```

### Option 3: Use Cron Instead (Alternative)

If launchd continues to have issues, you can use cron:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 6 AM daily)
0 6 * * * /Users/josh_li/.pyenv/versions/3.12.11/bin/python3 /Users/josh_li/Downloads/bofa_hqla/tools/news_ingestion/run_daily.sh >> /Users/josh_li/Downloads/bofa_hqla/tools/news_ingestion/logs/cron.log 2>&1
```

## Verification

After applying a fix, verify it works:

1. **Check service status**:
   ```bash
   launchctl list com.news.ingestion
   ```

2. **Manually trigger a test run**:
   ```bash
   launchctl start com.news.ingestion
   ```

3. **Check logs**:
   ```bash
   tail -f ~/Downloads/bofa_hqla/tools/news_ingestion/logs/launchd.log
   tail -f ~/Downloads/bofa_hqla/tools/news_ingestion/logs/launchd.error.log
   ```

4. **Wait for scheduled run**: Check tomorrow at 6 AM if the pipeline ran automatically

## Current Status

- ✅ Plist configuration: Fixed and valid
- ✅ Python path: Updated to use actual binary
- ✅ Environment variables: Added
- ⚠️ macOS security: Needs Full Disk Access or project move

## Next Steps

1. Apply one of the solutions above (Option 1 is quickest)
2. Test the automation by manually triggering: `launchctl start com.news.ingestion`
3. Monitor logs tomorrow morning to confirm 6 AM run works
4. If issues persist, consider Option 2 (moving project)

