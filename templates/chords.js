/**
 * Christian LyricsHub - Chord & Key Transposition Engine
 * Supports ChordPro syntax, chord-over-lyric detection, 12-semitone key transposing,
 * Capo calculation, and responsive stacked chord typography.
 */

(function () {
    const SHARPS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const FLATS  = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

    // Enharmonic normalization
    const NOTE_TO_INDEX = {
        'C': 0, 'B#': 0,
        'C#': 1, 'DB': 1, 'Db': 1,
        'D': 2,
        'D#': 3, 'EB': 3, 'Eb': 3,
        'E': 4, 'FB': 4,
        'F': 5, 'E#': 5,
        'F#': 6, 'GB': 6, 'Gb': 6,
        'G': 7,
        'G#': 8, 'AB': 8, 'Ab': 8,
        'A': 9,
        'A#': 10, 'BB': 10, 'Bb': 10,
        'B': 11, 'CB': 11
    };

    // Keys that naturally use flats
    const FLAT_KEYS = ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Dm', 'Gm', 'Cm', 'Fm', 'Bbm'];

    function transposeNote(note, semitones, preferFlats) {
        if (!note) return "";
        const idx = NOTE_TO_INDEX[note];
        if (idx === undefined) return note;

        let newIdx = (idx + semitones) % 12;
        if (newIdx < 0) newIdx += 12;

        const scale = preferFlats ? FLATS : SHARPS;
        return scale[newIdx];
    }

    function transposeChord(chord, semitones, preferFlats) {
        if (!chord || semitones === 0) return chord;

        // Match root, quality/modifiers, and optional slash bass note
        const match = chord.match(/^([A-G][b#]?)(.*?)(\/([A-G][b#]?))?$/);
        if (!match) return chord;

        const root = match[1];
        const modifier = match[2] || "";
        const slashBass = match[4];

        const newRoot = transposeNote(root, semitones, preferFlats);
        const newBass = slashBass ? "/" + transposeNote(slashBass, semitones, preferFlats) : "";

        return newRoot + modifier + newBass;
    }

    // Seed Library for Popular Worship Songs
    const SEED_CHORDS = {
        "10000-reasons.html": {
            key: "G",
            text: `[Chorus]
[C]Bless the [G]Lord, O my [D/F#]soul, [Em]O my soul
[C]Worship His [G]holy [Dsus4]name   [D]
Sing like [C]never be[Em]fore, [C] [D]O my [Em]soul
I'll [C]worship Your [D]holy [G]name

[Verse 1]
The [C]sun comes [G]up, it's a [D]new day [Em]dawning
[C]It's time to [G]sing Your [D]song a[Em]gain
[C]Whatever may [G]pass and what[D]ever lies be[Em]fore me
[C2]Let me be [G]singing when the [Dsus4]eve - [D]ning [G]comes

[Verse 2]
You're [C]rich in [G]love and You're [D]slow to [Em]anger
Your [C]name is [G]great and Your [D]heart is [Em]kind
For [C]all Your [G]goodness I will [D]keep on [Em]singing
[C2]Ten thousand [G]reasons for my [Dsus4]heart [D]to [G]find

[Verse 3]
And [C]on that [G]day when my [D]strength is [Em]failing
The [C]end draws [G]near and my [D]time has [Em]come
[C]Still my [G]soul will sing Your [D]praise un[Em]ending
[C2]Ten thousand [G]years and then for[Dsus4]ever - [D] [G]more!`
        },
        "amazing-grace.html": {
            key: "G",
            text: `[Verse 1]
A[G]mazing grace! How [C]sweet the [G]sound
That saved a [D]wretch like me!
I [G]once was lost, but [C]now am [G]found;
Was blind, but [D]now I [G]see.

[Verse 2]
'Twas [G]grace that taught my [C]heart to [G]fear,
And grace my [D]fears relieved;
How [G]precious did that [C]grace ap[G]pear
The hour I [D]first be[G]lieved.

[Verse 3]
Through [G]many dangers, [C]toils and [G]snares,
I have al[D]ready come;
'Tis [G]grace hath brought me [C]safe thus [G]far,
And grace will [D]lead me [G]home.

[Verse 4]
When [G]we've been there ten [C]thousand [G]years,
Bright shining [D]as the sun,
We've [G]no less days to [C]sing God's [G]praise
Than when we'd [D]first be[G]gun.`
        },
        "what_a_beautiful_name.html": {
            key: "D",
            text: `[Verse 1]
[D]You were the Word at the beginning
One With [G]God the Lord Most [Bm]High [A]
[D]Your hidden glory in creation
Now re[G]vealed in You Our [Bm]Christ [A]

[Chorus 1]
What a beautiful Name it [D]is
What a beautiful Name it [A]is
The Name of [Bm]Jesus [A]Christ my [G]King
What a beautiful Name it [D/F#]is
Nothing compares to [A]this
What a beautiful Name it [Bm]is
The [A]Name of [G]Jesus

[Verse 2]
[D]You didn't want heaven without us
So Jesus, [G]You brought heaven [Bm]down [A]
[D]My sin was great, Your love was greater
What could [G]separate us [Bm]now [A]

[Chorus 2]
What a wonderful Name it [D]is
What a wonderful Name it [A]is
The Name of [Bm]Jesus [A]Christ my [G]King
What a wonderful Name it [D/F#]is
Nothing compares to [A]this
What a wonderful Name it [Bm]is
The [A]Name of [G]Jesus`
        },
        "goodness-of-god-bethel-music.html": {
            key: "G",
            text: `[Verse 1]
I love You, [G]Lord
For Your [C]mercy never [G]fails me
All my [Em]days, I've been [C]held in Your [D]hands
From the moment that I [Em]wake up [C]
Until I lay my [G]head [D/F#] [Em]
Oh, I will [C]sing of the [D]goodness of [G]God

[Chorus]
And all my life You have been [C]faithful [G]
And all my life You have been [C]so, so [G]good [D]
With every breath that I am [C]able [G] [D/F#] [Em]
Oh, I will [C]sing of the [D]goodness of [G]God

[Verse 2]
I love Your [G]voice
You have [C]led me through the [G]fire
In darkest [Em]night You are [C]close like no [D]other
I've known You as a [Em]Father [C]
I've known You as a [Friend] [G] [D/F#] [Em]
And I have [C]lived in the [D]goodness of [G]God`
        }
    };

    // State
    let currentKeyOffset = 0;
    let currentCapo = 0;
    let originalKey = "G";
    let chordsVisible = true;
    let currentSongId = "";
    let activeChordText = "";

    function initChordsEngine() {
        const path = window.location.pathname;
        const filename = path.substring(path.lastIndexOf('/') + 1);
        currentSongId = filename;

        // Check for stored custom chords, or seed chords
        const storedCustom = localStorage.getItem('custom_chords_' + currentSongId);
        if (storedCustom) {
            try {
                const parsed = JSON.parse(storedCustom);
                activeChordText = parsed.text;
                originalKey = parsed.key || "G";
            } catch (e) {
                activeChordText = storedCustom;
            }
        } else if (SEED_CHORDS[currentSongId]) {
            activeChordText = SEED_CHORDS[currentSongId].text;
            originalKey = SEED_CHORDS[currentSongId].key;
        }

        // If this song has chords, inject the toolbar and render
        renderMusicianToolbar();
        if (activeChordText) {
            renderChordsToLyrics();
        }
    }

    function renderMusicianToolbar() {
        const existingToolbar = document.getElementById('musicianToolbar');
        if (existingToolbar) return;

        const lyricsBody = document.querySelector('.lyrics-body');
        if (!lyricsBody) return;

        const hasChords = !!activeChordText;
        const toolbar = document.createElement('div');
        toolbar.id = 'musicianToolbar';
        toolbar.className = 'musician-toolbar';

        toolbar.innerHTML = `
            <div class="musician-toolbar-left">
                <button class="btn-chord-toggle ${hasChords ? 'active' : ''}" id="btnToggleChords" title="Toggle Chord Charts Above Lyrics">
                    🎸 Chords: <span id="chordsStatus">${hasChords ? 'ON' : 'OFF'}</span>
                </button>
                <div class="key-control-group" id="keyControlGroup" style="display: ${hasChords ? 'flex' : 'none'};">
                    <span class="toolbar-label">Key:</span>
                    <button class="btn-key-step" id="btnKeyDown" title="Transpose Down 1 Semitone (♭)">♭</button>
                    <span class="current-key-badge" id="currentKeyBadge">${originalKey}</span>
                    <button class="btn-key-step" id="btnKeyUp" title="Transpose Up 1 Semitone (♯)">♯</button>
                    <button class="btn-key-reset" id="btnKeyReset" title="Reset to Original Key">Reset</button>
                </div>
                <div class="capo-control-group" id="capoControlGroup" style="display: ${hasChords ? 'flex' : 'none'};">
                    <span class="toolbar-label">Capo:</span>
                    <select id="selectCapo" class="capo-select">
                        <option value="0">None</option>
                        <option value="1">Capo 1</option>
                        <option value="2">Capo 2</option>
                        <option value="3">Capo 3</option>
                        <option value="4">Capo 4</option>
                        <option value="5">Capo 5</option>
                        <option value="6">Capo 6</option>
                        <option value="7">Capo 7</option>
                    </select>
                    <span class="capo-hint" id="capoHint"></span>
                </div>
            </div>
            <div class="musician-toolbar-right">
                <button class="btn-tool-secondary" id="btnAddSetlist" title="Add this song to your Sunday Service Setlist">
                    📋 + Setlist
                </button>
                <button class="btn-tool-secondary" id="btnEditChords" title="${hasChords ? 'Edit chords for this song' : 'Add guitar chords for this song'}">
                    ✏️ ${hasChords ? 'Edit Chords' : 'Add Chords'}
                </button>
                <button class="btn-tool-secondary" id="btnPrintLeadSheet" onclick="window.print()" title="Print Chord Chart / Lead Sheet">
                    🖨️ Print
                </button>
            </div>
        `;

        lyricsBody.parentNode.insertBefore(toolbar, lyricsBody);
        bindToolbarEvents();
    }

    function bindToolbarEvents() {
        const toggleBtn = document.getElementById('btnToggleChords');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                if (!activeChordText) {
                    openChordEditor();
                    return;
                }
                chordsVisible = !chordsVisible;
                toggleBtn.classList.toggle('active', chordsVisible);
                document.getElementById('chordsStatus').innerText = chordsVisible ? 'ON' : 'OFF';
                
                const container = document.querySelector('.lyrics-body');
                if (container) {
                    container.classList.toggle('hide-chords', !chordsVisible);
                }
            });
        }

        const btnDown = document.getElementById('btnKeyDown');
        const btnUp = document.getElementById('btnKeyUp');
        const btnReset = document.getElementById('btnKeyReset');

        if (btnDown) {
            btnDown.addEventListener('click', () => {
                currentKeyOffset--;
                updateKeyDisplay();
                renderChordsToLyrics();
            });
        }
        if (btnUp) {
            btnUp.addEventListener('click', () => {
                currentKeyOffset++;
                updateKeyDisplay();
                renderChordsToLyrics();
            });
        }
        if (btnReset) {
            btnReset.addEventListener('click', () => {
                currentKeyOffset = 0;
                currentCapo = 0;
                document.getElementById('selectCapo').value = "0";
                updateKeyDisplay();
                renderChordsToLyrics();
            });
        }

        const capoSelect = document.getElementById('selectCapo');
        if (capoSelect) {
            capoSelect.addEventListener('change', (e) => {
                currentCapo = parseInt(e.target.value) || 0;
                updateKeyDisplay();
            });
        }

        const addSetlistBtn = document.getElementById('btnAddSetlist');
        if (addSetlistBtn) {
            addSetlistBtn.addEventListener('click', addCurrentSongToSetlist);
        }

        const editChordsBtn = document.getElementById('btnEditChords');
        if (editChordsBtn) {
            editChordsBtn.addEventListener('click', openChordEditor);
        }
    }

    function updateKeyDisplay() {
        const preferFlats = FLAT_KEYS.includes(originalKey);
        const transposedKey = transposeNote(originalKey, currentKeyOffset, preferFlats);
        const badge = document.getElementById('currentKeyBadge');
        if (badge) {
            badge.innerText = transposedKey;
        }

        const capoHint = document.getElementById('capoHint');
        if (capoHint) {
            if (currentCapo > 0) {
                const soundsKey = transposeNote(transposedKey, currentCapo, preferFlats);
                capoHint.innerText = `(Sounds in ${soundsKey})`;
            } else {
                capoHint.innerText = '';
            }
        }
    }

    // Convert ChordPro [Chord]Lyric into HTML
    function formatChordProToHtml(text, semitones) {
        if (!text) return "";
        const preferFlats = FLAT_KEYS.includes(originalKey);

        const lines = text.split('\n');
        const htmlLines = lines.map(line => {
            const trimmed = line.trim();
            // Section tags like [Chorus], [Verse 1], etc.
            if (trimmed.match(/^\[(verse|chorus|bridge|pre-chorus|intro|outro|tag|ending|\d+)[\w\s]*\]/i)) {
                const sectionName = trimmed.replace(/^\[|\]$/g, '');
                return `<div class="chord-section-header">${escapeHtml(sectionName)}</div>`;
            }

            // Split line by [Chord] tokens
            const parts = line.split(/(\[[^\]]+\])/);
            let lineHtml = '<div class="chord-line-row">';
            let hasChords = false;

            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                if (part.startsWith('[') && part.endsWith(']')) {
                    hasChords = true;
                    const rawChord = part.slice(1, -1);
                    const transposed = transposeChord(rawChord, semitones, preferFlats);
                    const nextLyric = parts[i + 1] && !parts[i + 1].startsWith('[') ? parts[++i] : " ";

                    lineHtml += `
                        <span class="chord-wrapper">
                            <span class="chord">${escapeHtml(transposed)}</span>
                            <span class="lyric">${escapeHtml(nextLyric)}</span>
                        </span>
                    `;
                } else if (part.length > 0) {
                    lineHtml += `<span class="lyric-plain">${escapeHtml(part)}</span>`;
                }
            }

            lineHtml += '</div>';
            return lineHtml;
        });

        return htmlLines.join('\n');
    }

    function renderChordsToLyrics() {
        if (!activeChordText) return;

        const lyricBody = document.querySelector('.lyrics-body');
        if (!lyricBody) return;

        const formattedHtml = formatChordProToHtml(activeChordText, currentKeyOffset);
        
        let chordContainer = document.getElementById('renderedChordChart');
        if (!chordContainer) {
            chordContainer = document.createElement('div');
            chordContainer.id = 'renderedChordChart';
            chordContainer.className = 'chord-chart-container';
            
            // Hide standard raw text div while chord chart is active
            const rawLyricText = lyricBody.querySelector('.lyric-text');
            if (rawLyricText) rawLyricText.style.display = 'none';
            
            lyricBody.appendChild(chordContainer);
        }

        chordContainer.innerHTML = formattedHtml;
    }

    function addCurrentSongToSetlist() {
        const titleEl = document.querySelector('.song-title');
        const artistEl = document.querySelector('.song-artist');
        const title = titleEl ? titleEl.innerText : document.title;
        const artist = artistEl ? artistEl.innerText : "Worship";

        let setlist = [];
        try {
            setlist = JSON.parse(localStorage.getItem('sunday_setlist') || '[]');
        } catch (e) {
            setlist = [];
        }

        // Avoid exact duplicate
        const alreadyIn = setlist.some(s => s.id === currentSongId);
        if (alreadyIn) {
            alert(`"${title}" is already in your Sunday Setlist!`);
            return;
        }

        setlist.push({
            id: currentSongId,
            title: title,
            artist: artist,
            key: originalKey || "G",
            notes: "",
            leader: ""
        });

        localStorage.setItem('sunday_setlist', JSON.stringify(setlist));
        
        // Visual feedback
        const btn = document.getElementById('btnAddSetlist');
        if (btn) {
            const oldText = btn.innerText;
            btn.innerText = '✅ Added!';
            btn.style.borderColor = '#10b981';
            btn.style.color = '#10b981';
            setTimeout(() => {
                btn.innerText = oldText;
                btn.style.borderColor = '';
                btn.style.color = '';
            }, 2000);
        }
    }

    function openChordEditor() {
        let modal = document.getElementById('chordEditorModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'chordEditorModal';
            modal.className = 'chord-editor-modal-overlay';
            modal.innerHTML = `
                <div class="chord-editor-card">
                    <div class="editor-header">
                        <h3>🎸 Edit Chord Chart (ChordPro)</h3>
                        <button class="btn-close-modal" id="btnCloseChordModal">✕</button>
                    </div>
                    <div class="editor-body">
                        <p class="editor-hint">
                            Add chords inline using brackets, e.g.: <code>[G]Amazing [D]grace, how [Em]sweet the [C]sound</code><br>
                            Use tags like <code>[Verse 1]</code> and <code>[Chorus]</code> for sections.
                        </p>
                        <div class="editor-controls-row">
                            <label>Default Key: </label>
                            <select id="editorSongKey" class="key-select">
                                ${SHARPS.map(k => `<option value="${k}">${k}</option>`).join('')}
                            </select>
                        </div>
                        <textarea id="chordEditTextarea" rows="16" placeholder="Paste or type ChordPro text here..."></textarea>
                    </div>
                    <div class="editor-footer">
                        <button class="btn-modal-secondary" id="btnResetToLyrics">Load Base Lyrics</button>
                        <button class="btn-modal-primary" id="btnSaveChords">💾 Save Chord Chart</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            document.getElementById('btnCloseChordModal').addEventListener('click', () => {
                modal.classList.remove('open');
            });
            document.getElementById('btnSaveChords').addEventListener('click', saveCustomChords);
            document.getElementById('btnResetToLyrics').addEventListener('click', loadBaseLyricsIntoEditor);
        }

        const textarea = document.getElementById('chordEditTextarea');
        textarea.value = activeChordText || "";
        document.getElementById('editorSongKey').value = originalKey || "G";

        modal.classList.add('open');
    }

    function loadBaseLyricsIntoEditor() {
        const rawEl = document.querySelector('.lyric-text');
        if (rawEl) {
            const raw = rawEl.innerText;
            const textarea = document.getElementById('chordEditTextarea');
            textarea.value = raw;
        }
    }

    function saveCustomChords() {
        const textarea = document.getElementById('chordEditTextarea');
        const keySelect = document.getElementById('editorSongKey');
        const text = textarea.value.trim();
        const key = keySelect.value;

        if (!text) {
            localStorage.removeItem('custom_chords_' + currentSongId);
            activeChordText = "";
            location.reload();
            return;
        }

        const payload = { key: key, text: text };
        localStorage.setItem('custom_chords_' + currentSongId, JSON.stringify(payload));

        activeChordText = text;
        originalKey = key;
        currentKeyOffset = 0;

        document.getElementById('chordEditorModal').classList.remove('open');
        renderMusicianToolbar();
        updateKeyDisplay();
        renderChordsToLyrics();

        alert("Chord chart saved successfully! Transposer and chords are now active.");
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Auto-run on DOM Ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChordsEngine);
    } else {
        initChordsEngine();
    }

    // Expose for Setlist and Band View
    window.LyricsHubChords = {
        transposeChord,
        transposeNote,
        formatChordProToHtml,
        SEED_CHORDS
    };
})();
