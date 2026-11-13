export async function onRequestPost(context) {
    try {
        const update = await context.request.json();
        const myChatId = String(context.env.TELEGRAM_CHAT_ID || "");
        const botToken = context.env.TELEGRAM_BOT_TOKEN;
        const githubToken = context.env.GITHUB_TOKEN;

        // -------------------------------------------------------------
        // A. HANDLE INLINE BUTTON TAPS (CALLBACK QUERIES)
        // -------------------------------------------------------------
        if (update.callback_query) {
            const cb = update.callback_query;
            const senderId = String(cb.from.id);

            if (!myChatId || senderId !== myChatId) {
                return new Response("Unauthorized", { status: 200 });
            }

            const data = cb.data || "";
            await answerCallbackQuery(botToken, cb.id);

            // 1. Preview Song from madely.us
            if (data.startsWith("m_prev:")) {
                const url = decodeURIComponent(data.slice(7));
                await editTelegramMessage(botToken, senderId, cb.message.message_id, "⏳ <i>Fetching and cleaning lyrics from madely.us...</i>");
                
                const song = await fetchMadelySong(url);
                if (!song) {
                    await editTelegramMessage(botToken, senderId, cb.message.message_id, "❌ <i>Failed to load song from source.</i>");
                    return new Response("OK", { status: 200 });
                }

                const previewMal = song.mal ? song.mal.split("\n").slice(0, 4).join("\n") : "";
                const previewMan = song.man ? song.man.split("\n").slice(0, 4).join("\n") : "";

                const msg =
                    `🎵 <b>${escapeHtml(song.title)}</b>\n` +
                    `🎤 <b>Artist:</b> Malayalam Worship\n\n` +
                    (previewMal ? `<b>[Malayalam Script]</b>\n<i>${escapeHtml(previewMal)}...</i>\n\n` : "") +
                    (previewMan ? `<b>[Manglish / English Script]</b>\n<i>${escapeHtml(previewMan)}...</i>\n\n` : "") +
                    `<i>Publish this song to malachidaniel.com?</i>`;

                const buttons = {
                    inline_keyboard: [
                        [
                            { text: "✅ Publish to Site", callback_data: `m_pub:${encodeURIComponent(url)}` },
                            { text: "❌ Cancel", callback_data: "cancel" }
                        ]
                    ]
                };
                await editTelegramMessage(botToken, senderId, cb.message.message_id, msg, buttons);
                return new Response("OK", { status: 200 });
            }

            // 2. Publish Song to GitHub from madely.us
            if (data.startsWith("m_pub:")) {
                const url = decodeURIComponent(data.slice(6));
                await editTelegramMessage(botToken, senderId, cb.message.message_id, "⏳ <i>Fetching Apple Music ID & committing to GitHub...</i>");
                
                const song = await fetchMadelySong(url);
                if (!song) {
                    await editTelegramMessage(botToken, senderId, cb.message.message_id, "❌ <i>Failed to load song.</i>");
                    return new Response("OK", { status: 200 });
                }

                let lyricsBody = "";
                if (song.mal && song.man) {
                    lyricsBody = `[Malayalam]\n${song.mal}\n\n[Manglish]\n${song.man}`;
                } else if (song.mal) {
                    lyricsBody = song.mal;
                } else {
                    lyricsBody = song.man;
                }

                const title = song.title;
                const artist = "Malayalam Worship";

                // Fetch Apple Music Track ID
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
                } catch (e) {
                    console.error("iTunes fetch error:", e);
                }

                const fileContent =
                    `${title}\n` +
                    `${artist}\n` +
                    `meaning\n\n` +
                    `apple_data\n` +
                    `${appleId}\n` +
                    `lyrics\n` +
                    `${lyricsBody}\n`;

                const slug = slugify(`${title}-${artist}`);
                const filename = `${slug}.txt`;
                const githubPath = `raw_lyrics/${filename}`;
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
                        message: `Add Malayalam song: ${title} via Telegram Bot`,
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
                        `🌐 Live on <a href="https://malachidaniel.com">malachidaniel.com</a> in ~30 seconds!`;
                    await editTelegramMessage(botToken, senderId, cb.message.message_id, successMsg);
                } else {
                    const err = await commitRes.text();
                    await editTelegramMessage(botToken, senderId, cb.message.message_id, `❌ <b>GitHub Commit Error:</b>\n<code>${escapeHtml(err.slice(0, 200))}</code>`);
                }
                return new Response("OK", { status: 200 });
            }

            // 3. Cancel
            if (data === "cancel") {
                await editTelegramMessage(botToken, senderId, cb.message.message_id, "❌ <i>Action cancelled.</i>");
                return new Response("OK", { status: 200 });
            }

            return new Response("OK", { status: 200 });
        }

        // -------------------------------------------------------------
        // B. HANDLE STANDARD CHAT MESSAGES & PHOTOS
        // -------------------------------------------------------------
        const message = update.message;
        if (!message) {
            return new Response("OK", { status: 200 });
        }

        const senderId = String(message.chat.id);

        // Security check
        if (!myChatId || senderId !== myChatId) {
            console.warn(`Unauthorized attempt from chat ID: ${senderId}`);
            return new Response("Unauthorized", { status: 200 });
        }

        // 1. PHOTO / SCREENSHOT OCR
        if (message.photo && message.photo.length > 0) {
            const geminiKey = context.env.GEMINI_API_KEY;
            if (!geminiKey) {
                await sendTelegram(
                    botToken, 
                    senderId, 
                    "⚠️ <b>Gemini API Key missing!</b>\nPlease add <code>GEMINI_API_KEY</code> to Cloudflare Pages environment variables to enable Vision OCR."
                );
                return new Response("OK", { status: 200 });
            }

            await sendTelegram(botToken, senderId, "📸 <i>Analyzing image with Gemini Vision OCR...</i>");
            try {
                const photo = message.photo[message.photo.length - 1];
                const fileRes = await fetch(`https://api.telegram.org/bot${botToken}/getFile?file_id=${photo.file_id}`);
                const fileData = await fileRes.json();
                
                if (!fileData.ok) {
                    await sendTelegram(botToken, senderId, "❌ <i>Failed to fetch image from Telegram.</i>");
                    return new Response("OK", { status: 200 });
                }

                const photoUrl = `https://api.telegram.org/file/bot${botToken}/${fileData.result.file_path}`;
                const imgBuffer = await (await fetch(photoUrl)).arrayBuffer();
                const base64Img = btoa(String.fromCharCode(...new Uint8Array(imgBuffer)));

                const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiKey}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        contents: [{
                            parts: [
                                { text: "Extract Christian worship song lyrics from this image. Return pure JSON with keys: title, artist, lyrics. Do not use markdown backticks." },
                                { inline_data: { mime_type: "image/jpeg", data: base64Img } }
                            ]
                        }]
                    })
                });

                const geminiData = await geminiRes.json();
                let textOut = geminiData.candidates?.[0]?.content?.parts?.[0]?.text || "";
                textOut = textOut.replace(/^```json\s*/i, "").replace(/\s*```$/i, "").trim();
                const parsed = JSON.parse(textOut);

                const title = parsed.title || "Worship Song";
                const artist = parsed.artist || "Traditional";
                const lyrics = parsed.lyrics || "";

                const previewMsg =
                    `📸 <b>Lyrics Extracted via Vision OCR!</b>\n\n` +
                    `🎼 <b>Title:</b> ${escapeHtml(title)}\n` +
                    `🎤 <b>Artist:</b> ${escapeHtml(artist)}\n\n` +
                    `<b>Preview:</b>\n<i>${escapeHtml(lyrics.slice(0, 250))}...</i>\n\n` +
                    `To publish this song, send:\n<code>/add ${escapeHtml(title)} by ${escapeHtml(artist)}\n${escapeHtml(lyrics)}</code>`;

                await sendTelegram(botToken, senderId, previewMsg);
            } catch (err) {
                console.error("OCR error:", err);
                await sendTelegram(botToken, senderId, `❌ <i>OCR Error: ${escapeHtml(String(err).slice(0, 150))}</i>`);
            }
            return new Response("OK", { status: 200 });
        }

        // Text messages
        if (!message.text) {
            return new Response("OK", { status: 200 });
        }

        const text = message.text.trim();

        // 2. HELP / START COMMAND
        if (text === "/start" || text === "/help") {
            const helpMessage = 
                `👋 <b>Welcome Malachi!</b>\n\n` +
                `Here are your mobile worship management commands:\n\n` +
                `🔍 <b>Search & Add Songs (Malayalam & Hindi):</b>\n` +
                `• <code>/find Sneham</code> or <code>/search krooshile</code>\n` +
                `  <i>Searches 8,200+ songs on madely.us & shows 1-tap preview & publish buttons!</i>\n\n` +
                `📸 <b>Image-to-Text OCR:</b>\n` +
                `• <i>Send or forward any photo/screenshot of lyrics directly to this chat!</i>\n\n` +
                `📊 <b>Check Website Views & Traffic:</b>\n` +
                `• <code>/stats</code> or <code>/views</code>\n\n` +
                `🚀 <b>Add & Publish Any Custom Song:</b>\n` +
                `• <b>Quick:</b> <code>/add Way Maker by Sinach</code>\n` +
                `• <b>With Full Lyrics:</b>\n` +
                `<code>/add Oceans - Hillsong United\n` +
                `[Verse 1]\n` +
                `You call me out upon the waters...</code>\n\n` +
                `⚙️ <b>Other:</b>\n` +
                `• <code>/status</code> - Check bot health`;

            await sendTelegram(botToken, senderId, helpMessage);
            return new Response("OK", { status: 200 });
        }

        // 3. STATUS COMMAND
        if (text === "/status") {
            await sendTelegram(botToken, senderId, "✅ <b>Bot is active and securely connected to malachidaniel.com!</b>");
            return new Response("OK", { status: 200 });
        }

        // 4. STATS & ANALYTICS COMMAND
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

        // 5. SEARCH & INGEST MALAYALAM SONGS (/search or /find)
        if (text.startsWith("/search") || text.startsWith("/find")) {
            const query = text.replace(/^(\/search|\/find)/i, "").trim();
            if (!query) {
                await sendTelegram(botToken, senderId, "❌ <i>Please specify a search term!</i>\nExample: <code>/find Sneham</code> or <code>/search krooshile</code>");
                return new Response("OK", { status: 200 });
            }

            await sendTelegram(botToken, senderId, `🔍 <i>Searching madely.us for "<b>${escapeHtml(query)}</b>"...</i>`);
            const results = await searchMadely(query);
            
            if (!results.length) {
                await sendTelegram(botToken, senderId, `⚠️ <i>No songs found for "<b>${escapeHtml(query)}</b>" on madely.us. Try another spelling or word.</i>`);
                return new Response("OK", { status: 200 });
            }

            const buttons = results.slice(0, 5).map((r, i) => [
                { text: `${i + 1}. ${r.title.slice(0, 36)}`, callback_data: `m_prev:${encodeURIComponent(r.url)}` }
            ]);

            await sendTelegram(
                botToken, 
                senderId, 
                `🎵 <b>Found ${results.length} songs for "${escapeHtml(query)}":</b>\n<i>Tap a song below to preview lyrics & confirm:</i>`, 
                { inline_keyboard: buttons }
            );
            return new Response("OK", { status: 200 });
        }

        // 6. ADD CUSTOM SONG COMMAND (/add)
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

