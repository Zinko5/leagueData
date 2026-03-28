const MATCH_CONTAINER = document.getElementById('match-list');
const UPDATE_BTN = document.getElementById('update-btn');
const MODAL = document.getElementById('match-modal');
const MODAL_BODY = document.getElementById('modal-body');
const CLOSE_BTN = document.querySelector('.close-btn');
const TOTAL_BADGE = document.getElementById('total-matches-badge');
const CHAMP_FILTER = document.getElementById('champion-filter');
const POS_FILTER = document.getElementById('position-filter');
const STAT_FILTER = document.getElementById('stat-filter');

const PREV_BTN = document.getElementById('prev-page');
const NEXT_BTN = document.getElementById('next-page');
const PAGE_DISPLAY = document.getElementById('page-display');

let profileData = null;
let currentPage = 1;
let filtersPopulated = false;

// Variables that don't make sense to compare as a "score"
const IGNORED_STATS = ['jugador', 'match_id', 'side', 'win', 'championName', 'champLevel', 'individualPosition', 'timePlayed', 'gameCreation'];

async function fetchProfile(page = 1) {
    currentPage = page;
    const champ = CHAMP_FILTER.value;
    const pos = POS_FILTER.value;
    
    let url = `http://localhost:8000/api/profile?page=${page}`;
    if (champ) url += `&champion=${encodeURIComponent(champ)}`;
    if (pos) url += `&position=${encodeURIComponent(pos)}`;

    try {
        const response = await fetch(url);
        profileData = await response.json();
        
        if (profileData.error) {
            MATCH_CONTAINER.innerHTML = `<div style="text-align:center; padding: 40px;">${profileData.error}</div>`;
            return;
        }

        TOTAL_BADGE.innerText = `Total: ${profileData.total_matches || 0} Matches`;
        PAGE_DISPLAY.innerText = `Page ${profileData.page} of ${profileData.total_pages || 1}`;
        
        PREV_BTN.disabled = (profileData.page <= 1);
        NEXT_BTN.disabled = (profileData.page >= profileData.total_pages);
        
        // Populate filters
        if (!filtersPopulated) {
            if (profileData.champions) {
                CHAMP_FILTER.innerHTML = '<option value="">All Champions</option>';
                profileData.champions.forEach(c => { const opt = new Option(c, c); CHAMP_FILTER.add(opt); });
            }
            if (profileData.positions) {
                POS_FILTER.innerHTML = '<option value="">All Positions</option>';
                profileData.positions.forEach(p => { const opt = new Option(p, p); POS_FILTER.add(opt); });
            }
            if (profileData.all_stats) {
                STAT_FILTER.innerHTML = '<option value="">Select Stat Score</option>';
                profileData.all_stats.filter(s => !IGNORED_STATS.includes(s)).forEach(s => {
                    const cleanName = s.replace('challenge_', '').replace(/([A-Z])/g, ' $1').trim();
                    const opt = new Option(cleanName, s); STAT_FILTER.add(opt);
                });
            }
            filtersPopulated = true;
        }

        renderMatches(profileData.matches);
    } catch (err) {
        MATCH_CONTAINER.innerHTML = `<p class="error">Connection Failed.</p>`;
    }
}

function getScoreClass(score) {
    if (score >= 90) return 'score-god';
    if (score >= 75) return 'score-high';
    if (score >= 40) return 'score-mid';
    return 'score-low';
}

function renderMatches(matches) {
    if (!matches || matches.length === 0) {
        MATCH_CONTAINER.innerHTML = '<p style="text-align:center; padding: 40px; opacity: 0.5;">No matches found.</p>';
        return;
    }
    const selectedStat = STAT_FILTER.value;
    MATCH_CONTAINER.innerHTML = '';
    matches.forEach(m => {
        const card = document.createElement('div');
        card.className = `match-card ${m.win ? 'win' : 'loss'}`;
        card.onclick = () => showMatchDetails(m);
        
        let individualScoreHtml = '';
        if (selectedStat && m.stats[selectedStat]) {
            const score = m.stats[selectedStat].score;
            const scoreClass = getScoreClass(score);
            individualScoreHtml = `<div class="individual-stat-badge visible ${scoreClass}">${score}</div>`;
        } else {
            individualScoreHtml = `<div class="individual-stat-badge"></div>`;
        }

        card.innerHTML = `
            <div></div>
            <div class="win-status"><div>${m.win ? 'Victory' : 'Defeat'}</div><div class="match-date">${m.date}</div></div>
            <div class="champ-info"><div class="champ-avatar">${m.champion.substring(0,2)}</div><div>
                <div style="font-weight: 800; font-size: 1.1rem;">${m.champion}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">${m.position}</div>
            </div></div>
            <div class="kda-box"><span>${m.kills}</span> / <span class="deaths">${m.deaths}</span> / <span>${m.assists}</span></div>
            <div class="score-badge">${m.overall_score}</div>
            ${individualScoreHtml}
        `;
        MATCH_CONTAINER.appendChild(card);
    });
}

