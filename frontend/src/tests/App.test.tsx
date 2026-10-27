import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "../App";

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("App Navigation & Tabs", () => {
  it("renders header and toggles between Forecast and Accuracy tabs", () => {
    renderWithClient(<App />);
    expect(screen.getByText("UK Wind Day-Ahead Decision Support")).toBeInTheDocument();

    const forecastTab = screen.getByRole("button", { name: /Forecast at Decision/i });
    const accuracyTab = screen.getByRole("button", { name: /Forecast Accuracy/i });

    expect(forecastTab).toBeInTheDocument();
    expect(accuracyTab).toBeInTheDocument();

    // Click Accuracy tab
    fireEvent.click(accuracyTab);
    expect(screen.getByText("Quantitative Accuracy & Risk Sizing")).toBeInTheDocument();

    // Click back to Forecast tab
    fireEvent.click(forecastTab);
    expect(screen.getByText("Day-Ahead Decision Window")).toBeInTheDocument();
  });
});
