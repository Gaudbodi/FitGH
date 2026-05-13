"""Flask app factory for FitGH.

Phase 1 Walking Skeleton — WS-B.2.

The factory wires Sentry FIRST (before any other init that could throw and miss
the event), then flask-cors with an explicit origin allowlist (SEC-03), then the
route blueprints. The blueprints are imported lazily inside create_app() so the
module can be imported without side effects (important for pytest collection).
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load .env.local (real secrets, gitignored) then .env from the backend dir.
# python-dotenv does NOT override pre-existing env vars, so Render-injected env
# in production and pytest monkeypatched env in tests both take precedence.
# In local dev where neither is set, this picks up the file.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env.local")
load_dotenv(_BACKEND_DIR / ".env")

from flask import Flask  # noqa: E402
from flask_cors import CORS  # noqa: E402

from app.config import Config  # noqa: E402
from app.extensions import init_sentry  # noqa: E402


def create_app(config: Config | None = None) -> Flask:
    """Construct the FitGH Flask application.

    Parameters
    ----------
    config : Config | None
        Optional config override (used by tests). Defaults to Config() which
        reads from environment.
    """
    cfg = config or Config()

    # 1) Sentry must be initialized BEFORE the Flask app so the FlaskIntegration
    #    can hook the WSGI middleware. send_default_pii=False is the safety net;
    #    before_send (in extensions.scrub) is the explicit scrubber.
    init_sentry(cfg)

    app = Flask(__name__)
    app.config["FITGH"] = cfg

    # 2) CORS with EXPLICIT origin allowlist (SEC-03). NEVER '*' with credentials.
    #    supports_credentials=False because the cross-origin caller is the BFF
    #    forwarding a Bearer JWT, not a browser sending cookies.
    CORS(
        app,
        resources={r"/*": {"origins": cfg.CORS_ALLOWED_ORIGINS}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    )

    # 3) Register blueprints. Imported here (not at module top) so that import-
    #    time side effects in app.db (singleton MongoClient) only fire when an
    #    app is actually being constructed — not on `import app`.
    #
    # Note: the Clerk svix webhook blueprint was dropped in the 2026-05-12
    # Render-only rewrite (WS-E.1). User-creation now happens via
    # sync-on-demand inside /me (see app/routes/me.py).
    from app.routes.health import bp as health_bp
    from app.routes.me import bp as me_bp
    from app.routes.profile import bp as profile_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(profile_bp)

    # Phase 2 — /weights blueprint (registered here, route module created in
    # Task P2-A.4). Import is conditional on the module existing so the
    # factory stays import-safe during interleaved development.
    try:
        from app.routes.weights import bp as weights_bp
        app.register_blueprint(weights_bp)
    except ImportError:
        pass

    # Phase 3 — /foods (P3-B.1) and /meals (P3-B.2..P3-B.4) blueprints.
    # Imports are conditional during interleaved development; once both
    # modules land, every Render redeploy boots with them.
    try:
        from app.routes.foods import bp as foods_bp
        app.register_blueprint(foods_bp)
    except ImportError:
        pass
    try:
        from app.routes.meals import bp as meals_bp
        app.register_blueprint(meals_bp)
    except ImportError:
        pass

    return app
