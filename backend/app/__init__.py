"""Flask app factory for FitGH.

Phase 1 Walking Skeleton — WS-B.2.

The factory wires Sentry FIRST (before any other init that could throw and miss
the event), then flask-cors with an explicit origin allowlist (SEC-03), then the
route blueprints. The blueprints are imported lazily inside create_app() so the
module can be imported without side effects (important for pytest collection).
"""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import init_sentry


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
        methods=["GET", "POST", "OPTIONS"],
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

    app.register_blueprint(health_bp)
    app.register_blueprint(me_bp)

    return app
