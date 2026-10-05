// ======================================================
// Helper: safely update an element's text
// ======================================================

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


// ======================================================
// Load Dashboard
// ======================================================

async function loadDashboard() {

    console.log("Loading dashboard data...");

    try {

        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error(
                `Dashboard request failed: ${response.status}`
            );
        }

        const data = await response.json();

        console.log("Dashboard data:", data);

        window.latestDashboardData = data;


        // ==================================================
        // SUMMARY METRICS
        // ==================================================

        setText(
            "total-registrations",
            data.summary.total_registrations
        );

        setText(
            "total-referrals",
            data.summary.total_referrals
        );

        setText(
            "active-referrers",
            data.summary.active_referrers
        );

        setText(
            "referral-rate",
            `${data.summary.referral_rate}%`
        );


        // ==================================================
        // CAMPAIGN PROGRESS
        // ==================================================

        const registrations =
            data.summary.total_registrations;

        const remaining =
            data.summary.registrations_remaining;

        const progress =
            data.summary.goal_progress;


        setText(
            "progress-count",
            registrations
        );

        setText(
            "progress-remaining",
            `${remaining} registrations remaining`
        );

        setText(
            "progress-percentage",
            `${progress}%`
        );


        const progressBar =
            document.getElementById("progress-bar");

        if (progressBar) {

            progressBar.style.width =
                `${Math.min(progress, 100)}%`;
        }


        // ==================================================
        // GROWTH INTELLIGENCE
        // ==================================================

        const intelligence =
            data.growth_intelligence || {};

        const topReferrer =
            intelligence.top_referrer;

        const topCollege =
            intelligence.top_college;


        if (topReferrer) {

            setText(
                "top-referrer-name",
                topReferrer.name
            );

            setText(
                "top-referrer-college",
                topReferrer.college
            );

            setText(
                "top-referrer-count",
                topReferrer.referrals
            );

            setText(
                "top-referrer-label",
                topReferrer.referrals === 1
                    ? "referral"
                    : "referrals"
            );

        } else {

            setText(
                "top-referrer-name",
                "No referrers yet"
            );

            setText(
                "top-referrer-college",
                "—"
            );

            setText(
                "top-referrer-count",
                "0"
            );

            setText(
                "top-referrer-label",
                "referrals"
            );
        }


        if (topCollege) {

            setText(
                "top-college-name",
                topCollege.college
            );

            setText(
                "top-college-count",
                topCollege.registrations
            );

            setText(
                "top-college-label",
                topCollege.registrations === 1
                    ? "registration"
                    : "registrations"
            );

        } else {

            setText(
                "top-college-name",
                "No colleges yet"
            );

            setText(
                "top-college-count",
                "0"
            );

            setText(
                "top-college-label",
                "registrations"
            );
        }


        setText(
            "tied-colleges",
            intelligence.tied_colleges ?? 0
        );


        setText(
            "campaign-status",
            intelligence.campaign_status ||
            "Early Growth"
        );


        // ==================================================
        // INDIVIDUAL LEADERBOARD
        // ==================================================

        const individualLeaderboard =
            document.getElementById(
                "individual-leaderboard"
            );

        if (individualLeaderboard) {

            individualLeaderboard.innerHTML = "";

            const students =
                data.individual_leaderboard || [];


            if (students.length === 0) {

                individualLeaderboard.innerHTML = `
                    <div class="loading">
                        No registrations yet.
                    </div>
                `;

            } else {

                students.forEach((student) => {

                    const referralText =
                        student.referrals === 1
                            ? "referral"
                            : "referrals";


                    const row =
                        document.createElement("div");

                    row.className =
                        "leaderboard-row";


                    row.innerHTML = `
                        <div class="leaderboard-rank">
                            ${student.rank}
                        </div>

                        <div class="leaderboard-main">
                            <strong>
                                ${escapeHtml(student.name)}
                            </strong>

                            <span>
                                ${escapeHtml(student.college)}
                            </span>
                        </div>

                        <div class="leaderboard-score">
                            <strong>
                                ${student.referrals}
                            </strong>

                            <span>
                                ${referralText}
                            </span>
                        </div>
                    `;


                    individualLeaderboard.appendChild(row);
                });
            }
        }


        // ==================================================
        // COLLEGE LEADERBOARD
        // ==================================================

        const collegeLeaderboard =
            document.getElementById(
                "college-leaderboard"
            );


        if (collegeLeaderboard) {

            collegeLeaderboard.innerHTML = "";

            const colleges =
                data.college_leaderboard || [];


            if (colleges.length === 0) {

                collegeLeaderboard.innerHTML = `
                    <div class="loading">
                        No registrations yet.
                    </div>
                `;

            } else {

                colleges.forEach((college) => {

                    const registrationText =
                        college.registrations === 1
                            ? "registration"
                            : "registrations";


                    const row =
                        document.createElement("div");

                    row.className =
                        "leaderboard-row";


                    row.innerHTML = `
                        <div class="leaderboard-rank">
                            ${college.rank}
                        </div>

                        <div class="leaderboard-main">
                            <strong>
                                ${escapeHtml(
                                    college.college
                                )}
                            </strong>

                            <span>
                                College
                            </span>
                        </div>

                        <div class="leaderboard-score">
                            <strong>
                                ${college.registrations}
                            </strong>

                            <span>
                                ${registrationText}
                            </span>
                        </div>
                    `;


                    collegeLeaderboard.appendChild(row);
                });
            }
        }


        // ==================================================
        // LAST UPDATED
        // ==================================================

        setText(
            "last-updated",
            `Last updated: ${new Date().toLocaleTimeString()}`
        );


        console.log(
            "Dashboard data loaded successfully."
        );


    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );
    }
}


