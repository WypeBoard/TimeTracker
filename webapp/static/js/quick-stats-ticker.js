/*
 * Client-side "ticker" for the Today page's Quick Stats row.
 *
 * This is purely cosmetic interpolation between real server renders: it
 * re-runs the same arithmetic already used by
 * webapp/services/today_service.py (_running_hours, _leave_projection)
 * against the baseline snapshot embedded by _quick_stats.html, so the
 * Today/Rem./Leave/Week figures keep advancing once a minute while a
 * session is open, with no network call.
 *
 * It is NOT a second source of truth: every real mutation (New
 * Session/Resume/Lunch/Stop) re-renders the fragment from the database as
 * before, and reloading the page always re-syncs to the server snapshot.
 * Known limitations (shared with the Python reference formulas): no
 * midnight-rollover handling, and the browser clock is assumed to match the
 * server's (true for this loopback-only, same-machine app).
 *
 * See features/standalone-web-app.md Manual Changes, 2026-11-27, "Quick
 * Stats client-side ticker".
 */
(function () {
    "use strict";

    function fmtHHMM(totalMinutes) {
        var m = ((totalMinutes % (24 * 60)) + 24 * 60) % (24 * 60);
        var h = Math.floor(m / 60);
        var mm = m % 60;
        return (h < 10 ? "0" : "") + h + ":" + (mm < 10 ? "0" : "") + mm;
    }

    function parseHHMM(s) {
        var parts = s.split(":");
        return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
    }

    function tick(data) {
        var now = new Date();
        var nowMinutes = now.getHours() * 60 + now.getMinutes();
        var startMinutes = parseHHMM(data.active_start);
        var activeHours = Math.max(0, (nowMinutes - startMinutes) / 60);

        var todayLogged = data.baseline_today + activeHours;
        var weekLogged = data.baseline_week + activeHours;
        var todayRemaining = Math.max(0, data.daily_target - todayLogged);
        var weekRemaining = Math.max(0, data.week_target - weekLogged);

        var todayEl = document.getElementById("qs-today");
        if (todayEl) {
            todayEl.textContent = todayLogged.toFixed(1) + "h / " + data.daily_target.toFixed(1) + "h";
        }
        var remEl = document.getElementById("qs-rem");
        if (remEl) {
            remEl.textContent = todayRemaining.toFixed(1) + "h / " + weekRemaining.toFixed(1) + "h";
        }
        var weekEl = document.getElementById("qs-week");
        if (weekEl) {
            weekEl.textContent = weekLogged.toFixed(1) + "h / " + data.week_target.toFixed(1) + "h";
        }

        var leaveEl = document.getElementById("qs-leave");
        if (leaveEl) {
            if (todayRemaining > 0) {
                var leaveMinutes = nowMinutes + Math.round(todayRemaining * 60);
                var html = "~" + fmtHHMM(leaveMinutes);
                if (data.lunch_excluded && !data.lunch_logged && data.lunch_duration) {
                    html += " / ~" + fmtHHMM(leaveMinutes + data.lunch_duration) +
                        ' <span class="text-secondary fs-5">(w/ lunch)</span>';
                }
                leaveEl.innerHTML = html;
            } else {
                leaveEl.innerHTML = "&mdash;";
            }
        }
    }

    // Exposed globally so the inline <script> at the bottom of
    // _quick_stats.html can call it both on first page load and after every
    // HTMX fragment swap (htmx re-runs inline <script> tags found in
    // swapped-in content by default).
    window.initQuickStatsTicker = function () {
        if (window._quickStatsTickerHandle) {
            clearInterval(window._quickStatsTickerHandle);
            window._quickStatsTickerHandle = null;
        }

        var rowEl = document.getElementById("quick-stats-row");
        if (!rowEl) {
            return;
        }
        var data;
        try {
            data = JSON.parse(rowEl.dataset.ticker || "{}");
        } catch (e) {
            return;
        }
        if (!data.active_start) {
            return; // No open session: nothing changes over time, server render stands.
        }

        tick(data); // Re-sync immediately, in case this runs mid-minute.
        window._quickStatsTickerHandle = setInterval(function () {
            tick(data);
        }, 60000); // Every minute, per the "update every minute" requirement.
    };
})();
