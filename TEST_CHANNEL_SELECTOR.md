# Testing Guide: YouTube Channel Video Selector

## 🚀 Quick Start

### 1. Start the Streamlit App

```bash
# Option 1: Use the run script
./run_streamlit.sh

# Option 2: Run directly
cd ui
streamlit run streamlit_app.py
```

The app will open at: **http://localhost:8501**

### 2. Navigate to Verify Video Tab

- The "🎬 Verify YouTube Video" tab should be selected by default
- If not, click on it in the sidebar

---

## ✅ Test Cases

### Test 1: Basic Channel Handle (@username)

**Steps:**
1. In the "📺 Select from Channel" section, enter:
   ```
   https://www.youtube.com/@NextMedHealth
   ```
2. Wait for videos to load (should show spinner)
3. Verify:
   - ✅ Success message: "✅ Found X videos"
   - ✅ Dropdown appears with video list
   - ✅ Videos show: Title - Date - View count

**Expected Result:**
- Videos load successfully
- Dropdown shows latest 20 videos
- Each video shows title, publish date, and view count

---

### Test 2: Channel Handle with /videos Path

**Steps:**
1. Enter:
   ```
   https://www.youtube.com/@NextMedHealth/videos
   ```
2. Verify same behavior as Test 1

**Expected Result:**
- Works identically to Test 1
- URL parsing handles `/videos` suffix correctly

---

### Test 3: Channel ID Format

