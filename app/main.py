from pathlib import Path
import os
import secrets
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_connection, init_db


# ============================================================
# PROJECT PATHS / ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Campus AI Growth Hub",
    description="AI-powered growth campaign dashboard for the workshop.",
    version="1.0.0",
)


# ============================================================
# STATIC FILES / TEMPLATES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "app" / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "app" / "templates"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# REFERRAL CODE GENERATOR
# ============================================================

def generate_referral_code():
    return secrets.token_hex(4).upper()


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def home(request: Request):

    ref = request.query_params.get("ref", "")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "ref": ref
        }
    )


# ============================================================
# REGISTRATION
# ============================================================

@app.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    college: str = Form(...),
    referred_by: str = Form("")
):

    conn = get_connection()

    # Check whether email already exists
    existing = conn.execute(
        """
        SELECT id
        FROM students
        WHERE email = ?
        """,
        (email.strip().lower(),)
    ).fetchone()

    if existing:

        conn.close()

        return RedirectResponse(
            url="/success?existing=1",
            status_code=303
        )

    # Generate unique referral code
    referral_code = generate_referral_code()

    while conn.execute(
        """
        SELECT id
        FROM students
        WHERE referral_code = ?
        """,
        (referral_code,)
    ).fetchone():

        referral_code = generate_referral_code()

    # Validate referring code
    clean_referrer = referred_by.strip() or None

    if clean_referrer:

        referrer_exists = conn.execute(
            """
            SELECT id
            FROM students
            WHERE referral_code = ?
            """,
            (clean_referrer,)
        ).fetchone()

        if not referrer_exists:
            clean_referrer = None

    # Insert student
    conn.execute(
        """
        INSERT INTO students
        (
            name,
            email,
            college,
            referral_code,
            referred_by
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            name.strip(),
            email.strip().lower(),
            college.strip(),
            referral_code,
            clean_referrer
        )
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/success?code={referral_code}",
        status_code=303
    )


# ============================================================
# SUCCESS PAGE
# ============================================================

@app.get("/success")
def success(request: Request):

    code = request.query_params.get("code", "")
    existing = request.query_params.get("existing", "")

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "code": code,
            "existing": existing
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# DASHBOARD API
# ============================================================

@app.get("/api/dashboard")
def dashboard_api():

    conn = get_connection()

    # --------------------------------------------------------
    # Total registrations
    # --------------------------------------------------------

    total_registrations = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM students
        """
    ).fetchone()["count"]

    # --------------------------------------------------------
    # Total referrals
    # --------------------------------------------------------

    total_referrals = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM students
        WHERE referred_by IS NOT NULL
        AND referred_by != ''
        """
    ).fetchone()["count"]

    # --------------------------------------------------------
    # Active referrers
    # --------------------------------------------------------

    active_referrers = conn.execute(
        """
        SELECT COUNT(DISTINCT referred_by) AS count
        FROM students
        WHERE referred_by IS NOT NULL
        AND referred_by != ''
        """
    ).fetchone()["count"]

    # --------------------------------------------------------
    # Referral rate
    # --------------------------------------------------------

    referral_rate = 0

    if total_registrations > 0:

        referral_rate = round(
            (total_referrals / total_registrations) * 100,
            1
        )

    # --------------------------------------------------------
    # Campaign goal
    # --------------------------------------------------------

    campaign_goal = 500

    registrations_remaining = max(
        campaign_goal - total_registrations,
        0
    )

    goal_progress = round(
        (total_registrations / campaign_goal) * 100,
        1
    )

    # --------------------------------------------------------
    # Individual leaderboard
    # --------------------------------------------------------

    individual_rows = conn.execute(
        """
        SELECT
            s.id,
            s.name,
            s.college,
            s.referral_code,
            COUNT(r.id) AS referrals
        FROM students s
        LEFT JOIN students r
            ON r.referred_by = s.referral_code
        GROUP BY
            s.id,
            s.name,
            s.college,
            s.referral_code
        ORDER BY
            referrals DESC,
            s.created_at ASC
        """
    ).fetchall()

    individual_leaderboard = []

    for rank, row in enumerate(
        individual_rows,
        start=1
    ):

        individual_leaderboard.append(
            {
                "rank": rank,
                "name": row["name"],
                "college": row["college"],
                "referral_code": row["referral_code"],
                "referrals": row["referrals"]
            }
        )

    # --------------------------------------------------------
    # College leaderboard
    # --------------------------------------------------------

    college_rows = conn.execute(
        """
        SELECT
            college,
            COUNT(*) AS registrations
        FROM students
        GROUP BY college
        ORDER BY
            registrations DESC,
            college ASC
        """
    ).fetchall()

    college_leaderboard = []

    for rank, row in enumerate(
        college_rows,
        start=1
    ):

        college_leaderboard.append(
            {
                "rank": rank,
                "college": row["college"],
                "registrations": row["registrations"]
            }
        )

    # --------------------------------------------------------
    # Top referrer
    # --------------------------------------------------------

    top_referrer = None

    if individual_leaderboard:

        top = individual_leaderboard[0]

        if top["referrals"] > 0:

            top_referrer = {
                "name": top["name"],
                "college": top["college"],
                "referrals": top["referrals"]
            }

    # --------------------------------------------------------
    # Top college / ties
    # --------------------------------------------------------

    top_college = None
    tied_colleges = 0

    if college_leaderboard:

        highest_registration_count = (
            college_leaderboard[0]["registrations"]
        )

        tied_colleges = sum(
            1
            for college in college_leaderboard
            if college["registrations"]
            == highest_registration_count
        )

        top_college = {
            "college": college_leaderboard[0]["college"],
            "registrations": highest_registration_count
        }

    # --------------------------------------------------------
    # Campaign status
    # --------------------------------------------------------

    if goal_progress >= 100:

        campaign_status = "Goal Reached"

    elif goal_progress >= 75:

        campaign_status = "Strong Growth"

    elif goal_progress >= 40:

        campaign_status = "Growing"

    elif goal_progress >= 10:

        campaign_status = "Building Momentum"

    else:

        campaign_status = "Early Growth"

    conn.close()

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "summary": {
            "total_registrations": total_registrations,
            "total_referrals": total_referrals,
            "active_referrers": active_referrers,
            "referral_rate": referral_rate,
            "campaign_goal": campaign_goal,
            "registrations_remaining": registrations_remaining,
            "goal_progress": goal_progress
        },

        "growth_intelligence": {
            "top_referrer": top_referrer,
            "top_college": top_college,
            "tied_colleges": tied_colleges,
            "campaign_status": campaign_status
        },

        "individual_leaderboard":
            individual_leaderboard,

        "college_leaderboard":
            college_leaderboard
    }


# ============================================================
# AI GROWTH COPILOT
# ============================================================

@app.post("/api/ai-growth")
def ai_growth(request: Request):

    try:

        import google.genai

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:

            return {
                "success": False,
                "error": "GOOGLE_API_KEY is not configured."
            }

        # ----------------------------------------------------
        # REQUEST DATA
        # ----------------------------------------------------

        import asyncio

        # FastAPI's Request object is async, but this endpoint
        # is intentionally kept simple and synchronous elsewhere.
        # Read the request body safely.
        body = asyncio.run(request.json())

        # ----------------------------------------------------
        # CREATE GEMINI CLIENT
        # ----------------------------------------------------

        client = google.genai.Client(
            api_key=api_key
        )

        # ----------------------------------------------------
        # AI PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are the AI Growth Copilot for a student workshop campaign.

WORKSHOP:
"Build Your First AI Project in 60 Minutes"

CAMPAIGN GOAL:
Get 500 final-year engineering students registered within 7 days.

Your job is to analyze the CURRENT campaign data and recommend
the single most useful NEXT growth action.

CURRENT CAMPAIGN DATA:
{body}

============================================================
CORE RULES
============================================================

1. USE ONLY THE DATA PROVIDED.

Use the actual campaign numbers in the supplied data.

Do not invent:
- registrations
- referrals
- conversion rates
- students
- colleges
- campaign results
- experiments
- performance metrics

2. DO NOT INVENT CAMPAIGN CAPABILITIES.

Do not claim that the campaign has:
- rewards
- prizes
- discounts
- starter kits
- project templates
- exclusive access
- priority access
- certificates
- paid advertising budget
- special workshop benefits
- ambassador programs
- other incentives

unless those capabilities are explicitly present in the
campaign data provided to you.

If an incentive or capability is not provided, do not promise it.

3. DO NOT INVENT BUDGET USAGE.

The campaign has a limited budget.

Prefer practical low-cost or zero-cost actions.

Do not recommend spending money unless the supplied campaign
data explicitly supports a paid experiment.

4. MATCH THE STRATEGY TO THE CAMPAIGN STAGE.

Consider:
- total registrations
- campaign goal
- registrations remaining
- goal progress
- total referrals
- active referrers
- referral rate
- top referrer
- top college
- campaign status

Examples:

If registrations are very low:
focus on activating initial registrants, campus communities,
peer sharing, ambassadors, and awareness.

If referral performance is strong:
consider scaling the existing referral mechanism.

If referral performance is weak:
identify the referral/share mechanism as a potential weakness
and recommend improving or testing it rather than blindly
scaling it.

If the campaign is close to the goal:
focus on converting the remaining registrations using the
strongest demonstrated channel.

5. DO NOT BLINDLY REPEAT THE SAME STRATEGY.

The recommendation must respond to the current numbers.

A strong referral rate and a weak referral rate should lead
to meaningfully different recommendations.

6. BE PRACTICAL.

Recommend something the campaign team can realistically do
immediately using the channels and capabilities supported
by the supplied campaign information.

7. DO NOT OVERSTATE CAUSALITY.

If the data only shows correlation or early evidence, describe
it as evidence or a signal rather than proof that a channel
caused registrations.

============================================================
PREFERRED LOW-COST CHANNELS
============================================================

When appropriate, consider:

- student referrals
- college ambassadors
- WhatsApp communities
- peer-to-peer sharing
- campus groups
- organic Instagram content
- organic LinkedIn content
- direct student outreach

These are possible channels, not guaranteed campaign features.
Do not claim that a specific channel is already active unless
the supplied data says so.

============================================================
OUTPUT FORMAT
============================================================

Return EXACTLY these three sections and nothing else:

TITLE:
A short growth recommendation title.

RECOMMENDATION:
A concise explanation of what the campaign should do next
and why. Use the actual campaign data.

ACTION:
One specific action the team can take immediately.

Do not add:
- greetings
- markdown headings
- bullet lists
- extra sections
- notes
- disclaimers
- invented incentives
- invented campaign capabilities
"""

        # ----------------------------------------------------
        # GEMINI RETRY CONFIGURATION
        # ----------------------------------------------------

        max_attempts = 3

        # Short exponential backoff:
        # attempt 1 -> immediate
        # attempt 2 -> 2 seconds
        # attempt 3 -> 4 seconds
        retry_delays = [0, 2, 4]

        last_error = None

        # ----------------------------------------------------
        # GEMINI REQUEST WITH RETRIES
        # ----------------------------------------------------

        for attempt in range(1, max_attempts + 1):

            try:

                print(
                    f"AI Growth Copilot attempt "
                    f"{attempt}/{max_attempts}..."
                )

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )

                text = (
                    getattr(response, "text", None)
                    or ""
                ).strip()

                if not text:

                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                print(
                    "AI Growth Copilot generated "
                    "a recommendation successfully."
                )

                # ------------------------------------------------
                # PARSE RESPONSE
                # ------------------------------------------------

                title = ""
                recommendation = ""
                action = ""

                current_section = None

                for raw_line in text.splitlines():

                    line = raw_line.strip()

                    if not line:
                        continue

                    upper_line = line.upper()

                    if upper_line.startswith("TITLE:"):

                        current_section = "title"

                        title = line[
                            len("TITLE:")
                        ].strip()

                        continue

                    if upper_line.startswith(
                        "RECOMMENDATION:"
                    ):

                        current_section = "recommendation"

                        recommendation = line[
                            len("RECOMMENDATION:")
                        ].strip()

                        continue

                    if upper_line.startswith(
                        "ACTION:"
                    ):

                        current_section = "action"

                        action = line[
                            len("ACTION:")
                        ].strip()

                        continue

                    if current_section == "title":

                        title += " " + line

                    elif current_section == "recommendation":

                        recommendation += " " + line

                    elif current_section == "action":

                        action += " " + line

                # ------------------------------------------------
                # CLEAN RESPONSE TEXT
                # ------------------------------------------------

                title = " ".join(title.split()).strip()

                recommendation = (
                    " ".join(recommendation.split()).strip()
                )

                action = " ".join(action.split()).strip()

                # ------------------------------------------------
                # FALLBACK IF GEMINI FORMAT IS IMPERFECT
                # ------------------------------------------------

                if not title:

                    title = "Growth recommendation"

                if not recommendation:

                    recommendation = text.strip()

                if not action:

                    action = (
                        "Use this recommendation as the "
                        "next campaign growth experiment."
                    )

                return {
                    "success": True,
                    "title": title,
                    "recommendation": recommendation,
                    "action": action
                }

            except Exception as error:

                last_error = error

                error_text = str(error)

                print(
                    f"AI Growth Copilot error on "
                    f"attempt {attempt}: {error_text}"
                )

                # ------------------------------------------------
                # DO NOT RETRY QUOTA ERRORS
                # ------------------------------------------------

                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED"
                    in error_text.upper()
                    or "quota" in error_text.lower()
                ):

                    print(
                        "Gemini quota/rate limit detected. "
                        "Not retrying automatically."
                    )

                    return {
                        "success": False,
                        "error": (
                            "Gemini API quota or rate limit "
                            "has been reached. Please wait "
                            "before trying again."
                        ),
                        "retryable": False
                    }

                # ------------------------------------------------
                # RETRY TEMPORARY SERVER ERRORS
                # ------------------------------------------------

                retryable = any(
                    code in error_text
                    for code in [
                        "503",
                        "500",
                        "502",
                        "504",
                        "UNAVAILABLE",
                        "INTERNAL",
                        "DEADLINE_EXCEEDED"
                    ]
                )

                if (
                    retryable
                    and attempt < max_attempts
                ):

                    delay = retry_delays[attempt]

                    print(
                        f"Temporary Gemini error. "
                        f"Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)

                    continue

                # No more retries
                break

        # --------------------------------------------------------
        # FINAL FAILURE
        # --------------------------------------------------------

        print(
            "AI Growth Copilot failed after "
            f"{max_attempts} attempts."
        )

        return {
            "success": False,
            "error": (
                "The AI service is temporarily unavailable. "
                "The system automatically retried the request. "
                "Please try again in a moment."
            ),
            "retryable": True
        }

    except ImportError:

        return {
            "success": False,
            "error": (
                "The google-genai package is not installed."
            ),
            "retryable": False
        }

    except Exception as error:

        print(
            f"AI Growth Copilot unexpected error: "
            f"{error}"
        )

        return {
            "success": False,
            "error": (
                "The AI service could not generate "
                "a recommendation right now."
            ),
            "retryable": True
        }


# ============================================================
# DASHBOARD PAGE
# ============================================================

@app.get("/dashboard")
def dashboard(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={}
    )