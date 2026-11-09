export async function onRequestPost(context) {
    try {
        const update = await context.request.json();
        const message = update.message;

        if (!message || !message.text) {
            return new Response("OK", { status: 200 });
        }

        const senderId = String(message.chat.id);
        const myChatId = String(context.env.TELEGRAM_CHAT_ID || "");
        const botToken = context.env.TELEGRAM_BOT_TOKEN;
        const githubToken = context.env.GITHUB_TOKEN;

        // --- SECURITY CHECK (Only YOU can execute commands) ---
        if (!myChatId || senderId !== myChatId) {
            console.warn(`Unauthorized attempt from chat ID: ${senderId}`);
            return new Response("Unauthorized", { status: 200 });
        }

        const text = message.text.trim();

        // 1. HELP / START COMMAND
        if (text === "/start" || text === "/help") {
            const helpMessage = 
                `👋 <b>Welcome Malachi!</b>\n\n` +
                `Here are the commands you can use right from your phone:\n\n` +
                `📊 <b>Check Website Views & Traffic:</b>\n` +
                `• <code>/stats</code> or <code>/views</code>\n\n` +
                `🚀 <b>Add & Publish a New Song:</b>\n` +
                `• <b>Quick:</b> <code>/add Way Maker by Sinach</code>\n` +
                `• <b>With Lyrics:</b>\n` +
                `<code>/add Oceans - Hillsong United\n` +
                `[Verse 1]\n` +
                `You call me out upon the waters...</code>\n\n` +
                `⚙️ <b>Other:</b>\n` +
                `• <code>/status</code> - Check bot health`;

            await sendTelegram(botToken, senderId, helpMessage);
            return new Response("OK", { status: 200 });
        }

        // 2. STATUS COMMAND
        if (text === "/status") {
            await sendTelegram(botToken, senderId, "✅ <b>Bot is active and securely connected to malachidaniel.com!</b>");
            return new Response("OK", { status: 200 });
        }

        // 3. STATS & ANALYTICS COMMAND (/stats or /views)
        if (text === "/stats" || text === "/views" || text === "/analytics") {
            if (!context.env || !context.env.SONG_REQUESTS) {
                await sendTelegram(botToken, senderId, "⚠️ <b>KV Database not connected!</b>\nPlease ensure SONG_REQUESTS is bound in Cloudflare.");
                return new Response("OK", { status: 200 });
            }

            const kv = context.env.SONG_REQUESTS;
            const now = new Date();
            const todayStr = getISTDate(now);
            const yesterdayDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            const yesterdayStr = getISTDate(yesterdayDate);

            let todayStats = null;
            let yesterdayStats = null;
            let totalViews = "0";

            try {
                const [todayRaw, yesterdayRaw, totalRaw] = await Promise.all([
                    kv.get(`stats_daily_${todayStr}`, "json"),
                    kv.get(`stats_daily_${yesterdayStr}`, "json"),
                    kv.get("stats_total")
                ]);
                todayStats = todayRaw;
                yesterdayStats = yesterdayRaw;
                totalViews = totalRaw || "0";
            } catch (err) {
                console.error("Failed to read stats from KV:", err);
            }

            const tViews = todayStats ? (todayStats.views || 0) : 0;
            const tVisitors = todayStats ? (todayStats.visitors || 0) : 0;
            const yViews = yesterdayStats ? (yesterdayStats.views || 0) : 0;
            const yVisitors = yesterdayStats ? (yesterdayStats.visitors || 0) : 0;

            let topSongsHtml = "• <i>No song pageviews recorded yet today.</i>";
            if (todayStats && todayStats.top && Object.keys(todayStats.top).length > 0) {
                const sorted = Object.entries(todayStats.top)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5);

                topSongsHtml = sorted.map((entry, idx) => {
                    const cleanName = formatPageTitle(entry[0]);
                    return `${idx + 1}. <b>${escapeHtml(cleanName)}</b> — ${entry[1]} view${entry[1] > 1 ? 's' : ''}`;
                }).join("\n");
            }

            const timeNow = now.toLocaleTimeString("en-US", {
                timeZone: "Asia/Kolkata",
                hour: "2-digit",
                minute: "2-digit"
            });

            const statsMessage = 
                `📊 <b>Website Analytics (malachidaniel.com)</b>\n\n` +
                `📅 <b>Today:</b>\n` +
                `• 👁️ <b>Views:</b> ${tViews.toLocaleString()}\n` +
                `• 👥 <b>Unique Visitors:</b> ${tVisitors.toLocaleString()}\n\n` +
                `⏮️ <b>Yesterday:</b>\n` +
                `• 👁️ <b>Views:</b> ${yViews.toLocaleString()}\n` +
                `• 👥 <b>Unique Visitors:</b> ${yVisitors.toLocaleString()}\n\n` +
                `📈 <b>All-Time Pageviews:</b> ${Number(totalViews).toLocaleString()}\n\n` +
                `🔥 <b>Top Pages Today:</b>\n${topSongsHtml}\n\n` +
                `🕒 <i>Live as of ${timeNow} IST</i>`;

            await sendTelegram(botToken, senderId, statsMessage);
            return new Response("OK", { status: 200 });
        }

        // 4. ADD SONG COMMAND
        if (text.startsWith("/add")) {
            if (!githubToken) {
                await sendTelegram(
                    botToken, 
                    senderId, 
                    "⚠️ <b>GitHub Token missing!</b>\nPlease add <code>GITHUB_TOKEN</code> to your Cloudflare Pages environment variables so I can commit files."
                );
                return new Response("OK", { status: 200 });
            }

            const payload = text.slice(4).trim();
            if (!payload) {
                await sendTelegram(
                    botToken, 
                    senderId, 
                    "❌ <b>Please specify the song!</b>\nExample: <code>/add Goodness of God by Bethel Music</code>"
                );
                return new Response("OK", { status: 200 });
            }

            let title = "";
            let artist = "Unknown Artist";
            let lyrics = "";

            const lines = payload.split("\n");
            const firstLine = lines[0].trim();

            if (firstLine.includes(" by ")) {
                const parts = firstLine.split(" by ");
                title = parts[0].trim();
                artist = parts.slice(1).join(" by ").trim();
            } else if (firstLine.includes(" - ")) {
                const parts = firstLine.split(" - ");
                title = parts[0].trim();
                artist = parts.slice(1).join(" - ").trim();
            } else {
                title = firstLine;
            }

            if (lines.length > 1) {
                lyrics = lines.slice(1).join("\n").trim();
            }

            if (!lyrics) {
                lyrics = "Lyrics coming soon...";
            }

            await sendTelegram(botToken, senderId, `⏳ Adding <b>${escapeHtml(title)}</b> by <b>${escapeHtml(artist)}</b>...`);

            // Fetch Apple Music Track ID automatically
            let appleId = "NONE";
            try {
                const itunesQuery = encodeURIComponent(`${title} ${artist}`.trim());
                const itunesRes = await fetch(`https://itunes.apple.com/search?term=${itunesQuery}&entity=song&limit=1`);
                if (itunesRes.ok) {
                    const itunesData = await itunesRes.json();
                    if (itunesData.resultCount > 0) {
                        appleId = String(itunesData.results[0].trackId);
                    }
                }
            } catch (err) {
                console.error("iTunes fetch failed:", err);
            }

            // Generate raw_lyrics standard format
            const fileContent = 
                `${title}\n` +
                `${artist}\n` +
                `meaning\n\n` +
                `apple_data\n` +
                `${appleId}\n` +
                `lyrics\n` +
                `${lyrics}\n`;

            const slug = slugify(`${title}-${artist}`);
            const filename = `${slug}.txt`;
            const githubPath = `raw_lyrics/${filename}`;

            // Commit to GitHub via GitHub API
            const repoOwner = "malachi8off-ship-it";
            const repoName = "malachidaniel";
            const commitUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/contents/${githubPath}`;

            const base64Content = btoa(unescape(encodeURIComponent(fileContent)));

            const commitRes = await fetch(commitUrl, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${githubToken}`,
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Cloudflare-Pages-TelegramBot",
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: `Add song: ${title} by ${artist} via Telegram`,
                    content: base64Content
                })
            });

            if (commitRes.ok) {
                const successMsg = 
                    `🚀 <b>Song Successfully Published!</b>\n\n` +
                    `🎼 <b>Title:</b> ${escapeHtml(title)}\n` +
                    `🎤 <b>Artist:</b> ${escapeHtml(artist)}\n` +
                    `🍎 <b>Apple Music ID:</b> ${appleId}\n` +
                    `📁 <b>File:</b> <code>${filename}</code>\n\n` +
                    `🌐 Cloudflare is deploying it live to <a href="https://malachidaniel.com">malachidaniel.com</a> in ~30 seconds!\n\n` +
                    `💻 <i>(Your laptop will sync this automatically next time you run <code>git pull</code> or start up)</i>`;

                await sendTelegram(botToken, senderId, successMsg);
            } else {
                const errData = await commitRes.text();
                console.error("GitHub commit error:", errData);
                await sendTelegram(botToken, senderId, `❌ <b>GitHub Commit Failed:</b>\n<code>${escapeHtml(errData.slice(0, 200))}</code>`);
            }

            return new Response("OK", { status: 200 });
        }

        return new Response("OK", { status: 200 });

    } catch (error) {
        console.error("Webhook error:", error);
        return new Response("Internal Error", { status: 200 });
    }
}

async function sendTelegram(botToken, chatId, htmlText) {
    if (!botToken || !chatId) return;
    try {
        await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                chat_id: chatId,
                text: htmlText,
                parse_mode: "HTML",
                disable_web_page_preview: true
            })
        });
    } catch (e) {
        console.error("Failed to send telegram message:", e);
    }
}

function getISTDate(date) {
    return date.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
}

function formatPageTitle(path) {
    if (!path || path === "/" || path === "/index.html") return "🏠 Homepage";
    if (path.includes("presenter.html")) return "📺 Presenter View";
    if (path.includes("request.html")) return "📝 Request Page";
    if (path.includes("lyrics-archive/index.html")) return "📚 All Lyrics Archive";
    if (path.includes("karaoke-tracks/index.html")) return "🎤 Karaoke Hub";

    let name = path.split("/").pop() || path;
    name = name.replace(".html", "").replace(".txt", "");
    name = name.replace(/-/g, " ").replace(/_/g, " ");
    return name.replace(/\b\w/g, c => c.toUpperCase());
}

function slugify(text) {
    return text
        .toString()
        .toLowerCase()
        .trim()
        .replace(/[\s\W-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
