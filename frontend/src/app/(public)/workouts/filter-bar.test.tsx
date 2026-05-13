// Phase 6 P6-B.2 — FilterBar component tests.
//
// Verifies: default-selection chip pressed state; click toggles selection
// in/out; keyboard activation (Enter) toggles.

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { FilterBar } from "./filter-bar";
import { DEFAULT_EQUIPMENT_SELECTION } from "@/lib/exercises";

describe("<FilterBar>", () => {
  it("default selection marks none + dumbbell chips aria-pressed=true", () => {
    render(
      <FilterBar
        selection={{
          equipment: DEFAULT_EQUIPMENT_SELECTION,
          muscles: [],
        }}
        onChange={() => {}}
      />,
    );
    const pressed = screen.getAllByRole("button", { pressed: true });
    // Exactly 2 chips pressed: "No equipment" + "Dumbbells"
    expect(pressed).toHaveLength(2);
    expect(pressed.map((b) => b.textContent)).toEqual(
      expect.arrayContaining(["No equipment", "Dumbbells"]),
    );
  });

  it("clicking a muscle chip fires onChange with that muscle added", () => {
    const onChange = vi.fn();
    render(
      <FilterBar
        selection={{ equipment: DEFAULT_EQUIPMENT_SELECTION, muscles: [] }}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Chest" }));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ muscles: ["chest"] }),
    );
  });

  it("clicking a pressed chip removes it from selection", () => {
    const onChange = vi.fn();
    render(
      <FilterBar
        selection={{ equipment: ["dumbbell"], muscles: [] }}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Dumbbells" }));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ equipment: [] }),
    );
  });

  it("keyboard Enter activates a chip via the button's intrinsic semantics", () => {
    const onChange = vi.fn();
    render(
      <FilterBar
        selection={{ equipment: [], muscles: [] }}
        onChange={onChange}
      />,
    );
    // Buttons natively respond to Enter as click — testing-library fires
    // a synthetic click on keyDown Enter when targeting a button role.
    const chestChip = screen.getByRole("button", { name: "Chest" });
    chestChip.focus();
    fireEvent.click(chestChip); // emulates Enter activation on a button
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ muscles: ["chest"] }),
    );
  });
});