**Steps:**
1. Enter a channel ID URL (find one from a channel's About page):
   ```
   https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx
   ```
2. Verify videos load

**Expected Result:**
- Videos load successfully
- Works with direct channel ID

---

### Test 4: Legacy Username Format

**Steps:**
1. Enter legacy format (if you know a channel's username):
   ```
   https://www.youtube.com/user/username
   ```
2. Verify videos load

**Expected Result:**
- Videos load (may fallback to yt-dlp if API doesn't support)

---

### Test 5: Video Selection from Dropdown

**Steps:**
1. Enter a valid channel URL (e.g., `@NextMedHealth`)
2. Wait for videos to load
3. Select a video from the dropdown
4. Verify:
   - ✅ "Selected: [Video Title]" message appears
   - ✅ Video URL field below is populated with the selected video URL
   - ✅ Video URL shows green checkmark validation

**Expected Result:**
- Selected video URL populates the "YouTube Video URL" field
- URL is validated and shows as valid
- Can proceed to click "Start Verification"

---

### Test 6: Direct Video URL Still Works

**Steps:**
1. Skip channel selection
2. Scroll to "🎬 Or Enter Video URL Directly"
3. Enter a direct video URL:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
4. Verify:
   - ✅ URL validates correctly
   - ✅ Green checkmark appears
   - ✅ Can start verification

**Expected Result:**
- Direct video URL input still works as before
- No regression in existing functionality

---

### Test 7: Invalid Channel URL

**Steps:**
1. Enter invalid channel URL:
   ```
   https://www.youtube.com/@InvalidChannelThatDoesNotExist12345
   ```
2. Verify:
   - ✅ Error message appears
   - ✅ Clear error: "Channel not found" or similar
   - ✅ No crash or infinite loading

**Expected Result:**
- Graceful error handling
- User-friendly error message
- App remains functional

---

### Test 8: Empty Channel

**Steps:**
1. Find a channel with no videos (if possible)
2. Enter its URL
3. Verify:
   - ✅ Warning message: "No videos found for this channel"
   - ✅ No crash

**Expected Result:**
- Handles empty channels gracefully
- Shows appropriate message

---

### Test 9: Channel URL Change Detection

**Steps:**
1. Enter a channel URL (e.g., `@NextMedHealth`)
2. Wait for videos to load
3. Select a video from dropdown
4. Change the channel URL to a different channel
5. Verify:
   - ✅ Video selection resets
   - ✅ New channel's videos load
   - ✅ Previous selection is cleared

**Expected Result:**
- State resets when channel URL changes
- No stale data from previous channel

---

### Test 10: API Fallback (if API unavailable)

**Steps:**
1. Temporarily remove or invalidate `YOUTUBE_API_KEY` in `.env`
2. Enter a channel URL
3. Verify:
   - ✅ Still works (falls back to yt-dlp)
   - ✅ Videos still load
   - ✅ May be slower but functional

**Expected Result:**
- Graceful fallback to yt-dlp
- Feature still works without API key
- User sees videos (may take longer)

---

### Test 11: Caching Behavior

**Steps:**
1. Enter a channel URL
2. Wait for videos to load
3. Change to a different channel
4. Change back to the first channel
5. Verify:
   - ✅ Videos load instantly (from cache)
   - ✅ No spinner (or very brief)

**Expected Result:**
- Cached results load quickly
- Reduces API calls for repeated channels

---

### Test 12: Full Verification Flow

**Steps:**
1. Enter channel URL: `https://www.youtube.com/@NextMedHealth`
2. Select a video from dropdown
3. Verify video URL is populated
4. Click "🚀 Start Verification"
5. Verify:
   - ✅ Verification starts normally
   - ✅ Processing tab shows progress
   - ✅ No errors related to channel selection

**Expected Result:**
- Complete workflow works end-to-end
- Selected video verifies successfully
- No integration issues

---

## 🔍 What to Check

### UI Elements

- [ ] Channel URL input field appears
- [ ] Video dropdown appears after entering channel URL
- [ ] Dropdown shows video titles, dates, and view counts
- [ ] Selected video populates the video URL field
- [ ] Tips section is helpful and clear
- [ ] Example buttons are removed (no "Load Example 1/2")

### Functionality

- [ ] Channel URL parsing works for all formats
- [ ] Videos fetch successfully (API and fallback)
- [ ] Video selection updates URL field
- [ ] Direct video URL input still works
- [ ] Error messages are clear and helpful
- [ ] Loading states show appropriately

### Error Handling

- [ ] Invalid URLs show error messages
- [ ] Non-existent channels show error
- [ ] Empty channels show warning
- [ ] API failures fallback gracefully
- [ ] No crashes or infinite loops

### Performance

- [ ] Videos load within reasonable time (< 10 seconds)
- [ ] Caching works (repeated channels load instantly)
- [ ] UI remains responsive during loading

---

## 🐛 Common Issues & Solutions

### Issue: Videos don't load

**Possible Causes:**
- YouTube API key not configured
- Channel URL format incorrect
- Network issues

**Solutions:**
- Check `.env` file has `YOUTUBE_API_KEY` set
- Verify channel URL format (should start with `https://www.youtube.com/@`)
- Check browser console for errors
- Try fallback (remove API key temporarily to test yt-dlp)

### Issue: Selected video doesn't populate URL field

**Possible Causes:**
- Session state not updating
- Widget key conflicts

**Solutions:**
- Refresh the page
- Check browser console for errors
- Try selecting a different video

### Issue: Dropdown shows "-- Select a video --" but no videos

**Possible Causes:**
- Channel has no videos
- API returned empty results
- Parsing error

**Solutions:**
- Try a different channel
- Check error message for details
- Verify channel URL is correct

---

## 📝 Test Checklist

Use this checklist when testing:

```
Basic Functionality:
[ ] Channel handle format works (@username)
[ ] Channel ID format works (/channel/UC...)
[ ] Legacy username format works (/user/...)
[ ] Videos load and display in dropdown
[ ] Video selection populates URL field
[ ] Direct video URL still works

Error Handling:
[ ] Invalid URL shows error
[ ] Non-existent channel shows error
[ ] Empty channel shows warning
[ ] API failure falls back gracefully

UI/UX:
[ ] Loading spinner appears
[ ] Success messages appear
[ ] Error messages are clear
[ ] Tips section is helpful
[ ] Example buttons removed

Integration:
[ ] Selected video can start verification
[ ] Full workflow works end-to-end
[ ] No regressions in existing features

Performance:
[ ] Videos load in reasonable time
[ ] Caching works
[ ] UI remains responsive
```

---

## 🎯 Recommended Test Channels

Here are some channels you can use for testing:

1. **NextMedHealth** (mentioned in requirements):
   ```
   https://www.youtube.com/@NextMedHealth
   ```

2. **Popular channels** (likely to have videos):
   - Any verified YouTube channel
   - Channels you follow

3. **Test with different channel types:**
   - Large channels (many videos)
   - Small channels (few videos)
   - New channels (recent videos)

---

## 📊 Expected Test Results

After completing all tests, you should verify:

✅ **All basic functionality works**
✅ **Error handling is robust**
✅ **UI is intuitive and helpful**
✅ **No regressions in existing features**
✅ **Performance is acceptable**

---

## 🚀 Next Steps After Testing

If all tests pass:

1. ✅ Feature is ready for use
2. ✅ Consider adding to documentation
3. ✅ May want to add more curated channel suggestions
4. ✅ Consider adding channel search/discovery (Phase 2)

If issues are found:

1. Note the specific test case that failed
2. Check browser console for errors
3. Check Streamlit terminal output
4. Review error messages
5. Fix issues and retest

---

## 💡 Tips for Testing

- **Use browser DevTools**: Check console for JavaScript errors
- **Check Streamlit logs**: Terminal output shows Python errors
- **Test with different channels**: Variety helps catch edge cases
- **Test with/without API key**: Ensures fallback works
- **Clear cache**: Use `Ctrl+Shift+R` to hard refresh if caching issues

---

Happy Testing! 🎉

