# 🌐 Cloudflare Tunnel Demo

This workflow demonstrates how to expose services running in GitHub Actions to the public internet using Cloudflare Tunnel - **completely free** and without any account setup!

## 🎯 What This Does

Exposes your GitHub Actions runner to the internet via Cloudflare Tunnel, allowing you to:

- ✅ **Share live demos** with recruiters/interviewers
- ✅ **Test webhooks** that need public URLs
- ✅ **Debug remotely** without SSH
- ✅ **Demo ML APIs** in real-time
- ✅ **Zero configuration** - no Cloudflare account needed
- ✅ **Free** - uses GitHub Actions free tier

## 🚀 Quick Start

### Step 1: Trigger the Workflow

1. Go to **Actions** tab in your GitHub repository
2. Select **"🌐 Cloudflare Tunnel Demo"** workflow
3. Click **"Run workflow"**
4. Choose your options:
   - **Service to expose:**
     - `ml-inference` - ML API only
     - `static-web` - Demo website only
     - `both` - Both services
   - **Keep tunnel open:** Duration in minutes (default: 15)
5. Click **"Run workflow"**

### Step 2: Get Your Public URL

Watch the workflow logs. After ~10-15 seconds, you'll see:

```
================================================
📋 PUBLIC URLS - Share these links:
================================================

🤖 ML Inference API:
   https://abc123def.trycloudflare.com

📄 Demo Website:
   https://xyz789uvw.trycloudflare.com
================================================
```

### Step 3: Share and Test!

**Share the URLs** - anyone can access them! The tunnels stay open for the duration you specified.

## 📚 Service Options

### Option 1: ML Inference API

Exposes the FastAPI ML inference service:

**What you get:**
- ✅ Sentiment analysis API
- ✅ Swagger docs at `/docs`
- ✅ Health checks at `/health`
- ✅ Prometheus metrics at `/metrics`

**Example usage:**
```bash
# Replace with your actual URL from the logs
URL="https://abc123def.trycloudflare.com"

# Health check
curl $URL/health

# Predict sentiment
curl -X POST $URL/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing!"}'

# Batch prediction
curl -X POST $URL/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Great!", "Terrible!", "Okay"]}'

# Interactive docs
open $URL/docs
```

### Option 2: Static Demo Website

Serves a beautiful demo page with:

- ✅ Project overview
- ✅ Interactive API testing
- ✅ Live metrics display
- ✅ Links to documentation

**Perfect for:**
- Showing to recruiters
- Portfolio demonstrations
- Quick project showcases

### Option 3: Both Services

Runs both services simultaneously with separate public URLs.

## 🎓 Use Cases

### 1. **Interview Demonstrations**

```yaml
# Run before interview:
Service: both
Duration: 30 minutes

# During interview:
"Let me show you the live demo..."
- Share demo website URL
- Walk through API endpoints
- Show real-time metrics
```

### 2. **Webhook Testing**

```yaml
# For testing GitHub webhooks, Slack bots, etc:
Service: ml-inference
Duration: 10 minutes

# Use the public URL as webhook target:
https://abc123.trycloudflare.com/webhook
```

### 3. **Quick API Testing**

```yaml
# Test your API from mobile/tablet:
Service: ml-inference
Duration: 15 minutes

# Access from any device - no VPN needed!
```

### 4. **Portfolio Showcase**

```yaml
# Show your project to anyone:
Service: static-web
Duration: 20 minutes

# Share the URL - they see your polished demo page
```

## 💡 Advanced Features

### Customize the Demo Page

Edit `.github/workflows/cloudflare-tunnel-demo.yml` to customize the static page:

```yaml
# Find the "Create static demo page" step
# Modify the HTML in the heredoc
cat > /tmp/demo-site/index.html << 'EOF'
<!DOCTYPE html>
<html>
  <!-- Your custom HTML here -->
</html>
EOF
```

### Add More Services

You can expose additional ports:

```yaml
# In the "Start Cloudflare Tunnels" step:
cloudflared tunnel --url http://localhost:3000 > /tmp/cf-app.log 2>&1 &
cloudflared tunnel --url http://localhost:5000 > /tmp/cf-api.log 2>&1 &
```

### Extend Tunnel Duration

Maximum is 30 minutes (workflow timeout). To extend:

```yaml
# In the workflow file, change:
timeout-minutes: 30  # Increase this
```

## 🔒 Security Notes

### ✅ **Safe:**
- Temporary URLs (expire when workflow ends)
- No persistent access
- URLs are random and hard to guess
- Controlled by you (manual trigger)

### ⚠️ **Be Careful:**
- URLs are **public** - anyone with the link can access
- Don't expose sensitive data
- Monitor the logs for access patterns
- Use for demos/testing only, not production

## 🐛 Troubleshooting

### "Tunnel not appearing in logs"

Wait 10-15 seconds after the step starts. Cloudflare takes a moment to provision.

### "Connection refused"

The service might not be ready. Check:
```yaml
# Add more wait time:
sleep 10  # Instead of sleep 5
```

### "Tunnel closed early"

Default duration is 15 minutes. Increase via input parameter or in the workflow file.

### "Can't access the URL"

1. Check if workflow is still running
2. Copy the URL exactly (including https://)
3. Try a different browser
4. Check for firewall/VPN issues

## 📊 Monitoring

### View Live Logs

Watch the workflow in real-time:
1. Go to Actions → Running workflow
2. Click on the job
3. Expand "Start Cloudflare Tunnels" step
4. See the public URLs and keep the tab open

### Access Logs

After the workflow completes:
1. Check "Show tunnel logs" step
2. See how many people accessed your service
3. Review any errors

## 💰 Cost

**$0.00** - Completely free!

- GitHub Actions: Unlimited for public repos
- Cloudflare Tunnel: Free tier (no account needed)
- Duration: Up to 30 minutes per run

## 🎯 Best Practices

1. **Before interviews:**
   - Run workflow 5 minutes before
   - Test the URL yourself first
   - Have the demo website ready

2. **For demos:**
   - Use `both` option for full experience
   - Set 20-30 minutes duration
   - Prepare a script of what to show

3. **For testing:**
   - Use specific service types
   - Shorter duration (10-15 min)
   - Monitor logs for debugging

## 📚 Example Scenarios

### Scenario 1: Job Interview

```yaml
# 5 minutes before interview:
1. Trigger workflow (both services, 30 min)
2. Get URLs from logs
3. Test both URLs
4. Share demo website URL with interviewer

# During interview:
"I have a live demo running on GitHub Actions..."
- Walk through the demo page
- Show API in action
- Discuss the architecture
```

### Scenario 2: Quick API Test

```yaml
# Need to test from phone:
1. Trigger workflow (ml-inference, 10 min)
2. Copy URL to phone
3. Test API endpoints
4. Debug any issues
```

### Scenario 3: Portfolio Showcase

```yaml
# Showing to friend/colleague:
1. Trigger workflow (static-web, 15 min)
2. Share the beautiful demo page
3. Let them click through features
4. Answer questions
```

## 🔗 Related Workflows

- **🔧 Debug SSH Access** - For interactive debugging
- **🎯 GitOps Infrastructure Demo** - Full deployment demo

## 📖 Learn More

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Ready to share your work with the world? Run the workflow and get your public URL in seconds!** 🚀
