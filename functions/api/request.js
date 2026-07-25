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

        // 4. Save the data to your Cloudflare KV namespace (SONG_REQUESTS)
        await context.env.SONG_REQUESTS.put(uniqueKey, JSON.stringify({
            songName: songName,
            artistName: artistName || "Unknown Artist",
            submittedAt: timestamp
        }));

        // 5. Tell the frontend that it was successful!
        return new Response(JSON.stringify({ message: "Success!" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
        });

    } catch (error) {
        // If something crashes, tell the frontend there was an error
        return new Response(JSON.stringify({ error: "Server Error" }), { 
            status: 500,
            headers: { "Content-Type": "application/json" }
        });
    }
}