export async function onRequestPost(context) {
    return handleView(context);
}

export async function onRequestGet(context) {
    return handleView(context);
}

async function handleView(context) {
    try {
        const kv = context.env.SONG_REQUESTS;
        if (!kv) {
            return new Response("OK", { status: 200 });
        }

        // 1. Get requested path
        let pagePath = "/";
        const url = new URL(context.request.url);

        if (url.searchParams.has("p")) {
            pagePath = url.searchParams.get("p") || "/";
        } else if (context.request.headers.get("content-type")?.includes("application/json")) {
            try {
                const body = await context.request.json();
                if (body && body.p) pagePath = body.p;
            } catch (e) {}
        }

        // Clean path (strip query params / hashes)
        pagePath = pagePath.split("?")[0].split("#")[0];
        if (!pagePath.startsWith("/")) pagePath = "/" + pagePath;

        // Ignore internal API or static asset pings
        if (pagePath.startsWith("/api/") || 
            pagePath.includes("favicon") || 
            pagePath.endsWith(".png") || 
            pagePath.endsWith(".jpg") || 
            pagePath.endsWith(".ico") || 
            pagePath.endsWith(".css") || 
            pagePath.endsWith(".js")) {
            return new Response("OK", { status: 200 });
        }

        // 2. Date in IST (Asia/Kolkata)
        const now = new Date();
        const todayStr = now.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });

        // 3. Unique visitor hash (Salted IP + User-Agent + Date)
        const clientIp = context.request.headers.get("cf-connecting-ip") || "0.0.0.0";
        const userAgent = context.request.headers.get("user-agent") || "";
        const rawVisitorStr = `${clientIp}-${userAgent}-${todayStr}`;

        let hash = 0;
        for (let i = 0; i < rawVisitorStr.length; i++) {
            hash = ((hash << 5) - hash) + rawVisitorStr.charCodeAt(i);
            hash |= 0;
        }
        const visitorKey = `vis_${todayStr}_${Math.abs(hash)}`;

        let isNewVisitor = false;
        try {
            const existingVisitor = await kv.get(visitorKey);
            if (!existingVisitor) {
                isNewVisitor = true;
                // Auto-expire visitor key after 48 hours to save KV storage
                await kv.put(visitorKey, "1", { expirationTtl: 172800 });
            }
        } catch (e) {
            console.error("Visitor check error:", e);
        }

        // 4. Update Daily Stats in KV
        const dailyKey = `stats_daily_${todayStr}`;
        let dailyStats = null;
        try {
            dailyStats = await kv.get(dailyKey, "json");
        } catch (e) {}

        if (!dailyStats) {
            dailyStats = { views: 0, visitors: 0, top: {} };
        }

        dailyStats.views = (dailyStats.views || 0) + 1;
        if (isNewVisitor) {
            dailyStats.visitors = (dailyStats.visitors || 0) + 1;
        }

        if (!dailyStats.top) dailyStats.top = {};
        dailyStats.top[pagePath] = (dailyStats.top[pagePath] || 0) + 1;

        // Keep top list clean (prune to top 40 pages if too large)
        const topEntries = Object.entries(dailyStats.top);
        if (topEntries.length > 50) {
            topEntries.sort((a, b) => b[1] - a[1]);
            dailyStats.top = Object.fromEntries(topEntries.slice(0, 35));
        }

        // Save back with 30-day retention
        await kv.put(dailyKey, JSON.stringify(dailyStats), { expirationTtl: 86400 * 30 });

        // 5. Update All-Time Pageviews Counter
        try {
            const totalRaw = await kv.get("stats_total");
            const newTotal = totalRaw ? parseInt(totalRaw, 10) + 1 : 1;
            await kv.put("stats_total", String(newTotal));
        } catch (e) {}

        return new Response("OK", {
            status: 200,
            headers: {
                "Content-Type": "text/plain",
                "Access-Control-Allow-Origin": "*"
            }
        });

    } catch (err) {
        console.error("View tracking error:", err);
        return new Response("OK", { status: 200 });
    }
}
