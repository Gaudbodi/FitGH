// FoodSearch — Phase 3 Plan 03 (P3-C.2).
//
// Client component. Wraps the shadcn Command primitive (cmdk under the
// hood). Debounces query to /api/foods, renders ranked results, fires
// onSelect with the chosen GhanaFood when an item is clicked.

"use client";

import * as React from "react";

import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import type { GhanaFoodResponse } from "@/lib/zod-schemas";

interface FoodSearchProps {
  onSelect: (food: GhanaFoodResponse) => void;
}

export function FoodSearch({ onSelect }: FoodSearchProps) {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<GhanaFoodResponse[]>([]);
  const [loading, setLoading] = React.useState(false);

  // Debounce 200 ms before firing the network request. Tracks the active
  // query in a ref so a stale response cannot overwrite a fresher one.
  const latestQueryRef = React.useRef<string>("");

  React.useEffect(() => {
    latestQueryRef.current = query;
    const trimmed = query.trim();
    const handle = setTimeout(async () => {
      setLoading(true);
      try {
        const url = trimmed
          ? `/api/foods?q=${encodeURIComponent(trimmed)}&limit=10`
          : "/api/foods?limit=10";
        const res = await fetch(url, { cache: "no-store" });
        if (!res.ok) {
          setResults([]);
          return;
        }
        const body = (await res.json()) as { foods: GhanaFoodResponse[] };
        // Only commit results if this response matches the latest query.
        if (latestQueryRef.current === query) {
          setResults(body.foods ?? []);
        }
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [query]);

  return (
    // shouldFilter=false — server already ranks the results; cmdk's
    // built-in fuzzy filter would re-order them.
    <Command shouldFilter={false} className="border border-input/40">
      <CommandInput
        placeholder="Search: jollof, banku, waakye..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {loading && (
          <div className="px-3 py-2 text-xs text-muted-foreground">
            Searching...
          </div>
        )}
        {!loading && results.length === 0 && (
          <CommandEmpty>No foods match.</CommandEmpty>
        )}
        {results.map((food) => {
          const firstPortion = food.portion_defaults[0];
          return (
            <CommandItem
              key={food.food_id}
              value={food.food_id}
              onSelect={() => {
                onSelect(food);
                setQuery("");
              }}
            >
              <div className="flex flex-1 items-center justify-between gap-3">
                <div className="flex flex-col">
                  <span className="font-medium">{food.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {firstPortion.label} ({firstPortion.grams} g)
                  </span>
                </div>
                <span className="tabular-nums text-xs text-muted-foreground">
                  {Math.round(food.kcal_per_100g)} kcal / 100 g
                </span>
              </div>
            </CommandItem>
          );
        })}
      </CommandList>
    </Command>
  );
}
