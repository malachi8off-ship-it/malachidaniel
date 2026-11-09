export async function onRequestPost(context) {
    try {
        // 1. Grab the data sent from your frontend form
        const data = await context.request.json();
        const { songName, artistName } = data;

        // 2. Make sure a song name was actually provided
        if (!songName) {
            return new Response("Missing song name", { status: 400 });
        }

        // 3. Create a unique ID for this database entry using the current time
        const timestamp = new Date().toISOString();
        const uniqueKey = `request_${timestamp}`;

        // 4. Save the data to Cloudflare KV namespace (SONG_REQUESTS) if bound
        if (context.env && context.env.SONG_REQUESTS) {
            try {
                await context.env.SONG_REQUESTS.put(uniqueKey, JSON.stringify({
                    songName: songName,
                    artistName: artistName || "Unknown Artist",
                    submittedAt: timestamp
                }));
            } catch (kvErr) {
                console.error("KV save error:", kvErr);
            }
        }

        // 5. Send Telegram instant push notification
        const botToken = context.env ? context.env.TELEGRAM_BOT_TOKEN : null;
        const chatId = context.env ? context.env.TELEGRAM_CHAT_ID : null;

        if (botToken && chatId) {
            try {
                const formattedTime = new Date().toLocaleString("en-US", {
                    timeZone: "Asia/Kolkata",
                    dateStyle: "medium",
                    timeStyle: "short"
                });

                const safeSong = escapeHtml(songName);
                const safeArtist = escapeHtml(artistName || "Unknown Artist");

                const messageText = 
                    `🎵 <b>New Song Request!</b>\n\n` +
                    `🎼 <b>Song:</b> ${safeSong}\n` +
                    `🎤 <b>Artist:</b> ${safeArtist}\n` +
                    `🕒 <b>Time:</b> ${formattedTime}\n\n` +
                    `🌐 <i>Submitted on malachidaniel.com</i>`;

                const youtubeQuery = encodeURIComponent(`${songName} ${artistName || ""}`.trim());
                const youtubeUrl = `https://www.youtube.com/results?search_query=${youtubeQuery}`;

                await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        chat_id: chatId,
                        text: messageText,
                        parse_mode: "HTML",
                        reply_markup: {
                            inline_keyboard: [
                                [
                                    { text: "🔍 Search on YouTube", url: youtubeUrl }
                                ]
                            ]
                        }
                    })
                });
            } catch (tgErr) {
                console.error("Telegram notification error:", tgErr);
            }
        }

        // 6. Tell the frontend that it was successful!
        return new Response(JSON.stringify({ message: "Success!" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
        });

    } catch (error) {
        // If something crashes, tell the frontend there was an error
        return new Response(JSON.stringify({ error: "Server Error", details: error.message }), { 
            status: 500,
            headers: { "Content-Type": "application/json" }
        });
    }
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
