import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Hello FitGH</CardTitle>
          <CardDescription>
            Walking-skeleton home page. Phase 1 / Slice A / WS-A.2.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">
            shadcn/ui + Tailwind v4 + Next.js 15 App Router are wired. Sign-in/up
            and the dashboard land in subsequent slices.
          </p>
          <Button>Test</Button>
        </CardContent>
      </Card>
    </main>
  );
}
