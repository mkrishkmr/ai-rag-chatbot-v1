# 🚀 Deployment Guide: Groww Fact Engine

Your project code is now strictly tailored for production deployment. Follow these exact steps to push your AI engine live onto **Render (Backend)** and **Vercel (Frontend)**.

---

## Step 1: Push Code to GitHub

First, you must push this entire directory to a new public or private GitHub repository.

```bash
git init
git add .
git commit -m "feat: Ready for production deployment"
git branch -M main
# Add your GitHub remote and push
git remote add origin https://github.com/your-username/groww-ai-engine.git
git push -u origin main
```

---

## Step 2: Deploy Backend to Render

You are going to use Render's "Blueprint" feature which auto-configures the server based on the `render.yaml` file I just generated.

1. Create an account on [Render.com](https://render.com/).
2. On your Render Dashboard, click **New +** and select **Blueprint**.
3. Connect your GitHub account and select the repository you just created in Step 1.
4. Render will automatically detect the `render.yaml` blueprint. Click **Apply**.
5. The `render-build.sh` script will run, installing Python requirements and the headless Chromium binaries required for Playwright.
6. **Important: Provide Environment Variables**. Render will prompt you to enter the values for:
   * `GROQ_API_KEY`
   * `GOOGLE_API_KEY`
7. Copy the final assigned `*.onrender.com` URL once the service goes live.

---

## Step 3: Deploy Frontend to Vercel

Vercel is natively tailored for Next.js applications and will recognize the `frontend` folder instantly.

1. Create an account on [Vercel.com](https://vercel.com).
2. On the dashboard, click **Add New** -> **Project**.
3. Import your GitHub repository.
4. In the configuration settings, **change the Root Directory** from `/` to `frontend`.
5. Open the **Environment Variables** tab and add:
   * **Name**: `NEXT_PUBLIC_API_URL`
   * **Value**: *[The URL of your Render backend from step 2]* (e.g., `https://groww-fact-engine-api.onrender.com`)
6. Click **Deploy**. Vercel will install the Node modules, build Next.js, and provide a live sharing URL.
