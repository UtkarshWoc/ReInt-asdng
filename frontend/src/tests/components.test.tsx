import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { KpiCard } from "../components/ui/KpiCard";
import { DeliveryDatePicker } from "../components/controls/DeliveryDatePicker";
import { CutoffSelector } from "../components/controls/CutoffSelector";

describe("UI Components & Controls", () => {
  it("renders KpiCard with value, unit, and label", () => {
    render(
      <KpiCard
        label="Expected Wind"
        value="12,500"
        unit="MW"
        subtitle="Delivery period peak"
        tooltip="Peak wind forecast"
      />
    );
    expect(screen.getByText("Expected Wind")).toBeInTheDocument();
    expect(screen.getByText("12,500")).toBeInTheDocument();
    expect(screen.getByText("MW")).toBeInTheDocument();
    expect(screen.getByText("Delivery period peak")).toBeInTheDocument();
  });

  it("handles DeliveryDatePicker date changes and previous/next navigation", () => {
    const dates = ["2026-01-02", "2026-01-03", "2026-01-04"];
    const handleChange = vi.fn();

    render(
      <DeliveryDatePicker
        selectedDate="2026-01-03"
        availableDates={dates}
        onChange={handleChange}
      />
    );

    const prevButton = screen.getByLabelText("Previous day");
    const nextButton = screen.getByLabelText("Next day");

    fireEvent.click(prevButton);
    expect(handleChange).toHaveBeenCalledWith("2026-01-02");

    fireEvent.click(nextButton);
    expect(handleChange).toHaveBeenCalledWith("2026-01-04");
  });

  it("handles CutoffSelector changes", () => {
    const handleChange = vi.fn();
    render(<CutoffSelector cutoff="09:00" onChange={handleChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "07:30" } });
    expect(handleChange).toHaveBeenCalledWith("07:30");
  });
});