function showMatchDetails(match) {
    MODAL.style.display = 'block';
    const radarKeys = ['kills', 'visionScore', 'challenge_damagePerMinute', 'challenge_goldPerMinute', 'challenge_teamDamagePercentage', 'challenge_killParticipation'];
    const radarData = radarKeys.map(k => match.stats[k]?.score || 0);
    const displayLabels = ['Kills', 'Vision', 'Damage/m', 'Gold/m', '%Team Dmg', 'Kill Part.'];

    MODAL_BODY.innerHTML = `
        <h2 style="font-family: 'Outfit'; font-size: 2.2rem; margin-bottom: 5px;"><span style="color: var(--primary)">${match.champion}</span> Analysis</h2>
        <p style="margin-bottom: 25px; color: var(--text-secondary); font-size: 0.9rem;">Partida: ${match.date}</p>
        <div class="modal-grid">
            <div class="radar-section"><div style="width: 100%; max-width: 400px;"><canvas id="radar-chart"></canvas></div></div>
            <div class="stats-grid">
                ${Object.entries(match.stats).filter(([k]) => !k.includes('teamRift') && !k.includes('Elder')).slice(0, 10).map(([key, stat]) => {
                    const cleanName = key.replace('challenge_', '').replace(/([A-Z])/g, ' $1').trim();
                    const displayValue = stat.per_min ? `${stat.per_min}/m` : stat.value.toLocaleString();
                    return `
                    <div class="stat-row">
                        <div class="stat-label-row">
                            <span>${cleanName} <strong>${displayValue}</strong></span>
                            <span style="color: ${stat.score > 80 ? 'var(--win)' : stat.score < 30 ? 'var(--loss)' : 'gold'}">${stat.score}%</span>
                        </div>
                        <div class="stat-bar-container"><div class="stat-bar-fill" style="width: 0%" data-width="${stat.score}%"></div></div>
                    </div>
                `}).join('')}
            </div>
        </div>
    `;

    const ctx = document.getElementById('radar-chart').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: displayLabels,
            datasets: [{ data: radarData, backgroundColor: 'rgba(99, 102, 241, 0.4)', borderColor: 'var(--primary)', borderWidth: 2, pointBackgroundColor: 'white' },
            { data: [50, 50, 50, 50, 50, 50], backgroundColor: 'transparent', borderColor: 'rgba(255, 255, 255, 0.1)', borderDash: [5, 5], borderWidth: 1, pointRadius: 0 }]
        },
        options: {
            scales: { r: { min: 0, max: 100, ticks: { display: false }, grid: { color: 'rgba(255,255,255,0.05)' }, angleLines: { color: 'rgba(255,255,255,0.1)' }, pointLabels: { color: '#94a3b8' } } },
            plugins: { legend: { display: false } }
        }
    });
    setTimeout(() => { document.querySelectorAll('.stat-bar-fill').forEach(bar => bar.style.width = bar.getAttribute('data-width')); }, 50);
}

UPDATE_BTN.onclick = async () => {
    UPDATE_BTN.disabled = true; UPDATE_BTN.innerText = 'PROCESSING...';
    try {
        const res = await fetch('http://localhost:8000/api/update', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'api_error') alert('⚠️ ' + data.message);
        else if (data.status === 'success') { filtersPopulated = false; await fetchProfile(1); }
        else alert('Error: ' + data.message);
    } catch (e) { alert('API Offline'); }
    finally { UPDATE_BTN.disabled = false; UPDATE_BTN.innerText = 'UPDATE MATCHES'; }
};

PREV_BTN.onclick = () => { if (currentPage > 1) fetchProfile(currentPage - 1); };
NEXT_BTN.onclick = () => { if (currentPage < profileData.total_pages) fetchProfile(currentPage + 1); };
CHAMP_FILTER.onchange = () => fetchProfile(1);
POS_FILTER.onchange = () => fetchProfile(1);
STAT_FILTER.onchange = () => renderMatches(profileData.matches);

CLOSE_BTN.onclick = () => MODAL.style.display = 'none';
window.onclick = (e) => { if (e.target == MODAL) MODAL.style.display = 'none'; };

fetchProfile();
