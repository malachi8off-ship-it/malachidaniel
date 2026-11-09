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
            // Return 200 to Telegram so it doesn't keep retrying
            return new Response("Unauthorized", { status: 200 });
        }

        const text = message.text.trim();

        // 1. HELP COMMAND
        if (text === "/start" || text === "/help") {
            const helpMessage = 
                `👋 <b>Welcome Malachi!</b>\n\n` +
                `Here is how you can publish songs to your website directly from your phone:\n\n` +
                `<b>Option 1: Quick Add (Title by Artist)</b>\n` +
                `<code>/add Way Maker by Sinach</code>\n\n` +
                `<b>Option 2: Add with Lyrics</b>\n` +
                `<code>/add Oceans - Hillsong United\n` +
                `[Verse 1]\n` +
                `You call me out upon the waters\n` +
                `The great unknown where feet may fail...</code>\n\n` +
                `<b>Other Commands:</b>\n` +
                `• <code>/status</code> - Check repository status\n` +
                `• <code>/help</code> - Show this menu`;

            await sendTelegram(botToken, senderId, helpMessage);
            return new Response("OK", { status: 200 });
        }

        // 2. STATUS COMMAND
        if (text === "/status") {
            await sendTelegram(botToken, senderId, "✅ <b>Bot is active and securely connected to malachidaniel.com!</b>");
            return new Response("OK", { status: 200 });
        }

        // 3. ADD SONG COMMAND
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

            // Check if user wrote "Title by Artist" or "Title - Artist"
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

            // Remaining lines (if any) are the lyrics
            if (lines.length > 1) {
                lyrics = lines.slice(1).join("\n").trim();
            }

            if (!lyrics) {
                lyrics = "Lyrics coming soon...";
            }

            // Notify Malachi that we're processing
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
