# Deployment Guide

This bot can be deployed on any platform that supports Docker. Here are instructions for two popular "free tier" friendly platforms: **Render** and **Railway**.

## Prerequisites
- A **GitHub account** (to host your code).
- An **Instagram account** (username/password) for the bot to use.
- A **Telegram Bot Token** (from @BotFather).

## 1. Push Code to GitHub
1. Create a new repository on GitHub.
2. Push the code from `insta_frame_bot` directory to this repository.

## 2. Deploy on Render.com (Free Tier available)
1. Sign up/Log in to [Render.com](https://render.com).
2. Click **New +** -> **Background Worker** (Recommended for Bots) or **Web Service**.
   - *Note: Free Web Services spin down after inactivity. Background Workers are paid. If you want truly free, you might need "Web Service" and use a cron job to ping it, or accept it sleeps.*
3. Connect your GitHub repository.
4. **Runtime**: Docker.
5. **Environment Variables**:
   Add the following variables:
   - `BOT_TOKEN`: Your Telegram Bot Token.
   - `INSTAGRAM_USERNAME`: Your Instagram Username.
   - `INSTAGRAM_PASSWORD`: Your Instagram Password.
6. Click **Create Service**.
7. **Important**: Once deployed, your service will have a URL (e.g., `https://my-bot.onrender.com`).
8. Go to [UptimeRobot.com](https://uptimerobot.com), create a free account.
9. Add a **New Monitor**:
   - Type: HTTP(s)
   - URL: `https://my-bot.onrender.com`
   - Interval: 5 minutes.
   - This prevents the bot from "sleeping".

## 3. Deploy on Railway.app (Trial/Hobby)
1. Sign up at [Railway.app](https://railway.app).
2. Click **New Project** -> **GitHub Repo**.
3. Select your repository.
4. Go to **Variables** tab.
5. Add:
   - `BOT_TOKEN`
   - `INSTAGRAM_USERNAME`
   - `INSTAGRAM_PASSWORD`
6. Railway detects the `Dockerfile` and builds automatically.

## Important Notes on "Free" Hosting
- **Instagram Login Challenges**: Instagram often flags logins from data center IPs (like AWS/GCP used by Render/Railway) as suspicious. You might get "Challenge Required" errors.
    - **Fix**: Login locally first using `instaloader`, export the session file, and copy it to the server (more advanced).
    - **Alternative**: Use a proxy (requires code changes).
- **Disk Space**: The bot downloads videos temporarily. Ensure the platform has some ephemeral disk space (Docker containers usually do). The bot cleans up after itself.
- **Memory**: Video processing with OpenCV can vary in RAM usage. 512MB RAM (common free tier limit) should be enough for short, standard-def videos, but might crash on 4K long videos.
