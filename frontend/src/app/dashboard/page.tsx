import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

// Placeholder /dashboard route — Phase 1 / Slice A / WS-A.3.
// This is a SERVER COMPONENT (no "use client"). In Slice E it will fetch
// /api/me; for now it renders a static "loading…" card so size-limit can
// measure the bundle.
export default function DashboardPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>FitGH Dashboard</CardTitle>
          <CardDescription>Loading your account&hellip;</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Avatar>
            {/* Static SVG placeholder for the Rive avatar — Phase 5 wires the
                real .riv runtime + state machine. Avoiding @rive-app/* import
                here keeps the bundle under the 180 KB budget. */}
            <AvatarFallback aria-label="Avatar placeholder">FG</AvatarFallback>
          </Avatar>
          <p className="text-sm text-muted-foreground">
            The dashboard will fetch your profile once sign-in is wired in
            Slice D/E.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
