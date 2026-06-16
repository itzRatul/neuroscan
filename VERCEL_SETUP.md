# NeuroScan Vercel Deployment Setup Guide

## Architecture
The application is deployed across multiple platforms:

```
┌─────────────────────────────────────┐
│  Vercel Web App                     │
│  (neuroscan.vercel.app)             │
│  - Photo Scan HTML/JS               │
│  - AI Chat Interface                │
│  - Research Hub                     │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────────────┐ ┌──────▼──────────────┐
│ HuggingFace Space 1 │ │ HuggingFace Space 2 │
│ Photo Scan Backend  │ │ AI Chat Backend     │
│ https://itzratul-   │ │ https://itzratul-   │
│ neuroscan-          │ │ neuroscan-chat-     │
│ backend.hf.space    │ │ backend.hf.space    │
└─────────────────────┘ └─────────────────────┘
```

## Current Setup (Already Configured)

### ✅ Frontend URLs (Updated)
Both HTML files are configured to use Hugging Face backends:

**Photo Scan (`webapp/photo-scan.html`):**
```javascript
let BACKEND_URL = localStorage.getItem('ns_backend_url') 
  || 'https://itzratul-neuroscan-backend.hf.space';
```

**AI Chat (`webapp/ai-chat.html`):**
```javascript
const CHAT_BACKEND_URL = localStorage.getItem('ns_chat_backend_url') 
  || 'https://itzratul-neuroscan-chat-backend.hf.space';
```

### ✅ Backend Configurations
Both backends have CORS enabled for all origins (`allow_origins=["*"]`).

### ✅ Environment Variables (Hugging Face)
```
MAIN_BACKEND_URL=https://itzratul-neuroscan-backend.hf.space
CHAT_BACKEND_URL=https://itzratul-neuroscan-chat-backend.hf.space
```

## Deployment Steps

### 1. Deploy to Vercel

```bash
vercel deploy --prod
```

Or connect your GitHub repo directly to Vercel for continuous deployment.

### 2. Verify Backend URLs

Test the backends are accessible:

```bash
# Main Backend (Photo Scan)
curl https://itzratul-neuroscan-backend.hf.space/health

# Chat Backend
curl https://itzratul-neuroscan-chat-backend.hf.space/
```

Expected responses:
```json
{ "status": "ok", "service": "NeuroScan Face Analysis API" }
{ "status": "ok", "service": "NeuroScan AI Chat Backend" }
```

### 3. Test from Vercel

Once deployed, test the functionality:

1. **Photo Scan**: Upload an image → should call `https://itzratul-neuroscan-backend.hf.space/analyze`
2. **AI Chat**: Send a message → should call `https://itzratul-neuroscan-chat-backend.hf.space/chat`

Open browser DevTools (F12) → Network tab to verify requests are going to the correct URLs.

## Troubleshooting

### Issue: Chat not connecting on Vercel
- **Check 1**: Browser DevTools → Network tab
  - Look for requests to `https://itzratul-neuroscan-chat-backend.hf.space/chat`
  - Check the response status and error messages

- **Check 2**: CORS Headers
  - Both backends send `Access-Control-Allow-Origin: *`
  - If you see CORS errors, ensure the HF backends are running and CORS is enabled

- **Check 3**: Backend Status
  - Visit `https://itzratul-neuroscan-backend.hf.space/health`
  - Visit `https://itzratul-neuroscan-chat-backend.hf.space/`
  - If they return 404 or timeout, the spaces may need to restart

### Issue: Photo scan taking too long
- Photo scan API calls the ML model (can take 30-60 seconds)
- Check HF Space logs if it times out
- May need to increase API timeout or upgrade HF Space resources

### Issue: Images/PDFs not loading after scan
- Check that the image URLs are being constructed correctly
- PDFs are served from `${BACKEND_URL}/results/{session_id}/...`
- Verify files exist in the HF Space's results directory

## Advanced Configuration

### Custom Backend URLs (for testing)

Users can override backend URLs in localStorage via browser console:

```javascript
// Override chat backend
localStorage.setItem('ns_chat_backend_url', 'http://localhost:8001');

// Override photo scan backend  
localStorage.setItem('ns_backend_url', 'http://localhost:8000');

// Override API key
localStorage.setItem('ns_api_key', 'your-api-key');

// Reload page
window.location.reload();
```

### Environment Variables (Future Enhancement)

To make it easier to configure backends via environment variables in Vercel:

1. Go to Vercel Dashboard → Project Settings → Environment Variables
2. Add:
   - `NEXT_PUBLIC_BACKEND_URL` = `https://itzratul-neuroscan-backend.hf.space`
   - `NEXT_PUBLIC_CHAT_BACKEND_URL` = `https://itzratul-neuroscan-chat-backend.hf.space`

Then update HTML files to use these:
```javascript
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL 
  || localStorage.getItem('ns_backend_url')
  || 'https://itzratul-neuroscan-backend.hf.space';
```

## Monitoring & Maintenance

### Check HF Space Status
```bash
python scratch/check_logs.py  # View recent HF space logs
python scratch/check_stage.py # Check deployment stage
```

### Update Environment Variables on HF
```bash
python scratch/setup_space_env.py  # Re-sync secrets and variables
```

### Health Check Endpoints
- **Main Backend**: `https://itzratul-neuroscan-backend.hf.space/health`
- **Chat Backend**: `https://itzratul-neuroscan-chat-backend.hf.space/` (root endpoint)

## CORS Configuration Details

Both backends are configured with:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow all origins (including Vercel)
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],            # Allow all headers including Content-Type
)
```

This means:
- ✅ Requests from `neuroscan.vercel.app` are accepted
- ✅ Requests from localhost during development are accepted
- ✅ Cross-origin requests with credentials are allowed
- ⚠️ For production, consider restricting `allow_origins` to specific domains

## Summary

| Component | URL | Status |
|-----------|-----|--------|
| Web App | https://neuroscan.vercel.app | Hosted on Vercel ✅ |
| Photo Backend | https://itzratul-neuroscan-backend.hf.space | Hosted on HF Spaces ✅ |
| Chat Backend | https://itzratul-neuroscan-chat-backend.hf.space | Hosted on HF Spaces ✅ |
| Frontend Config | localStorage + HTML defaults | Updated ✅ |
| CORS Settings | Both backends: `*` | Enabled ✅ |
| Environment Vars | HF Spaces secrets setup | Configured ✅ |

Everything is configured! The app should now work seamlessly with Vercel frontend and HuggingFace backends.
