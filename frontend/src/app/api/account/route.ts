// BFF /api/account DELETE — Phase 2 Plan 02 (P2-D.3).
//
// Forwards DELETE to Flask DELETE /me which cascade-deletes profile +
// weight_logs + users + the Clerk auth record via the Python SDK
// (P2-A.5). Status codes pass through unchanged:
//   200: full success {ok, deleted: {...}}
//   401: unauthorized
//   502: clerk_delete_failed — Mongo data IS deleted; the client should
//        show a "data deleted but auth not" message and NOT sign the user
//        out (so they can retry from /settings)
//
// The handler does NOT call Clerk's signOut() here — the client component
// triggers useClerk().signOut() after seeing 200 (D-DELETE-CASCADE-SHAPE;
// clearer separation; the BFF stays a forwarder).

import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function DELETE() {
  return forwardToFlask("DELETE", "/me");
}