// -------------------------------------------------------------
// HELPER FUNCTIONS
// -------------------------------------------------------------

async function sendTelegram(botToken, chatId, htmlText, replyMarkup = null) {
    if (!botToken || !chatId) return;
    try {
        const payload = {
            chat_id: chatId,
            text: htmlText,
            parse_mode: "HTML",
            disable_web_page_preview: true
        };
        if (replyMarkup) {
            payload.reply_markup = replyMarkup;
        }
        await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error("Failed to send telegram message:", e);
    }
}

async function editTelegramMessage(botToken, chatId, messageId, htmlText, replyMarkup = null) {
    try {
        const payload = {
            chat_id: chatId,
            message_id: messageId,
            text: htmlText,
            parse_mode: "HTML",
            disable_web_page_preview: true
        };
        if (replyMarkup) {
            payload.reply_markup = replyMarkup;
        }
        await fetch(`https://api.telegram.org/bot${botToken}/editMessageText`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error("Failed to edit telegram message:", e);
    }
}

async function answerCallbackQuery(botToken, callbackQueryId, text = "") {
    try {
        await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                callback_query_id: callbackQueryId,
                text: text
            })
        });
    } catch (e) {
        console.error("Failed to answer callback query:", e);
    }
}

async function searchMadely(query) {
    const url = `https://madely.us/?s=${encodeURIComponent(query)}`;
    const res = await fetch(url, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
    });
    if (!res.ok) return [];
    const html = await res.text();
    const linkRegex = /<a[^>]*href=["'](https:\/\/madely\.us\/lyrics\/[^"'#]+)["'][^>]*>([\s\S]*?)<\/a>/gi;
    let match;
    const results = [];
    const seen = new Set();
    const skipPhrases = ["Open Song Lyrics ->>", "No comments yet", "Home", "Lyrics", "Read More"];
    
    while ((match = linkRegex.exec(html)) !== null) {
        const href = match[1];
        const text = match[2].replace(/<[^>]+>/g, "").trim();
        if (!href.endsWith("/lyrics/") && !seen.has(href) && text.length > 2) {
            if (!skipPhrases.some(s => text.includes(s)) && !/^[A-Za-z]+\s+\d+,\s+\d{4}$/.test(text)) {
                seen.add(href);
                results.push({ title: text, url: href });
                if (results.length >= 5) break;
            }
        }
    }
    return results;
}