// ======================================================
// AI GROWTH COPILOT
// ======================================================

async function generateAIRecommendation() {

    console.log(
        "AI Growth Copilot button clicked"
    );


    const button =
        document.getElementById(
            "generate-ai-insight"
        );

    const title =
        document.getElementById(
            "ai-recommendation-title"
        );

    const recommendation =
        document.getElementById(
            "ai-recommendation"
        );

    const action =
        document.getElementById(
            "ai-action"
        );


    if (!button || !title || !recommendation || !action) {

        console.error(
            "AI Growth Copilot UI elements are missing."
        );

        return;
    }


    // ==================================================
    // Make sure campaign data is available
    // ==================================================

    if (!window.latestDashboardData) {

        await loadDashboard();
    }


    if (!window.latestDashboardData) {

        title.textContent =
            "Campaign data unavailable";

        recommendation.textContent =
            "We couldn't load the current campaign data.";

        action.textContent =
            "Please refresh the dashboard.";

        return;
    }


    // ==================================================
    // Loading state
    // ==================================================

    button.disabled = true;

    button.textContent =
        "Generating recommendation...";


    title.textContent =
        "Analyzing campaign performance...";


    recommendation.textContent =
        "Gemini is analyzing registrations, referrals and college performance.";


    action.textContent =
        "This may take a few seconds. Please wait...";


    try {

        console.log(
            "Sending request to /api/ai-growth"
        );


        const response =
            await fetch(
                "/api/ai-growth",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(
                        window.latestDashboardData
                    )
                }
            );


        console.log(
            "AI response status:",
            response.status
        );


        const data =
            await response.json();


        console.log(
            "AI response:",
            data
        );


        // ==================================================
        // SUCCESS
        // ==================================================

        if (
            response.ok &&
            data.success
        ) {

            title.textContent =
                data.title ||
                "Growth recommendation";


            recommendation.textContent =
                data.recommendation ||
                "No recommendation returned.";


            action.textContent =
                data.action ||
                "No action returned.";


            button.textContent =
                "Generate New Recommendation →";


            return;
        }


        // ==================================================
        // FAILURE
        // ==================================================

        throw new Error(
            data.error ||
            "The AI service could not generate a recommendation."
        );


    } catch (error) {

        console.error(
            "AI Growth Copilot error:",
            error
        );


        title.textContent =
            "AI recommendation temporarily unavailable";


        recommendation.textContent =
            "The AI service encountered a temporary problem.";


        action.textContent =
            error.message ||
            "Please try again in a moment.";


        button.textContent =
            "Try Again →";


    } finally {

        button.disabled = false;
    }
}


// ======================================================
// HTML ESCAPING
// ======================================================

function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}


// ======================================================
// EVENT LISTENERS
// ======================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "Dashboard JavaScript loaded"
        );


        loadDashboard();


        // --------------------------------------------------
        // AI button
        // --------------------------------------------------

        const aiButton =
            document.getElementById(
                "generate-ai-insight"
            );


        if (aiButton) {

            console.log(
                "AI Growth Copilot button found"
            );


            aiButton.addEventListener(
                "click",
                generateAIRecommendation
            );

        } else {

            console.error(
                "AI Growth Copilot button NOT found"
            );
        }


        // --------------------------------------------------
        // Refresh button
        // --------------------------------------------------

        const refreshButton =
            document.getElementById(
                "refresh-button"
            );


        if (refreshButton) {

            refreshButton.addEventListener(
                "click",
                loadDashboard
            );
        }
    }
);