async function fetchMadelySong(url) {
    const res = await fetch(url, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
    });
    if (!res.ok) return null;
    let data = await res.text();

    const titleMatch = data.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || data.match(/<h2[^>]*class=["'][^"']*entry-title[^"']*["'][^>]*>([\s\S]*?)<\/h2>/i);
    let title = titleMatch ? titleMatch[1].replace(/<[^>]+>/g, "").trim() : "Malayalam Song";
    title = title.replace(/\s*(Malayalam|Manglish|Song\s+Lyrics|Lyrics|-|–|MADELY).*$/i, "").trim();

    // Remove junk containers from HTML before extracting
    data = data.replace(/<div[^>]*id=["']divAfterLyricContent["'][\s\S]*?<\/div>/gi, "");
    data = data.replace(/<div[^>]*id=["']Tagging["'][\s\S]*?<\/div>/gi, "");
    data = data.replace(/<div[^>]*id=["']divUserNotes["'][\s\S]*?<\/div>/gi, "");
    data = data.replace(/<div[^>]*class=["'][^"']*divAfterLyricContent[^"']*["'][\s\S]*?<\/div>/gi, "");
    data = data.replace(/<div[^>]*class=["'][^"']*lyric-print[^"']*["'][\s\S]*?<\/div>/gi, "");
    data = data.replace(/<script[\s\S]*?<\/script>/gi, "");
    data = data.replace(/<style[\s\S]*?<\/style>/gi, "");

    // 1. Malayalam from LyricsTable or section 0
    let malHtml = "";
    const tableMatch = data.match(/<table[^>]*class=["'][^"']*LyricsTable[^"']*["'][^>]*>([\s\S]*?)<\/table>/i);
    if (tableMatch) {
        malHtml = tableMatch[1];
    } else {
        const secMatch = data.match(/<section[^>]*>([\s\S]*?)<\/section>/i);
        if (secMatch) malHtml = secMatch[1];
    }

    // 2. Manglish from spanManglish or section 1
    let manHtml = "";
    const spanMatch = data.match(/<span[^>]*class=["'][^"']*spanManglish[^"']*["'][^>]*>([\s\S]*?)<\/span>/i);
    if (spanMatch) {
        manHtml = spanMatch[1].replace(/<div[\s\S]*?<\/div>/gi, "");
    } else {
        const allSecs = [...data.matchAll(/<section[^>]*>([\s\S]*?)<\/section>/gi)];
        if (allSecs.length > 1) {
            manHtml = allSecs[1][1];
        }
    }

    function cleanSec(html) {
        const text = html.replace(/<br\s*[\/]?>/gi, "\n").replace(/<\/p>/gi, "\n").replace(/<[^>]+>/g, "");
        const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 0);
        const skipPhrases = [
            "change singing roles", "double tapping", "segway notation", "faq page",
            "song lyrics of", "devotional lyrics", "syro malabar", "syro-malabar",
            "syromalabar", "karaoke |", "midi |", "ലിറിക്സ്", "ലിറിക്‌സ്", "വരികൾ",
            "all;", "male;", "female;", "reverend", "shusrooshi", "szuroochi"
        ];
        const skipHeaders = new Set(["malayalam lyrics", "manglish lyrics", "my notes", "a", "|", "media", "loading..."]);
        const cleaned = [];
        for (let l of lines) {
            if (skipHeaders.has(l.toLowerCase())) continue;
            const lower = l.toLowerCase();
            if (skipPhrases.some(sp => lower.includes(sp))) continue;
            l = l.replace(/^(M|F|A|R\/S|R|S)\s*$/, "").replace(/[🔔—–-]{2,}/g, "").trim();
            if (l.split("|").length >= 3) continue;
            if (l && (!cleaned.length || l !== cleaned[cleaned.length - 1])) {
                cleaned.push(l);
            }
        }
        return cleaned.join("\n");
    }

    const mal = cleanSec(malHtml);
    const man = cleanSec(manHtml);

    return { title, mal, man, url };
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

